"""
signal_validation.py — P1 Signal Foundation Review
====================================================
Checks whether the MA20 touch signal has statistical directional bias,
independent of entry logic, SL, targets, or position sizing.

Method:
  - Find every candle where low <= MA20 (touch event)
  - Record close of touch candle T as reference point
  - Measure forward returns at N=1 to N=20 candles
  - Report: count, mean, median, % positive, t-stat, p-value

Two variants:
  V1 — Pure touch    : low <= MA20 only
  V2 — Strategy touch: low <= MA20 + volume filter (vol >= 1.2x avg)

Split: year-wise 2015–2025 + overall

Dataset: DS3, all stocks (excluding NIFTY50, VI)
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

# ── CONFIG ───────────────────────────────────────────────────────────────────
FV1_DIR   = SANDBOX_DIR.parent
DS3_DIR   = FV1_DIR / "data/historical/intraday_5min_DS3"
EXCLUDE   = {"NIFTY50", "VI"}
VOL_MULT  = 1.2
MAX_N     = 20
START_YR  = 2015

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
        "close":    df["close"].to_numpy(dtype=float),
        "low":      df["low"].to_numpy(dtype=float),
        "volume":   df["volume"].to_numpy(dtype=float),
        "avg_vol":  df["avg_volume"].to_numpy(dtype=float),
        "ma20":     df["ma20"].to_numpy(dtype=float),
        "year":     dti.year.to_numpy(),
        "date":     dti.date,
        "n":        len(df),
    }

print(f"  Done in {time.time()-t0:.1f}s", flush=True)


# ── STEP 2: COLLECT TOUCH EVENTS ─────────────────────────────────────────────
print("Step 2: Collecting touch events...", flush=True)

# Each record: (year, ref_close, fwd_returns[1..20])
# fwd_returns[k] = (close[T+k] - close[T]) / close[T]  for k=1..20
# None where index goes out of bounds (near EOD/end of data)

records_v1 = []  # pure touch
records_v2 = []  # strategy touch (+ volume filter)

for stock, arrs in stock_arrays.items():
    n       = arrs["n"]
    close   = arrs["close"]
    low     = arrs["low"]
    vol     = arrs["volume"]
    avg_vol = arrs["avg_vol"]
    ma20    = arrs["ma20"]
    year    = arrs["year"]

    for i in range(n - MAX_N - 1):
        if np.isnan(ma20[i]):
            continue

        is_touch = low[i] <= ma20[i]
        if not is_touch:
            continue

        ref = close[i]
        if ref <= 0 or np.isnan(ref):
            continue

        yr = year[i]

        # forward returns N=1..20
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

        records_v1.append((yr, fwd))

        # volume filter for V2
        if not np.isnan(avg_vol[i]) and vol[i] >= avg_vol[i] * VOL_MULT:
            records_v2.append((yr, fwd))

print(f"  V1 (pure touch)     : {len(records_v1):,} touch events", flush=True)
print(f"  V2 (strategy touch) : {len(records_v2):,} touch events", flush=True)


# ── STEP 3: COMPUTE STATS ────────────────────────────────────────────────────

def compute_stats(records, label):
    """
    records: list of (year, fwd_list) where fwd_list[k] = return at N=k+1
    Returns: overall DataFrame + dict of year-wise DataFrames
    """

    def stats_for_subset(recs, n_val):
        returns = np.array([r[1][n_val - 1] for r in recs])
        count   = len(returns)
        if count < 5:
            return {
                "N": n_val, "count": count,
                "mean_pct": np.nan, "median_pct": np.nan,
                "pct_positive": np.nan, "t_stat": np.nan, "p_value": np.nan,
            }
        mean    = returns.mean()
        median  = np.median(returns)
        pct_pos = (returns > 0).mean() * 100
        t_stat, p_val = stats.ttest_1samp(returns, 0)
        return {
            "N":           n_val,
            "count":       count,
            "mean_pct":    round(mean * 100, 4),
            "median_pct":  round(median * 100, 4),
            "pct_positive": round(pct_pos, 2),
            "t_stat":      round(t_stat, 3),
            "p_value":     round(p_val, 4),
        }

    # overall
    overall_rows = [stats_for_subset(records, n) for n in range(1, MAX_N + 1)]
    df_overall   = pd.DataFrame(overall_rows)

    # year-wise
    years       = sorted(set(r[0] for r in records))
    year_dfs    = {}
    for yr in years:
        yr_recs = [r for r in records if r[0] == yr]
        rows    = [stats_for_subset(yr_recs, n) for n in range(1, MAX_N + 1)]
        year_dfs[yr] = pd.DataFrame(rows)

    return df_overall, year_dfs


print("Step 3: Computing statistics...", flush=True)

df_v1_overall, df_v1_years = compute_stats(records_v1, "V1")
df_v2_overall, df_v2_years = compute_stats(records_v2, "V2")

print("  Done.", flush=True)


# ── STEP 4: PRINT RESULTS ────────────────────────────────────────────────────

COL_W = 12

def print_table(df, title):
    print(f"\n{'='*80}", flush=True)
    print(f"  {title}", flush=True)
    print(f"{'='*80}", flush=True)
    header = (
        f"{'N':>4}  {'Count':>8}  {'Mean%':>8}  {'Median%':>8}  "
        f"{'%Pos':>7}  {'t-stat':>8}  {'p-value':>8}"
    )
    print(header, flush=True)
    print("-" * 70, flush=True)
    for _, row in df.iterrows():
        sig = "*" if (not np.isnan(row["p_value"]) and row["p_value"] < 0.05) else " "
        print(
            f"{int(row['N']):>4}  {int(row['count']):>8,}  "
            f"{row['mean_pct']:>8.4f}  {row['median_pct']:>8.4f}  "
            f"{row['pct_positive']:>7.2f}  {row['t_stat']:>8.3f}  "
            f"{row['p_value']:>8.4f}{sig}",
            flush=True
        )
    print("  * p < 0.05 (statistically significant)", flush=True)


# ── OVERALL ──
print_table(df_v1_overall, "V1 — PURE TOUCH (low <= MA20) — OVERALL 2015–2025")
print_table(df_v2_overall, "V2 — STRATEGY TOUCH (+ volume filter) — OVERALL 2015–2025")

# ── YEAR-WISE ──
all_years = sorted(set(list(df_v1_years.keys()) + list(df_v2_years.keys())))

for yr in all_years:
    if yr in df_v1_years:
        print_table(df_v1_years[yr], f"V1 — PURE TOUCH — {yr}")
    if yr in df_v2_years:
        print_table(df_v2_years[yr], f"V2 — STRATEGY TOUCH — {yr}")


# ── STEP 5: SAVE OUTPUTS ─────────────────────────────────────────────────────
print("\nStep 5: Saving outputs...", flush=True)

# Save overall CSVs
for variant, df in [("v1_pure_touch", df_v1_overall), ("v2_strategy_touch", df_v2_overall)]:
    for out in [OUT_DIR, MOBILE_DIR]:
        df.to_csv(out / f"signal_validation_{variant}_overall.csv", index=False)

# Save year-wise CSVs (combined)
for variant, year_dfs in [("v1_pure_touch", df_v1_years), ("v2_strategy_touch", df_v2_years)]:
    rows = []
    for yr, df in year_dfs.items():
        df = df.copy()
        df.insert(0, "year", yr)
        rows.append(df)
    combined = pd.concat(rows, ignore_index=True)
    for out in [OUT_DIR, MOBILE_DIR]:
        combined.to_csv(out / f"signal_validation_{variant}_yearly.csv", index=False)

print(f"  Outputs saved to: {OUT_DIR}", flush=True)
print(f"  Mobile copy  to : {MOBILE_DIR}", flush=True)
print("\nDone.", flush=True)
