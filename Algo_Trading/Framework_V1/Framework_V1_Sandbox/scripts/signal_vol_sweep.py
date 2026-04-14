"""
signal_vol_sweep.py — Volume Threshold Sweep
=============================================
Tests how signal edge changes as volume multiplier threshold increases.
Reference point: close of touch candle T (confirmed, no lookahead).
Reports key N values (N=5, N=8, N=10, N=20) for each threshold.

Thresholds tested: 1.0, 1.1, 1.2, 1.3, 1.5, 1.7, 2.0, 2.5, 3.0
Output: overall summary + year-wise at N=8 (peak N from prior run)
"""

import sys
import io
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from scipy import stats

SANDBOX_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SANDBOX_DIR))
from core.indicators import add_intraday_indicators, add_atr

FV1_DIR   = SANDBOX_DIR.parent
DS3_DIR   = FV1_DIR / "data/historical/intraday_5min_DS3"
EXCLUDE   = {"NIFTY50", "VI"}
MAX_N     = 20
START_YR  = 2015

VOL_THRESHOLDS = [1.0, 1.1, 1.2, 1.3, 1.5, 1.7, 2.0, 2.5, 3.0]
KEY_NS         = [5, 8, 10, 20]

OUT_DIR    = SANDBOX_DIR / "outputs" / "signal_validation"
MOBILE_DIR = Path(r"C:\Users\saurav\OneDrive\CodePonting_Mobile\sandbox\signal_validation")
OUT_DIR.mkdir(parents=True, exist_ok=True)
MOBILE_DIR.mkdir(parents=True, exist_ok=True)

# ── STEP 1: LOAD DATA ────────────────────────────────────────────────────────
print("Step 1: Loading DS3 data...", flush=True)
t0 = time.time()

stock_files = sorted(f for f in DS3_DIR.glob("*.parquet") if f.stem not in EXCLUDE)
print(f"  {len(stock_files)} stocks found", flush=True)

stock_arrays = {}

