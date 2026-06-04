"""Build a datamade-format budget_finished.csv from the adopted/proposed CSVs.

Reads every per-fiscal-year file in ``data/output`` that represents an adopted
(or, for the latest year, proposed) budget and pivots the rows into the wide
"budget_finished" shape the datamade visualization expects:

    Function, Agency, Fund Type, FP Category, Fund, <year columns...>

Column mapping (per source schema fiscal_year,fund,department,tag_peoples_budget,class,total):
    Function    <- tag_peoples_budget
    Agency      <- department
    Fund Type   <- fund
    Fund        <- fund
    FP Category <- class

Each year column holds the summed ``total`` for that (Function, Agency,
Fund Type, FP Category, Fund) group in the corresponding fiscal year.

Four trailing description columns are appended to match the datamade schema.
Their text is looked up from ``input/datamade/descriptions.csv`` (keyed by
Breakdown Type + Name):
    Agency Description      <- (Agency,      Agency)
    Fund Description        <- (Fund,        Fund)
    FP Category Description <- (FP Category, FP Category)
    Fund Type Description   <- (Fund,        Fund Type)  # Fund Type == Fund here

Run:
    cd data
    uv run python datamade.py
"""

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(HERE, "output")
DEST_DIR = os.path.join(OUTPUT_DIR, "datamade")
DEST_PATH = os.path.join(DEST_DIR, "budget_finished.csv")
DESCRIPTIONS_PATH = os.path.join(HERE, "input", "datamade", "descriptions.csv")

# Each year column label maps to the source CSV (relative to output/) whose
# ``total`` values fill that column. "2026-27" is fiscal_year 2027, "2018-19"
# is fiscal_year 2019, etc. FY2027 is proposed; the rest are adopted.
YEAR_COLUMNS = [
    ("2026-27  Estimates", "FY2027-proposed.csv"),
    ("2025-26  Estimates", "FY2026-adopted.csv"),
    ("2024-25  Actuals", "FY2025-adopted.csv"),
    ("2023-24  Actuals", "FY2024-adopted.csv"),
    ("2022-23  Actuals", "FY2023-adopted.csv"),
    ("2021-22  Actuals", "FY2022-adopted.csv"),
    ("2020-21  Actuals", "FY2021-adopted.csv"),
    ("2019-20  Actuals", "FY2020-adopted.csv"),
    ("2018-19  Actuals", "FY2019-adopted.csv"),
]

KEY_COLUMNS = ["Function", "Agency", "Fund Type", "FP Category", "Fund"]
DESCRIPTION_COLUMNS = [
    "Agency Description",
    "Fund Description",
    "FP Category Description",
    "Fund Type Description",
]
HEADER = (
    KEY_COLUMNS
    + [label for label, _ in YEAR_COLUMNS]
    + DESCRIPTION_COLUMNS
)


def load_descriptions(path):
    """(Breakdown Type, Name) -> Description from descriptions.csv."""
    descriptions = {}
    if not os.path.exists(path):
        print(f"warning: missing {path}, descriptions left blank")
        return descriptions
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            descriptions[(row["Breakdown Type"], row["Name"])] = row["Description"]
    return descriptions


def group_key(row):
    """(Function, Agency, Fund Type, FP Category, Fund) for one source row."""
    return (
        row["tag_peoples_budget"],  # Function
        row["department"],          # Agency
        row["fund"],                # Fund Type
        row["class"],               # FP Category
        row["fund"],                # Fund
    )


def main():
    descriptions = load_descriptions(DESCRIPTIONS_PATH)

    # rows: key -> {year_label: summed total}
    rows = {}

    for label, filename in YEAR_COLUMNS:
        path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(path):
            print(f"warning: missing source file {filename}, skipping")
            continue
        with open(path, newline="") as fh:
            for row in csv.DictReader(fh):
                key = group_key(row)
                bucket = rows.setdefault(key, {})
                bucket[label] = bucket.get(label, 0) + float(row["total"])

    os.makedirs(DEST_DIR, exist_ok=True)
    with open(DEST_PATH, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADER)
        # Sort for stable, readable output: by the key columns.
        for key in sorted(rows):
            function, agency, fund_type, fp_category, fund = key
            out = [function, agency, fund_type, fp_category, fund]
            for label, _ in YEAR_COLUMNS:
                value = rows[key].get(label)
                out.append("" if value is None else value)
            out.extend([
                descriptions.get(("Agency", agency), ""),
                descriptions.get(("Fund", fund), ""),
                descriptions.get(("FP Category", fp_category), ""),
                descriptions.get(("Fund", fund_type), ""),
            ])
            writer.writerow(out)

    print(f"wrote {len(rows)} rows to {DEST_PATH}")


if __name__ == "__main__":
    main()
