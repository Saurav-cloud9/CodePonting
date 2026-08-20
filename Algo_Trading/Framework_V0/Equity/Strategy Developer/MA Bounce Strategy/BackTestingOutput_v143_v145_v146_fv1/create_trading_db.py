"""
create_trading_db.py
====================
Creates a persistent DuckDB database (trading.db) by importing
all backtest all_trades CSV files as named tables.

Tables created:
  fv1  ← Framework_V1 outputs (clean, no NIFTY50)
  v146 ← v1.4.6 batch (all fixes applied, no NIFTY50)
  v145 ← v1.4.5 batch (original bugs preserved, no NIFTY50)
  v143 ← v1.4.3 batch (legacy)
"""

import duckdb
from pathlib import Path

# ─────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────
BASE    = Path(__file__).parent
SQL_DIR = BASE.parent / "BackTesting_Realistic_Execution"
FV1_DIR = Path(r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V1\outputs\trades")

DB_PATH = BASE / "trading.db"

TABLES = {
    "fv1":  FV1_DIR / "fv1_all_trades.csv",
    "v146": SQL_DIR / "v146_all_trades.csv",
    "v145": SQL_DIR / "v145_all_trades.csv",
    "v143": BASE.parent / "SQL" / "v143_all_trades.csv",
}

# ─────────────────────────────────────────────────────────────────
# CREATE DB
# ─────────────────────────────────────────────────────────────────
print(f"Creating database: {DB_PATH}\n")

con = duckdb.connect(str(DB_PATH))

for table_name, csv_path in TABLES.items():
    if not csv_path.exists():
        print(f"  [SKIP] {table_name}: file not found → {csv_path}")
        continue

    con.execute(f"DROP TABLE IF EXISTS {table_name}")
    con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_path.as_posix()}')")
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"  {table_name:<6} → {count:>10,} rows   ({csv_path.name})")

con.close()
print(f"\nDone. Database saved to:\n  {DB_PATH}")
