"""Extracts General Fund obligation-history rows from the FY2024 budget-in-brief
PDF. Same 5-column layout as FY2025 (FY2022 Actual / Increase / FY2023 Estimated /
Increase / FY2024 Adopted)."""

from budget_lib import parse_general_fund, write_general_fund_csvs

PDF_PATH = "input/Mayors-Operating-Budget-in-Brief-for-FY2024-as-Approved-by-Council-June-2023.pdf"
OUTPUT_DIR = "output"

# Pages 79-85 (1-indexed) are 0-indexed 78-84.
START_PAGE = 78
END_PAGE = 84

# (label, output filename, 0-based number-column index, fiscal year string)
FISCAL_YEARS = [
    ("FY2022 Actual",    "FY2022-actual.csv",    0, "2022"),
    ("FY2023 Estimated", "FY2023-estimated.csv", 2, "2023"),
    ("FY2024 Adopted",   "FY2024-adopted.csv",   4, "2024"),
]


def main():
    rows = parse_general_fund(PDF_PATH, FISCAL_YEARS, START_PAGE, END_PAGE)
    write_general_fund_csvs(rows, FISCAL_YEARS, OUTPUT_DIR)


if __name__ == "__main__":
    main()
