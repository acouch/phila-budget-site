import pdfplumber
import csv
import re
import os

PDF_PATH = "input/budget-in-brief-fy2027-proposed.pdf"
OUTPUT_PATH = "output/general-fund-obligation-history.csv"

# Pages 81-88 in the document are 0-indexed 80-87
START_PAGE = 80
END_PAGE = 87

CLASS_NAMES = [
    "Pers. Svcs.-Emp.Benefits",
    "Advances and Other Misc. Payments",
    "Contrib., Indemnities & Taxes",
    "Materials, Supplies & Equip.",
    "Payments to Other Funds",
    "Purchase of Services",
    "Personal Services",
    "Debt Service",
]

SKIP_PATTERNS = [
    r"^General Fund$",
    r"^Obligation History$",
    r"^Fiscal Years \d+ - \d+$",
    r"^Fiscal Year",
    r"^\d{4}\s+\d{4}\s+\d{4}\s+\d{4}$",
    r"^Actual Increase",
    r"^Department / Agency",
    r"^\(\d+\)",
    r"^\d+\s*$",
    r"^Total, General Fund",
]


def should_skip(line):
    for pat in SKIP_PATTERNS:
        if re.match(pat, line):
            return True
    return False


def parse_number(s):
    s = s.strip()
    negative = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[(),]", "", s).replace(",", "")
    try:
        return -int(s) if negative else int(s)
    except ValueError:
        return None


def extract_numbers(text):
    matches = re.findall(r"\([\d,]+\)|[\d,]+", text)
    return [n for m in matches if (n := parse_number(m)) is not None]


def parse_budget_pdf(pdf_path):
    rows = []
    fund = "General Fund"

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx in range(START_PAGE, END_PAGE + 1):
            page = pdf.pages[page_idx]
            text = page.extract_text()
            if not text:
                continue

            current_dept = None
            dept_buffer = []

            for line in text.split("\n"):
                stripped = line.strip()
                if not stripped or should_skip(stripped):
                    continue

                matched_class = next(
                    (cls for cls in CLASS_NAMES if stripped.startswith(cls)), None
                )

                if matched_class:
                    if dept_buffer:
                        name = " ".join(dept_buffer)
                        current_dept = re.sub(r"\s*\(\d+\)\s*$", "", name).strip()
                        dept_buffer = []

                    numbers = extract_numbers(stripped[len(matched_class):])
                    if len(numbers) >= 7:
                        for fiscal_year, val in [
                            ("FY2025 Actual", numbers[0]),
                            ("FY2026 Adopted", numbers[2]),
                            ("FY2026 Estimated", numbers[4]),
                            ("FY2027 Proposed", numbers[6]),
                        ]:
                            rows.append({
                                "fiscal_year": fiscal_year,
                                "fund": fund,
                                "department": current_dept,
                                "class": matched_class,
                                "total": val,
                            })
                    continue

                if stripped.startswith("Total"):
                    dept_buffer = []
                    continue

                dept_buffer.append(stripped)

    return rows


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    rows = parse_budget_pdf(PDF_PATH)

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["fiscal_year", "fund", "department", "class", "total"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
