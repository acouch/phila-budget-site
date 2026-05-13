"""Extracts non-General-Fund rows from the FY2023 budget-in-brief PDF and
appends them to FY2023-adopted.csv. FY2023 has sections 3-17 (no Transportation Fund)."""

from budget_lib import OTHER_FUNDS_SECTIONS, append_other_funds_csv, parse_other_funds

PDF_PATH = "input/Mayors-Operating-Budget-in-Brief-for-FY2023-as-Approved-by-Council-June-2022.pdf"
OUTPUT_FILE = "output/FY2023-adopted.csv"
FISCAL_YEAR = "2023"

# SECTION 3 on page 94 (0-idx 93); SECTIONS 16-17 on 0-idx 106.
START_PAGE = 93
END_PAGE = 107


def main():
    rows = parse_other_funds(
        PDF_PATH, FISCAL_YEAR, START_PAGE, END_PAGE, OTHER_FUNDS_SECTIONS,
    )
    append_other_funds_csv(rows, OUTPUT_FILE)


if __name__ == "__main__":
    main()
