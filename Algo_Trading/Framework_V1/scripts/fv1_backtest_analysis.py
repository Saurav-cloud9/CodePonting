#!/usr/bin/env python3
"""
fv1_backtest_analysis.py
========================
Computes comprehensive backtest performance metrics for the FV1 MA Bounce strategy.

Outputs:
  outputs/stats/fv1_metrics.csv           — per-stock metrics (best config)
  outputs/stats/fv1_portfolio_metrics.txt — portfolio-level metrics
  outputs/reports/portfolio_equity_curve.png
  outputs/reports/top5_equity_curves.png
  outputs/reports/drawdown_chart.png
  outputs/reports/monthly_pnl_heatmap.png
  outputs/reports/profit_factor_by_stock.png
"""

import sys, io
# Force UTF-8 stdout/stderr (needed on Windows cp1252 terminals)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

# ─── PATHS ────────────────────────────────────────────────────────────────────
BASE         = Path(__file__).resolve().parent.parent
TRADES_FILE  = BASE / "outputs" / "trades" / "fv1_all_trades.csv"
RESULTS_FILE = BASE / "outputs" / "trades" / "fv1_30stocks_results.csv"
STATS_DIR    = BASE / "outputs" / "stats"
REPORTS_DIR  = BASE / "outputs" / "reports"

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
# Best configs for the 5 specified stocks (override auto-detection)
SPECIFIED_BEST = {
    "SUNPHARMA": "Extreme-4",
    "BHARTIARTL": "Extreme-1",
    "HDFCBANK":   "Extreme-4",
    "ICICIBANK":  "Extreme-4",
    "ASHOKLEY":   "Extreme-4",
}
EXCLUDE         = {"VI", "IDEA", "NIFTY50"}
TOP5            = ["SUNPHARMA", "BHARTIARTL", "HDFCBANK", "ICICIBANK", "ASHOKLEY"]
INITIAL_EQUITY  = 1_000_000          # ₹10,00,000
YEARS_BACKTEST  = 4
LOW_TRADE_FLAG  = 100

# Colour palette (dark theme)
CYAN   = "#00d4ff"
RED    = "#ff4444"
YELLOW = "#ffd700"
GREEN  = "#00e676"
STOCK_COLORS = [
    "#00d4ff", "#ff6b6b", "#ffd700", "#00e676", "#a78bfa",
    "#fb923c", "#34d399", "#f472b6", "#60a5fa", "#facc15",
]

# ─── LOAD & PREP ──────────────────────────────────────────────────────────────
print("[1/6] Loading data …")
df = pd.read_csv(TRADES_FILE)
results_df = pd.read_csv(RESULTS_FILE)

df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True)
df["exit_time"]  = pd.to_datetime(df["exit_time"],  utc=True)
df["pps"]        = df["pnl"] / df["qty"]          # per-share PnL
df["ym"]         = df["entry_time"].dt.to_period("M")

# ─── DETERMINE BEST CONFIG PER STOCK ─────────────────────────────────────────
print("[2/6] Determining best config per stock …")
res_clean   = results_df[~results_df["stock"].isin(EXCLUDE)].copy()
best_idx    = res_clean.groupby("stock")["pnl_per_share"].idxmax()
best_cfg    = dict(zip(
    res_clean.loc[best_idx, "stock"],
    res_clean.loc[best_idx, "config"],
))
best_cfg.update(SPECIFIED_BEST)          # override with user-specified configs

all_stocks  = sorted(best_cfg.keys())
print(f"   → Portfolio: {len(all_stocks)} stocks")
print(f"   → Best configs: {best_cfg}")

# ─── FILTER TO BEST CONFIG PER STOCK ─────────────────────────────────────────
df_clean = df[~df["stock"].isin(EXCLUDE)].copy()

