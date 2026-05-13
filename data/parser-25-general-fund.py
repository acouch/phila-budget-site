"""Extracts General Fund obligation-history rows from the FY2025 budget-in-brief
PDF. The FY2025 PDF has a 5-column number layout (FY2023 Actual / Increase /
FY2024 Estimated / Increase / FY2025 Adopted) — versus the 7-column layout in
later PDFs — so it emits three CSVs."""

from budget_lib import parse_general_fund, write_general_fund_csvs

PDF_PATH = "input/budget-in-brief-FY2025-approved.pdf"
OUTPUT_DIR = "output"

# Pages 78-84 (1-indexed) are 0-indexed 77-83.
START_PAGE = 77
END_PAGE = 83

# (label, output filename, 0-based number-column index, fiscal year string)
FISCAL_YEARS = [
    ("FY2023 Actual",     "FY2023-actual.csv",     0, "2023"),
    ("FY2024 Estimated",  "FY2024-estimated.csv",  2, "2024"),
    ("FY2025 Adopted",    "FY2025-adopted.csv",    4, "2025"),
]


def main():
    rows = parse_general_fund(PDF_PATH, FISCAL_YEARS, START_PAGE, END_PAGE)
    write_general_fund_csvs(rows, FISCAL_YEARS, OUTPUT_DIR)


if __name__ == "__main__":
    main()
