"""Extracts non-General-Fund rows from the FY2026 budget-in-brief PDF and
appends them to the FY2026-adopted.csv produced by parser-27-general-fund.py."""

from budget_lib import OTHER_FUNDS_SECTIONS, append_other_funds_csv, parse_other_funds

PDF_PATH = "input/budget-in-brief-FY2026-approved-2.pdf"
OUTPUT_FILE = "output/FY2026-adopted.csv"
FISCAL_YEAR = "2026"

# 0-indexed page range for the other-funds appropriations ordinance (pages 100-115).
START_PAGE = 99
END_PAGE = 114


def main():
    rows = parse_other_funds(
        PDF_PATH, FISCAL_YEAR, START_PAGE, END_PAGE, OTHER_FUNDS_SECTIONS,
    )
    append_other_funds_csv(rows, OUTPUT_FILE)


if __name__ == "__main__":
    main()
