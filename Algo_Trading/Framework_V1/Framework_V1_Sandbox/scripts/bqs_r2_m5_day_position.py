"""
bqs_r2_m5_day_position.py — BQS Round 2 M5: Day Position at Touch
==================================================================
For each trade at m6_touch_candle_index:
  day_high = max(high) from 09:15 to touch_idx (inclusive, no lookahead)
  day_low  = min(low)  from 09:15 to touch_idx (inclusive, no lookahead)
  day_position = (touch_close - day_low) / (day_high - day_low)

  0 = touch at day low so far | 1 = touch at day high so far

Winner definitions (inline):
  w1 = exit_reason == "target"
  w2 = pnl > upstox_charges
  w3 = pnl > kite_charges

Buckets: 0–0.2 | 0.2–0.4 | 0.4–0.6 | 0.6–0.8 | 0.8–1.0
"""

import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

SANDBOX_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SANDBOX_DIR))

FV1_DIR  = SANDBOX_DIR.parent
DS3_DIR  = FV1_DIR / "data/historical/intraday_5min_DS3"
BQS_PATH = SANDBOX_DIR / "outputs/bqs/bqs_trades.parquet"

EXCLUDE    = {"NIFTY50", "VI"}
_OPEN_MINS = 9 * 60 + 15
BASELINES  = {"w1": 14.8, "w2": 32.5, "w3": 35.3}


# ── CHARGE FORMULA ───────────────────────────────────────────────────────────

def _charges_vec(entry, exit_price, qty, bkr_rate):
    buy_val   = entry      * qty
    sell_val  = exit_price * qty
    brokerage = np.minimum(buy_val * bkr_rate, 20.0) + np.minimum(sell_val * bkr_rate, 20.0)
    stt       = sell_val * 0.00025
    exchange  = (buy_val + sell_val) * 0.0000345
    sebi      = (buy_val + sell_val) * 0.000001
    gst       = (brokerage + exchange + sebi) * 0.18
    stamp     = buy_val * 0.00003
    return brokerage + stt + exchange + sebi + gst + stamp


# ── STEP 1: LOAD ─────────────────────────────────────────────────────────────

print("Step 1: Loading bqs_trades.parquet...", flush=True)
df = pd.read_parquet(BQS_PATH)
df = df.reset_index(drop=True)
n  = len(df)
print(f"  {n:,} trades", flush=True)


# ── STEP 2: w1 / w2 / w3 ────────────────────────────────────────────────────

print("\nStep 2: Deriving winner labels...", flush=True)
ep  = df["entry_price"].to_numpy()
xp  = df["exit_price"].to_numpy()
qty = df["qty"].to_numpy()
pnl = df["pnl"].to_numpy()

df["w1"] = (df["exit_reason"] == "target").astype(int)
df["w2"] = (pnl > _charges_vec(ep, xp, qty, 0.0005)).astype(int)
df["w3"] = (pnl > _charges_vec(ep, xp, qty, 0.0003)).astype(int)

print(f"  w1 target hit : {df['w1'].sum():,} ({df['w1'].mean()*100:.1f}%)", flush=True)
print(f"  w2 net upstox : {df['w2'].sum():,} ({df['w2'].mean()*100:.1f}%)", flush=True)
print(f"  w3 net kite   : {df['w3'].sum():,} ({df['w3'].mean()*100:.1f}%)", flush=True)


# ── STEP 3: LOAD DS3 + COMPUTE DAY POSITION ──────────────────────────────────

print("\nStep 3: Loading DS3 and computing day position...", flush=True)

stocks_needed = set(df["stock"].unique())
stock_files   = sorted(f for f in DS3_DIR.glob("*.parquet") if f.stem not in EXCLUDE)

day_pos    = np.full(n, np.nan, dtype=float)
stock_to_rows = df.groupby("stock").indices

