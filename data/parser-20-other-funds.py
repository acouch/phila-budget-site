"""Extracts non-General-Fund rows from the FY2020 budget-in-brief PDF and
appends them to FY2020-adopted.csv. FY2020 has sections 3-16."""

from budget_lib import OTHER_FUNDS_SECTIONS, append_other_funds_csv, parse_other_funds

PDF_PATH = "input/budget-in-brief-FY2020-approved.pdf"
OUTPUT_FILE = "output/FY2020-adopted.csv"
FISCAL_YEAR = "2020"

# SECTION 3 on page 97 (0-idx 96); SECTION 16 on 0-idx 109.
START_PAGE = 96
END_PAGE = 110


def main():
    rows = parse_other_funds(
        PDF_PATH, FISCAL_YEAR, START_PAGE, END_PAGE, OTHER_FUNDS_SECTIONS,
    )
    append_other_funds_csv(rows, OUTPUT_FILE)


if __name__ == "__main__":
    main()
