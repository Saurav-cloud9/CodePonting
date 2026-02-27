"""
fv1_ma_filter_sweep.py
======================
Runs 8 MA trend filter combinations (F0–F7) on fv1_all_trades.csv.
ALL filters use PREVIOUS DAY's close (LAG) — strictly no lookahead.

Outputs:
  outputs/stats/ma_filter_comparison.csv
  outputs/stats/best_filter_per_stock.csv
  outputs/reports/ma_filter_comparison.png
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import duckdb
import pathlib
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE        = pathlib.Path(__file__).resolve().parent.parent
DAILY_DIR   = BASE / "data" / "historical" / "daily"
TRADES_CSV  = BASE / "outputs" / "trades"  / "fv1_all_trades.csv"
STATS_DIR   = BASE / "outputs" / "stats"
REPORTS_DIR = BASE / "outputs" / "reports"

DAILY_GLOB  = str(DAILY_DIR / "*.parquet").replace("\\", "/")
TRADES_PATH = str(TRADES_CSV).replace("\\", "/")

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

FILTER_DEFS = {
    "F0": "1=1",                                                  # no filter
    "F1": "prev_close > prev_ma50",
    "F2": "prev_close > prev_ma100",
    "F3": "prev_close > prev_ma200",
    "F4": "prev_close > prev_ma50  AND prev_close > prev_ma100",
    "F5": "prev_close > prev_ma50  AND prev_close > prev_ma200",
    "F6": "prev_close > prev_ma100 AND prev_close > prev_ma200",
    "F7": "prev_close > prev_ma50  AND prev_close > prev_ma100 AND prev_close > prev_ma200",
}

FILTER_LABELS = {
    "F0": "F0\nNo filter",
    "F1": "F1\n>MA50",
    "F2": "F2\n>MA100",
    "F3": "F3\n>MA200",
    "F4": "F4\n>MA50\n&MA100",
    "F5": "F5\n>MA50\n&MA200",
    "F6": "F6\n>MA100\n&MA200",
    "F7": "F7\n>MA50\n&MA100\n&MA200",
}

print("[1/5] Setting up DuckDB views …")
con = duckdb.connect()

# ── Trades view ────────────────────────────────────────────────────────────────
con.execute(f"""
    CREATE VIEW trades_raw AS
    SELECT
        stock,
        atr_config,
        pnl,
        qty,
        pnl / qty  AS pps,
        (CAST(entry_time AS TIMESTAMPTZ) AT TIME ZONE 'Asia/Kolkata')::DATE AS trade_date
    FROM read_csv_auto('{TRADES_PATH}')
""")

# ── Best-config filter ─────────────────────────────────────────────────────────
cfg_rows = ", ".join(f"('{k}', '{v}')" for k, v in BEST_CFG.items())
con.execute(f"""
    CREATE VIEW best_cfg AS
    SELECT * FROM (VALUES {cfg_rows}) t(stock, best_config)
""")

con.execute("""
    CREATE VIEW best_trades AS
    SELECT t.stock, t.pnl, t.pps, t.trade_date
    FROM trades_raw t
    JOIN best_cfg b ON t.stock = b.stock AND t.atr_config = b.best_config
    WHERE t.stock NOT IN ('VI', 'IDEA', 'NIFTY50')
""")

# ── Daily MA table: MA50 / MA100 / MA200 + all LAG columns ────────────────────
print("[2/5] Computing daily MA50 / MA100 / MA200 with LAG from parquet files …")

con.execute(f"""
    CREATE VIEW daily_mas AS
    WITH base AS (
        SELECT
            regexp_extract(filename, '([A-Z0-9]+)\\.parquet$', 1)  AS stock,
            CAST(datetime AS DATE)                                   AS trade_date,
            close,
            AVG(close) OVER w50                                      AS ma50,
            AVG(close) OVER w100                                     AS ma100,
            AVG(close) OVER w200                                     AS ma200,
            COUNT(*)   OVER w50                                      AS n50,
            COUNT(*)   OVER w100                                     AS n100,
            COUNT(*)   OVER w200                                     AS n200
        FROM read_parquet('{DAILY_GLOB}', filename=true)
        WHERE regexp_extract(filename, '([A-Z0-9]+)\\.parquet$', 1) != 'NIFTY50'
        WINDOW
            w50  AS (PARTITION BY regexp_extract(filename, '([A-Z0-9]+)\\.parquet$', 1)
                     ORDER BY CAST(datetime AS DATE)
                     ROWS BETWEEN 49  PRECEDING AND CURRENT ROW),
            w100 AS (PARTITION BY regexp_extract(filename, '([A-Z0-9]+)\\.parquet$', 1)
                     ORDER BY CAST(datetime AS DATE)
                     ROWS BETWEEN 99  PRECEDING AND CURRENT ROW),
            w200 AS (PARTITION BY regexp_extract(filename, '([A-Z0-9]+)\\.parquet$', 1)
                     ORDER BY CAST(datetime AS DATE)
                     ROWS BETWEEN 199 PRECEDING AND CURRENT ROW)
    )
    SELECT
        stock,
        trade_date,
        -- LAG columns: previous trading day's values (no lookahead)
        LAG(close) OVER (PARTITION BY stock ORDER BY trade_date)  AS prev_close,
        LAG(ma50)  OVER (PARTITION BY stock ORDER BY trade_date)  AS prev_ma50,
        LAG(ma100) OVER (PARTITION BY stock ORDER BY trade_date)  AS prev_ma100,
        LAG(ma200) OVER (PARTITION BY stock ORDER BY trade_date)  AS prev_ma200,
        LAG(n50)   OVER (PARTITION BY stock ORDER BY trade_date)  AS prev_n50,
        LAG(n100)  OVER (PARTITION BY stock ORDER BY trade_date)  AS prev_n100,
        LAG(n200)  OVER (PARTITION BY stock ORDER BY trade_date)  AS prev_n200
    FROM base
