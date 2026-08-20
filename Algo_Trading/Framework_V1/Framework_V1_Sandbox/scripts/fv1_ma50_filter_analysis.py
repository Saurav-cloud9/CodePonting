"""
fv1_ma50_filter_analysis.py
============================
SQL-based analysis (DuckDB) of how the MA50 trend filter
would change FV1 portfolio PnL without re-running the backtest.

Runs TWO versions of the filter and compares all three scenarios:
  v0 — No filter         : all trades
  v1 — Same-day close    : trade_day_close > MA50  (minor lookahead)
  v2 — Prev-day LAG      : prev_day_close > prev_day_MA50  (strict, no lookahead)
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import duckdb
import pathlib

BASE      = pathlib.Path(__file__).resolve().parent.parent
DAILY_DIR = BASE / "data" / "historical" / "daily"
TRADES    = BASE / "outputs" / "trades" / "fv1_all_trades.csv"

BEST_CFG = {
    "ADANIPORTS": "Extreme-2", "ASHOKLEY": "Extreme-4", "AXISBANK": "Extreme-2",
    "BANDHANBNK": "Extreme-2", "BHARTIARTL": "Extreme-1", "CIPLA": "Extreme-2",
    "COALINDIA": "Extreme-1", "DABUR": "Extreme-3", "DIVISLAB": "Extreme-4",
    "HDFCBANK": "Extreme-4", "HINDALCO": "Extreme-4", "ICICIBANK": "Extreme-4",
    "INDUSINDBK": "Extreme-4", "INFY": "Extreme-2", "ITC": "Extreme-1",
    "JSWSTEEL": "Extreme-4", "NATIONALUM": "Extreme-2", "NTPC": "Extreme-2",
    "ONGC": "Extreme-2", "PNB": "Extreme-2", "POWERGRID": "Extreme-3",
    "RELIANCE": "Extreme-2", "SBIN": "Extreme-1", "SUNPHARMA": "Extreme-4",
    "TATAMOTORS": "Extreme-1", "TATASTEEL": "Extreme-2", "TECHM": "Extreme-2",
    "VEDL": "Extreme-4", "WIPRO": "Extreme-1",
}

DAILY_GLOB = str(DAILY_DIR / "*.parquet").replace("\\", "/")
TRADES_PATH = str(TRADES).replace("\\", "/")

con = duckdb.connect()

# ── Register trades ────────────────────────────────────────────────────────────
con.execute(f"""
    CREATE VIEW trades AS
    SELECT
        stock,
        atr_config,
        pnl,
        qty,
        pnl / qty  AS pps,
        CAST(entry_time AS TIMESTAMPTZ) AS entry_ts,
        (CAST(entry_time AS TIMESTAMPTZ) AT TIME ZONE 'Asia/Kolkata')::DATE AS trade_date
    FROM read_csv_auto('{TRADES_PATH}')
""")

# ── Compute daily MA50 + LAG columns from parquet files ───────────────────────
con.execute(f"""
    CREATE VIEW daily_ma50 AS
    WITH base AS (
        SELECT
            regexp_extract(filename, '([A-Z0-9]+)\\.parquet$', 1) AS stock,
            CAST(datetime AS DATE)                                  AS trade_date,
            close                                                   AS daily_close,
            AVG(close) OVER (
                PARTITION BY regexp_extract(filename, '([A-Z0-9]+)\\.parquet$', 1)
                ORDER BY CAST(datetime AS DATE)
                ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
            )                                                       AS ma50,
            COUNT(*) OVER (
                PARTITION BY regexp_extract(filename, '([A-Z0-9]+)\\.parquet$', 1)
                ORDER BY CAST(datetime AS DATE)
                ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
            )                                                       AS window_rows
        FROM read_parquet('{DAILY_GLOB}', filename=true)
        WHERE regexp_extract(filename, '([A-Z0-9]+)\\.parquet$', 1) != 'NIFTY50'
    )
    SELECT
        stock,
        trade_date,
        daily_close,
        ma50,
        window_rows,
        -- Previous trading day values (true no-lookahead)
        LAG(daily_close) OVER (PARTITION BY stock ORDER BY trade_date) AS prev_close,
        LAG(ma50)        OVER (PARTITION BY stock ORDER BY trade_date) AS prev_ma50,
        LAG(window_rows) OVER (PARTITION BY stock ORDER BY trade_date) AS prev_window_rows
    FROM base
