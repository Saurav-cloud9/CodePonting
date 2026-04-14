"""
bqs_r2_m1_slope.py — BQS Round 2 M1: MA20 Slope at Touch
==========================================================
For each trade in bqs_trades.parquet (2022-2025):
  touch_idx = m6_touch_candle_index (bar index from 09:15, 5-min steps)
  slope     = (MA20[touch_idx] - MA20[touch_idx-5]) / price × 100
  category  : rising >+0.05% | flat ±0.05% | falling <-0.05%

Winner definitions (computed inline):
  w1 = exit_reason == "target"
  w2 = pnl > upstox_charges
  w3 = pnl > kite_charges

Output: W vs L breakdown by slope category for w1 / w2 / w3
"""

import sys
import io
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

EXCLUDE    = {"NIFTY50", "VI"}
_OPEN_MINS = 9 * 60 + 15   # 555 — 09:15

SLOPE_THRESH = 0.05   # % — rising > +0.05 | falling < -0.05


# ── CHARGE FORMULA (from core/portfolio.py) ──────────────────────────────────

def _charges_vec(entry, exit_price, qty, bkr_rate):
    """Vectorized round-trip NSE intraday charges."""
    buy_val   = entry      * qty
    sell_val  = exit_price * qty
    brokerage = np.minimum(buy_val * bkr_rate, 20.0) + np.minimum(sell_val * bkr_rate, 20.0)
    stt       = sell_val * 0.00025
    exchange  = (buy_val + sell_val) * 0.0000345
    sebi      = (buy_val + sell_val) * 0.000001
    gst       = (brokerage + exchange + sebi) * 0.18
    stamp     = buy_val * 0.00003
    return brokerage + stt + exchange + sebi + gst + stamp


# ── STEP 1: LOAD BQS TRADES ───────────────────────────────────────────────────

print("Step 1: Loading bqs_trades.parquet...", flush=True)
df = pd.read_parquet(BQS_PATH)
print(f"  {len(df):,} trades  |  columns: {df.columns.tolist()}", flush=True)


# ── STEP 2: DERIVE w1 / w2 / w3 ──────────────────────────────────────────────

print("\nStep 2: Deriving winner labels...", flush=True)

df["w1"] = (df["exit_reason"] == "target").astype(int)

ep  = df["entry_price"].to_numpy()
xp  = df["exit_price"].to_numpy()
qty = df["qty"].to_numpy()

df["w2"] = (df["pnl"].to_numpy() > _charges_vec(ep, xp, qty, 0.0005)).astype(int)
df["w3"] = (df["pnl"].to_numpy() > _charges_vec(ep, xp, qty, 0.0003)).astype(int)

n = len(df)
print(f"  w1 target hit : {df['w1'].sum():,} ({df['w1'].mean()*100:.1f}%)", flush=True)
print(f"  w2 net upstox : {df['w2'].sum():,} ({df['w2'].mean()*100:.1f}%)", flush=True)
print(f"  w3 net kite   : {df['w3'].sum():,} ({df['w3'].mean()*100:.1f}%)", flush=True)


# ── STEP 3: LOAD DS3 + COMPUTE MA20 SLOPE ────────────────────────────────────

print("\nStep 3: Loading DS3 and computing slopes...", flush=True)

stocks_needed = set(df["stock"].unique())
stock_files   = sorted(f for f in DS3_DIR.glob("*.parquet") if f.stem not in EXCLUDE)

slopes = np.full(n, np.nan, dtype=float)

# Build a fast row-index map: df index by stock for vectorized assignment
df = df.reset_index(drop=True)
stock_to_rows = df.groupby("stock").indices   # stock → array of df row indices

