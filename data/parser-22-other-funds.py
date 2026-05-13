"""Extracts non-General-Fund rows from the FY2022 budget-in-brief PDF and
appends them to FY2022-adopted.csv. FY2022 has sections 3-16 (no Philadelphia
County Demolition Fund or Transportation Fund)."""

from budget_lib import OTHER_FUNDS_SECTIONS, append_other_funds_csv, parse_other_funds

PDF_PATH = "input/budget-in-brief-FY2022-approved.pdf"
OUTPUT_FILE = "output/FY2022-adopted.csv"
FISCAL_YEAR = "2022"

# SECTION 3 on page 89 (0-idx 88); SECTION 16 on 0-idx 102.
START_PAGE = 88
END_PAGE = 103


def main():
    rows = parse_other_funds(
        PDF_PATH, FISCAL_YEAR, START_PAGE, END_PAGE, OTHER_FUNDS_SECTIONS,
    )
    append_other_funds_csv(rows, OUTPUT_FILE)


if __name__ == "__main__":
    main()
