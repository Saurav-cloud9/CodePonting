"""
bqs_r2_join.py — BQS Step 4.4b P2: Join R2 Metrics onto bqs_trades.parquet
============================================================================
Loads the P1 parquet (with w2/w3), computes all 11 R2 metrics from DS3
in a single pass per stock, then overwrites bqs_trades.parquet.

R2 metrics added:
  r2_m1_ma20_slope   : (MA20[touch] - MA20[touch-5]) / close × 100
  r2_m2_rsi14        : Wilder RSI-14 at touch candle (continuous across days)
  r2_m3_freshness    : count of candles in last 20 where low <= MA20
  r2_m4_vol_trend    : avg(vol[-2:]) - avg(vol[-5:-3]) before touch candle
  r2_m5_day_position : (touch_close - day_low) / (day_high - day_low), no lookahead
  r2_m6_body_ratio   : abs(touch_close-touch_open) / abs(prior_close-prior_open)
  r2_m61_wick_body   : (min(o,c) - low) / abs(c - o) at touch candle
  r2_m7_candle_type  : 0=dragonfly 1=gravestone 2=long_legged 3=bullish 4=bearish
  r2_m8_dow          : day-of-week (0=Mon … 4=Fri), derived from entry_date
  r2_m9_vol_ratio    : bounce_vol / touch_vol (same-day only)
  r2_m10_gap_open    : (open@09:15 - MA20@09:15) / MA20 × 100

Column names in parquet use the exact names above.
Candle-type encoding: dragonfly=0, gravestone=1, long_legged=2, bullish=3, bearish=4.
NaN = insufficient data (first candle of day, not enough history, etc.).
"""

import sys
import io
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

SANDBOX_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SANDBOX_DIR))
from core.indicators import add_intraday_indicators

FV1_DIR    = SANDBOX_DIR.parent
DS3_DIR    = FV1_DIR / "data/historical/intraday_5min_DS3"
BQS_PATH   = SANDBOX_DIR / "outputs/bqs/bqs_trades.parquet"
MOBILE_DIR = Path(r"C:\Users\saurav\OneDrive\CodePonting_Mobile\sandbox\bqs")

EXCLUDE     = {"NIFTY50", "VI"}
_OPEN_MINS  = 9 * 60 + 15   # 555 — 09:15
RSI_PERIOD  = 14
LOOKBACK_M3 = 20             # freshness lookback
SLOPE_BARS  = 5              # MA slope lookback
DOJI_THRESH = 0.1            # body/range < 10% → doji


# ── WILDER RSI (identical to bqs_r2_m2_rsi.py) ────────────────────────────────

def compute_rsi_array(close_arr, period=14):
    """Wilder's RSI for a full array. Continuous — crosses day boundaries."""
    n   = len(close_arr)
    rsi = np.full(n, np.nan, dtype=float)
    if n < period + 1:
        return rsi
    delta    = np.diff(close_arr)
    gains    = np.where(delta > 0, delta, 0.0)
    losses   = np.where(delta < 0, -delta, 0.0)
    avg_gain = float(np.mean(gains[:period]))
    avg_loss = float(np.mean(losses[:period]))
    if avg_loss == 0.0:
        rsi[period] = 100.0
    else:
        rsi[period] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    for i in range(period, n - 1):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0.0:
            rsi[i + 1] = 100.0
        else:
            rsi[i + 1] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    return rsi


# ── STEP 1: LOAD PARQUET ───────────────────────────────────────────────────────

print("Step 1: Loading bqs_trades.parquet...", flush=True)
df = pd.read_parquet(BQS_PATH)
df = df.reset_index(drop=True)
n  = len(df)
print(f"  {n:,} trades  |  {df.shape[1]} columns", flush=True)

for required in ("winner", "w2", "w3"):
    if required not in df.columns:
        print(f"  ERROR: '{required}' column missing. Run P1 (bqs_export.py) first.", flush=True)
        sys.exit(1)

print(f"  P1 columns confirmed: winner, w2, w3 present", flush=True)


# ── STEP 2: r2_m8_dow — derived from entry_date, no DS3 needed ────────────────

print("\nStep 2: Computing r2_m8_dow from entry_date...", flush=True)
df["r2_m8_dow"] = pd.to_datetime(
    df["entry_date"].astype(str), format="%Y%m%d"
).dt.dayofweek   # 0=Mon … 4=Fri
print(f"  Done  |  range: {int(df['r2_m8_dow'].min())}–{int(df['r2_m8_dow'].max())}", flush=True)