# Efficient filter: merge with best-config map
cfg_map   = pd.DataFrame(list(best_cfg.items()), columns=["stock", "best_config"])
df_merged = df_clean.merge(cfg_map, on="stock", how="left")
df_best   = (
    df_merged[df_merged["atr_config"] == df_merged["best_config"]]
    .copy()
    .sort_values("entry_time")
    .reset_index(drop=True)
)
print(f"   → Total trades after filtering: {len(df_best):,}")


# ─── METRIC HELPERS ───────────────────────────────────────────────────────────

def _max_dd_and_duration(cum_pnl: np.ndarray, entry_times: pd.Series) -> tuple[float, int]:
    """
    Returns (max_drawdown, max_dd_duration_days).
    max_drawdown     : largest peak-to-trough drop in cumulative pnl
    max_dd_duration  : longest calendar-day period equity stayed below a previous peak
    """
    peak    = np.maximum.accumulate(cum_pnl)
    dd      = cum_pnl - peak          # always <= 0

    max_dd  = float(dd.min()) if len(dd) > 0 else 0.0

    # Duration: walk trade-by-trade, track when below peak
    in_dd      = dd < 0
    max_dur    = 0
    start_t    = None
    times_arr  = entry_times.values   # numpy array of np.datetime64

    for flag, t in zip(in_dd, times_arr):
        if flag and start_t is None:
            start_t = t
        elif not flag and start_t is not None:
            dur     = int((t - start_t) / np.timedelta64(1, "D"))
            max_dur = max(max_dur, dur)
            start_t = None

    if start_t is not None:           # still in drawdown at end of data
        dur     = int((times_arr[-1] - start_t) / np.timedelta64(1, "D"))
        max_dur = max(max_dur, dur)

    return max_dd, max_dur


def _win_loss_streaks(pnl: np.ndarray) -> tuple[int, int]:
    max_win = max_loss = cur_win = cur_loss = 0
    for p in pnl:
        if p > 0:
            cur_win += 1;  cur_loss  = 0
        elif p < 0:
            cur_loss += 1; cur_win   = 0
        else:
            cur_win = cur_loss = 0
        max_win  = max(max_win,  cur_win)
        max_loss = max(max_loss, cur_loss)
    return max_win, max_loss


def _sharpe(trades_sub: pd.DataFrame) -> float:
    """Monthly Sharpe: mean(monthly_pps) / std(monthly_pps)."""
    monthly = trades_sub.groupby("ym")["pps"].sum()
    if len(monthly) < 2 or monthly.std() == 0:
        return float("nan")
    return float(monthly.mean() / monthly.std())


def compute_metrics(trades_sub: pd.DataFrame) -> dict:
    """Compute all 17 metrics for a given trades subset."""
    pnl    = trades_sub["pps"].values
    times  = trades_sub["entry_time"]
    n      = len(pnl)

    wins   = pnl[pnl > 0]
    losses = pnl[pnl < 0]

    total_pnl   = float(pnl.sum())
    win_rate    = len(wins) / n   if n > 0 else 0.0
    loss_rate   = 1.0 - win_rate
    avg_pnl     = total_pnl / n   if n > 0 else 0.0
    avg_win     = float(wins.mean())   if len(wins)   > 0 else 0.0
    avg_loss    = float(losses.mean()) if len(losses) > 0 else 0.0
    sum_wins    = float(wins.sum())    if len(wins)   > 0 else 0.0
    sum_losses  = float(losses.sum())  if len(losses) > 0 else 0.0

    if sum_losses != 0:
        pf = abs(sum_wins) / abs(sum_losses)
    else:
        pf = float("inf")

    expectancy   = (win_rate * avg_win) + (loss_rate * avg_loss)
    largest_win  = float(pnl.max()) if n > 0 else 0.0
    largest_loss = float(pnl.min()) if n > 0 else 0.0
    median_ret   = float(np.median(pnl)) if n > 0 else 0.0

    cum_pnl              = np.cumsum(pnl)
    max_dd, max_dd_dur   = _max_dd_and_duration(cum_pnl, times)
    ret_to_dd            = (total_pnl / abs(max_dd)) if max_dd != 0 else float("inf")

    sharpe               = _sharpe(trades_sub)
    max_win_s, max_loss_s = _win_loss_streaks(pnl)

    return {
        "total_pnl":         round(total_pnl, 4),
        "total_trades":      n,
        "win_rate":          round(win_rate * 100, 2),
        "avg_pnl_per_trade": round(avg_pnl, 4),
        "avg_win":           round(avg_win, 4),
        "avg_loss":          round(avg_loss, 4),
        "profit_factor":     round(pf, 4) if not np.isinf(pf) else 9999.0,
        "expectancy":        round(expectancy, 4),
        "largest_win":       round(largest_win, 4),
        "largest_loss":      round(largest_loss, 4),
        "median_return":     round(median_ret, 4),
        "max_drawdown":      round(max_dd, 4),
        "max_dd_duration":   max_dd_dur,
        "sharpe_ratio":      round(sharpe, 4) if not np.isnan(sharpe) else 0.0,
        "return_to_maxdd":   round(ret_to_dd, 4) if not np.isinf(ret_to_dd) else 9999.0,
        "max_win_streak":    max_win_s,
        "max_loss_streak":   max_loss_s,
    }


