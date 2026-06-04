import csv
import sqlite3
import subprocess
import sys
from pathlib import Path

import datamade
from budget_lib import DEFAULT_TAG, TAGGING_YML, load_peoples_budget_tags

HERE = Path(__file__).resolve().parent

# General fund overwrites the FY*.csv files; other-funds parser appends to FY2027-proposed.csv.
# Run general-fund first so the append starts from a fresh file.
SCRIPTS = [
    # General-fund parsers run first (in chronological order so later parsers
    # overwrite earlier ones for shared years' adopted snapshots); the
    # other-funds parsers then append non-General-Fund rows to the matching FY file.
    "parser-18-general-fund.py",   # FY2016/2017/2018
    "parser-19-general-fund.py",   # FY2017/2018/2019
    "parser-20-general-fund.py",   # FY2018/2019/2020
    "parser-21-general-fund.py",   # FY2019/2020/2021
    "parser-22-general-fund.py",   # FY2020/2021/2022
    "parser-23-general-fund.py",   # FY2021/2022/2023
    "parser-24-general-fund.py",   # FY2022/2023/2024
    "parser-25-general-fund.py",   # FY2023/2024/2025
    "parser-27-general-fund.py",   # FY2025/2026/2027
    "parser-18-other-funds.py",
    "parser-19-other-funds.py",
    "parser-20-other-funds.py",
    "parser-21-other-funds.py",
    "parser-22-other-funds.py",
    "parser-23-other-funds.py",
    "parser-24-other-funds.py",
    "parser-25-other-funds.py",
    "parser-26-other-funds.py",
    "parser-27-other-funds.py",
]

PIVOTS = [
    (HERE / "output" / "FY2027-proposed.csv", HERE / "output" / "FY2027-proposed-pivot.csv"),
    (HERE / "output" / "FY2026-adopted.csv",  HERE / "output" / "FY2026-adopted-pivot.csv"),
    (HERE / "output" / "FY2025-adopted.csv",  HERE / "output" / "FY2025-adopted-pivot.csv"),
    (HERE / "output" / "FY2024-adopted.csv",  HERE / "output" / "FY2024-adopted-pivot.csv"),
    (HERE / "output" / "FY2023-adopted.csv",  HERE / "output" / "FY2023-adopted-pivot.csv"),
    (HERE / "output" / "FY2022-adopted.csv",  HERE / "output" / "FY2022-adopted-pivot.csv"),
    (HERE / "output" / "FY2021-adopted.csv",  HERE / "output" / "FY2021-adopted-pivot.csv"),
    (HERE / "output" / "FY2020-adopted.csv",  HERE / "output" / "FY2020-adopted-pivot.csv"),
    (HERE / "output" / "FY2019-adopted.csv",  HERE / "output" / "FY2019-adopted-pivot.csv"),
    (HERE / "output" / "FY2018-adopted.csv",  HERE / "output" / "FY2018-adopted-pivot.csv"),
]


def run_parsers():
    for script in SCRIPTS:
        print(f"\n=== Running {script} ===")
        result = subprocess.run([sys.executable, script], cwd=HERE)
        if result.returncode != 0:
            sys.exit(result.returncode)


def load_csv(path):
    with path.open(newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cols = ", ".join(f'"{c}"' for c in header)
        placeholders = ", ".join("?" for _ in header)
        cur.execute(f"CREATE TABLE rows ({cols})")
        cur.executemany(f"INSERT INTO rows ({cols}) VALUES ({placeholders})", rows)
    return cur, conn


def fund_column_name(fund):
    return (
        fund.lower()
        .replace("&", "and")
        .replace("/", "_")
        .replace("-", "_")
        .replace(".", "")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
        .replace(" ", "_")
    )


def create_pivot(input_csv, output_csv, dept_tags):
    print(f"\n=== Pivoting {input_csv.name} -> {output_csv.name} ===")
    cur, conn = load_csv(input_csv)

    cur.execute("SELECT DISTINCT fiscal_year FROM rows ORDER BY fiscal_year")
    fiscal_years = [r[0] for r in cur.fetchall()]
    if len(fiscal_years) != 1:
        print(f"  WARNING: expected 1 fiscal_year in {input_csv.name}, got {fiscal_years}")
    fiscal_year = fiscal_years[0] if fiscal_years else ""

    cur.execute("SELECT DISTINCT fund FROM rows ORDER BY fund")
    funds = [r[0] for r in cur.fetchall()]
    print(f"Found {len(funds)} distinct funds:")
    for f in funds:
        print(f"  - {f}")

    fund_cols = [(f, fund_column_name(f)) for f in funds]
    case_clauses = ",\n  ".join(
        f"SUM(CASE WHEN fund = ? THEN total ELSE 0 END) AS {col}"
        for _, col in fund_cols
    )
    query = f"""
        SELECT
          department,
          {case_clauses},
          SUM(total) AS total
        FROM rows
        GROUP BY department
        ORDER BY department
    """
    cur.execute(query, [f for f, _ in fund_cols])
    rows = cur.fetchall()

    sql_header = [d[0] for d in cur.description]
    out_header = ["fiscal_year", sql_header[0], "tag_peoples_budget"] + sql_header[1:]

    untagged = set()
    with output_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(out_header)
        for row in rows:
            dept = row[0]
            tag = dept_tags.get(dept)
            if tag is None:
                untagged.add(dept)
                tag = DEFAULT_TAG
            writer.writerow((fiscal_year, dept, tag) + row[1:])

    conn.close()
    print(f"Wrote {output_csv}")
    if untagged:
        print(f"  {len(untagged)} departments fell through to '{DEFAULT_TAG}':")
        for d in sorted(untagged):
            print(f"    - {d}")


def main():
    run_parsers()
    dept_tags = load_peoples_budget_tags(TAGGING_YML)
    print(f"\nLoaded {len(dept_tags)} department tags from {TAGGING_YML.name}")
    for input_csv, output_csv in PIVOTS:
        create_pivot(input_csv, output_csv, dept_tags)

    print("\n=== Building datamade budget_finished.csv ===")
    datamade.main()


if __name__ == "__main__":
    main()
