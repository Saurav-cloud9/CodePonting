"""
bqs_filter_cagr.py — BQS Step 4.4c: Apply 9 DT bucket filters, measure CAGR
=============================================================================
For each of 9 DT leaf bucket filters (F1-F9), applies the filter as a hard
entry gate on the bqs_trades parquet and computes CAGR + win rates.

Methodology: REPLAY approximation.
  - Uses pre-computed PnL from the Step 3.3 baseline backtest (original
    position sizes, slippage-included). Position sizes are NOT recomputed
    for the filtered equity curve — so CAGR figures are approximate.
  - CAGR direction and ordering across filters is reliable.
  - Absolute CAGR may differ from a proper per-filter backtest by ~1-3pp
    for sparse filters (due to compounding drift).
  - A proper backtest should be run on any filter that looks promising
    before acting on it.

Baseline: 28,085 trades | CAGR -8.62% (slippage only, no charges)

Column mapping used by filter rules (from bqs_leaf_analysis.py ABBREV):
  hrs_close   → m5_hours_until_close
  ma20_dist%  → m8_ma20_distance_pct
  touch_idx   → m6_touch_candle_index
  ma20_slope  → r2_m1_ma20_slope
  bounce_str  → m2_bounce_strength_pct
  vol_ratio   → m1_volume_ratio  (R1: bounce_vol / avg_vol_20d)
  wick_body   → r2_m61_wick_body (R2: lower_wick / body at touch)
  freshness   → r2_m3_freshness  (R2: prior touch count, last 20 bars)
  day_pos     → r2_m5_day_position (R2: (close-day_low)/(day_high-day_low))

NaN handling: NaN in any filter column → trade excluded (not taken).
"""

import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

SANDBOX_DIR     = Path(__file__).resolve().parent.parent
BQS_PATH        = SANDBOX_DIR / "outputs/bqs/bqs_trades.parquet"
INITIAL_CAPITAL = 1_000_000
YEARS           = 4

# ── LOAD ──────────────────────────────────────────────────────────────────────

print("Loading bqs_trades.parquet...", flush=True)
df = pd.read_parquet(BQS_PATH)
df = df.reset_index(drop=True)
n  = len(df)

if "w1" not in df.columns and "winner" in df.columns:
    df["w1"] = df["winner"]

print(f"  {n:,} trades  |  {df.shape[1]} columns", flush=True)


# ── SHORTCUTS ─────────────────────────────────────────────────────────────────

h  = df["m5_hours_until_close"]        # hours until 15:30 at entry
d  = df["m8_ma20_distance_pct"]        # (MA20 - touch_low) / MA20 %
ti = df["m6_touch_candle_index"]       # bar index from 09:15 (0=09:15, 1=09:20…)
sl = df["r2_m1_ma20_slope"]            # MA20 5-bar slope / close × 100
bs = df["m2_bounce_strength_pct"]      # (bounce_close - touch_low) / touch_low %
vr = df["m1_volume_ratio"]             # bounce_vol / avg_vol_20d  (R1)
wb = df["r2_m61_wick_body"]            # lower_wick / body at touch
fr = df["r2_m3_freshness"]             # prior touches in last 20 bars
dp = df["r2_m5_day_position"]          # (touch_close - day_low) / day_range


# ── FILTER DEFINITIONS ────────────────────────────────────────────────────────

FILTERS = {
    "F1 (W1 #1)": (h  > 2.29)  & (d  <= 0.28)  & (ti <= 36.5) & (h <= 4.96),
    "F2 (W1 #2)": (h  > 2.29)  & (d  <= 0.28)  & (ti >  36.5),
    "F3 (W1 #3)": (h  > 2.29)  & (d  >  0.28)  & (sl >  -0.46),
    "F4 (W2 #1)": (ti <= 27.5) & (bs >  0.178) & (vr <= 1.016) & (wb <= 4.45),
    "F5 (W2 #2)": (ti <= 27.5) & (bs >  0.178) & (vr >  1.016),
    "F6 (W2 #3)": (ti <= 27.5) & (bs <= 0.178) & (d  <= 0.10),
    "F7 (W3 #1)": (ti <= 27.5) & (bs >  0.178) & (vr <= 1.016) & (fr > 7.5),
    "F8 (W3 #2)": (ti >  27.5) & (bs <= 0.367) & (dp >  0.569),
    "F9 (W3 #3)": (ti <= 27.5) & (bs >  0.178) & (vr >  1.016),
}