""")

# ── Enrich trades with MA data ─────────────────────────────────────────────────
# NaN-safe: trades where any required MA is NULL are flagged and skipped
# (they are in the early period before MA windows fill up)
con.execute("""
    CREATE VIEW enriched AS
    SELECT
        t.stock,
        t.pnl,
        t.pps,
        -- Strictly NULL-safe flags: skip if MA not yet available
        CASE WHEN d.prev_n50  >= 50  AND d.prev_close > d.prev_ma50  THEN 1 ELSE 0 END AS f1,
        CASE WHEN d.prev_n100 >= 100 AND d.prev_close > d.prev_ma100 THEN 1 ELSE 0 END AS f2,
        CASE WHEN d.prev_n200 >= 200 AND d.prev_close > d.prev_ma200 THEN 1 ELSE 0 END AS f3,
        -- Combination flags
        CASE WHEN d.prev_n50  >= 50  AND d.prev_close > d.prev_ma50
              AND d.prev_n100 >= 100 AND d.prev_close > d.prev_ma100 THEN 1 ELSE 0 END AS f4,
        CASE WHEN d.prev_n50  >= 50  AND d.prev_close > d.prev_ma50
              AND d.prev_n200 >= 200 AND d.prev_close > d.prev_ma200 THEN 1 ELSE 0 END AS f5,
        CASE WHEN d.prev_n100 >= 100 AND d.prev_close > d.prev_ma100
              AND d.prev_n200 >= 200 AND d.prev_close > d.prev_ma200 THEN 1 ELSE 0 END AS f6,
        CASE WHEN d.prev_n50  >= 50  AND d.prev_close > d.prev_ma50
              AND d.prev_n100 >= 100 AND d.prev_close > d.prev_ma100
              AND d.prev_n200 >= 200 AND d.prev_close > d.prev_ma200 THEN 1 ELSE 0 END AS f7,
        -- NULL flag: any MA data missing
        CASE WHEN d.prev_close IS NULL
                  OR d.prev_ma50 IS NULL
                  OR d.prev_ma100 IS NULL
                  OR d.prev_ma200 IS NULL THEN 1 ELSE 0 END AS has_null_ma
    FROM best_trades t
    LEFT JOIN daily_mas d
           ON t.stock = d.stock AND t.trade_date = d.trade_date
