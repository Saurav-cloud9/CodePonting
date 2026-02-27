"""
fv1_nifty_regime.py
====================
Single-stock regime signal test using NIFTY50 as the master.
NIFTY50 daily close > MA50  →  regime = uptrend
Filter all 29 best-config trades to those dates and report metrics.
Same-day close used (intentional — matches the regime sweep methodology).
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import duckdb
import pathlib

BASE        = pathlib.Path(__file__).resolve().parent.parent
DAILY_GLOB  = str(BASE / "data/historical/daily/*.parquet").replace("\\", "/")
TRADES_PATH = str(BASE / "outputs/trades/fv1_all_trades.csv").replace("\\", "/")

INITIAL_EQUITY = 1_000_000
YEARS          = 4

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

cfg_rows = ", ".join(f"('{k}','{v}')" for k, v in BEST_CFG.items())

con = duckdb.connect()

# Best trades view
con.execute(f"""
    CREATE VIEW best_trades AS
    WITH raw AS (
        SELECT stock, atr_config, pnl,
            (CAST(entry_time AS TIMESTAMPTZ) AT TIME ZONE 'Asia/Kolkata')::DATE AS trade_date
        FROM read_csv_auto('{TRADES_PATH}')
    ),
    cfg AS (SELECT * FROM (VALUES {cfg_rows}) t(stock, best_config))
    SELECT r.stock, r.pnl, r.trade_date
    FROM raw r JOIN cfg c ON r.stock = c.stock AND r.atr_config = c.best_config
    WHERE r.stock NOT IN ('VI', 'IDEA', 'NIFTY50')
""")

# Baseline
base = con.execute("""
    SELECT
        COUNT(*)                                                      AS trades,
        ROUND(SUM(pnl), 0)                                           AS total_pnl_rs,
        ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)
                    / COUNT(*), 2)                                    AS win_rate,
        ROUND(SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END)
            / NULLIF(ABS(SUM(CASE WHEN pnl < 0 THEN pnl ELSE 0 END)),0),4)
                                                                      AS profit_factor
    FROM best_trades
""").df().iloc[0]

base_total = int(base["trades"])
base_pnl   = float(base["total_pnl_rs"])
base_cagr  = ((INITIAL_EQUITY + base_pnl) / INITIAL_EQUITY) ** (1 / YEARS) - 1

# NIFTY50 regime dates: same-day close > MA50
nifty = con.execute(f"""
    WITH nifty_daily AS (
        SELECT
            CAST(datetime AS DATE) AS trade_date,
            close,
            AVG(close) OVER (
                ORDER BY CAST(datetime AS DATE)
                ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
            ) AS ma50,
            COUNT(*) OVER (
                ORDER BY CAST(datetime AS DATE)
                ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
            ) AS window_rows
        FROM read_parquet('{DAILY_GLOB}', filename=true)
        WHERE regexp_extract(filename, '([A-Z0-9]+)\.parquet$', 1) = 'NIFTY50'
    )
    SELECT DISTINCT trade_date
    FROM nifty_daily
    WHERE window_rows >= 50
      AND close > ma50
""").df()

nifty_dates = set(nifty["trade_date"].tolist())
print(f"NIFTY50 uptrend days (close > MA50): {len(nifty_dates):,}")

# Filtered trades
r = con.execute(f"""
    WITH regime_dates AS (
        WITH nifty_daily AS (
            SELECT
                CAST(datetime AS DATE) AS trade_date,
                close,
                AVG(close) OVER (
                    ORDER BY CAST(datetime AS DATE)
                    ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
                ) AS ma50,
                COUNT(*) OVER (
                    ORDER BY CAST(datetime AS DATE)
                    ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
                ) AS window_rows
            FROM read_parquet('{DAILY_GLOB}', filename=true)
            WHERE regexp_extract(filename, '([A-Z0-9]+)\.parquet$', 1) = 'NIFTY50'
        )
        SELECT DISTINCT trade_date
        FROM nifty_daily
        WHERE window_rows >= 50
          AND close > ma50
    )
    SELECT
        COUNT(*)                                                      AS trades,
        ROUND(SUM(t.pnl), 0)                                         AS total_pnl_rs,
        ROUND(100.0 * SUM(CASE WHEN t.pnl > 0 THEN 1 ELSE 0 END)
                    / COUNT(*), 2)                                    AS win_rate,
        ROUND(SUM(CASE WHEN t.pnl > 0 THEN t.pnl ELSE 0 END)
            / NULLIF(ABS(SUM(CASE WHEN t.pnl < 0 THEN t.pnl ELSE 0 END)),0),4)
                                                                      AS profit_factor
    FROM best_trades t
    INNER JOIN regime_dates rd ON t.trade_date = rd.trade_date
""").df().iloc[0]

trades   = int(r["trades"])
pnl      = float(r["total_pnl_rs"])
cagr     = ((INITIAL_EQUITY + pnl) / INITIAL_EQUITY) ** (1 / YEARS) - 1
removed  = round(100 * (base_total - trades) / base_total, 1)
exp      = pnl / trades if trades > 0 else 0

con.close()

SEP = "=" * 72
print()
print(SEP)
print("  NIFTY50 REGIME SIGNAL  vs  BASELINE  vs  BEST (JSWSTEEL)")
print("  Filter: NIFTY50 daily close > MA50  (same-day, matches sweep method)")
print(SEP)

header = f"  {'master':<14} {'trades':>10} {'removed%':>9} {'total_pnl':>12} {'win_rate':>9} {'pf':>7} {'cagr':>8}"
print(header)
print("  " + "-" * 66)
print(f"  {'[NO FILTER]':<14} {base_total:>10,} {'0.0%':>9} "
      f"{int(base_pnl):>+12,} {base['win_rate']:>8.2f}% {base['profit_factor']:>7.4f} "
      f"{base_cagr*100:>7.2f}%")
print("  " + "-" * 66)
print(f"  {'JSWSTEEL*':<14} {'~est':>10} {'~est':>9} {'~est':>12} {'~est':>9} {'~est':>7} {'  +2.42%':>8}")
print("  " + "-" * 66)
print(f"  {'NIFTY50':<14} {trades:>10,} {removed:>8.1f}% "
      f"{int(pnl):>+12,} {float(r['win_rate']):>8.2f}% {float(r['profit_factor']):>7.4f} "
      f"{cagr*100:>7.2f}%")
print(SEP)
print()
print(f"  NIFTY50 regime CAGR  : {cagr*100:.2f}%")
print(f"  Baseline CAGR         : {base_cagr*100:.2f}%")
print(f"  Delta vs baseline     : {(cagr - base_cagr)*100:+.2f}pp")
print(f"  Trades kept           : {trades:,} / {base_total:,}  ({100-removed:.1f}% kept)")
print(f"  Total PnL             : Rs {int(pnl):+,}")
print(f"  Expectancy/trade      : Rs {exp:,.0f}")
print(SEP)
print()
print("  * JSWSTEEL was best single stock in the 29-stock sweep (same-day method)")
