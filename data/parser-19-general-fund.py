"""Extracts General Fund obligation-history rows from the FY2019 budget-in-brief PDF."""

from budget_lib import parse_general_fund, write_general_fund_csvs

PDF_PATH = "input/FY19-BudgetinBrief_Adopted.pdf"
OUTPUT_DIR = "output"

# Pages 75-83 (1-indexed) are 0-indexed 74-82.
START_PAGE = 74
END_PAGE = 82

FISCAL_YEARS = [
    ("FY2017 Actual",    "FY2017-actual.csv",    0, "2017"),
    ("FY2018 Estimated", "FY2018-estimated.csv", 2, "2018"),
    ("FY2019 Adopted",   "FY2019-adopted.csv",   4, "2019"),
]


def main():
    rows = parse_general_fund(PDF_PATH, FISCAL_YEARS, START_PAGE, END_PAGE)
    write_general_fund_csvs(rows, FISCAL_YEARS, OUTPUT_DIR)


if __name__ == "__main__":
    main()
