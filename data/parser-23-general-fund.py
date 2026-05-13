"""Extracts General Fund obligation-history rows from the FY2023 budget-in-brief PDF."""

from budget_lib import parse_general_fund, write_general_fund_csvs

PDF_PATH = "input/Mayors-Operating-Budget-in-Brief-for-FY2023-as-Approved-by-Council-June-2022.pdf"
OUTPUT_DIR = "output"

# Pages 74-80 (1-indexed) are 0-indexed 73-79.
START_PAGE = 73
END_PAGE = 79

FISCAL_YEARS = [
    ("FY2021 Actual",    "FY2021-actual.csv",    0, "2021"),
    ("FY2022 Estimated", "FY2022-estimated.csv", 2, "2022"),
    ("FY2023 Adopted",   "FY2023-adopted.csv",   4, "2023"),
]


def main():
    rows = parse_general_fund(PDF_PATH, FISCAL_YEARS, START_PAGE, END_PAGE)
    write_general_fund_csvs(rows, FISCAL_YEARS, OUTPUT_DIR)


if __name__ == "__main__":
    main()
