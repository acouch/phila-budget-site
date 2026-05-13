"""Extracts non-General-Fund rows from the FY2027 budget-in-brief PDF and
appends them to the FY2027-proposed.csv produced by parser-27-general-fund.py."""

from budget_lib import OTHER_FUNDS_SECTIONS, append_other_funds_csv, parse_other_funds

PDF_PATH = "input/budget-in-brief-fy2027-proposed.pdf"
OUTPUT_FILE = "output/FY2027-proposed.csv"
FISCAL_YEAR = "2027"

# 0-indexed page range for the other-funds appropriations ordinance (pages 102-116).
START_PAGE = 101
END_PAGE = 115


def main():
    rows = parse_other_funds(
        PDF_PATH, FISCAL_YEAR, START_PAGE, END_PAGE, OTHER_FUNDS_SECTIONS,
    )
    append_other_funds_csv(rows, OUTPUT_FILE)


if __name__ == "__main__":
    main()