for sp in stock_files:
    stock = sp.stem
    if stock not in stocks_needed:
        continue

    row_indices = stock_to_rows[stock]
    stock_df_rows = df.iloc[row_indices]

    # Load DS3 for this stock
    sdf = pd.read_parquet(sp)
    sdf["datetime"] = pd.to_datetime(sdf["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S"))
    sdf = sdf.sort_values("datetime").reset_index(drop=True)
    sdf = sdf[sdf["datetime"].dt.year >= 2022].reset_index(drop=True)
    _t  = sdf["datetime"].dt.time
    sdf = sdf[_t.between(pd.Timestamp("09:15").time(), pd.Timestamp("15:30").time())]
    sdf = sdf.reset_index(drop=True)
    sdf = add_intraday_indicators(sdf)

    dti           = pd.DatetimeIndex(sdf["datetime"])
    date_int_arr  = (dti.year * 10000 + dti.month * 100 + dti.day).to_numpy()
    time_int_arr  = (dti.hour * 100 + dti.minute).to_numpy()
    ma20_arr      = sdf["ma20"].to_numpy(dtype=float)
    close_arr     = sdf["close"].to_numpy(dtype=float)

    # within_day_idx for each bar (0 = 09:15, 1 = 09:20, ...)
    time_mins_arr = (time_int_arr // 100) * 60 + (time_int_arr % 100)
    wd_idx_arr    = ((time_mins_arr - _OPEN_MINS) // 5).astype(int)

    # Build lookup: (date_int, within_day_idx) → absolute row position
    lookup = {}
    for abs_i in range(len(sdf)):
        key = (date_int_arr[abs_i], wd_idx_arr[abs_i])
        lookup[key] = abs_i

    # Compute slope for each trade in this stock
    for df_row, tr in zip(row_indices, stock_df_rows.itertuples()):
        date = int(tr.entry_date)
        m6   = int(round(tr.m6_touch_candle_index))

        if m6 < 5:
            # Not enough bars within the day for 5-bar lookback
            continue

        abs_i = lookup.get((date, m6))
        if abs_i is None:
            continue

        # Guard: bar 5 steps back must be on the same date
        if abs_i < 5 or date_int_arr[abs_i - 5] != date:
            continue

        ma_now  = ma20_arr[abs_i]
        ma_back = ma20_arr[abs_i - 5]
        price   = close_arr[abs_i]

        if np.isnan(ma_now) or np.isnan(ma_back) or price <= 0:
            continue

        slopes[df_row] = (ma_now - ma_back) / price * 100

    print(f"  {stock}: {len(row_indices)} trades", flush=True)

df["ma_slope"] = slopes

n_valid = df["ma_slope"].notna().sum()
n_nan   = df["ma_slope"].isna().sum()
print(f"\n  Slope computed: {n_valid:,} valid | {n_nan:,} NaN (m6<5 or MA not ready)", flush=True)


# ── STEP 4: CATEGORIZE ────────────────────────────────────────────────────────

def _cat(s):
    if pd.isna(s):
        return "nan"
    return "rising" if s > SLOPE_THRESH else ("falling" if s < -SLOPE_THRESH else "flat")

df["slope_cat"] = df["ma_slope"].map(_cat)

dist = df["slope_cat"].value_counts()
print(f"\n  Slope distribution:", flush=True)
for cat in ["rising", "flat", "falling", "nan"]:
    cnt = dist.get(cat, 0)
    print(f"    {cat:<10} {cnt:>8,}  ({cnt/n*100:.1f}%)", flush=True)


# ── STEP 5: W vs L BREAKDOWN ──────────────────────────────────────────────────

CATS      = ["rising", "flat", "falling"]
BASELINES = {"w1": 14.8, "w2": 32.5, "w3": 35.3}
LABELS    = {
    "w1": "W1 — target hit      (baseline 14.8%)",
    "w2": "W2 — net Upstox +ve  (baseline 32.5%)",
    "w3": "W3 — net Kite +ve    (baseline 35.3%)",
}

df_valid = df[df["slope_cat"] != "nan"].copy()

print(f"\n{'='*70}", flush=True)
print("  BQS-R2 M1 — MA20 SLOPE AT TOUCH vs WIN RATE", flush=True)
print(f"  Slope threshold: ±{SLOPE_THRESH}% | 5-bar lookback (25 min)", flush=True)
print(f"{'='*70}", flush=True)

for wc in ["w1", "w2", "w3"]:
    base = BASELINES[wc]
    print(f"\n  {LABELS[wc]}", flush=True)
    print(f"  {'Category':<10} {'Trades':>8} {'Win':>7} {'Win%':>7} {'vs Base':>9}", flush=True)
    print(f"  {'─'*48}", flush=True)

    for cat in CATS:
        sub = df_valid[df_valid["slope_cat"] == cat]
        cnt = len(sub)
        win = int(sub[wc].sum())
        wr  = win / cnt * 100 if cnt > 0 else 0.0
        vs  = wr - base
        sign = "+" if vs >= 0 else ""
        print(f"  {cat:<10} {cnt:>8,} {win:>7,} {wr:>6.1f}%  {sign}{vs:.1f}pp", flush=True)

    # Overall (valid only)
    sub_all = df_valid
    cnt_all = len(sub_all)
    win_all = int(sub_all[wc].sum())
    wr_all  = win_all / cnt_all * 100 if cnt_all > 0 else 0.0
    print(f"  {'─'*48}", flush=True)
    print(f"  {'ALL valid':<10} {cnt_all:>8,} {win_all:>7,} {wr_all:>6.1f}%", flush=True)

print(f"\n{'='*70}", flush=True)
