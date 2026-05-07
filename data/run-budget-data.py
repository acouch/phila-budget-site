import csv
import sqlite3
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# General fund overwrites the FY*.csv files; other-funds parser appends to FY2027-proposed.csv.
# Run general-fund first so the append starts from a fresh file.
SCRIPTS = [
    "parser-27-general-fund.py",
    "parser-26-other-funds.py",
    "parser-27-other-funds.py",
]

PIVOTS = [
    (HERE / "output" / "FY2027-proposed.csv", HERE / "output" / "FY2027-proposed-pivot.csv"),
    (HERE / "output" / "FY2026-adopted.csv",  HERE / "output" / "FY2026-adopted-pivot.csv"),
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


def create_pivot(input_csv, output_csv):
    print(f"\n=== Pivoting {input_csv.name} -> {output_csv.name} ===")
    cur, conn = load_csv(input_csv)

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

    out_header = [d[0] for d in cur.description]
    with output_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(out_header)
        writer.writerows(cur.fetchall())

    conn.close()
    print(f"Wrote {output_csv}")


def main():
    run_parsers()
    for input_csv, output_csv in PIVOTS:
        create_pivot(input_csv, output_csv)


if __name__ == "__main__":
    main()
