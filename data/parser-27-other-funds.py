import pdfplumber
import csv
import re
import os

PDF_PATH = "input/budget-in-brief-fy2027-proposed.pdf"
OUTPUT_FILE = "output/FY2027-proposed.csv"

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
                    current_dept = m.group(1).strip()
                    dept_lines = []
                    continue

                # Detect continuation of a wrapped department name (no amount)
                # — item headers sometimes wrap across lines before a class line
                if current_dept and not AMOUNT_RE.match(stripped) and not stripped.startswith("Total"):
                    # If it looks like a plain text continuation (no dots, no $)
                    if "." not in stripped and "$" not in stripped:
                        dept_lines.append(stripped)
                        current_dept = current_dept + " " + " ".join(dept_lines)
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
                                "fiscal_year": "2027",
                                "fund": current_fund,
                                "department": current_dept,
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