# ─── TASK 1 — PER-STOCK METRICS ───────────────────────────────────────────────
print("[3/6] Computing per-stock metrics …")

rows       = []
flagged    = []
METRIC_COLS = [
    "stock", "best_config", "total_pnl", "total_trades",
    "win_rate", "avg_pnl_per_trade", "avg_win", "avg_loss",
    "profit_factor", "expectancy", "largest_win", "largest_loss",
    "median_return", "max_drawdown", "max_dd_duration",
    "sharpe_ratio", "return_to_maxdd", "max_win_streak", "max_loss_streak",
]

for stock in sorted(all_stocks):
    sub = df_best[df_best["stock"] == stock].copy()
    m   = compute_metrics(sub)
    m["stock"]       = stock
    m["best_config"] = best_cfg[stock]
    rows.append(m)
    if m["total_trades"] < LOW_TRADE_FLAG:
        flagged.append(stock)
        print(f"  ⚠  FLAG: {stock} — only {m['total_trades']} trades")

metrics_df = pd.DataFrame(rows)[METRIC_COLS]
metrics_df.to_csv(STATS_DIR / "fv1_metrics.csv", index=False)
print(f"   → Saved: {STATS_DIR / 'fv1_metrics.csv'}")


# ─── TASK 2 — PORTFOLIO METRICS ───────────────────────────────────────────────
print("[4/6] Computing portfolio-level metrics …")

port_m            = compute_metrics(df_best)
total_pnl_rupees  = float(df_best["pnl"].sum())
final_equity      = INITIAL_EQUITY + total_pnl_rupees
cagr              = (final_equity / INITIAL_EQUITY) ** (1.0 / YEARS_BACKTEST) - 1

port_monthly_pnl  = df_best.groupby("ym")["pnl"].sum()
monthly_win_rate  = (port_monthly_pnl > 0).mean() * 100

first_date        = df_best["entry_time"].min().date()
last_date         = df_best["entry_time"].max().date()

