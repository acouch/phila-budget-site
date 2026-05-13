"""Shared logic for the budget-in-brief PDF parsers."""

import csv
import re
from collections import Counter
from pathlib import Path

import pdfplumber

HERE = Path(__file__).resolve().parent
TAGGING_YML = HERE / "tagging.yml"
DEFAULT_TAG = "Government Operations"

CSV_FIELDNAMES = [
    "fiscal_year",
    "fund",
    "department",
    "tag_peoples_budget",
    "class",
    "total",
]


# ---------------------------------------------------------------------------
# People's Budget tagging
# ---------------------------------------------------------------------------

def load_peoples_budget_tags(path=TAGGING_YML):
    """Parse the `peoples_budget:` section of tagging.yml into a dept->tag dict."""
    dept_to_tag = {}
    current_tag = None
    in_section = False
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" "):
            in_section = line.strip().rstrip(":") == "peoples_budget"
            current_tag = None
            continue
        if not in_section:
            continue
        stripped = line.strip()
        if line.startswith("    -"):
            dept = stripped[1:].strip()
            if dept and current_tag:
                dept_to_tag[dept] = current_tag
        elif line.startswith("  ") and stripped.endswith(":"):
            current_tag = stripped[:-1].strip()
        elif line.startswith("  ") and stripped.endswith("[]"):
            current_tag = None
    return dept_to_tag


_DEPT_TAGS = load_peoples_budget_tags()


def tag_for(dept):
    return _DEPT_TAGS.get(dept, DEFAULT_TAG)


# ---------------------------------------------------------------------------
# Department name normalization (other-funds parsers)
# ---------------------------------------------------------------------------

# Aligns the appropriations-ordinance ("Department Of X") names with the names
# the general-fund parser emits, so the same department in different funds
# collapses to one row in downstream pivots.
# Keys are written in the canonical form produced by normalize_dept:
# joining words ("of", "and", "the", "to", "for") lowercase, hyphens with
# single-space padding on both sides, em/en dashes collapsed to "-".
DEPT_ALIASES = {
    "Auditing Department": "Auditing (City Controller)",
    "Board of Pensions and Retirement": "Sinking Fund Commission (Debt Service)",
    "Board of Trustees of the Free Library of Philadelphia": "Free Library",
    "Department of Aviation": "Aviation",
    "Department of Fleet Services": "Fleet Services",
    "Department of Fleet Services - Vehicle Purchase": "Fleet Services -Vehicle Lease/Purch.",
    "Department of Human Services": "Human Services",
    "Department of Human Services - Office of Homeless Services": "Office of Homeless Services",
    "Department of Licenses and Inspections": "Licenses & Inspection",
    "Department of Parks and Recreation": "Parks and Recreation",
    "Department of Planning and Development": "Planning and Development",
    "Department of Public Health": "Public Health",
    "Department of Public Health - Office of Behavioral Health and Intellectual Disability": "Office of Behavioral Health and Intellectual disAbility",
    "Department of Public Health - State Payment": "Public Health",
    "Department of Public Property": "Public Property",
    "Department of Public Property - Utilities": "Public Property-Utilities",
    "Department of Revenue": "Revenue",
    "Department of Revenue - Sinking Fund Commission": "Sinking Fund Commission (Debt Service)",
    "Department of Sanitation": "Sanitation",
    "Department of Streets": "Streets",
    "Department of Streets - Sanitation": "Sanitation",
    "Director of Commerce": "Commerce",
    "Director of Finance": "Finance",
    "Director of Finance - Budget Stabilization": "Finance-Budget Stabilization",
    "Director of Finance - Community Development Block Grant - to Be Allocated": "Finance",
    "Director of Finance - Fringe Benefits": "Finance-Employee Benefits",
    "Director of Finance - Indemnities": "Finance-Indemnities",
    "Director of Finance - Provision for Other Grants": "Finance",
    "Fire Department": "Fire",
    "First Judicial District of Pennsylvania": "First Judicial District",
    "Law Department": "Law",
    "Mayor - Office of Arts, Culture and the Creative Economy": "Office of Arts and Culture and the Creative Economy",
    "Mayor - Office of Arts Culture and the Creative Economy": "Office of Arts and Culture and the Creative Economy",
    "Mayor - Office of Community Empowerment and Opportunity": "Office of Community Empowerment and Opportunity",
    "Mayor - Office of Education": "Office of Education",
    "Mayor - Office of Innovation and Technology": "Office of Innovation and Technology",
    "Office of Public Safety": "Office of Public Safety",
    "Office of Sustainability": "Office of Sustainability",
    "Register of Wills": "Register of Wills",
    "Police Department": "Police",
    "Procurement Department": "Procurement",
    "Water Department": "Water",
    "Water Department - Philadelphia Water, Sewer, and Stormwater Rate Board": "Water",
    "Council - Veterans Advisory Commission": "City Council",
}

