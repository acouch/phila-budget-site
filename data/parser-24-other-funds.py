"""Extracts non-General-Fund rows from the FY2024 budget-in-brief PDF and
appends them to the FY2024-adopted.csv produced by parser-24-general-fund.py.

Same section-to-fund mapping as the FY25 PDF (includes Transportation Fund)."""

from budget_lib import OTHER_FUNDS_SECTIONS, append_other_funds_csv, parse_other_funds

PDF_PATH = "input/Mayors-Operating-Budget-in-Brief-for-FY2024-as-Approved-by-Council-June-2023.pdf"
OUTPUT_FILE = "output/FY2024-adopted.csv"
FISCAL_YEAR = "2024"

# 0-indexed page range for the other-funds appropriations ordinance.
# SECTION 3 starts on page 99 (0-indexed 98); SECTIONS 16-18 are on 0-indexed 112.
START_PAGE = 98
END_PAGE = 112

# FY2024 includes a Transportation Fund (SECTION 18) like FY2025.
SECTION_FUNDS = {
    **OTHER_FUNDS_SECTIONS,
    18: "Transportation Fund",
}


def main():
    rows = parse_other_funds(
        PDF_PATH, FISCAL_YEAR, START_PAGE, END_PAGE, SECTION_FUNDS,
    )
    append_other_funds_csv(rows, OUTPUT_FILE)


if __name__ == "__main__":
    main()
