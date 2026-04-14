"""
bqs_r2_m7_doji.py — BQS Round 2 M7: Candle Type at Touch
==========================================================
For each trade at m6_touch_candle_index:

  Doji definition: body / range < 0.1  (body < 10% of total candle range)

  Doji subtypes:
    dragonfly  = lower_wick > 2x upper_wick AND doji
    gravestone = upper_wick > 2x lower_wick AND doji
    long_legged= both wicks present AND doji (neither of above)

  Non-doji:
    bullish = close > open
    bearish = close < open

Categories: dragonfly | gravestone | long_legged | bullish | bearish

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

FV1_DIR  = SANDBOX_DIR.parent
DS3_DIR  = FV1_DIR / "data/historical/intraday_5min_DS3"
BQS_PATH = SANDBOX_DIR / "outputs/bqs/bqs_trades.parquet"

EXCLUDE    = {"NIFTY50", "VI"}
_OPEN_MINS = 9 * 60 + 15
BASELINES  = {"w1": 14.8, "w2": 32.5, "w3": 35.3}
DOJI_THRESH = 0.1   # body / range < 10%


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


# ── STEP 3: LOAD DS3 + CLASSIFY CANDLE TYPE ──────────────────────────────────

print("\nStep 3: Loading DS3 and classifying touch candles...", flush=True)

stocks_needed = set(df["stock"].unique())
stock_files   = sorted(f for f in DS3_DIR.glob("*.parquet") if f.stem not in EXCLUDE)

candle_type = np.full(n, "nan", dtype=object)
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
    open_arr     = sdf["open"].to_numpy(dtype=float)
    close_arr    = sdf["close"].to_numpy(dtype=float)
    high_arr     = sdf["high"].to_numpy(dtype=float)
    low_arr      = sdf["low"].to_numpy(dtype=float)

    time_mins_arr = (time_int_arr // 100) * 60 + (time_int_arr % 100)
    wd_idx_arr    = ((time_mins_arr - _OPEN_MINS) // 5).astype(int)

    lookup = {}
    for abs_i in range(len(sdf)):
        lookup[(date_int_arr[abs_i], wd_idx_arr[abs_i])] = abs_i

    for df_row, tr in zip(row_indices, stock_df_rows.itertuples()):
        date  = int(tr.entry_date)
        m6    = int(round(tr.m6_touch_candle_index))
        abs_i = lookup.get((date, m6))
        if abs_i is None:
            continue

        o = open_arr[abs_i]
        c = close_arr[abs_i]
        h = high_arr[abs_i]
        l = low_arr[abs_i]

        body        = abs(c - o)
        rng         = h - l
        lower_wick  = min(o, c) - l
        upper_wick  = h - max(o, c)

        if rng < 1e-8:
            continue   # flat bar — skip

        is_doji = (body / rng) < DOJI_THRESH

        if is_doji:
            if lower_wick > 2 * upper_wick:
                candle_type[df_row] = "dragonfly"
            elif upper_wick > 2 * lower_wick:
                candle_type[df_row] = "gravestone"
            else:
                candle_type[df_row] = "long_legged"
        else:
            candle_type[df_row] = "bullish" if c > o else "bearish"

    print(f"  {stock}: {len(row_indices)} trades", flush=True)

df["candle_type"] = candle_type
df_valid = df[df["candle_type"] != "nan"].copy()

n_valid = len(df_valid)
n_skip  = n - n_valid
print(f"\n  Valid: {n_valid:,} | Skipped (flat/missing): {n_skip:,}", flush=True)


# ── STEP 4: DISTRIBUTION ─────────────────────────────────────────────────────

CATS = ["dragonfly", "gravestone", "long_legged", "bullish", "bearish"]
LABELS = {
    "w1": "W1 — target hit      (baseline 14.8%)",
    "w2": "W2 — net Upstox +ve  (baseline 32.5%)",
    "w3": "W3 — net Kite +ve    (baseline 35.3%)",
}

dist = df_valid["candle_type"].value_counts()
print(f"\n  Candle type distribution:", flush=True)
for cat in CATS:
    cnt = dist.get(cat, 0)
    print(f"    {cat:<14} {cnt:>7,}  ({cnt/n_valid*100:.1f}%)", flush=True)


# ── STEP 5: W vs L BREAKDOWN ──────────────────────────────────────────────────

print(f"\n{'='*68}", flush=True)
print("  BQS-R2 M7 — CANDLE TYPE AT TOUCH vs WIN RATE", flush=True)
print(f"  Doji threshold: body/range < {DOJI_THRESH*100:.0f}%", flush=True)
print(f"  Dragonfly: lower_wick > 2x upper | Gravestone: upper_wick > 2x lower", flush=True)
print(f"{'='*68}", flush=True)

for wc in ["w1", "w2", "w3"]:
    base = BASELINES[wc]
    print(f"\n  {LABELS[wc]}", flush=True)
    print(f"  {'Category':<14} {'Trades':>8} {'Win':>7} {'Win%':>7} {'vs Base':>9}", flush=True)
    print(f"  {'─'*52}", flush=True)

    for cat in CATS:
        sub = df_valid[df_valid["candle_type"] == cat]
        cnt = len(sub)
        if cnt == 0:
            print(f"  {cat:<14} {'0':>8}", flush=True)
            continue
        win  = int(sub[wc].sum())
        wr   = win / cnt * 100
        vs   = wr - base
        sign = "+" if vs >= 0 else ""
        print(f"  {cat:<14} {cnt:>8,} {win:>7,} {wr:>6.1f}%  {sign}{vs:.1f}pp", flush=True)

    cnt_all = n_valid
    win_all = int(df_valid[wc].sum())
    wr_all  = win_all / cnt_all * 100
    print(f"  {'─'*52}", flush=True)
    print(f"  {'ALL valid':<14} {cnt_all:>8,} {win_all:>7,} {wr_all:>6.1f}%", flush=True)

print(f"\n{'='*68}", flush=True)
