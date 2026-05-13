"""Extracts General Fund obligation-history rows from the FY2022 budget-in-brief PDF."""

from budget_lib import parse_general_fund, write_general_fund_csvs

PDF_PATH = "input/budget-in-brief-FY2022-approved.pdf"
OUTPUT_DIR = "output"

# Pages 70-76 (1-indexed) are 0-indexed 69-75.
START_PAGE = 69
END_PAGE = 75

FISCAL_YEARS = [
    ("FY2020 Actual",    "FY2020-actual.csv",    0, "2020"),
    ("FY2021 Estimated", "FY2021-estimated.csv", 2, "2021"),
    ("FY2022 Adopted",   "FY2022-adopted.csv",   4, "2022"),
]


def main():
    rows = parse_general_fund(PDF_PATH, FISCAL_YEARS, START_PAGE, END_PAGE)
    write_general_fund_csvs(rows, FISCAL_YEARS, OUTPUT_DIR)


if __name__ == "__main__":
    main()