""")

# ── Best-config lookup table ───────────────────────────────────────────────────
cfg_rows = ", ".join(f"('{k}', '{v}')" for k, v in BEST_CFG.items())
con.execute(f"""
    CREATE VIEW best_cfg AS
    SELECT * FROM (VALUES {cfg_rows}) t(stock, best_config)
""")

# ── Best trades (one config per stock) ────────────────────────────────────────
con.execute("""
    CREATE VIEW best_trades AS
    SELECT t.*
    FROM trades t
    JOIN best_cfg b ON t.stock = b.stock AND t.atr_config = b.best_config
    WHERE t.stock NOT IN ('VI', 'IDEA', 'NIFTY50')
""")

# ══════════════════════════════════════════════════════════════════════════════
# QUERY 1 — Portfolio-level: 3-way comparison (no filter / same-day / LAG)
# ══════════════════════════════════════════════════════════════════════════════
PORTFOLIO_Q = """
WITH enriched AS (
    SELECT
        t.stock,
        t.pnl,
        t.pps,
        -- v1: same-day close vs same-day MA50  (minor lookahead)
        CASE
            WHEN d.window_rows >= 50 AND d.daily_close > d.ma50 THEN 1
            ELSE 0
        END AS uptrend_v1,
        -- v2: previous day close vs previous day MA50  (strict, no lookahead)
        CASE
            WHEN d.prev_window_rows >= 50 AND d.prev_close > d.prev_ma50 THEN 1
            ELSE 0
        END AS uptrend_v2
    FROM best_trades t
    LEFT JOIN daily_ma50 d
           ON t.stock = d.stock AND t.trade_date = d.trade_date
),

agg AS (
    SELECT
        COUNT(*)                                                        AS n,
        ROUND(SUM(pnl), 0)                                             AS pnl,
        ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)
                    / COUNT(*), 2)                                      AS wr,
        ROUND(SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END)
            / NULLIF(ABS(SUM(CASE WHEN pnl < 0 THEN pnl ELSE 0 END)), 0), 4)
                                                                        AS pf,
        'v0  No filter         (all trades)'                           AS scenario
    FROM enriched
    UNION ALL
    SELECT
        COUNT(*), ROUND(SUM(pnl),0),
        ROUND(100.0*SUM(CASE WHEN pnl>0 THEN 1 ELSE 0 END)/COUNT(*),2),
        ROUND(SUM(CASE WHEN pnl>0 THEN pnl ELSE 0 END)
            / NULLIF(ABS(SUM(CASE WHEN pnl<0 THEN pnl ELSE 0 END)),0),4),
        'v1  Same-day MA50     (minor lookahead)'
    FROM enriched WHERE uptrend_v1 = 1
    UNION ALL
    SELECT
        COUNT(*), ROUND(SUM(pnl),0),
        ROUND(100.0*SUM(CASE WHEN pnl>0 THEN 1 ELSE 0 END)/COUNT(*),2),
        ROUND(SUM(CASE WHEN pnl>0 THEN pnl ELSE 0 END)
            / NULLIF(ABS(SUM(CASE WHEN pnl<0 THEN pnl ELSE 0 END)),0),4),
        'v2  Prev-day MA50 LAG (no lookahead)'
    FROM enriched WHERE uptrend_v2 = 1
)
SELECT scenario, n AS trades, pnl AS total_pnl_rs, wr AS win_rate_pct, pf AS profit_factor
FROM agg
"""

# ══════════════════════════════════════════════════════════════════════════════
# QUERY 2 — Per-stock: v1 vs v2 side-by-side
# ══════════════════════════════════════════════════════════════════════════════
PER_STOCK_Q = """
WITH enriched AS (
    SELECT
        t.stock, t.pnl,
        CASE WHEN d.window_rows      >= 50 AND d.daily_close > d.ma50      THEN 1 ELSE 0 END AS v1,
        CASE WHEN d.prev_window_rows >= 50 AND d.prev_close  > d.prev_ma50 THEN 1 ELSE 0 END AS v2
    FROM best_trades t
    LEFT JOIN daily_ma50 d ON t.stock = d.stock AND t.trade_date = d.trade_date
)
SELECT
    stock,
    COUNT(*)                                                            AS trades,
    ROUND(SUM(pnl), 0)                                                 AS pnl_no_filter,
    -- v1 same-day
    SUM(CASE WHEN v1=1 THEN 1 ELSE 0 END)                             AS v1_trades,
    ROUND(SUM(CASE WHEN v1=1 THEN pnl ELSE 0 END), 0)                 AS v1_pnl,
    ROUND(SUM(CASE WHEN v1=1 THEN pnl ELSE 0 END) - SUM(pnl), 0)     AS v1_delta,
    -- v2 prev-day LAG
    SUM(CASE WHEN v2=1 THEN 1 ELSE 0 END)                             AS v2_trades,
    ROUND(SUM(CASE WHEN v2=1 THEN pnl ELSE 0 END), 0)                 AS v2_pnl,
    ROUND(SUM(CASE WHEN v2=1 THEN pnl ELSE 0 END) - SUM(pnl), 0)     AS v2_delta,
    -- v1 vs v2 pnl difference
    ROUND(SUM(CASE WHEN v2=1 THEN pnl ELSE 0 END)
        - SUM(CASE WHEN v1=1 THEN pnl ELSE 0 END), 0)                 AS v2_vs_v1_delta