sep = "─" * 58
portfolio_lines = [
    "=" * 60,
    "  FV1 MA BOUNCE — PORTFOLIO PERFORMANCE METRICS",
    "=" * 60,
    f"  Stocks  : {len(all_stocks)} (best config per stock)",
    f"  Period  : {first_date}  →  {last_date}",
    f"  Trades  : {port_m['total_trades']:,}",
    "",
    f"{sep}",
    "  PnL METRICS  (per-share)",
    f"{sep}",
    f"  Total PnL (per-share sum)  : {port_m['total_pnl']:>12.4f}",
    f"  Total PnL (₹ actual)       : ₹{total_pnl_rupees:>12,.2f}",
    f"  Avg PnL per Trade          : {port_m['avg_pnl_per_trade']:>12.4f}",
    f"  Avg Win                    : {port_m['avg_win']:>12.4f}",
    f"  Avg Loss                   : {port_m['avg_loss']:>12.4f}",
    f"  Largest Win                : {port_m['largest_win']:>12.4f}",
    f"  Largest Loss               : {port_m['largest_loss']:>12.4f}",
    f"  Median Return              : {port_m['median_return']:>12.4f}",
    "",
    f"{sep}",
    "  RISK METRICS",
    f"{sep}",
    f"  Win Rate                   : {port_m['win_rate']:>11.2f} %",
    f"  Profit Factor              : {port_m['profit_factor']:>12.4f}",
    f"  Expectancy                 : {port_m['expectancy']:>12.4f}",
    f"  Max Drawdown (per-share)   : {port_m['max_drawdown']:>12.4f}",
    f"  Max DD Duration            : {port_m['max_dd_duration']:>9} days",
    f"  Return / Max Drawdown      : {port_m['return_to_maxdd']:>12.4f}",
    f"  Sharpe Ratio (monthly)     : {port_m['sharpe_ratio']:>12.4f}",
    "",
    f"{sep}",
    "  STREAK METRICS",
    f"{sep}",
    f"  Max Win Streak             : {port_m['max_win_streak']:>8} trades",
    f"  Max Loss Streak            : {port_m['max_loss_streak']:>8} trades",
    "",
    f"{sep}",
    "  PORTFOLIO GROWTH",
    f"{sep}",
    f"  Initial Equity             : ₹{INITIAL_EQUITY:>12,}",
    f"  Final Equity               : ₹{final_equity:>12,.2f}",
    f"  CAGR (4-year)              : {cagr*100:>11.2f} %",
    f"  Monthly Win Rate           : {monthly_win_rate:>11.2f} %",
]

if flagged:
    portfolio_lines += [
        "",
        f"{sep}",
        "  ⚠  FLAGS  (<100 trades)",
        f"{sep}",
    ] + [f"     {s}" for s in flagged]

portfolio_lines.append("=" * 60)
portfolio_report = "\n".join(portfolio_lines)

(STATS_DIR / "fv1_portfolio_metrics.txt").write_text(portfolio_report, encoding="utf-8")
print(f"   → Saved: {STATS_DIR / 'fv1_portfolio_metrics.txt'}")


# ─── TASK 3 — CHARTS ──────────────────────────────────────────────────────────
print("[5/6] Generating charts …")
plt.style.use("dark_background")

# Helper: build monthly x-axis labels with reduced ticks
def _month_xticks(ax, periods, step=6):
    n = len(periods)
    tick_pos  = list(range(0, n, step))
    tick_labs = [str(periods[i]) for i in tick_pos]
    ax.set_xticks(tick_pos)
    ax.set_xticklabels(tick_labs, rotation=45, ha="right", fontsize=8)


# ── CHART 1 : Portfolio equity curve ──────────────────────────────────────────
port_monthly = df_best.groupby("ym")["pps"].sum()
port_cum     = port_monthly.cumsum()
periods      = list(port_cum.index)
eq_vals      = port_cum.values
x_idx        = np.arange(len(eq_vals))
peak_vals    = np.maximum.accumulate(eq_vals)

fig, (ax_eq, ax_dd) = plt.subplots(
    2, 1, figsize=(14, 9),
    gridspec_kw={"height_ratios": [3, 1]},
    sharex=True,
)
fig.patch.set_facecolor("#0d1117")
for ax in (ax_eq, ax_dd):
    ax.set_facecolor("#0d1117")

ax_eq.plot(x_idx, eq_vals, color=CYAN, linewidth=2, label="Equity Curve", zorder=3)
ax_eq.fill_between(x_idx, peak_vals, eq_vals,
                    where=(eq_vals < peak_vals),
                    alpha=0.35, color=RED, label="Drawdown region", zorder=2)