FILTER_RULES = {
    "F1 (W1 #1)": "hrs_close>2.29 AND ma20_dist%<=0.28 AND touch_idx<=36.5 AND hrs_close<=4.96",
    "F2 (W1 #2)": "hrs_close>2.29 AND ma20_dist%<=0.28 AND touch_idx>36.5",
    "F3 (W1 #3)": "hrs_close>2.29 AND ma20_dist%>0.28 AND ma20_slope>-0.46",
    "F4 (W2 #1)": "touch_idx<=27.5 AND bounce_str>0.178 AND vol_ratio<=1.016 AND wick_body<=4.45",
    "F5 (W2 #2)": "touch_idx<=27.5 AND bounce_str>0.178 AND vol_ratio>1.016",
    "F6 (W2 #3)": "touch_idx<=27.5 AND bounce_str<=0.178 AND ma20_dist%<=0.10",
    "F7 (W3 #1)": "touch_idx<=27.5 AND bounce_str>0.178 AND vol_ratio<=1.016 AND freshness>7.5",
    "F8 (W3 #2)": "touch_idx>27.5 AND bounce_str<=0.367 AND day_pos>0.569",
    "F9 (W3 #3)": "touch_idx<=27.5 AND bounce_str>0.178 AND vol_ratio>1.016",
}


# ── CAGR HELPER ───────────────────────────────────────────────────────────────

def replay_cagr(pnl_series, cap=INITIAL_CAPITAL, yrs=YEARS):
    """Sum-of-PnL replay CAGR. Approximate — uses original position sizes."""
    total_pnl = float(pnl_series.sum())
    final_eq  = cap + total_pnl
    if final_eq <= 0:
        return -100.0
    return ((final_eq / cap) ** (1 / yrs) - 1) * 100


# ── BASELINE ──────────────────────────────────────────────────────────────────

base_cagr = replay_cagr(df["pnl"])
base_w1   = df["w1"].mean() * 100
base_w2   = df["w2"].mean() * 100
base_w3   = df["w3"].mean() * 100

print(f"\n  Baseline: {n:,} trades | CAGR {base_cagr:+.2f}% | "
      f"w1 {base_w1:.1f}% | w2 {base_w2:.1f}% | w3 {base_w3:.1f}%", flush=True)


# ── RUN FILTERS ───────────────────────────────────────────────────────────────

results = []

for fname, mask in FILTERS.items():
    sub  = df[mask]
    cnt  = len(sub)
    cagr = replay_cagr(sub["pnl"]) if cnt > 0 else -100.0
    vs   = cagr - base_cagr
    w1p  = sub["w1"].mean() * 100 if cnt > 0 else 0.0
    w2p  = sub["w2"].mean() * 100 if cnt > 0 else 0.0
    w3p  = sub["w3"].mean() * 100 if cnt > 0 else 0.0

    # NaN note: which filter cols have NaN in matched trades
    nan_note = ""
    if any(col in FILTER_RULES[fname] for col in ("ma20_slope", "wick_body", "freshness", "day_pos")):
        orig_possible = (~mask | mask).sum()   # total possible — just show NaN excluded count
        # Count how many were excluded due to NaN (compare to if we dropped conditions)
        # Simpler: count NaN in the relevant R2 cols for trades that would match without that col
        # Skip detailed NaN breakdown for brevity

    results.append({
        "filter": fname,
        "trades": cnt,
        "pct":    cnt / n * 100,
        "cagr":   cagr,
        "vs":     vs,
        "w1":     w1p,
        "w2":     w2p,
        "w3":     w3p,
        "total_pnl": float(sub["pnl"].sum()),
    })


# ── NaN EXCLUSION COUNTS ──────────────────────────────────────────────────────

