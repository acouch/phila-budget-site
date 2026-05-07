import pdfplumber
import csv
import re
import os

PDF_PATH = "input/budget-in-brief-FY2026-approved-2.pdf"
OUTPUT_FILE = "output/FY2026-adopted.csv"

# 0-indexed page range for the other-funds appropriations ordinance (pages 100-115)
START_PAGE = 99
END_PAGE = 114

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


# Aligns the appropriations-ordinance ("Department Of X") names with the names
# the general-fund parser emits, so the same department in different funds
# collapses to one row in downstream pivots.
DEPT_ALIASES = {
    "Auditing Department": "Auditing (City Controller)",
    "Board Of Pensions And Retirement": "Sinking Fund Commission (Debt Service)",
    "Board Of Trustees Of The Free Library Of Philadelphia": "Free Library",
    "Department Of Aviation": "Aviation",
    "Department Of Fleet Services": "Fleet Services",
    "Department Of Fleet Services - Vehicle Purchase": "Fleet Services -Vehicle Lease/Purch.",
    "Department Of Human Services": "Human Services",
    "Department Of Human Services - Office Of Homeless Services": "Office of Homeless Services",
    "Department Of Licenses And Inspections": "Licenses & Inspection",
    "Department Of Parks And Recreation": "Parks and Recreation",
    "Department Of Planning And Development": "Planning and Development",
    "Department Of Public Health": "Public Health",
    "Department Of Public Health - Office Of Behavioral Health And Intellectual Disability": "Office of Behavioral Health and Intellectual disAbility",
    "Department Of Public Health - State Payment": "Public Health",
    "Department Of Public Property": "Public Property",
    "Department Of Public Property - Utilities": "Public Property-Utilities",
    "Department Of Revenue": "Revenue",
    "Department Of Revenue - Sinking Fund Commission": "Sinking Fund Commission (Debt Service)",
    "Department Of Streets": "Streets",
    "Department Of Streets - Sanitation": "Sanitation",
    "Director Of Commerce": "Commerce",
    "Director Of Finance": "Finance",
    "Director Of Finance - Budget Stabilization": "Finance-Budget Stabilization",
    "Director Of Finance - Community Development Block Grant - To Be Allocated": "Finance",
    "Director Of Finance - Fringe Benefits": "Finance-Employee Benefits",
    "Director Of Finance - Indemnities": "Finance-Indemnities",
    "Director Of Finance - Provision For Other Grants": "Finance",
    "Fire Department": "Fire",
    "First Judicial District Of Pennsylvania": "First Judicial District",
    "Law Department": "Law",
    "Mayor - Office Of Arts, Culture And The Creative Economy": "Office of Arts and Culture and the Creative Economy",
    "Mayor - Office Of Community Empowerment And Opportunity": "Office of Community Empowerment and Opportunity",
    "Mayor - Office Of Education": "Office of Education",
    "Mayor - Office Of Innovation And Technology": "Office of Innovation and Technology",
    "Police Department": "Police",
    "Procurement Department": "Procurement",
    "Water Department": "Water",
    "Water Department - Philadelphia Water, Sewer, And Stormwater Rate Board": "Water",
    "Council - Veterans Advisory Commission": "City Council",
}


def normalize_dept(name):
    name = name.replace("–", "-").replace("—", "-")
    name = " ".join(name.split())
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
                            rows.append({
                                "fiscal_year": "2026",
                                "fund": current_fund,
                                "department": normalize_dept(current_dept),
                                "class": CLASS_NAME_MAP[matched_class],
                                "total": amount,
                            })
                    continue

    return rows


def main():
    rows = parse_budget_pdf(PDF_PATH)

    fieldnames = ["fiscal_year", "fund", "department", "class", "total"]
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