ax_eq.set_title(
    "Portfolio Equity Curve — FV1 MA Bounce (29 Stocks, Best Configs)",
    color="white", fontsize=13, fontweight="bold", pad=10,
)
ax_eq.set_ylabel("Cumulative PnL per share  (₹)", color="white")
ax_eq.legend(loc="upper left", fontsize=9)
ax_eq.grid(alpha=0.15)
ax_eq.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))

dd_vals = eq_vals - peak_vals
ax_dd.fill_between(x_idx, dd_vals, 0, alpha=0.7, color=RED)
ax_dd.plot(x_idx, dd_vals, color=RED, linewidth=0.8)
ax_dd.set_ylabel("Drawdown", color=RED)
ax_dd.set_xlabel("Month", color="white")
ax_dd.grid(alpha=0.15)
_month_xticks(ax_dd, periods, step=6)

plt.tight_layout()
fig.savefig(REPORTS_DIR / "portfolio_equity_curve.png", dpi=150, bbox_inches="tight")
plt.close()
print("   → portfolio_equity_curve.png")


# ── CHART 2 : Top-5 equity curves ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 7))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#0d1117")

for i, stock in enumerate(TOP5):
    sub      = df_best[df_best["stock"] == stock]
    monthly  = sub.groupby("ym")["pps"].sum()
    cum      = monthly.cumsum()
    x_s      = np.arange(len(cum))
    ax.plot(x_s, cum.values, label=stock,
            color=STOCK_COLORS[i], linewidth=1.8)
    _month_xticks(ax, list(cum.index), step=6)

ax.set_title("Top-5 Stocks — Individual Equity Curves (Best Config)",
             color="white", fontsize=13, fontweight="bold")
ax.set_xlabel("Month", color="white")
ax.set_ylabel("Cumulative PnL per share  (₹)", color="white")
ax.legend(fontsize=10)
ax.grid(alpha=0.15)
plt.tight_layout()
fig.savefig(REPORTS_DIR / "top5_equity_curves.png", dpi=150, bbox_inches="tight")
plt.close()
print("   → top5_equity_curves.png")


# ── CHART 3 : Portfolio drawdown % ────────────────────────────────────────────
# Use monthly portfolio pnl (in rupees) for drawdown %
port_monthly_rupee = df_best.groupby("ym")["pnl"].sum()
port_cum_rupee     = port_monthly_rupee.cumsum() + INITIAL_EQUITY
eq_r               = port_cum_rupee.values
peak_r             = np.maximum.accumulate(eq_r)
dd_pct             = ((eq_r - peak_r) / peak_r) * 100
periods_r          = list(port_cum_rupee.index)
x_r                = np.arange(len(eq_r))

fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#0d1117")
ax.fill_between(x_r, dd_pct, 0, alpha=0.7, color=RED)
ax.plot(x_r, dd_pct, color=RED, linewidth=1.2)
ax.set_title("Portfolio Drawdown Over Time — FV1 MA Bounce",
             color="white", fontsize=13, fontweight="bold")
ax.set_xlabel("Month", color="white")
ax.set_ylabel("Drawdown %", color=RED)
ax.grid(alpha=0.15)
_month_xticks(ax, periods_r, step=6)
plt.tight_layout()
fig.savefig(REPORTS_DIR / "drawdown_chart.png", dpi=150, bbox_inches="tight")
plt.close()
print("   → drawdown_chart.png")


# ── CHART 4 : Monthly PnL heatmap ─────────────────────────────────────────────
port_by_ym         = df_best.groupby("ym")["pps"].sum().reset_index()
port_by_ym["year"] = port_by_ym["ym"].dt.year
port_by_ym["month"]= port_by_ym["ym"].dt.month

years_list    = sorted(port_by_ym["year"].unique())
month_names   = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"]