# ── STEP 3: INITIALIZE R2 ARRAYS ──────────────────────────────────────────────

r2_m1  = np.full(n, np.nan, dtype=float)   # ma20_slope
r2_m2  = np.full(n, np.nan, dtype=float)   # rsi14
r2_m3  = np.full(n, np.nan, dtype=float)   # freshness (count, NaN if insufficient)
r2_m4  = np.full(n, np.nan, dtype=float)   # vol_trend (raw difference)
r2_m5  = np.full(n, np.nan, dtype=float)   # day_position [0,1]
r2_m6  = np.full(n, np.nan, dtype=float)   # body_ratio
r2_m61 = np.full(n, np.nan, dtype=float)   # wick/body ratio
r2_m7  = np.full(n, np.nan, dtype=float)   # candle_type (0–4 encoded)
r2_m9  = np.full(n, np.nan, dtype=float)   # bounce/touch vol ratio
r2_m10 = np.full(n, np.nan, dtype=float)   # gap_open pct


# ── STEP 4: PER-STOCK DS3 LOAD + COMPUTE ALL R2 METRICS ───────────────────────

print("\nStep 3: Loading DS3 and computing all R2 metrics...", flush=True)
t0 = time.time()

stocks_needed = set(df["stock"].unique())
stock_files   = sorted(f for f in DS3_DIR.glob("*.parquet") if f.stem not in EXCLUDE)
stock_to_rows = df.groupby("stock").indices