for sp in stock_files:
    stock = sp.stem
    df = pd.read_parquet(sp)
    df["datetime"] = pd.to_datetime(df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S"))
    df = df.sort_values("datetime").reset_index(drop=True)
    df = df[df["datetime"].dt.year >= START_YR].reset_index(drop=True)
    _t = df["datetime"].dt.time
    df = df[_t.between(pd.Timestamp("09:15").time(), pd.Timestamp("15:30").time())]
    df = df.reset_index(drop=True)
    df = add_intraday_indicators(df)
    df = add_atr(df)

    dti = pd.DatetimeIndex(df["datetime"])
    stock_arrays[stock] = {
        "close":   df["close"].to_numpy(dtype=float),
        "low":     df["low"].to_numpy(dtype=float),
        "volume":  df["volume"].to_numpy(dtype=float),
        "avg_vol": df["avg_volume"].to_numpy(dtype=float),
        "ma20":    df["ma20"].to_numpy(dtype=float),
        "year":    dti.year.to_numpy(),
        "n":       len(df),
    }

print(f"  Done in {time.time()-t0:.1f}s", flush=True)


# ── STEP 2: COLLECT TOUCH EVENTS FOR ALL THRESHOLDS ─────────────────────────
print("Step 2: Collecting touch events...", flush=True)

# records[thresh] = list of (year, fwd_list[0..19])
records = {t: [] for t in VOL_THRESHOLDS}

for stock, arrs in stock_arrays.items():
    n       = arrs["n"]
    close   = arrs["close"]
    low     = arrs["low"]
    vol     = arrs["volume"]
    avg_vol = arrs["avg_vol"]
    ma20    = arrs["ma20"]
    year    = arrs["year"]

    for i in range(n - MAX_N - 1):
        if np.isnan(ma20[i]) or low[i] > ma20[i]:
            continue
        ref = close[i]
        if ref <= 0 or np.isnan(ref):
            continue

        # compute fwd returns once
        fwd = []
        valid = True
        for k in range(1, MAX_N + 1):
            c_fwd = close[i + k]
            if np.isnan(c_fwd):
                valid = False
                break
            fwd.append((c_fwd - ref) / ref)
        if not valid:
            continue

        yr      = year[i]
        vol_i   = vol[i]
        avg_i   = avg_vol[i]
        vol_rat = vol_i / avg_i if (not np.isnan(avg_i) and avg_i > 0) else 0.0

        for thresh in VOL_THRESHOLDS:
            if vol_rat >= thresh:
                records[thresh].append((yr, fwd))

for t in VOL_THRESHOLDS:
    print(f"  vol >= {t:.1f}x : {len(records[t]):>10,} touch events", flush=True)


# ── STEP 3: COMPUTE STATS ────────────────────────────────────────────────────

def row_stats(recs, n_val):
    if len(recs) < 5:
        return dict(count=len(recs), mean=np.nan, pct_pos=np.nan, t_stat=np.nan, p_val=np.nan)
    returns = np.array([r[1][n_val - 1] for r in recs])
    t_stat, p_val = stats.ttest_1samp(returns, 0)
    return dict(
        count   = len(returns),
        mean    = round(returns.mean() * 100, 4),
        pct_pos = round((returns > 0).mean() * 100, 2),
        t_stat  = round(t_stat, 2),
        p_val   = round(p_val, 4),
    )


# ── STEP 4: PRINT OVERALL SUMMARY ───────────────────────────────────────────
print("\n", flush=True)

for n_val in KEY_NS:
    print(f"{'='*80}", flush=True)
    print(f"  OVERALL 2015–2025 — N={n_val} candles ahead", flush=True)
    print(f"{'='*80}", flush=True)
    print(f"{'Vol>=':>6}  {'Count':>10}  {'Mean%':>8}  {'%Pos':>7}  {'t-stat':>8}  {'p-val':>8}", flush=True)
    print(f"{'-'*60}", flush=True)
    for t in VOL_THRESHOLDS:
        s = row_stats(records[t], n_val)
        sig = "*" if (not np.isnan(s["p_val"]) and s["p_val"] < 0.05) else " "
        print(
            f"{t:>5.1f}x  {s['count']:>10,}  {s['mean']:>8.4f}  "
            f"{s['pct_pos']:>7.2f}  {s['t_stat']:>8.2f}  {s['p_val']:>8.4f}{sig}",
            flush=True
        )

# ── STEP 5: YEAR-WISE AT N=8 ────────────────────────────────────────────────
N_YW = 8
years = sorted(set(r[0] for recs in records.values() for r in recs))

print(f"\n{'='*100}", flush=True)
print(f"  YEAR-WISE — N={N_YW} candles ahead  (Mean% | %Pos | t-stat)", flush=True)
print(f"{'='*100}", flush=True)

# header
hdr = f"{'Vol>=':>6} | " + " | ".join(f"{y}" for y in years)
print(hdr, flush=True)
print("-" * (9 + 22 * len(years)), flush=True)

for t in VOL_THRESHOLDS:
    recs = records[t]
    cells = []
    for yr in years:
        yr_recs = [r for r in recs if r[0] == yr]
        s = row_stats(yr_recs, N_YW)
        sig = "*" if (not np.isnan(s["p_val"]) and s["p_val"] < 0.05) else " "
        cells.append(f"{s['mean']:>+7.4f}% {s['pct_pos']:>5.1f}% {s['t_stat']:>5.1f}{sig}")
    print(f"{t:>5.1f}x | " + " | ".join(cells), flush=True)

# ── STEP 6: SAVE OUTPUTS ─────────────────────────────────────────────────────
print("\nSaving outputs...", flush=True)

# Overall summary across all key N values
rows = []
for t in VOL_THRESHOLDS:
    for n_val in range(1, MAX_N + 1):
        s = row_stats(records[t], n_val)
        rows.append({"vol_thresh": t, "N": n_val, **s})
df_overall = pd.DataFrame(rows)

# Year-wise at N=8
yw_rows = []
for t in VOL_THRESHOLDS:
    for yr in years:
        yr_recs = [r for r in records[t] if r[0] == yr]
        s = row_stats(yr_recs, N_YW)
        yw_rows.append({"vol_thresh": t, "year": yr, "N": N_YW, **s})
df_yw = pd.DataFrame(yw_rows)

for out in [OUT_DIR, MOBILE_DIR]:
    df_overall.to_csv(out / "vol_sweep_overall.csv", index=False)
    df_yw.to_csv(out / "vol_sweep_yearwise_N8.csv", index=False)

print(f"  Saved to: {OUT_DIR}", flush=True)
print(f"  Mobile  : {MOBILE_DIR}", flush=True)
print("\nDone.", flush=True)
