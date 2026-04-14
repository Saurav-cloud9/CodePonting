"""
bqs_r2_m10_gap_open.py — BQS Round 2 M10: Day Open Gap to MA20
===============================================================
For each trade, at the 09:15 candle (first candle of entry_date):
  day_open = open price of 09:15 candle
  day_ma20 = MA20 value at 09:15 candle
  gap_pct  = (day_open - day_ma20) / day_ma20 × 100

Buckets: <0.5% | 0.5–1.0% | 1.0–1.5% | 1.5–2.5% | >2.5%
  (gap_pct can be negative — open below MA20 — kept as-is)

Winner definitions (inline):
  w1 = exit_reason == "target"
  w2 = pnl > upstox_charges
  w3 = pnl > kite_charges
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

FV1_DIR  = SANDBOX_DIR.parent
DS3_DIR  = FV1_DIR / "data/historical/intraday_5min_DS3"
BQS_PATH = SANDBOX_DIR / "outputs/bqs/bqs_trades.parquet"

EXCLUDE    = {"NIFTY50", "VI"}
_OPEN_MINS = 9 * 60 + 15
BASELINES  = {"w1": 14.8, "w2": 32.5, "w3": 35.3}


# ── CHARGE FORMULA ───────────────────────────────────────────────────────────

def _charges_vec(entry, exit_price, qty, bkr_rate):
    buy_val   = entry * qty
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


# ── STEP 3: LOAD DS3 + COMPUTE OPEN GAP TO MA20 ──────────────────────────────

print("\nStep 3: Loading DS3 and computing day open gap to MA20...", flush=True)

stocks_needed = set(df["stock"].unique())
stock_files   = sorted(f for f in DS3_DIR.glob("*.parquet") if f.stem not in EXCLUDE)

gap_pct_arr   = np.full(n, np.nan, dtype=float)
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
    sdf = add_intraday_indicators(sdf)

    dti          = pd.DatetimeIndex(sdf["datetime"])
    date_int_arr = (dti.year * 10000 + dti.month * 100 + dti.day).to_numpy()
    time_int_arr = (dti.hour * 100 + dti.minute).to_numpy()
    open_arr     = sdf["open"].to_numpy(dtype=float)
    ma20_arr     = sdf["ma20"].to_numpy(dtype=float)

    # Build lookup: date_int → abs row of 09:15 candle (wd_idx == 0)
    time_mins_arr = (time_int_arr // 100) * 60 + (time_int_arr % 100)
    day_open_lookup = {}   # date_int → (day_open, day_ma20)
    for abs_i in range(len(sdf)):
        if time_mins_arr[abs_i] == _OPEN_MINS:   # 09:15 candle
            d = date_int_arr[abs_i]
            if d not in day_open_lookup:
                day_open_lookup[d] = (open_arr[abs_i], ma20_arr[abs_i])

    for df_row, tr in zip(row_indices, stock_df_rows.itertuples()):
        date = int(tr.entry_date)
        vals = day_open_lookup.get(date)
        if vals is None:
            continue

        day_open, day_ma20 = vals
        if np.isnan(day_ma20) or day_ma20 < 1e-8:
            continue

        gap_pct_arr[df_row] = (day_open - day_ma20) / day_ma20 * 100

    print(f"  {stock}: {len(row_indices)} trades", flush=True)

df["gap_pct"] = gap_pct_arr

n_valid = df["gap_pct"].notna().sum()
n_nan   = df["gap_pct"].isna().sum()
print(f"\n  Valid  : {n_valid:,} | Skipped (no MA20 or missing): {n_nan:,}", flush=True)
print(f"  Range  : {df['gap_pct'].min():.2f}% – {df['gap_pct'].max():.2f}%", flush=True)
print(f"  Median : {df['gap_pct'].median():.3f}%", flush=True)
print(f"  Below MA20 (gap < 0): {(df['gap_pct'] < 0).sum():,}", flush=True)


# ── STEP 4: BUCKET + BREAKDOWN ────────────────────────────────────────────────

# Note: gap can be negative (opened below MA20) — bucket as <0.5
BUCKET_EDGES  = [float("-inf"), 0.5, 1.0, 1.5, 2.5, float("inf")]
BUCKET_LABELS = ["<0.5%", "0.5–1.0%", "1.0–1.5%", "1.5–2.5%", ">2.5%"]

df["gap_bucket"] = pd.cut(
    df["gap_pct"],
    bins=BUCKET_EDGES,
    labels=BUCKET_LABELS,
    right=False,
    include_lowest=True
)

df_valid = df[df["gap_pct"].notna()].copy()

LABELS = {
    "w1": "W1 — target hit      (baseline 14.8%)",
    "w2": "W2 — net Upstox +ve  (baseline 32.5%)",
    "w3": "W3 — net Kite +ve    (baseline 35.3%)",
}

print(f"\n{'='*68}", flush=True)
print("  BQS-R2 M10 — DAY OPEN GAP TO MA20 vs WIN RATE", flush=True)
print(f"  gap_pct = (day_open - MA20@09:15) / MA20 × 100", flush=True)
print(f"  Negative = opened below MA20", flush=True)
print(f"{'='*68}", flush=True)

for wc in ["w1", "w2", "w3"]:
    base = BASELINES[wc]
    print(f"\n  {LABELS[wc]}", flush=True)
    print(f"  {'Bucket':<12} {'Trades':>8} {'Win':>7} {'Win%':>7} {'vs Base':>9}", flush=True)
    print(f"  {'─'*50}", flush=True)

    for lbl in BUCKET_LABELS:
        sub = df_valid[df_valid["gap_bucket"] == lbl]
        cnt = len(sub)
        if cnt == 0:
            continue
        win  = int(sub[wc].sum())
        wr   = win / cnt * 100
        vs   = wr - base
        sign = "+" if vs >= 0 else ""
        print(f"  {lbl:<12} {cnt:>8,} {win:>7,} {wr:>6.1f}%  {sign}{vs:.1f}pp", flush=True)

    cnt_all = len(df_valid)
    win_all = int(df_valid[wc].sum())
    wr_all  = win_all / cnt_all * 100
    print(f"  {'─'*50}", flush=True)
    print(f"  {'ALL':<12} {cnt_all:>8,} {win_all:>7,} {wr_all:>6.1f}%", flush=True)

# Distribution
print(f"\n{'='*68}", flush=True)
print("  GAP DISTRIBUTION", flush=True)
print(f"  {'─'*42}", flush=True)
dist = df_valid["gap_bucket"].value_counts()
for lbl in BUCKET_LABELS:
    cnt = dist.get(lbl, 0)
    print(f"  {lbl:<12} {cnt:>8,}  ({cnt/len(df_valid)*100:.1f}%)", flush=True)
print(f"{'='*68}", flush=True)
