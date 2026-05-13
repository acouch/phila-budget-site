"""Extracts General Fund obligation-history rows from the FY2020 budget-in-brief PDF."""

from budget_lib import parse_general_fund, write_general_fund_csvs

PDF_PATH = "input/budget-in-brief-FY2020-approved.pdf"
OUTPUT_DIR = "output"

# Pages 75-82 (1-indexed) are 0-indexed 74-81.
START_PAGE = 74
END_PAGE = 81

FISCAL_YEARS = [
    ("FY2018 Actual",    "FY2018-actual.csv",    0, "2018"),
    ("FY2019 Estimated", "FY2019-estimated.csv", 2, "2019"),
    ("FY2020 Adopted",   "FY2020-adopted.csv",   4, "2020"),
]


def main():
    rows = parse_general_fund(PDF_PATH, FISCAL_YEARS, START_PAGE, END_PAGE)
    write_general_fund_csvs(rows, FISCAL_YEARS, OUTPUT_DIR)


if __name__ == "__main__":
    main()
