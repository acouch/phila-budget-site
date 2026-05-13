"""Extracts non-General-Fund rows from the FY2018 budget-in-brief PDF and
appends them to FY2018-adopted.csv. FY2018 has sections 3-15."""

from budget_lib import OTHER_FUNDS_SECTIONS, append_other_funds_csv, parse_other_funds

PDF_PATH = "input/budget-in-brief-FY2018-approved.pdf"
OUTPUT_FILE = "output/FY2018-adopted.csv"
FISCAL_YEAR = "2018"

# SECTION 3 on page 95 (0-idx 94); SECTION 15 on 0-idx 107.
START_PAGE = 94
END_PAGE = 108


def main():
    rows = parse_other_funds(
        PDF_PATH, FISCAL_YEAR, START_PAGE, END_PAGE, OTHER_FUNDS_SECTIONS,
    )
    append_other_funds_csv(rows, OUTPUT_FILE)


if __name__ == "__main__":
    main()
