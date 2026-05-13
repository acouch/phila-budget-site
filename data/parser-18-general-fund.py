"""Extracts General Fund obligation-history rows from the FY2018 budget-in-brief PDF."""

from budget_lib import parse_general_fund, write_general_fund_csvs

PDF_PATH = "input/budget-in-brief-FY2018-approved.pdf"
OUTPUT_DIR = "output"

# Pages 73-80 (1-indexed) are 0-indexed 72-79.
START_PAGE = 72
END_PAGE = 79

FISCAL_YEARS = [
    ("FY2016 Actual",    "FY2016-actual.csv",    0, "2016"),
    ("FY2017 Estimated", "FY2017-estimated.csv", 2, "2017"),
    ("FY2018 Adopted",   "FY2018-adopted.csv",   4, "2018"),
]


def main():
    rows = parse_general_fund(PDF_PATH, FISCAL_YEARS, START_PAGE, END_PAGE)
    write_general_fund_csvs(rows, FISCAL_YEARS, OUTPUT_DIR)


if __name__ == "__main__":
    main()