FROM enriched
GROUP BY stock
ORDER BY v2_pnl DESC
"""

# ══════════════════════════════════════════════════════════════════════════════
# RUN & PRINT
# ══════════════════════════════════════════════════════════════════════════════
SEP  = "=" * 78
SEP2 = "-" * 78
IE   = 1_000_000

print()
print(SEP)
print("  FV1 MA Bounce — MA50 Filter: Same-Day vs Prev-Day LAG Comparison")
print(SEP)

port_df = con.execute(PORTFOLIO_Q).df()
print(port_df.to_string(index=False))

print()
print(SEP2)
# CAGR for all three rows
for _, row in port_df.iterrows():
    cagr = ((IE + row["total_pnl_rs"]) / IE) ** (1/4) - 1
    label = row["scenario"].split()[0]
    print(f"  CAGR {label:<4}: {cagr*100:>7.2f}%   "
          f"trades={int(row['trades']):>6,}   "
          f"PnL = Rs {row['total_pnl_rs']:>+12,.0f}")

# Key delta numbers
r_v0 = port_df.iloc[0]
r_v1 = port_df.iloc[1]
r_v2 = port_df.iloc[2]

print()
print(f"  v1 vs v0 : Rs {r_v1['total_pnl_rs']-r_v0['total_pnl_rs']:>+10,.0f}  "
      f"({(r_v1['total_pnl_rs']-r_v0['total_pnl_rs'])/IE*100:+.2f}% of initial equity)  "
      f"trades removed: {int(r_v0['trades']-r_v1['trades']):,}")
print(f"  v2 vs v0 : Rs {r_v2['total_pnl_rs']-r_v0['total_pnl_rs']:>+10,.0f}  "
      f"({(r_v2['total_pnl_rs']-r_v0['total_pnl_rs'])/IE*100:+.2f}% of initial equity)  "
      f"trades removed: {int(r_v0['trades']-r_v2['trades']):,}")
print(f"  v2 vs v1 : Rs {r_v2['total_pnl_rs']-r_v1['total_pnl_rs']:>+10,.0f}  "
      f"(difference between the two filter versions)")

print()
print(SEP)
print("  PER-STOCK: No filter | v1 Same-day | v2 Prev-day LAG  (sorted by v2 PnL)")
print(SEP)
ps_df = con.execute(PER_STOCK_Q).df()
print(ps_df.to_string(index=False))

# Summary
v2_worse = ps_df[ps_df["v2_delta"] < 0]
v2_better = ps_df[ps_df["v2_delta"] > 0]
v1_v2_differ = ps_df[ps_df["v2_vs_v1_delta"] != 0]
print()
print(f"  Stocks improved by v2 (prev-day LAG) : {len(v2_better)}")
print(f"  Stocks worse under  v2               : {len(v2_worse)}")
print(f"  Stocks where v1 != v2 PnL            : {len(v1_v2_differ)}")
print()
print("  Biggest v2 vs v1 divergences (where LAG version differs most):")
top_diff = ps_df.reindex(ps_df["v2_vs_v1_delta"].abs().sort_values(ascending=False).index).head(8)
for _, r in top_diff.iterrows():
    direction = "LAG better" if r["v2_vs_v1_delta"] > 0 else "same-day better"
    print(f"    {r['stock']:<12}  v1_pnl={r['v1_pnl']:>+8,.0f}  "
          f"v2_pnl={r['v2_pnl']:>+8,.0f}  "
          f"diff={r['v2_vs_v1_delta']:>+7,.0f}  ({direction})")
print(SEP)

con.close()