""")

# Count NULL-MA trades
null_count = con.execute("SELECT COUNT(*) FROM enriched WHERE has_null_ma = 1").fetchone()[0]
total      = con.execute("SELECT COUNT(*) FROM enriched").fetchone()[0]
print(f"   Trades with NULL MA data (warm-up period): {null_count:,} / {total:,} "
      f"({100*null_count/total:.1f}%) — these are excluded from ALL filters")

# ── Step 3: Aggregate metrics for each filter ──────────────────────────────────
print("[3/5] Running all 8 filter combinations …")

def agg_query(flag_col):
    where = "1=1" if flag_col == "f0" else f"{flag_col} = 1"
    return f"""
        SELECT
            COUNT(*)                                                         AS trades,
            ROUND(SUM(pnl), 0)                                              AS total_pnl_rs,
            ROUND(SUM(pps), 4)                                              AS total_pps,
            ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)
                        / COUNT(*), 2)                                       AS win_rate,
            ROUND(SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END)
                / NULLIF(ABS(SUM(CASE WHEN pnl < 0 THEN pnl ELSE 0 END)),0),4)
                                                                             AS profit_factor,
            ROUND(AVG(pps), 4)                                              AS expectancy
        FROM enriched
        WHERE {where}
    """

results = []
for fname in ["f0","f1","f2","f3","f4","f5","f6","f7"]:
    row = con.execute(agg_query(fname)).df().iloc[0]
    pnl_rs = row["total_pnl_rs"]
    cagr   = ((INITIAL_EQUITY + pnl_rs) / INITIAL_EQUITY) ** (1/YEARS) - 1
    baseline_trades = total

    results.append({
        "filter":           fname.upper(),
        "trades":           int(row["trades"]),
        "trades_removed_%": round(100 * (total - row["trades"]) / total, 1),
        "total_pnl_rs":     int(pnl_rs),
        "win_rate":         float(row["win_rate"]),
        "profit_factor":    float(row["profit_factor"]),
        "expectancy":       float(row["expectancy"]),
        "cagr_%":           round(cagr * 100, 2),
    })

results_df = pd.DataFrame(results)
out_csv = STATS_DIR / "ma_filter_comparison.csv"
results_df.to_csv(out_csv, index=False)
print(f"   Saved: {out_csv}")

# Print summary table
print()
print("=" * 80)
print("  MA FILTER SWEEP — PORTFOLIO SUMMARY (all LAG, no lookahead)")
print("=" * 80)
print(results_df.to_string(index=False))
print()

# Identify best filter by CAGR (excluding F0)
best_row = results_df[results_df["filter"] != "F0"].sort_values("cagr_%", ascending=False).iloc[0]
best_filter_name = best_row["filter"].lower()
print(f"  Best filter by CAGR: {best_row['filter']}  "
      f"(CAGR={best_row['cagr_%']:.2f}%  PF={best_row['profit_factor']:.4f}  "
      f"WR={best_row['win_rate']:.2f}%  trades={best_row['trades']:,})")

# ── Step 4: Per-stock breakdown for best filter ────────────────────────────────
print(f"\n[4/5] Per-stock breakdown for best filter ({best_row['filter']}) …")

best_flag = best_filter_name   # e.g. "f3"
per_stock_q = f"""
SELECT
    stock,
    COUNT(*)                                                          AS trades_before,
    SUM(CASE WHEN {best_flag} = 1 THEN 1 ELSE 0 END)                AS trades_after,
    ROUND(100.0 * SUM(CASE WHEN {best_flag}=1 THEN 1 ELSE 0 END)
               / COUNT(*), 1)                                         AS kept_pct,
    ROUND(SUM(pnl), 0)                                               AS pnl_before_rs,
    ROUND(SUM(CASE WHEN {best_flag}=1 THEN pnl ELSE 0 END), 0)      AS pnl_after_rs,
    ROUND(SUM(CASE WHEN {best_flag}=1 THEN pnl ELSE 0 END)
          - SUM(pnl), 0)                                             AS pnl_delta_rs,
    ROUND(100.0 * SUM(CASE WHEN pnl>0 THEN 1 ELSE 0 END)
               / COUNT(*), 1)                                         AS wr_before,
    ROUND(100.0 * SUM(CASE WHEN {best_flag}=1 AND pnl>0 THEN 1 ELSE 0 END)
               / NULLIF(SUM(CASE WHEN {best_flag}=1 THEN 1 ELSE 0 END), 0), 1)
                                                                      AS wr_after
