"""Extracts non-General-Fund rows from the FY2025 budget-in-brief PDF and
appends them to the FY2025-adopted.csv produced by parser-25-general-fund.py.

The FY2025 appropriations ordinance adds SECTION 18 (Transportation Fund)
relative to the FY26/FY27 ordinance — we extend the shared section mapping
locally."""

from budget_lib import OTHER_FUNDS_SECTIONS, append_other_funds_csv, parse_other_funds

PDF_PATH = "input/budget-in-brief-FY2025-approved.pdf"
OUTPUT_FILE = "output/FY2025-adopted.csv"
FISCAL_YEAR = "2025"

# 0-indexed page range for the other-funds appropriations ordinance.
# SECTION 3 starts on page 97 (0-indexed 96); SECTIONS 16-18 are on 0-indexed 111.
START_PAGE = 96
END_PAGE = 111

# FY2025 has a Transportation Fund (SECTION 18) not present in FY26/FY27.
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
