"""Extracts non-General-Fund rows from the FY2021 budget-in-brief PDF and
appends them to FY2021-adopted.csv. FY2021 has sections 3-16."""

from budget_lib import OTHER_FUNDS_SECTIONS, append_other_funds_csv, parse_other_funds

PDF_PATH = "input/budget-in-brief-FY2021-approved.pdf"
OUTPUT_FILE = "output/FY2021-adopted.csv"
FISCAL_YEAR = "2021"

# SECTION 3 on page 94 (0-idx 93); SECTION 16 on 0-idx 107.
START_PAGE = 93
END_PAGE = 108


def main():
    rows = parse_other_funds(
        PDF_PATH, FISCAL_YEAR, START_PAGE, END_PAGE, OTHER_FUNDS_SECTIONS,
    )
    append_other_funds_csv(rows, OUTPUT_FILE)


if __name__ == "__main__":
    main()
