"""
fv1_ma50_charts.py
==================
Generates 3 charts for the MA50-filtered portfolio (same-day v1, 8.77% result).
All PnL values are in rupees (actual portfolio Rs) to match CAGR reporting.

Outputs:
  outputs/reports/ma50_equity_curve.png
  outputs/reports/ma50_drawdown_chart.png
  outputs/reports/ma50_monthly_pnl_heatmap.png
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import warnings
warnings.filterwarnings("ignore")

import duckdb
import pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BASE        = pathlib.Path(__file__).resolve().parent.parent
DAILY_GLOB  = str(BASE / "data/historical/daily/*.parquet").replace("\\", "/")
TRADES_PATH = str(BASE / "outputs/trades/fv1_all_trades.csv").replace("\\", "/")
REPORTS_DIR = BASE / "outputs" / "reports"

INITIAL_EQUITY = 1_000_000

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

# ── Style constants (match existing charts) ────────────────────────────────────
CYAN   = "#00d4ff"
RED    = "#ff4444"
YELLOW = "#ffd700"
BG     = "#0d1117"

plt.style.use("dark_background")


# ── Load filtered trades via DuckDB ───────────────────────────────────────────
print("[1/4] Loading and filtering trades (MA50 same-day filter) ...")

con = duckdb.connect()

con.execute(f"""
    CREATE VIEW best_trades AS
    WITH raw AS (
        SELECT stock, atr_config, pnl,
            (CAST(entry_time AS TIMESTAMPTZ) AT TIME ZONE 'Asia/Kolkata')::DATE AS trade_date,
            (CAST(entry_time AS TIMESTAMPTZ) AT TIME ZONE 'Asia/Kolkata')       AS entry_ts_ist
        FROM read_csv_auto('{TRADES_PATH}')
    ),
    cfg AS (SELECT * FROM (VALUES {cfg_rows}) t(stock, best_config))
    SELECT r.stock, r.pnl, r.trade_date, r.entry_ts_ist
    FROM raw r JOIN cfg c ON r.stock = c.stock AND r.atr_config = c.best_config
    WHERE r.stock NOT IN ('VI', 'IDEA', 'NIFTY50')
""")

con.execute(f"""
    CREATE VIEW daily_ma50 AS
    WITH base AS (
        SELECT
            regexp_extract(filename, '([A-Z0-9]+)[.]parquet$', 1) AS stock,
            CAST(datetime AS DATE) AS trade_date,
            close,
            AVG(close) OVER (
                PARTITION BY regexp_extract(filename, '([A-Z0-9]+)[.]parquet$', 1)
                ORDER BY CAST(datetime AS DATE)
                ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
            ) AS ma50,
            COUNT(*) OVER (
                PARTITION BY regexp_extract(filename, '([A-Z0-9]+)[.]parquet$', 1)
                ORDER BY CAST(datetime AS DATE)
                ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
            ) AS window_rows
        FROM read_parquet('{DAILY_GLOB}', filename=true)
        WHERE regexp_extract(filename, '([A-Z0-9]+)[.]parquet$', 1) != 'NIFTY50'
    )
    SELECT stock, trade_date, close, ma50, window_rows FROM base
""")

# Filtered trades: only uptrend days (same-day v1)
filtered_df = con.execute("""
    SELECT
        t.stock,
        t.pnl,
        t.trade_date,
        t.entry_ts_ist
    FROM best_trades t
    JOIN daily_ma50 d ON t.stock = d.stock AND t.trade_date = d.trade_date
    WHERE d.window_rows >= 50 AND d.close > d.ma50
    ORDER BY t.entry_ts_ist