_JOINER_WORDS = {"of", "and", "the", "to", "for"}


def normalize_dept(name):
    name = name.replace("–", "-").replace("—", "-")
    # Canonicalize hyphen spacing so "X-Y", "X -Y", "X- Y", "X - Y" all match.
    name = re.sub(r"\s*-\s*", " - ", name)
    name = " ".join(name.split())
    # Lowercase common joining words so .title()'d names match the
    # general-fund parser's "Office of Public Safety" style.
    parts = name.split(" ")
    parts = [
        w if i == 0 or w.lower() not in _JOINER_WORDS else w.lower()
        for i, w in enumerate(parts)
    ]
    name = " ".join(parts)
    return DEPT_ALIASES.get(name, name)


# ---------------------------------------------------------------------------
# General-fund (obligation history) parser
# ---------------------------------------------------------------------------

GENERAL_FUND_CLASS_NAMES = [
    "Pers. Svcs.-Emp.Benefits",
    "Advances and Other Misc. Payments",
    "Contrib., Indemnities & Taxes",
    "Materials, Supplies & Equip.",
    "Payments to Other Funds",
    "Purchase of Services",
    "Personal Services",
    "Debt Service",
]

_GENERAL_FUND_SKIP_PATTERNS = [
    re.compile(p) for p in [
        r"^General Fund$",
        r"^Obligation History$",
        r"^Fiscal Years \d+ - \d+$",
        r"^Fiscal Year",
        r"^\d{4}(?:\s+\d{4}){2,}$",
        r"^Actual Increase",
        r"^Department / Agency",
        r"^\(\d+\)",
        r"^\d+\s*$",
        r"^Total, General Fund",
    ]
]


def _gf_should_skip(line):
    return any(p.match(line) for p in _GENERAL_FUND_SKIP_PATTERNS)


def _gf_parse_number(s):
    s = s.strip()
    negative = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[(),]", "", s).replace(",", "")
    try:
        return -int(s) if negative else int(s)
    except ValueError:
        return None


def _gf_extract_numbers(text):
    matches = re.findall(r"\([\d,]+\)|[\d,]+", text)
    return [n for m in matches if (n := _gf_parse_number(m)) is not None]


def parse_general_fund(pdf_path, fiscal_years, start_page, end_page):
    """Extract General Fund obligation-history rows from a budget-in-brief PDF.

    `fiscal_years` is a list of (label, filename, number_index, year) tuples;
    `number_index` is the 0-based offset into the row's numeric columns.
    Pages are 0-indexed inclusive. Each emitted dict carries a "label" key
    used by write_general_fund_csvs() to split rows per output file.
    """
    rows = []
    fund = "General Fund"
    min_numbers = max(idx for _, _, idx, _ in fiscal_years) + 1

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx in range(start_page, end_page + 1):
            page = pdf.pages[page_idx]
            text = page.extract_text()
            if not text:
                continue

            current_dept = None
            dept_buffer = []

            for line in text.split("\n"):
                stripped = line.strip()
                if not stripped or _gf_should_skip(stripped):
                    continue

                matched_class = next(
                    (cls for cls in GENERAL_FUND_CLASS_NAMES if stripped.startswith(cls)),
                    None,
                )

                if matched_class:
                    if dept_buffer:
                        name = " ".join(dept_buffer)
                        current_dept = re.sub(r"\s*\(\d+\)\s*$", "", name).strip()
                        dept_buffer = []

                    numbers = _gf_extract_numbers(stripped[len(matched_class):])
                    if len(numbers) >= min_numbers:
                        for label, _, idx, year in fiscal_years:
                            rows.append({
                                "label": label,
                                "fiscal_year": year,
                                "fund": fund,
                                "department": current_dept,
                                "tag_peoples_budget": tag_for(current_dept),
                                "class": matched_class,
                                "total": numbers[idx],
                            })
                    continue

                if stripped.startswith("Total"):
                    dept_buffer = []
                    continue

                dept_buffer.append(stripped)

    return rows


