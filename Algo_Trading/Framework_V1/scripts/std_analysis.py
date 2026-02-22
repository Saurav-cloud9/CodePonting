"""
std_analysis.py
───────────────
Monthly PnL std-deviation analysis for top-5 fv1 stocks.

Top-5 stocks & their best ATR configs:
  SUNPHARMA  → Extreme-4
  BHARTIARTL → Extreme-1
  HDFCBANK   → Extreme-4
  ICICIBANK  → Extreme-4
  ASHOKLEY   → Extreme-4

Outputs (outputs/reports/):
  monthly_pnl_trend.png
  avg_vs_std.png
  sharpe_ratio.png
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRADES_CSV  = os.path.join(BASE_DIR, "outputs", "trades", "fv1_all_trades.csv")
REPORTS_DIR = os.path.join(BASE_DIR, "outputs", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# ── Config ─────────────────────────────────────────────────────────────────────
TOP5 = {
    "SUNPHARMA":  "Extreme-4",
    "BHARTIARTL": "Extreme-1",
    "HDFCBANK":   "Extreme-4",
    "ICICIBANK":  "Extreme-4",
    "ASHOKLEY":   "Extreme-4",
}

COLORS = {
    "SUNPHARMA":  "#00C9FF",
    "BHARTIARTL": "#FF6B6B",
    "HDFCBANK":   "#FFD93D",
    "ICICIBANK":  "#6BCB77",
    "ASHOKLEY":   "#C77DFF",
}

plt.style.use("dark_background")

# ── Load & filter ──────────────────────────────────────────────────────────────
print("Loading trades …")
df = pd.read_csv(TRADES_CSV, parse_dates=["exit_time"])

# Normalise timezone → tz-naive local date
df["exit_time"] = pd.to_datetime(df["exit_time"], utc=True).dt.tz_localize(None)

rows = []
for stock, cfg in TOP5.items():
    sub = df[(df["stock"] == stock) & (df["atr_config"] == cfg)].copy()
    sub["pnl_per_share"] = sub["pnl"] / sub["qty"]
    rows.append(sub)

filtered = pd.concat(rows, ignore_index=True)
filtered["month"] = filtered["exit_time"].dt.to_period("M")

# ── Monthly PnL per stock ──────────────────────────────────────────────────────
monthly = (
    filtered
    .groupby(["stock", "month"])["pnl_per_share"]
    .sum()
    .reset_index()
)
monthly["month_dt"] = monthly["month"].dt.to_timestamp()

# ── Summary stats ──────────────────────────────────────────────────────────────
stats = []
for stock in TOP5:
    vals = monthly.loc[monthly["stock"] == stock, "pnl_per_share"]
    avg  = vals.mean()
    std  = vals.std()
    sharpe = avg / std if std != 0 else 0.0
    stats.append({"stock": stock, "avg_monthly_pnl": avg, "std": std, "sharpe_ratio": sharpe})

stats_df = pd.DataFrame(stats).set_index("stock")

# ── Terminal summary ───────────────────────────────────────────────────────────
print("\n" + "-" * 62)
print(f"{'Stock':<12} {'Avg Monthly PnL/Sh':>18} {'Std Dev':>10} {'Sharpe':>10}")
print("-" * 62)
for stock, row in stats_df.iterrows():
    print(f"{stock:<12} {row['avg_monthly_pnl']:>18.4f} {row['std']:>10.4f} {row['sharpe_ratio']:>10.4f}")
print("-" * 62 + "\n")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 1 — Monthly PnL Trend (line)
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor("#0D1117")
ax.set_facecolor("#0D1117")

for stock in TOP5:
    sub = monthly[monthly["stock"] == stock].sort_values("month_dt")
    ax.plot(
        sub["month_dt"], sub["pnl_per_share"],
        label=stock, color=COLORS[stock],
        linewidth=1.6, alpha=0.9
    )

ax.axhline(0, color="#555", linewidth=0.8, linestyle="--")
ax.set_title("Monthly PnL per Share — Top 5 Stocks (48 months)", color="white", fontsize=14, pad=14)
ax.set_xlabel("Month", color="#AAAAAA", fontsize=11)
ax.set_ylabel("PnL / Share (₹)", color="#AAAAAA", fontsize=11)
ax.tick_params(colors="#AAAAAA")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b'%y"))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45)
ax.legend(facecolor="#1E1E2E", edgecolor="#555", labelcolor="white", fontsize=10)
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["left", "bottom"]].set_color("#444")
ax.yaxis.grid(True, color="#222", linewidth=0.6)
plt.tight_layout()
out1 = os.path.join(REPORTS_DIR, "monthly_pnl_trend.png")
plt.savefig(out1, dpi=150, facecolor=fig.get_facecolor())
plt.close()
print(f"Saved: {out1}")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 2 — Avg vs Std (grouped bar)
# ══════════════════════════════════════════════════════════════════════════════
stocks = list(TOP5.keys())
x      = np.arange(len(stocks))
width  = 0.35

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("#0D1117")
ax.set_facecolor("#0D1117")

bars_avg = ax.bar(
    x - width / 2,
    [stats_df.loc[s, "avg_monthly_pnl"] for s in stocks],
    width, label="Avg Monthly PnL/Sh",
    color=[COLORS[s] for s in stocks], alpha=0.85
)
bars_std = ax.bar(
    x + width / 2,
    [stats_df.loc[s, "std"] for s in stocks],
    width, label="Std Dev",
    color=[COLORS[s] for s in stocks], alpha=0.40, hatch="//"
)

# Value labels
for bar in bars_avg:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, h + 0.2,
            f"{h:.2f}", ha="center", va="bottom", color="white", fontsize=8)
for bar in bars_std:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, h + 0.2,
            f"{h:.2f}", ha="center", va="bottom", color="#AAAAAA", fontsize=8)

ax.set_xticks(x)
ax.set_xticklabels(stocks, color="white", fontsize=11)
ax.set_title("Avg Monthly PnL/Share vs Std Dev — Top 5 Stocks", color="white", fontsize=14, pad=14)
ax.set_ylabel("₹ per Share", color="#AAAAAA", fontsize=11)
ax.tick_params(colors="#AAAAAA")
ax.legend(facecolor="#1E1E2E", edgecolor="#555", labelcolor="white", fontsize=10)
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["left", "bottom"]].set_color("#444")
ax.yaxis.grid(True, color="#222", linewidth=0.6)
plt.tight_layout()
out2 = os.path.join(REPORTS_DIR, "avg_vs_std.png")
plt.savefig(out2, dpi=150, facecolor=fig.get_facecolor())
plt.close()
print(f"Saved: {out2}")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 3 — Sharpe Ratio (horizontal bar, ranked)
# ══════════════════════════════════════════════════════════════════════════════
sharpe_df = stats_df[["sharpe_ratio"]].sort_values("sharpe_ratio")

fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor("#0D1117")
ax.set_facecolor("#0D1117")

bar_colors = [COLORS[s] for s in sharpe_df.index]
bars = ax.barh(sharpe_df.index, sharpe_df["sharpe_ratio"], color=bar_colors, alpha=0.88, height=0.5)

for bar, val in zip(bars, sharpe_df["sharpe_ratio"]):
    ax.text(
        val + 0.002, bar.get_y() + bar.get_height() / 2,
        f"{val:.4f}", va="center", color="white", fontsize=10, fontweight="bold"
    )

ax.axvline(0, color="#555", linewidth=0.8, linestyle="--")
ax.set_title("Sharpe Ratio (Avg/Std) — Top 5 Stocks (Ranked)", color="white", fontsize=14, pad=14)
ax.set_xlabel("Sharpe Ratio", color="#AAAAAA", fontsize=11)
ax.tick_params(colors="#AAAAAA")
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["left", "bottom"]].set_color("#444")
ax.xaxis.grid(True, color="#222", linewidth=0.6)
plt.tight_layout()
out3 = os.path.join(REPORTS_DIR, "sharpe_ratio.png")
plt.savefig(out3, dpi=150, facecolor=fig.get_facecolor())
plt.close()
print(f"Saved: {out3}")

print("\nDone. All 3 charts saved to outputs/reports/")