""").df()

con.close()

print(f"   Filtered trades: {len(filtered_df):,}")

# ── Build monthly series ───────────────────────────────────────────────────────
filtered_df["ym"] = pd.to_datetime(filtered_df["entry_ts_ist"]).dt.to_period("M")

monthly_pnl  = filtered_df.groupby("ym")["pnl"].sum()
cum_pnl      = monthly_pnl.cumsum()
equity_curve = cum_pnl + INITIAL_EQUITY   # absolute equity in Rs

periods  = list(cum_pnl.index)
eq_vals  = equity_curve.values
cum_vals = cum_pnl.values
x_idx    = np.arange(len(eq_vals))

peak_vals  = np.maximum.accumulate(eq_vals)
dd_pct     = ((eq_vals - peak_vals) / peak_vals) * 100


# ── Helper: x-axis month ticks ────────────────────────────────────────────────
def _month_xticks(ax, step=6):
    n = len(periods)
    tick_pos  = list(range(0, n, step))
    tick_labs = [str(periods[i]) for i in tick_pos]
    ax.set_xticks(tick_pos)
    ax.set_xticklabels(tick_labs, rotation=45, ha="right", fontsize=8)


# ── CHART 1: Equity Curve ─────────────────────────────────────────────────────
print("[2/4] Equity curve ...")

fig, (ax_eq, ax_dd) = plt.subplots(
    2, 1, figsize=(14, 9),
    gridspec_kw={"height_ratios": [3, 1]},
    sharex=True,
)
fig.patch.set_facecolor(BG)
for ax in (ax_eq, ax_dd):
    ax.set_facecolor(BG)

ax_eq.plot(x_idx, eq_vals / 1e5, color=CYAN, linewidth=2,
           label="Equity (Rs)", zorder=3)
ax_eq.fill_between(x_idx, peak_vals / 1e5, eq_vals / 1e5,
                   where=(eq_vals < peak_vals),
                   alpha=0.35, color=RED, label="Drawdown region", zorder=2)
ax_eq.axhline(INITIAL_EQUITY / 1e5, color=YELLOW, linestyle="--",
              linewidth=1, alpha=0.6, label=f"Initial equity (Rs {INITIAL_EQUITY/1e5:.0f}L)")

total_pnl = cum_vals[-1]
cagr = ((INITIAL_EQUITY + total_pnl) / INITIAL_EQUITY) ** (1/4) - 1

ax_eq.set_title(
    f"Portfolio Equity Curve — FV1 MA Bounce  |  MA50 Filter (same-day)  |  CAGR: {cagr*100:.2f}%",
    color="white", fontsize=13, fontweight="bold", pad=10,
)
ax_eq.set_ylabel("Equity (Rs Lakhs)", color="white")
ax_eq.legend(loc="upper left", fontsize=9)
ax_eq.grid(alpha=0.15)
ax_eq.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1fL"))

dd_sub = eq_vals - peak_vals
ax_dd.fill_between(x_idx, (dd_sub / 1e5), 0, alpha=0.7, color=RED)
ax_dd.plot(x_idx, dd_sub / 1e5, color=RED, linewidth=0.8)
ax_dd.set_ylabel("Drawdown (Rs L)", color=RED)
ax_dd.set_xlabel("Month", color="white")
ax_dd.grid(alpha=0.15)
_month_xticks(ax_dd)

plt.tight_layout()
out1 = REPORTS_DIR / "ma50_equity_curve.png"
fig.savefig(out1, dpi=150, bbox_inches="tight")
plt.close()
print(f"   Saved: {out1.name}")


# ── CHART 2: Drawdown % ───────────────────────────────────────────────────────
print("[3/4] Drawdown chart ...")

fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

ax.fill_between(x_idx, dd_pct, 0, alpha=0.7, color=RED)
ax.plot(x_idx, dd_pct, color=RED, linewidth=1.2)

max_dd   = dd_pct.min()
max_dd_m = periods[int(np.argmin(dd_pct))]
ax.annotate(
    f"Max DD: {max_dd:.1f}%\n({max_dd_m})",
    xy=(int(np.argmin(dd_pct)), max_dd),
    xytext=(int(np.argmin(dd_pct)) + 2, max_dd * 0.6),
    color=YELLOW, fontsize=9,
    arrowprops=dict(arrowstyle="->", color=YELLOW, lw=1),
)

ax.set_title(
    "Portfolio Drawdown (%) — FV1 MA Bounce  |  MA50 Filter (same-day)",
    color="white", fontsize=13, fontweight="bold",
)
ax.set_xlabel("Month", color="white")
ax.set_ylabel("Drawdown %", color=RED)
ax.grid(alpha=0.15)
_month_xticks(ax)

plt.tight_layout()
out2 = REPORTS_DIR / "ma50_drawdown_chart.png"
fig.savefig(out2, dpi=150, bbox_inches="tight")
plt.close()
print(f"   Saved: {out2.name}")


# ── CHART 3: Monthly PnL Heatmap ──────────────────────────────────────────────
print("[4/4] Monthly PnL heatmap ...")

monthly_df        = monthly_pnl.reset_index()
monthly_df["year"]  = monthly_df["ym"].dt.year
monthly_df["month"] = monthly_df["ym"].dt.month

years_list  = sorted(monthly_df["year"].unique())
month_names = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]

heatmap = monthly_df.pivot(index="month", columns="year", values="pnl")
heatmap = heatmap.reindex(index=range(1, 13), columns=years_list)

# Rs values — display in thousands
heatmap_k = heatmap / 1000
vmax = heatmap_k.abs().max().max()

fig, ax = plt.subplots(figsize=(max(8, len(years_list) * 2.5), 7))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

im = ax.imshow(heatmap_k.values, aspect="auto",
               cmap="RdYlGn", vmin=-vmax, vmax=vmax)

ax.set_xticks(range(len(years_list)))
ax.set_xticklabels(years_list, color="white", fontsize=11)
ax.set_yticks(range(12))
ax.set_yticklabels(month_names, color="white", fontsize=10)
ax.set_title(
    "Monthly Portfolio PnL Heatmap — FV1 MA Bounce  |  MA50 Filter (same-day)  [Rs '000]",
    color="white", fontsize=13, fontweight="bold", pad=12,
)

cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
cb.set_label("PnL (Rs '000)", color="white")
cb.ax.yaxis.set_tick_params(color="white")
plt.setp(cb.ax.yaxis.get_ticklabels(), color="white")

for r in range(12):
    for c in range(len(years_list)):
        val = heatmap_k.values[r, c]
        if not np.isnan(val):
            txt_color = "white" if abs(val) > vmax * 0.5 else "black"
            ax.text(c, r, f"{val:+.0f}k", ha="center", va="center",
                    fontsize=8, color=txt_color, fontweight="bold")

plt.tight_layout()
out3 = REPORTS_DIR / "ma50_monthly_pnl_heatmap.png"
fig.savefig(out3, dpi=150, bbox_inches="tight")
plt.close()
print(f"   Saved: {out3.name}")

print()
print(f"  Total PnL (filtered) : Rs {total_pnl:+,.0f}")
print(f"  CAGR                 : {cagr*100:.2f}%")
print(f"  Max Drawdown         : {max_dd:.1f}%  ({max_dd_m})")
print("[DONE]")
