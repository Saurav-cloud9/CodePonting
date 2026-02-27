"""
fv1_ma50_regime_matrix.py
==========================
Builds a wide matrix of daily MA50 regime states for all 29 stocks.

For each stock on each trading day:
  "up"   = daily close > MA50  (same-day, the v1 / 8.77% methodology)
  "down" = daily close <= MA50, or MA50 not yet available (< 50 days of data)

Output:
  outputs/stats/ma50_regime_states.csv
  Rows = trading days, Columns = 29 stocks (alphabetical)
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import duckdb
import pathlib
import pandas as pd

BASE       = pathlib.Path(__file__).resolve().parent.parent
DAILY_GLOB = str(BASE / "data/historical/daily/*.parquet").replace("\\", "/")
STATS_DIR  = BASE / "outputs" / "stats"

BEST_CFG = {
    "ADANIPORTS":"Extreme-2", "ASHOKLEY":"Extreme-4",  "AXISBANK":"Extreme-2",
    "BANDHANBNK":"Extreme-2", "BHARTIARTL":"Extreme-1","CIPLA":"Extreme-2",
    "COALINDIA":"Extreme-1",  "DABUR":"Extreme-3",     "DIVISLAB":"Extreme-4",
    "HDFCBANK":"Extreme-4",   "HINDALCO":"Extreme-4",  "ICICIBANK":"Extreme-4",
    "INDUSINDBK":"Extreme-4", "INFY":"Extreme-2",      "ITC":"Extreme-1",
    "JSWSTEEL":"Extreme-4",   "NATIONALUM":"Extreme-2","NTPC":"Extreme-2",
    "ONGC":"Extreme-2",       "PNB":"Extreme-2",       "POWERGRID":"Extreme-3",
    "RELIANCE":"Extreme-2",   "SBIN":"Extreme-1",      "SUNPHARMA":"Extreme-4",
    "TATAMOTORS":"Extreme-1", "TATASTEEL":"Extreme-2", "TECHM":"Extreme-2",
    "VEDL":"Extreme-4",       "WIPRO":"Extreme-1",
}
ALL_STOCKS = sorted(BEST_CFG.keys())

# ── Query: long table, one row per (stock, date) ───────────────────────────────
print("Loading daily parquets and computing MA50 ...")
con = duckdb.connect()

long_df = con.execute(f"""
    SELECT
        regexp_extract(filename, '([A-Z0-9]+)[.]parquet$', 1) AS stock,
        CAST(datetime AS DATE)                                  AS trade_date,
        close,
        AVG(close) OVER (
            PARTITION BY regexp_extract(filename, '([A-Z0-9]+)[.]parquet$', 1)
            ORDER BY CAST(datetime AS DATE)
            ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
        )                                                       AS ma50,
        COUNT(*) OVER (
            PARTITION BY regexp_extract(filename, '([A-Z0-9]+)[.]parquet$', 1)
            ORDER BY CAST(datetime AS DATE)
            ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
        )                                                       AS window_rows
    FROM read_parquet('{DAILY_GLOB}', filename=true)
    WHERE regexp_extract(filename, '([A-Z0-9]+)[.]parquet$', 1) != 'NIFTY50'
    ORDER BY trade_date, stock
""").df()

con.close()
print(f"  Raw rows loaded: {len(long_df):,}")

# ── Label up / down ────────────────────────────────────────────────────────────
long_df["regime"] = "down"
long_df.loc[
    (long_df["window_rows"] >= 50) & (long_df["close"] > long_df["ma50"]),
    "regime"
] = "up"

# ── Pivot to wide format ───────────────────────────────────────────────────────
print("Pivoting to wide format ...")
wide_df = long_df.pivot(index="trade_date", columns="stock", values="regime")
wide_df.index.name   = "date"
wide_df.columns.name = None

# Keep only the 29 strategy stocks (drop any stray tickers)
available = [s for s in ALL_STOCKS if s in wide_df.columns]
wide_df = wide_df[available]

# ── Save ───────────────────────────────────────────────────────────────────────
out = STATS_DIR / "ma50_regime_states.csv"
wide_df.to_csv(out)
print(f"\nSaved: {out}")
print(f"Shape : {wide_df.shape[0]} trading days x {wide_df.shape[1]} stocks")

# ── Quick summary ──────────────────────────────────────────────────────────────
up_counts = (wide_df == "up").sum(axis=1)
SEP = "=" * 60

print()
print(SEP)
print("  SUMMARY")
print(SEP)
print(f"  Date range              : {wide_df.index.min()}  to  {wide_df.index.max()}")
print(f"  Total trading days      : {wide_df.shape[0]:,}")
print(f"  Stocks covered          : {wide_df.shape[1]}")
print(f"  Avg stocks 'up' per day : {up_counts.mean():.1f} / {wide_df.shape[1]}")
print(f"  Days all 29 up          : {(up_counts == wide_df.shape[1]).sum()}")
print(f"  Days all 29 down        : {(up_counts == 0).sum()}")
print(f"  Days majority up (>=15) : {(up_counts >= 15).sum()}")
print(f"  Days majority down (<15): {(up_counts < 15).sum()}")
print(SEP)

# Per-stock up% summary
print()
print("  Per-stock 'up' frequency:")
print(f"  {'stock':<14} {'up_days':>8} {'up_pct':>8}")
print("  " + "-" * 34)
for stock in available:
    n_up  = (wide_df[stock] == "up").sum()
    total = wide_df[stock].notna().sum()
    print(f"  {stock:<14} {n_up:>8,} {100*n_up/total:>7.1f}%")
print(SEP)
