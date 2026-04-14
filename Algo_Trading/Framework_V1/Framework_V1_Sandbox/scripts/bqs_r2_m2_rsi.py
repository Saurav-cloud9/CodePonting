"""
bqs_r2_m2_rsi.py — BQS Round 2 M2: RSI-14 at Touch
=====================================================
For each trade in bqs_trades.parquet (2022-2025):
  touch_idx = m6_touch_candle_index (bar index from 09:15, 5-min steps)
  RSI-14    = Wilder's RSI computed from raw DS3 close prices

Winner definitions (inline):
  w1 = exit_reason == "target"
  w2 = pnl > upstox_charges
  w3 = pnl > kite_charges

Output:
  Bucket breakdown (<20 | 20-30 | 30-40 | 40-50 | 50-60 | 60-70 | >70)
  Mean RSI for winners vs losers per w1/w2/w3
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
_OPEN_MINS = 9 * 60 + 15   # 555 — 09:15
RSI_PERIOD = 14
BASELINES  = {"w1": 14.8, "w2": 32.5, "w3": 35.3}


# ── CHARGE FORMULA (core/portfolio.py) ───────────────────────────────────────

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


# ── WILDER RSI ────────────────────────────────────────────────────────────────

def compute_rsi_array(close_arr, period=14):
    """
    Wilder's RSI for a full price array.
    Returns array same length as close_arr.
    First `period` values are NaN (not enough data).
    """
    n   = len(close_arr)
    rsi = np.full(n, np.nan, dtype=float)
    if n < period + 1:
        return rsi

    delta  = np.diff(close_arr)                          # length n-1
    gains  = np.where(delta > 0, delta, 0.0)
    losses = np.where(delta < 0, -delta, 0.0)

    # Seed: simple average of first `period` changes
    avg_gain = float(np.mean(gains[:period]))
    avg_loss = float(np.mean(losses[:period]))

    if avg_loss == 0.0:
        rsi[period] = 100.0
    else:
        rsi[period] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)

    # Wilder smoothing from period onward
    for i in range(period, n - 1):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0.0:
            rsi[i + 1] = 100.0
        else:
            rsi[i + 1] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)

    return rsi


# ── STEP 1: LOAD BQS TRADES ───────────────────────────────────────────────────

print("Step 1: Loading bqs_trades.parquet...", flush=True)
df = pd.read_parquet(BQS_PATH)
df = df.reset_index(drop=True)
n  = len(df)
print(f"  {n:,} trades", flush=True)


# ── STEP 2: DERIVE w1 / w2 / w3 ──────────────────────────────────────────────

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


# ── STEP 3: LOAD DS3 + COMPUTE RSI AT TOUCH ──────────────────────────────────

print("\nStep 3: Loading DS3 and computing RSI-14 at touch...", flush=True)

stocks_needed = set(df["stock"].unique())
stock_files   = sorted(f for f in DS3_DIR.glob("*.parquet") if f.stem not in EXCLUDE)

rsi_at_touch = np.full(n, np.nan, dtype=float)
stock_to_rows = df.groupby("stock").indices

for sp in stock_files:
    stock = sp.stem
    if stock not in stocks_needed:
        continue

    row_indices   = stock_to_rows[stock]
    stock_df_rows = df.iloc[row_indices]

    # Load DS3
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
    close_arr    = sdf["close"].to_numpy(dtype=float)

    # Compute RSI across full array (continuous — crosses day boundaries intentionally,
    # as RSI is a momentum indicator that uses prior session closes for warm-up)
    rsi_arr = compute_rsi_array(close_arr, period=RSI_PERIOD)

    # Build lookup: (date_int, within_day_idx) → absolute row
    time_mins_arr = (time_int_arr // 100) * 60 + (time_int_arr % 100)
    wd_idx_arr    = ((time_mins_arr - _OPEN_MINS) // 5).astype(int)

    lookup = {}
    for abs_i in range(len(sdf)):
        lookup[(date_int_arr[abs_i], wd_idx_arr[abs_i])] = abs_i

    # Look up RSI at touch candle for each trade
    for df_row, tr in zip(row_indices, stock_df_rows.itertuples()):
        date = int(tr.entry_date)
        m6   = int(round(tr.m6_touch_candle_index))
        abs_i = lookup.get((date, m6))
        if abs_i is None:
            continue
        rsi_at_touch[df_row] = rsi_arr[abs_i]

    print(f"  {stock}: {len(row_indices)} trades", flush=True)

df["rsi_touch"] = rsi_at_touch

n_valid = df["rsi_touch"].notna().sum()
n_nan   = df["rsi_touch"].isna().sum()
print(f"\n  RSI computed: {n_valid:,} valid | {n_nan:,} NaN (insufficient warm-up bars)", flush=True)
print(f"  RSI range: {df['rsi_touch'].min():.1f} – {df['rsi_touch'].max():.1f}", flush=True)


# ── STEP 4: BUCKET BREAKDOWN ──────────────────────────────────────────────────

BUCKET_EDGES  = [0, 20, 30, 40, 50, 60, 70, 100]
BUCKET_LABELS = ["<20", "20–30", "30–40", "40–50", "50–60", "60–70", ">70"]

df["rsi_bucket"] = pd.cut(
    df["rsi_touch"],
    bins=BUCKET_EDGES,
    labels=BUCKET_LABELS,
    right=False,
    include_lowest=True
)

df_valid = df[df["rsi_touch"].notna()].copy()

LABELS = {
    "w1": "W1 — target hit      (baseline 14.8%)",
    "w2": "W2 — net Upstox +ve  (baseline 32.5%)",
    "w3": "W3 — net Kite +ve    (baseline 35.3%)",
}

print(f"\n{'='*75}", flush=True)
print("  BQS-R2 M2 — RSI-14 AT TOUCH vs WIN RATE", flush=True)
print(f"  Wilder RSI | 14-period | 5-min candles", flush=True)
print(f"{'='*75}", flush=True)

for wc in ["w1", "w2", "w3"]:
    base = BASELINES[wc]
    print(f"\n  {LABELS[wc]}", flush=True)
    print(f"  {'Bucket':<10} {'Trades':>8} {'Win':>7} {'Win%':>7} {'vs Base':>9}", flush=True)
    print(f"  {'─'*50}", flush=True)

    for lbl in BUCKET_LABELS:
        sub = df_valid[df_valid["rsi_bucket"] == lbl]
        cnt = len(sub)
        win = int(sub[wc].sum())
        wr  = win / cnt * 100 if cnt > 0 else 0.0
        vs  = wr - base
        sign = "+" if vs >= 0 else ""
        print(f"  {lbl:<10} {cnt:>8,} {win:>7,} {wr:>6.1f}%  {sign}{vs:.1f}pp", flush=True)

    cnt_all = len(df_valid)
    win_all = int(df_valid[wc].sum())
    wr_all  = win_all / cnt_all * 100 if cnt_all > 0 else 0.0
    print(f"  {'─'*50}", flush=True)
    print(f"  {'ALL valid':<10} {cnt_all:>8,} {win_all:>7,} {wr_all:>6.1f}%", flush=True)


# ── STEP 5: MEAN RSI — WINNERS vs LOSERS ────────────────────────────────────

print(f"\n{'='*75}", flush=True)
print("  MEAN RSI — WINNERS vs LOSERS", flush=True)
print(f"{'='*75}", flush=True)
print(f"\n  {'Label':<28} {'W mean':>8} {'W std':>7} {'L mean':>8} {'L std':>7} {'Gap':>7}", flush=True)
print(f"  {'─'*65}", flush=True)

for wc, lbl in [("w1", "W1 target hit"), ("w2", "W2 net Upstox"), ("w3", "W3 net Kite")]:
    w_rsi = df_valid[df_valid[wc] == 1]["rsi_touch"]
    l_rsi = df_valid[df_valid[wc] == 0]["rsi_touch"]
    gap   = w_rsi.mean() - l_rsi.mean()
    sign  = "+" if gap >= 0 else ""
    print(
        f"  {lbl:<28} {w_rsi.mean():>8.2f} {w_rsi.std():>7.2f} "
        f"{l_rsi.mean():>8.2f} {l_rsi.std():>7.2f} {sign}{gap:.2f}",
        flush=True
    )

print(f"\n{'='*75}", flush=True)