for sp in stock_files:
    stock = sp.stem
    if stock not in stocks_needed:
        continue

    row_indices   = stock_to_rows[stock]
    stock_df_rows = df.iloc[row_indices]

    # ── Load DS3 for this stock ────────────────────────────────────────────────
    sdf = pd.read_parquet(sp)
    sdf["datetime"] = pd.to_datetime(sdf["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S"))
    sdf = sdf.sort_values("datetime").reset_index(drop=True)
    sdf = sdf[sdf["datetime"].dt.year >= 2022].reset_index(drop=True)
    _t  = sdf["datetime"].dt.time
    sdf = sdf[_t.between(pd.Timestamp("09:15").time(), pd.Timestamp("15:30").time())]
    sdf = sdf.reset_index(drop=True)
    sdf = add_intraday_indicators(sdf)
    N   = len(sdf)

    dti          = pd.DatetimeIndex(sdf["datetime"])
    date_int_arr = (dti.year * 10000 + dti.month * 100 + dti.day).to_numpy()
    time_int_arr = (dti.hour * 100 + dti.minute).to_numpy()
    open_arr     = sdf["open"].to_numpy(dtype=float)
    high_arr     = sdf["high"].to_numpy(dtype=float)
    low_arr      = sdf["low"].to_numpy(dtype=float)
    close_arr    = sdf["close"].to_numpy(dtype=float)
    vol_arr      = sdf["volume"].to_numpy(dtype=float)
    ma20_arr     = sdf["ma20"].to_numpy(dtype=float)

    # RSI computed continuously across full array
    rsi_arr = compute_rsi_array(close_arr, period=RSI_PERIOD)

    # Within-day bar index (0 = 09:15, 1 = 09:20, ...)
    time_mins_arr = (time_int_arr // 100) * 60 + (time_int_arr % 100)
    wd_idx_arr    = ((time_mins_arr - _OPEN_MINS) // 5).astype(int)

    # Primary lookup: (date_int, within_day_idx) → absolute row
    lookup = {}
    for abs_i in range(N):
        lookup[(date_int_arr[abs_i], wd_idx_arr[abs_i])] = abs_i

    # Day-start lookup: date_int → first absolute row of that trading day
    day_start = {}
    for abs_i in range(N):
        d = date_int_arr[abs_i]
        if d not in day_start:
            day_start[d] = abs_i

    # Day-open lookup: date_int → (open@09:15, ma20@09:15)
    day_open_lookup = {}
    for abs_i in range(N):
        if time_mins_arr[abs_i] == _OPEN_MINS:
            d = date_int_arr[abs_i]
            if d not in day_open_lookup:
                day_open_lookup[d] = (open_arr[abs_i], ma20_arr[abs_i])

    # ── Per-trade computation ──────────────────────────────────────────────────
    for df_row, tr in zip(row_indices, stock_df_rows.itertuples()):
        date = int(tr.entry_date)
        m6   = int(round(tr.m6_touch_candle_index))   # within-day touch bar
        gap  = int(round(tr.m7_bounce_gap))            # bounce offset from touch

        abs_i = lookup.get((date, m6))
        if abs_i is None:
            continue

        # pull touch candle OHLCV once
        o = open_arr[abs_i]
        h = high_arr[abs_i]
        l = low_arr[abs_i]
        c = close_arr[abs_i]

        # ── r2_m1: MA20 slope at touch (5-bar lookback, same day) ─────────────
        if m6 >= SLOPE_BARS and abs_i >= SLOPE_BARS:
            if date_int_arr[abs_i - SLOPE_BARS] == date:
                ma_now  = ma20_arr[abs_i]
                ma_back = ma20_arr[abs_i - SLOPE_BARS]
                if not (np.isnan(ma_now) or np.isnan(ma_back)) and c > 0:
                    r2_m1[df_row] = (ma_now - ma_back) / c * 100

        # ── r2_m2: RSI-14 at touch ────────────────────────────────────────────
        rsi_val = rsi_arr[abs_i]
        if not np.isnan(rsi_val):
            r2_m2[df_row] = rsi_val

        # ── r2_m3: MA freshness (count low <= MA20 in last 20 bars) ──────────
        if abs_i >= LOOKBACK_M3:
            w_low  = low_arr [abs_i - LOOKBACK_M3 : abs_i]
            w_ma20 = ma20_arr[abs_i - LOOKBACK_M3 : abs_i]
            valid  = ~np.isnan(w_ma20)
            if valid.sum() == LOOKBACK_M3:
                r2_m3[df_row] = float(np.sum(w_low[valid] <= w_ma20[valid]))

        # ── r2_m4: volume trend 5 bars before touch ───────────────────────────
        if abs_i >= 5:
            w_vol = vol_arr[abs_i - 5 : abs_i]   # oldest[0] … newest[4]
            if not np.any(np.isnan(w_vol)):
                r2_m4[df_row] = np.mean(w_vol[3:5]) - np.mean(w_vol[0:2])

        # ── r2_m5: day position at touch ──────────────────────────────────────
        start = day_start.get(date)
        if start is not None:
            w_hi   = high_arr[start : abs_i + 1]
            w_lo   = low_arr [start : abs_i + 1]
            d_high = np.max(w_hi)
            d_low  = np.min(w_lo)
            rng    = d_high - d_low
            if rng >= 1e-8:
                r2_m5[df_row] = (c - d_low) / rng

        # ── r2_m6: body ratio (touch body / prior body, same-day prior) ───────
        if abs_i >= 1 and date_int_arr[abs_i - 1] == date:
            touch_body = abs(c - o)
            prior_body = abs(close_arr[abs_i - 1] - open_arr[abs_i - 1])
            if prior_body >= 1e-8:
                r2_m6[df_row] = touch_body / prior_body

        # ── r2_m61: lower_wick / body at touch candle ─────────────────────────
        body = abs(c - o)
        if body >= 1e-8:
            wick = min(o, c) - l
            if wick < 0:
                wick = 0.0
            r2_m61[df_row] = wick / body

        # ── r2_m7: candle type at touch ───────────────────────────────────────
        rng_c = h - l
        if rng_c >= 1e-8:
            body2      = abs(c - o)
            lower_wick = min(o, c) - l
            upper_wick = h - max(o, c)
            is_doji    = (body2 / rng_c) < DOJI_THRESH
            if is_doji:
                if lower_wick > 2 * upper_wick:
                    r2_m7[df_row] = 0.0   # dragonfly
                elif upper_wick > 2 * lower_wick:
                    r2_m7[df_row] = 1.0   # gravestone
                else:
                    r2_m7[df_row] = 2.0   # long_legged
            else:
                r2_m7[df_row] = 3.0 if c > o else 4.0   # bullish / bearish

        # ── r2_m9: bounce/touch volume ratio ──────────────────────────────────
        bounce_wd  = m6 + gap
        bounce_abs = lookup.get((date, bounce_wd))
        if bounce_abs is not None and date_int_arr[bounce_abs] == date:
            t_vol = vol_arr[abs_i]
            b_vol = vol_arr[bounce_abs]
            if t_vol >= 1e-8:
                r2_m9[df_row] = b_vol / t_vol

        # ── r2_m10: day open gap to MA20 at 09:15 ─────────────────────────────
        vals = day_open_lookup.get(date)
        if vals is not None:
            d_open, d_ma20 = vals
            if not np.isnan(d_ma20) and d_ma20 >= 1e-8:
                r2_m10[df_row] = (d_open - d_ma20) / d_ma20 * 100

    print(f"  {stock}: {len(row_indices)} trades", flush=True)

elapsed = time.time() - t0
print(f"\n  DS3 pass done in {elapsed:.1f}s", flush=True)


# ── STEP 5: JOIN COLUMNS ONTO DATAFRAME ───────────────────────────────────────

print("\nStep 4: Joining R2 columns...", flush=True)

df["r2_m1_ma20_slope"]  = r2_m1
df["r2_m2_rsi14"]       = r2_m2
df["r2_m3_freshness"]   = r2_m3
df["r2_m4_vol_trend"]   = r2_m4
df["r2_m5_day_position"]= r2_m5
df["r2_m6_body_ratio"]  = r2_m6
df["r2_m61_wick_body"]  = r2_m61
df["r2_m7_candle_type"] = r2_m7
# r2_m8_dow already computed in Step 2
df["r2_m9_vol_ratio"]   = r2_m9
df["r2_m10_gap_open"]   = r2_m10


# ── STEP 6: COVERAGE REPORT ───────────────────────────────────────────────────

print(f"\n{'='*68}", flush=True)
print("  R2 METRIC COVERAGE REPORT", flush=True)
print(f"{'='*68}", flush=True)
print(f"  {'Metric':<28} {'Valid':>8}  {'NaN':>7}  {'Coverage':>9}", flush=True)
print(f"  {'─'*60}", flush=True)

r2_cols = [
    ("r2_m1_ma20_slope",   "R2-M1  MA20 slope"),
    ("r2_m2_rsi14",        "R2-M2  RSI-14"),
    ("r2_m3_freshness",    "R2-M3  Freshness"),
    ("r2_m4_vol_trend",    "R2-M4  Vol trend"),
    ("r2_m5_day_position", "R2-M5  Day position"),
    ("r2_m6_body_ratio",   "R2-M6  Body ratio"),
    ("r2_m61_wick_body",   "R2-M61 Wick/body"),
    ("r2_m7_candle_type",  "R2-M7  Candle type"),
    ("r2_m8_dow",          "R2-M8  Day of week"),
    ("r2_m9_vol_ratio",    "R2-M9  Vol ratio"),
    ("r2_m10_gap_open",    "R2-M10 Gap open"),
]

for col, label in r2_cols:
    valid = int(df[col].notna().sum())
    nan_c = n - valid
    pct   = valid / n * 100
    print(f"  {label:<28} {valid:>8,}  {nan_c:>7,}  {pct:>8.1f}%", flush=True)

print(f"\n  Final shape: {df.shape[0]:,} rows × {df.shape[1]} columns", flush=True)

# Print r2_m7 encoding legend
print(f"\n  r2_m7_candle_type encoding:", flush=True)
for code, name in [(0, "dragonfly"), (1, "gravestone"), (2, "long_legged"), (3, "bullish"), (4, "bearish")]:
    cnt = int((df["r2_m7_candle_type"] == code).sum())
    print(f"    {code} = {name:<12} {cnt:>7,}  ({cnt/n*100:.1f}%)", flush=True)


# ── STEP 7: SAVE ──────────────────────────────────────────────────────────────

print(f"\nStep 5: Saving...", flush=True)
df.to_parquet(BQS_PATH, index=False)
print(f"  {BQS_PATH}", flush=True)

MOBILE_DIR.mkdir(parents=True, exist_ok=True)
dst = MOBILE_DIR / "bqs_trades.parquet"
df.to_parquet(dst, index=False)
print(f"  Mobile: {dst}", flush=True)

print(f"\n{'='*68}", flush=True)
print("  P2 COMPLETE — parquet ready for P3 DT/RF", flush=True)
print(f"  Total time: {time.time() - t0:.1f}s", flush=True)
print(f"{'='*68}", flush=True)