FROM enriched
GROUP BY stock
ORDER BY pnl_delta_rs DESC
"""
ps_df = con.execute(per_stock_q).df()
ps_df["best_filter"] = best_row["filter"]
out_ps = STATS_DIR / "best_filter_per_stock.csv"
ps_df.to_csv(out_ps, index=False)
print(f"   Saved: {out_ps}")

print()
print(f"  PER-STOCK: {best_row['filter']} filter  (sorted by PnL delta)")
print("  " + "-"*76)
print(ps_df.to_string(index=False))
worse  = ps_df[ps_df["pnl_delta_rs"] < 0]
better = ps_df[ps_df["pnl_delta_rs"] > 0]
print(f"\n  Improved: {len(better)} stocks   Worse: {len(worse)} stocks")

# ── Step 5: Chart ──────────────────────────────────────────────────────────────
print("\n[5/5] Generating chart …")
plt.style.use("dark_background")

filters  = results_df["filter"].tolist()
x        = np.arange(len(filters))
n_f      = len(filters)

cagrs    = results_df["cagr_%"].tolist()
pfs      = results_df["profit_factor"].tolist()
wrs      = results_df["win_rate"].tolist()

CYAN     = "#00d4ff"
YELLOW   = "#ffd700"
GREEN    = "#00e676"
RED      = "#ff4444"
BG       = "#0d1117"

fig, axes = plt.subplots(3, 1, figsize=(14, 11), facecolor=BG)
fig.suptitle(
    "FV1 MA Bounce — 8 Trend Filter Combinations\n"
    "(all using previous day's close — strict no lookahead)",
    color="white", fontsize=13, fontweight="bold", y=0.98,
)

bar_colors = [GREEN if v > 0 else RED for v in cagrs]

def style_ax(ax):
    ax.set_facecolor(BG)
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("#444")
    ax.spines["left"].set_color("#444")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.15, linestyle="--")

# ── Subplot 1: CAGR ────────────────────────────────────────────────────────────
ax1 = axes[0]
ax1.set_facecolor(BG)
bars1 = ax1.bar(x, cagrs, color=bar_colors, edgecolor="none", width=0.6)
ax1.axhline(0, color="#888", linewidth=0.8, linestyle="--")
ax1.set_ylabel("CAGR  (%)", color="white", fontsize=10)
ax1.set_xticks(x)
ax1.set_xticklabels([FILTER_LABELS[f] for f in filters], color="white", fontsize=8)
style_ax(ax1)
# Annotate
for bar, val in zip(bars1, cagrs):
    ypos = val + 0.15 if val >= 0 else val - 0.4
    ax1.text(bar.get_x() + bar.get_width()/2, ypos,
             f"{val:+.2f}%", ha="center", va="bottom", fontsize=8, color="white")
# Highlight best
best_idx = cagrs.index(max(cagrs))
bars1[best_idx].set_edgecolor(YELLOW)
bars1[best_idx].set_linewidth(2)

# ── Subplot 2: Profit Factor ───────────────────────────────────────────────────
ax2 = axes[1]
ax2.set_facecolor(BG)
pf_colors = [GREEN if v >= 1.0 else RED for v in pfs]
bars2 = ax2.bar(x, pfs, color=pf_colors, edgecolor="none", width=0.6)
ax2.axhline(1.0, color=YELLOW, linewidth=1.2, linestyle="--", label="Breakeven PF=1.0")
ax2.set_ylabel("Profit Factor", color="white", fontsize=10)
ax2.set_xticks(x)
ax2.set_xticklabels([FILTER_LABELS[f] for f in filters], color="white", fontsize=8)
ax2.legend(fontsize=8, loc="upper right")
style_ax(ax2)
for bar, val in zip(bars2, pfs):
    ypos = val + 0.003
    ax2.text(bar.get_x() + bar.get_width()/2, ypos,
             f"{val:.4f}", ha="center", va="bottom", fontsize=8, color="white")
bars2[best_idx].set_edgecolor(YELLOW)
bars2[best_idx].set_linewidth(2)

# ── Subplot 3: Win Rate ────────────────────────────────────────────────────────
ax3 = axes[2]
ax3.set_facecolor(BG)
bars3 = ax3.bar(x, wrs, color=CYAN, edgecolor="none", width=0.6, alpha=0.85)
ax3.set_ylabel("Win Rate  (%)", color="white", fontsize=10)
ax3.set_xticks(x)
ax3.set_xticklabels([FILTER_LABELS[f] for f in filters], color="white", fontsize=8)
style_ax(ax3)
# Add trades-removed annotation on win rate bars
for i, (bar, val, rem) in enumerate(zip(bars3, wrs, results_df["trades_removed_%"])):
    ax3.text(bar.get_x() + bar.get_width()/2, val + 0.05,
             f"{val:.2f}%\n({rem:.0f}% removed)", ha="center", va="bottom",
             fontsize=7, color="white")
bars3[best_idx].set_edgecolor(YELLOW)
bars3[best_idx].set_linewidth(2)

# Add yellow star label for best filter
for ax in axes:
    ymin, ymax = ax.get_ylim()
    ax.set_xlim(-0.6, n_f - 0.4)

plt.tight_layout(rect=[0, 0, 1, 0.97])
chart_path = REPORTS_DIR / "ma_filter_comparison.png"
fig.savefig(chart_path, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close()
print(f"   Saved: {chart_path}")

# ── Final summary ──────────────────────────────────────────────────────────────
print()
print("=" * 80)
print("  FINAL SUMMARY")
print("=" * 80)
for _, r in results_df.iterrows():
    marker = "  <-- BEST" if r["filter"] == best_row["filter"] else ""
    print(f"  {r['filter']}:  CAGR={r['cagr_%']:>7.2f}%  "
          f"PF={r['profit_factor']:.4f}  WR={r['win_rate']:.2f}%  "
          f"Trades={r['trades']:>6,}  Removed={r['trades_removed_%']:.1f}%{marker}")
print("=" * 80)
print("\n[DONE]")

con.close()
