"""
bqs_r2_m6_body_ratio.py — BQS Round 2 M6: Touch Candle Body Ratio
===================================================================
For each trade at m6_touch_candle_index:
  touch_body = abs(close - open) of touch candle
  prior_body = abs(close - open) of candle before touch (same day only)
  body_ratio = touch_body / prior_body
  skip if prior_body == 0 or prior candle is on previous day

Winner definitions (inline):
  w1 = exit_reason == "target"
  w2 = pnl > upstox_charges
  w3 = pnl > kite_charges

Buckets: <0.5 | 0.5–1.0 | 1.0–1.5 | 1.5–2.0 | >2.0
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


# ── STEP 3: LOAD DS3 + COMPUTE BODY RATIO ────────────────────────────────────

print("\nStep 3: Loading DS3 and computing body ratio...", flush=True)

stocks_needed = set(df["stock"].unique())
stock_files   = sorted(f for f in DS3_DIR.glob("*.parquet") if f.stem not in EXCLUDE)

body_ratio    = np.full(n, np.nan, dtype=float)
stock_to_rows = df.groupby("stock").indices

n_zero_prior  = 0
n_cross_day   = 0

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
    open_arr     = sdf["open"].to_numpy(dtype=float)
    close_arr    = sdf["close"].to_numpy(dtype=float)

    time_mins_arr = (time_int_arr // 100) * 60 + (time_int_arr % 100)
    wd_idx_arr    = ((time_mins_arr - _OPEN_MINS) // 5).astype(int)

    lookup = {}
    for abs_i in range(len(sdf)):
        lookup[(date_int_arr[abs_i], wd_idx_arr[abs_i])] = abs_i

    for df_row, tr in zip(row_indices, stock_df_rows.itertuples()):
        date  = int(tr.entry_date)
        m6    = int(round(tr.m6_touch_candle_index))
        abs_i = lookup.get((date, m6))

        if abs_i is None or abs_i < 1:
            continue

        # Same-day check for prior candle
        if date_int_arr[abs_i - 1] != date:
            n_cross_day += 1
            continue

        touch_body = abs(close_arr[abs_i]     - open_arr[abs_i])
        prior_body = abs(close_arr[abs_i - 1] - open_arr[abs_i - 1])

        if prior_body < 1e-8:
            n_zero_prior += 1
            continue

        body_ratio[df_row] = touch_body / prior_body

    print(f"  {stock}: {len(row_indices)} trades", flush=True)

df["body_ratio"] = body_ratio

n_valid = df["body_ratio"].notna().sum()
n_nan   = df["body_ratio"].isna().sum()
print(f"\n  Computed : {n_valid:,} valid | {n_nan:,} skipped", flush=True)
print(f"  Skipped  : {n_cross_day} cross-day prior | {n_zero_prior} zero-body prior", flush=True)
print(f"  Range    : {df['body_ratio'].min():.3f} – {df['body_ratio'].max():.1f}", flush=True)
print(f"  Median   : {df['body_ratio'].median():.3f}", flush=True)


# ── STEP 4: BUCKET + BREAKDOWN ────────────────────────────────────────────────

BUCKET_EDGES  = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, float("inf")]
BUCKET_LABELS = ["<0.5", "0.5–1.0", "1.0–1.5", "1.5–2.0", "2.0–3.0", ">3.0"]

df["body_bucket"] = pd.cut(
    df["body_ratio"],
    bins=BUCKET_EDGES,
    labels=BUCKET_LABELS,
    right=False,
    include_lowest=True
)

df_valid = df[df["body_ratio"].notna()].copy()
n_capped = (df_valid["body_ratio"] > 5.0).sum()
df_valid = df_valid[df_valid["body_ratio"] <= 5.0].copy()

LABELS = {
    "w1": "W1 — target hit      (baseline 14.8%)",
    "w2": "W2 — net Upstox +ve  (baseline 32.5%)",
    "w3": "W3 — net Kite +ve    (baseline 35.3%)",
}

print(f"\n  Capped  : {n_capped:,} trades with ratio > 5.0 excluded", flush=True)
print(f"  Kept    : {len(df_valid):,} trades", flush=True)

print(f"\n{'='*65}", flush=True)
print("  BQS-R2 M6 — TOUCH BODY RATIO vs WIN RATE (capped at 5.0)", flush=True)
print(f"  touch_body / prior_body  |  same-day prior only", flush=True)
print(f"{'='*65}", flush=True)

for wc in ["w1", "w2", "w3"]:
    base = BASELINES[wc]
    print(f"\n  {LABELS[wc]}", flush=True)
    print(f"  {'Bucket':<10} {'Trades':>8} {'Win':>7} {'Win%':>7} {'vs Base':>9}", flush=True)
    print(f"  {'─'*48}", flush=True)

    for lbl in BUCKET_LABELS:
        sub = df_valid[df_valid["body_bucket"] == lbl]
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
print("  BODY RATIO DISTRIBUTION", flush=True)
print(f"  {'─'*38}", flush=True)
dist = df_valid["body_bucket"].value_counts()
for lbl in BUCKET_LABELS:
    cnt = dist.get(lbl, 0)
    print(f"  {lbl:<10} {cnt:>8,}  ({cnt/len(df_valid)*100:.1f}%)", flush=True)
print(f"{'='*65}", flush=True)
