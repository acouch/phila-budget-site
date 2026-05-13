"""Extracts General Fund obligation-history rows from the FY2027 budget-in-brief
PDF. Writes one CSV per fiscal year column (FY2025 actual, FY2026 adopted,
FY2026 estimated, FY2027 proposed) — these are the starting files that the
other-funds parsers later append to."""

from budget_lib import parse_general_fund, write_general_fund_csvs

PDF_PATH = "input/budget-in-brief-fy2027-proposed.pdf"
OUTPUT_DIR = "output"

# Pages 81-88 are 0-indexed 80-87.
START_PAGE = 80
END_PAGE = 87

# (label, output filename, 0-based number-column index, fiscal year string)
FISCAL_YEARS = [
    ("FY2025 Actual",    "FY2025-actual.csv",    0, "2025"),
    ("FY2026 Adopted",   "FY2026-adopted.csv",   2, "2026"),
    ("FY2026 Estimated", "FY2026-estimated.csv", 4, "2026"),
    ("FY2027 Proposed",  "FY2027-proposed.csv",  6, "2027"),
]


def main():
    rows = parse_general_fund(PDF_PATH, FISCAL_YEARS, START_PAGE, END_PAGE)
    write_general_fund_csvs(rows, FISCAL_YEARS, OUTPUT_DIR)


if __name__ == "__main__":
    main()