# Show how many trades each R2-dependent filter loses to NaN
nan_cols = {
    "r2_m1_ma20_slope":   "ma20_slope",
    "r2_m61_wick_body":   "wick_body",
    "r2_m3_freshness":    "freshness",
    "r2_m5_day_position": "day_pos",
}

nan_counts = {}
for col, short in nan_cols.items():
    nan_counts[short] = int(df[col].isna().sum())


# ── PRINT MAIN TABLE ──────────────────────────────────────────────────────────

print(f"\n{'='*95}", flush=True)
print(
    "  FILTER CAGR RESULTS   [REPLAY APPROXIMATION — original position sizes]",
    flush=True,
)
print(f"{'='*95}", flush=True)
print(
    f"  {'Filter':<13} {'Trades':>7} {'Trade%':>7} {'CAGR':>8} {'vs Base':>9}"
    f"  {'W1%':>6} {'W2%':>6} {'W3%':>6}  Total PnL (Rs)",
    flush=True,
)
print(f"  {'─'*90}", flush=True)

# Baseline row
print(
    f"  {'BASELINE':<13} {n:>7,} {'100.0%':>7} {base_cagr:>+8.2f}% {'—':>9}"
    f"  {base_w1:>5.1f}% {base_w2:>5.1f}% {base_w3:>5.1f}%  {df['pnl'].sum():>+14,.0f}",
    flush=True,
)
print(f"  {'─'*90}", flush=True)

for r in results:
    sign = "+" if r["vs"] >= 0 else ""
    pct_str = f"{r['pct']:.1f}%"
    print(
        f"  {r['filter']:<13} {r['trades']:>7,} {pct_str:>7} {r['cagr']:>+8.2f}%"
        f" {sign}{r['vs']:>7.2f}pp"
        f"  {r['w1']:>5.1f}% {r['w2']:>5.1f}% {r['w3']:>5.1f}%  {r['total_pnl']:>+14,.0f}",
        flush=True,
    )

print(f"{'='*95}", flush=True)


# ── FILTER RULES LEGEND ───────────────────────────────────────────────────────

print(f"\n  Filter rules:", flush=True)
for fname, rule in FILTER_RULES.items():
    print(f"  {fname:<13} {rule}", flush=True)

print(f"\n  NaN exclusion in R2 columns (global):", flush=True)
for short, cnt in nan_counts.items():
    print(f"    {short:<14} {cnt:>5,} NaN ({cnt/n*100:.1f}%) — trades with NaN excluded by any filter using this metric", flush=True)

print(f"\n  vol_ratio = m1_volume_ratio (R1: bounce_vol / avg_vol_20d)", flush=True)


# ── RANKED SUMMARY ────────────────────────────────────────────────────────────

print(f"\n{'='*95}", flush=True)
print("  RANKED BY CAGR IMPROVEMENT", flush=True)
print(f"{'='*95}", flush=True)
ranked = sorted(results, key=lambda x: x["cagr"], reverse=True)
print(
    f"  {'Rank':<5} {'Filter':<13} {'Trades':>7} {'CAGR':>8} {'vs Base':>9}"
    f"  {'W1%':>6} {'W2%':>6} {'W3%':>6}",
    flush=True,
)
print(f"  {'─'*72}", flush=True)
for rank, r in enumerate(ranked, 1):
    sign = "+" if r["vs"] >= 0 else ""
    print(
        f"  {rank:<5} {r['filter']:<13} {r['trades']:>7,} {r['cagr']:>+8.2f}%"
        f" {sign}{r['vs']:>7.2f}pp"
        f"  {r['w1']:>5.1f}% {r['w2']:>5.1f}% {r['w3']:>5.1f}%",
        flush=True,
    )

print(f"\n  ⚠  REPLAY APPROXIMATION — CAGR uses original position sizes.", flush=True)
print(f"     Direction and ranking are reliable. Absolute CAGR ±1-3pp vs proper backtest.", flush=True)
print(f"     Proper backtest needed before acting on any filter.", flush=True)
print(f"{'='*95}", flush=True)