for sp in stock_files:
    stock = sp.stem
    if stock not in stocks_needed:
        continue

    row_indices   = stock_to_rows[stock]
    stock_df_rows = df.iloc[row_indices]

    sdf = pd.read_parquet(sp)
    sdf["datetime"] = pd.to_datetime(sdf["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S"))
    sdf = sdf.sort_values("datetime").reset_index(drop=True)
    sdf = sdf[sdf["datetime"].dt.year >= 2022].reset_index(drop=True)
    _t  = sdf["datetime"].dt.time
    sdf = sdf[_t.between(pd.Timestamp("09:15").time(), pd.Timestamp("15:30").time())]
    sdf = sdf.reset_index(drop=True)

    dti          = pd.DatetimeIndex(sdf["datetime"])
    date_int_arr = (dti.year * 10000 + dti.month * 100 + dti.day).to_numpy()
    time_int_arr = (dti.hour * 100 + dti.minute).to_numpy()
    high_arr     = sdf["high"].to_numpy(dtype=float)
    low_arr      = sdf["low"].to_numpy(dtype=float)
    close_arr    = sdf["close"].to_numpy(dtype=float)

    time_mins_arr = (time_int_arr // 100) * 60 + (time_int_arr % 100)
    wd_idx_arr    = ((time_mins_arr - _OPEN_MINS) // 5).astype(int)

    # Build lookup: (date_int, within_day_idx) → absolute row
    lookup = {}
    for abs_i in range(len(sdf)):
        lookup[(date_int_arr[abs_i], wd_idx_arr[abs_i])] = abs_i

    # Build day-start lookup: date_int → first absolute row of that day
    day_start = {}
    for abs_i in range(len(sdf)):
        d = date_int_arr[abs_i]
        if d not in day_start:
            day_start[d] = abs_i

    for df_row, tr in zip(row_indices, stock_df_rows.itertuples()):
        date  = int(tr.entry_date)
        m6    = int(round(tr.m6_touch_candle_index))
        abs_i = lookup.get((date, m6))

        if abs_i is None:
            continue

        # Candles from 09:15 to touch_idx inclusive (no lookahead)
        start = day_start.get(date)
        if start is None:
            continue

        window_high  = high_arr [start : abs_i + 1]
        window_low   = low_arr  [start : abs_i + 1]
        touch_close  = close_arr[abs_i]

        day_high = np.max(window_high)
        day_low  = np.min(window_low)
        rng      = day_high - day_low

        if rng < 1e-8:
            continue   # degenerate day — skip

        day_pos[df_row] = (touch_close - day_low) / rng

    print(f"  {stock}: {len(row_indices)} trades", flush=True)

df["day_pos"] = day_pos

n_valid = df["day_pos"].notna().sum()
n_nan   = df["day_pos"].isna().sum()
print(f"\n  Computed: {n_valid:,} valid | {n_nan:,} skipped", flush=True)
print(f"  Range: {df['day_pos'].min():.3f} – {df['day_pos'].max():.3f}", flush=True)


# ── STEP 4: BUCKET + BREAKDOWN ────────────────────────────────────────────────

BUCKET_EDGES  = [0.0, 0.2, 0.4, 0.6, 0.8, 1.001]
BUCKET_LABELS = ["0.0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"]

df["pos_bucket"] = pd.cut(
    df["day_pos"],
    bins=BUCKET_EDGES,
    labels=BUCKET_LABELS,
    right=False,
    include_lowest=True
)

df_valid = df[df["day_pos"].notna()].copy()

LABELS = {
    "w1": "W1 — target hit      (baseline 14.8%)",
    "w2": "W2 — net Upstox +ve  (baseline 32.5%)",
    "w3": "W3 — net Kite +ve    (baseline 35.3%)",
}

print(f"\n{'='*65}", flush=True)
print("  BQS-R2 M5 — DAY POSITION AT TOUCH vs WIN RATE", flush=True)
print(f"  (touch_close - day_low) / (day_high - day_low)  |  no lookahead", flush=True)
print(f"  0 = at day low so far  |  1 = at day high so far", flush=True)
print(f"{'='*65}", flush=True)

for wc in ["w1", "w2", "w3"]:
    base = BASELINES[wc]
    print(f"\n  {LABELS[wc]}", flush=True)
    print(f"  {'Bucket':<10} {'Trades':>8} {'Win':>7} {'Win%':>7} {'vs Base':>9}", flush=True)
    print(f"  {'─'*48}", flush=True)

    for lbl in BUCKET_LABELS:
        sub = df_valid[df_valid["pos_bucket"] == lbl]
        cnt = len(sub)
        if cnt == 0:
            continue
        win  = int(sub[wc].sum())
        wr   = win / cnt * 100
        vs   = wr - base
        sign = "+" if vs >= 0 else ""
        print(f"  {lbl:<10} {cnt:>8,} {win:>7,} {wr:>6.1f}%  {sign}{vs:.1f}pp", flush=True)

    cnt_all = len(df_valid)
    win_all = int(df_valid[wc].sum())
    wr_all  = win_all / cnt_all * 100
    print(f"  {'─'*48}", flush=True)
    print(f"  {'ALL':<10} {cnt_all:>8,} {win_all:>7,} {wr_all:>6.1f}%", flush=True)

# Distribution
print(f"\n{'='*65}", flush=True)
print("  DAY POSITION DISTRIBUTION", flush=True)
print(f"  {'─'*40}", flush=True)
dist = df_valid["pos_bucket"].value_counts().sort_index()
for lbl in BUCKET_LABELS:
    cnt = dist.get(lbl, 0)
    print(f"  {lbl:<10} {cnt:>8,}  ({cnt/len(df_valid)*100:.1f}%)", flush=True)
print(f"{'='*65}", flush=True)
