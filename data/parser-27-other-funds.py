import pdfplumber
import csv
import re
import os
from pathlib import Path

PDF_PATH = "input/budget-in-brief-fy2027-proposed.pdf"
OUTPUT_FILE = "output/FY2027-proposed.csv"
TAGGING_YML = Path(__file__).resolve().parent / "tagging.yml"
DEFAULT_TAG = "Government Operations"


def load_peoples_budget_tags(path):
    # Minimal parser for the tagging.yml shape under `peoples_budget:`.
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


DEPT_TAGS = load_peoples_budget_tags(TAGGING_YML)


def tag_for(dept):
    return DEPT_TAGS.get(dept, DEFAULT_TAG)

# 0-indexed page range for the other-funds appropriations ordinance (pages 102-116)
START_PAGE = 101
END_PAGE = 115

# Maps "SECTION N" header text to fund name
SECTION_FUNDS = {
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

# Full class names as they appear in this section of the PDF, mapped to the
# abbreviated names used in the existing CSV rows.
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
# before checking "Personal Services-Employee Benefits"
CLASS_NAMES_SORTED = sorted(CLASS_NAME_MAP.keys(), key=len, reverse=True)

# Matches "SECTION N." at the start of a line
SECTION_RE = re.compile(r"^SECTION\s+(\d+)\.", re.IGNORECASE)

# Matches item headers like "3.5 TO THE WATER DEPARTMENT"
ITEM_RE = re.compile(r"^\d+\.\d+\s+TO\s+THE\s+(.+)$", re.IGNORECASE)

# Dotted-leader amount lines: "Class Name .... $ 1,234,567" or "Class Name .... 1,234,567"
AMOUNT_RE = re.compile(r"^(.+?)\s*[.]{4,}\s*\$?\s*([\d,]+)\s*$")

# Page numbers printed alone
PAGE_NUM_RE = re.compile(r"^\d{1,3}$")


def title_case_dept(name):
    return " ".join(
        w if w.lower() == "of" else w.capitalize()
        for w in name.split()
    )


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
    # The PDF uses an en/em dash; collapse to ASCII hyphen so alias keys match.
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


def parse_amount(s):
    try:
        return int(s.replace(",", ""))
    except ValueError:
        return None


def parse_budget_pdf(pdf_path):
    rows = []
    current_fund = None
    current_dept = None
    dept_lines = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx in range(START_PAGE, END_PAGE + 1):
            page = pdf.pages[page_idx]
            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                stripped = line.strip()
                if not stripped or PAGE_NUM_RE.match(stripped):
                    continue

                # Detect SECTION header → update current fund
                m = SECTION_RE.match(stripped)
                if m:
                    sec_num = int(m.group(1))
                    current_fund = SECTION_FUNDS.get(sec_num)
                    current_dept = None
                    dept_lines = []
                    continue

                if current_fund is None:
                    continue

                # Detect item header "N.N TO THE ..."
                m = ITEM_RE.match(stripped)
                if m:
                    current_dept = m.group(1).strip().title()
                    dept_lines = []
                    continue

                # Detect continuation of a wrapped department name (no amount)
                # — item headers sometimes wrap across lines before a class line
                if current_dept and not AMOUNT_RE.match(stripped) and not stripped.startswith("Total"):
                    # If it looks like a plain text continuation (no dots, no $)
                    if "." not in stripped and "$" not in stripped:
                        dept_lines.append(stripped)
                        current_dept = (current_dept + " " + " ".join(dept_lines)).title()
                        dept_lines = []
                        continue

                # Detect class/amount line
                m = AMOUNT_RE.match(stripped)
                if m:
                    raw_class = m.group(1).strip()
                    amount_str = m.group(2)

                    matched_class = next(
                        (cn for cn in CLASS_NAMES_SORTED if raw_class.startswith(cn)),
                        None,
                    )
                    if matched_class and current_dept:
                        amount = parse_amount(amount_str)
                        if amount is not None:
                            dept = normalize_dept(current_dept)
                            rows.append({
                                "fiscal_year": "2027",
                                "fund": current_fund,
                                "department": dept,
                                "tag_peoples_budget": tag_for(dept),
                                "class": CLASS_NAME_MAP[matched_class],
                                "total": amount,
                            })
                    continue

    return rows


def main():
    rows = parse_budget_pdf(PDF_PATH)

    fieldnames = ["fiscal_year", "fund", "department", "tag_peoples_budget", "class", "total"]
    with open(OUTPUT_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerows(rows)

    print(f"Appended {len(rows)} rows to {OUTPUT_FILE}")

    # Summary by fund
    from collections import Counter
    counts = Counter(r["fund"] for r in rows)
    for fund, n in sorted(counts.items()):
        print(f"  {fund}: {n} rows")


if __name__ == "__main__":
    main()