def write_general_fund_csvs(rows, fiscal_years, output_dir):
    """Split rows from parse_general_fund() per fiscal year and write each to CSV."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    for label, filename, _, _ in fiscal_years:
        fy_rows = [
            {k: v for k, v in r.items() if k != "label"}
            for r in rows if r["label"] == label
        ]
        path = os.path.join(output_dir, filename)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(fy_rows)
        print(f"Wrote {len(fy_rows)} rows to {path}")


# ---------------------------------------------------------------------------
# Other-funds (appropriations ordinance) parser
# ---------------------------------------------------------------------------

# Full class names as they appear in this section of the PDF, mapped to the
# abbreviated names used in the general-fund parser's CSV rows.
CLASS_NAME_MAP = {
    "Personal Services-Employee Benefits":      "Pers. Svcs.-Emp.Benefits",
    "Advances and Other Miscellaneous Payment": "Advances and Other Misc. Payments",
    "Contributions, Indemnities and Taxes":     "Contrib., Indemnities & Taxes",
    "Materials, Supplies and Equipment":        "Materials, Supplies & Equip.",
    "Payments to Other Funds":                  "Payments to Other Funds",
    "Purchase of Services":                     "Purchase of Services",
    "Personal Services":                        "Personal Services",
    "Debt Service":                             "Debt Service",
}

# Longest-first so prefix matching doesn't short-circuit on "Personal Services"
# before checking "Personal Services-Employee Benefits".
_CLASS_NAMES_SORTED = sorted(CLASS_NAME_MAP.keys(), key=len, reverse=True)

_SECTION_RE = re.compile(r"^SECTION\s+(\d+)\.", re.IGNORECASE)
_ITEM_RE = re.compile(r"^\d+\.\d+\s+TO\s+THE\s+(.+)$", re.IGNORECASE)
_AMOUNT_RE = re.compile(r"^(.+?)\s*[.]{4,}\s*\$?\s*([\d,]+)\s*$")
_PAGE_NUM_RE = re.compile(r"^\d{1,3}$")


def _parse_amount(s):
    try:
        return int(s.replace(",", ""))
    except ValueError:
        return None


def parse_other_funds(pdf_path, fiscal_year, start_page, end_page, section_funds):
    """Extract non-General-Fund department/class/total rows from an appropriations
    ordinance PDF.

    `start_page` and `end_page` are 0-indexed and inclusive.
    `section_funds` maps "SECTION N" numbers to fund names.
    """
    rows = []
    current_fund = None
    current_dept = None
    dept_lines = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx in range(start_page, end_page + 1):
            page = pdf.pages[page_idx]
            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                stripped = line.strip()
                if not stripped or _PAGE_NUM_RE.match(stripped):
                    continue

                m = _SECTION_RE.match(stripped)
                if m:
                    current_fund = section_funds.get(int(m.group(1)))
                    current_dept = None
                    dept_lines = []
                    continue

                if current_fund is None:
                    continue

                m = _ITEM_RE.match(stripped)
                if m:
                    current_dept = m.group(1).strip().title()
                    dept_lines = []
                    continue

                # Wrapped department-name continuation (no amount, no dots, no $).
                if (
                    current_dept
                    and not _AMOUNT_RE.match(stripped)
                    and not stripped.startswith("Total")
                    and "." not in stripped
                    and "$" not in stripped
                ):
                    dept_lines.append(stripped)
                    current_dept = (current_dept + " " + " ".join(dept_lines)).title()
                    dept_lines = []
                    continue

                m = _AMOUNT_RE.match(stripped)
                if m:
                    raw_class = m.group(1).strip()
                    matched_class = next(
                        (cn for cn in _CLASS_NAMES_SORTED if raw_class.startswith(cn)),
                        None,
                    )
                    if matched_class and current_dept:
                        amount = _parse_amount(m.group(2))
                        if amount is not None:
                            dept = normalize_dept(current_dept)
                            rows.append({
                                "fiscal_year": fiscal_year,
                                "fund": current_fund,
                                "department": dept,
                                "tag_peoples_budget": tag_for(dept),
                                "class": CLASS_NAME_MAP[matched_class],
                                "total": amount,
                            })

    return rows


def append_other_funds_csv(rows, output_path):
    """Append other-funds rows to a CSV produced by the general-fund parser."""
    with open(output_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writerows(rows)

    print(f"Appended {len(rows)} rows to {output_path}")
    counts = Counter(r["fund"] for r in rows)
    for fund, n in sorted(counts.items()):
        print(f"  {fund}: {n} rows")


# The appropriations-ordinance section numbering has been stable across the
# FY26 and FY27 PDFs. If a new fiscal-year PDF reorders sections, pass a
# custom mapping into parse_other_funds() rather than mutating this one.
OTHER_FUNDS_SECTIONS = {
    3:  "Water Fund",
    4:  "Water Residual Fund",
    5:  "County Liquid Fuels Tax Fund",
    6:  "Special Gasoline Tax Fund",
    7:  "Healthchoices Behavioral Health Revenue Fund",
    8:  "Hotel Room Rental Tax Fund",
    9:  "Grants Revenue Fund",
    10: "Aviation Fund",
    11: "Community Development Fund",
    12: "Car Rental Tax Fund",
    13: "Municipal Pension Fund",
    14: "Housing Trust Fund",
    15: "Acute Care Hospital Fund",
    16: "Budget Stabilization Fund",
    17: "Philadelphia County Demolition Fund",
}
