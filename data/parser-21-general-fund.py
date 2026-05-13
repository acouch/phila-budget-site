"""Extracts General Fund obligation-history rows from the FY2021 budget-in-brief PDF."""

from budget_lib import parse_general_fund, write_general_fund_csvs

PDF_PATH = "input/budget-in-brief-FY2021-approved.pdf"
OUTPUT_DIR = "output"

# Pages 75-81 (1-indexed) are 0-indexed 74-80.
START_PAGE = 74
END_PAGE = 80

FISCAL_YEARS = [
    ("FY2019 Actual",    "FY2019-actual.csv",    0, "2019"),
    ("FY2020 Estimated", "FY2020-estimated.csv", 2, "2020"),
    ("FY2021 Adopted",   "FY2021-adopted.csv",   4, "2021"),
]


def main():
    rows = parse_general_fund(PDF_PATH, FISCAL_YEARS, START_PAGE, END_PAGE)
    write_general_fund_csvs(rows, FISCAL_YEARS, OUTPUT_DIR)


if __name__ == "__main__":
    main()