heatmap = port_by_ym.pivot(index="month", columns="year", values="pps")
heatmap = heatmap.reindex(index=range(1, 13), columns=years_list)

vmax = heatmap.abs().max().max()

fig, ax = plt.subplots(figsize=(max(8, len(years_list) * 2.2), 7))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#0d1117")

im = ax.imshow(heatmap.values, aspect="auto",
               cmap="RdYlGn", vmin=-vmax, vmax=vmax)

ax.set_xticks(range(len(years_list)))
ax.set_xticklabels(years_list, color="white", fontsize=11)
ax.set_yticks(range(12))
ax.set_yticklabels(month_names, color="white", fontsize=10)
ax.set_title("Monthly Portfolio PnL Heatmap — FV1 MA Bounce",
             color="white", fontsize=13, fontweight="bold", pad=12)

cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
cb.set_label("PnL per share", color="white")
cb.ax.yaxis.set_tick_params(color="white")
plt.setp(cb.ax.yaxis.get_ticklabels(), color="white")

for r in range(12):
    for c in range(len(years_list)):
        val = heatmap.values[r, c]
        if not np.isnan(val):
            txt_color = "white" if abs(val) > vmax * 0.5 else "black"
            ax.text(c, r, f"{val:.2f}", ha="center", va="center",
                    fontsize=8, color=txt_color, fontweight="bold")

plt.tight_layout()
fig.savefig(REPORTS_DIR / "monthly_pnl_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("   → monthly_pnl_heatmap.png")


# ── CHART 5 : Profit factor by stock ──────────────────────────────────────────
mdf_sorted = metrics_df.sort_values("profit_factor", ascending=True).reset_index(drop=True)
bar_colors = [GREEN if v >= 1.0 else RED for v in mdf_sorted["profit_factor"]]

fig, ax = plt.subplots(figsize=(11, max(8, len(mdf_sorted) * 0.38)))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#0d1117")

bars = ax.barh(mdf_sorted["stock"], mdf_sorted["profit_factor"],
               color=bar_colors, edgecolor="none", height=0.7)

ax.axvline(1.0, color=YELLOW, linestyle="--", linewidth=1.5,
           label="Breakeven (PF = 1.0)")

ax.set_title("Profit Factor by Stock — FV1 MA Bounce (Best Config)",
             color="white", fontsize=13, fontweight="bold")
ax.set_xlabel("Profit Factor", color="white")
ax.tick_params(colors="white")
ax.legend(fontsize=9)
ax.grid(alpha=0.15, axis="x")

for bar, val in zip(bars, mdf_sorted["profit_factor"]):
    label = f"{val:.3f}" if val < 9999 else "∞"
    ax.text(
        val + max(mdf_sorted["profit_factor"].replace(9999, 0)) * 0.01,
        bar.get_y() + bar.get_height() / 2,
        label, va="center", fontsize=8, color="white",
    )

plt.tight_layout()
fig.savefig(REPORTS_DIR / "profit_factor_by_stock.png", dpi=150, bbox_inches="tight")
plt.close()
print("   → profit_factor_by_stock.png")


# ─── PRINT SUMMARY TABLE ──────────────────────────────────────────────────────
print("\n[6/6] Summary")
print("\n" + "=" * 100)
print("FV1 MA BOUNCE — PER-STOCK SUMMARY  (best config, pnl/share)")
print("=" * 100)
display_cols = [
    "stock", "best_config", "total_trades", "win_rate",
    "profit_factor", "total_pnl", "max_drawdown", "sharpe_ratio",
]
print(metrics_df[display_cols].to_string(index=False))
print()
print(portfolio_report)

if flagged:
    print(f"\n⚠  Stocks with < {LOW_TRADE_FLAG} trades: {flagged}")

print("\n[DONE]  All outputs saved.")
print(f"  Stats  : {STATS_DIR}")
print(f"  Reports: {REPORTS_DIR}")
