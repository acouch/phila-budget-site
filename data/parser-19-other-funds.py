"""Extracts non-General-Fund rows from the FY2019 budget-in-brief PDF and
appends them to FY2019-adopted.csv. FY2019 has sections 3-15 (no Budget
Stabilization Fund or later additions)."""

from budget_lib import OTHER_FUNDS_SECTIONS, append_other_funds_csv, parse_other_funds

PDF_PATH = "input/FY19-BudgetinBrief_Adopted.pdf"
OUTPUT_FILE = "output/FY2019-adopted.csv"
FISCAL_YEAR = "2019"

# SECTION 3 on page 99 (0-idx 98); SECTION 15 on 0-idx 111.
START_PAGE = 98
END_PAGE = 112


def main():
    rows = parse_other_funds(
        PDF_PATH, FISCAL_YEAR, START_PAGE, END_PAGE, OTHER_FUNDS_SECTIONS,
    )
    append_other_funds_csv(rows, OUTPUT_FILE)


if __name__ == "__main__":
    main()
