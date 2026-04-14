"""
bqs_export.py — BQS Step 4.3: DS3 Trade Export + Winner/Loser Analysis
=======================================================================
Runs the Step 3.3 winner config (identical to run_winner.py),
attaches 9 BQS raw metrics to every trade, then runs winner vs loser analysis.

Config  : SL=A, PG=True, CP=True, AF=True, EC=False, slippage=0.05
Dataset : DS3, 2022-2025
Expected: ~28,085 trades, CAGR ~-8.62%

Outputs:
  Framework_V1_Sandbox/outputs/bqs/bqs_trades.parquet
  Framework_V1_Sandbox/outputs/bqs/bqs_trades.csv
  (+ copies to OneDrive mobile)
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
from core.indicators import add_intraday_indicators, add_atr

# ── CONSTANTS (identical to run_winner.py) ──────────────────────────────────────
INITIAL_CAPITAL = 1_000_000
YEARS           = 4
NUM_STOCKS      = 30
EXCLUDE         = {"NIFTY50", "VI"}
ATR_MULT_STOP   = 2.5
RR_TARGET       = 4.5 / 2.5       # = 1.8
RISK_PER_TRADE  = 0.01
VOL_MULT        = 1.2
LOOKAHEAD       = 3
_EOD_INT        = 1500
_CUTOFF_DEFAULT = 1430
_AUCTION_INT    = 945
_TICK           = 0.05

FV1_DIR    = SANDBOX_DIR.parent
DS3_DIR    = FV1_DIR / "data/historical/intraday_5min_DS3"
OUT_DIR    = SANDBOX_DIR / "outputs" / "bqs"
MOBILE_DIR = Path(r"C:\Users\saurav\OneDrive\CodePonting_Mobile\sandbox\bqs")

OUT_DIR.mkdir(parents=True, exist_ok=True)
MOBILE_DIR.mkdir(parents=True, exist_ok=True)

_OPEN_MINS  = 9 * 60 + 15   # 555 mins — 09:15 market open
_CLOSE_MINS = 15 * 60 + 30  # 930 mins — 15:30 market close

# ── STEP 1: LOAD DATA ───────────────────────────────────────────────────────────
print("Step 1: Loading stock data...", flush=True)
t0 = time.time()

stock_files = sorted(f for f in DS3_DIR.glob("*.parquet") if f.stem not in EXCLUDE)
print(f"  {len(stock_files)} stocks", flush=True)

stock_arrays = {}
stock_dfs    = {}

for sp in stock_files:
    stock = sp.stem
    df = pd.read_parquet(sp)
    df["datetime"] = pd.to_datetime(df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S"))
    df = df.sort_values("datetime").reset_index(drop=True)
    df = df[df["datetime"].dt.year >= 2022].reset_index(drop=True)
    _t = df["datetime"].dt.time
    df = df[_t.between(pd.Timestamp("09:15").time(), pd.Timestamp("15:30").time())]
    df = df.reset_index(drop=True)
    df = add_intraday_indicators(df)
    df = add_atr(df)
    stock_dfs[stock] = df

    dti      = pd.DatetimeIndex(df["datetime"])
    date_int = (dti.year * 10000 + dti.month * 100 + dti.day).to_numpy()
    time_int = (dti.hour * 100 + dti.minute).to_numpy()

    stock_arrays[stock] = {
        "open":     df["open"].to_numpy(dtype=float),
        "high":     df["high"].to_numpy(dtype=float),
        "low":      df["low"].to_numpy(dtype=float),
        "close":    df["close"].to_numpy(dtype=float),
        "volume":   df["volume"].to_numpy(dtype=float),
        "avg_vol":  df["avg_volume"].to_numpy(dtype=float),
        "ma20":     df["ma20"].to_numpy(dtype=float),
        "atr":      df["atr_14"].to_numpy(dtype=float),
        "date_int": date_int,
        "time_int": time_int,
        "n":        len(df),
    }

print(f"  Done in {time.time()-t0:.1f}s", flush=True)


# ── STEP 2: GENERATE SIGNAL MAPS (extended with touch_idx + bounce_idx) ────────
# Returns: {entry_idx: (entry_price, touch_idx, bounce_idx)}
print("Step 2: Generating signal maps...", flush=True)


def gen_signals_extended(stock):
    arrs     = stock_arrays[stock]
    n        = arrs["n"]
    ma20     = arrs["ma20"]
    avg_vol  = arrs["avg_vol"]
    vol      = arrs["volume"]
    low      = arrs["low"]
    close    = arrs["close"]
    open_    = arrs["open"]
    time_int = arrs["time_int"]

    raw = []
    for i in range(0, n - 3):
        if np.isnan(ma20[i]):
            continue
        if not np.isnan(avg_vol[i]) and vol[i] < avg_vol[i] * VOL_MULT:
            continue
        if low[i] <= ma20[i]:
            ma_touch = ma20[i]
            for j in range(i, min(i + LOOKAHEAD + 1, n)):
                if close[j] > ma_touch:
                    nxt = j + 1
                    if nxt >= n:
                        break
                    t_nxt = time_int[nxt]
                    if t_nxt >= _CUTOFF_DEFAULT:
                        break
                    if t_nxt < _AUCTION_INT:
                        break
                    raw.append((nxt, open_[nxt], i, j))  # (entry_idx, price, touch_idx, bounce_idx)
                    break

    seen = set()
    sm   = {}
    for nxt, ep, ti, bi in raw:
        if nxt not in seen:
            seen.add(nxt)
            sm[nxt] = (ep, ti, bi)
    return sm


signal_maps = {stock: gen_signals_extended(stock) for stock in stock_arrays}
total_sigs  = sum(len(v) for v in signal_maps.values())
print(f"  {total_sigs:,} signals across {len(signal_maps)} stocks", flush=True)


# ── STEP 3: BACKTEST (identical logic to run_winner.py, extended trade records) ─
# Position record: [entry_idx, entry_date, entry_price, qty, stop, target,
#                   touch_idx, bounce_idx, risk_amt]
print("Step 3: Running backtest...", flush=True)
t1 = time.time()

all_trades = []
total_pnl  = 0.0

for stock, arrs in stock_arrays.items():
    sm = signal_maps[stock]
    if not sm:
        continue

    open_arr  = arrs["open"]
    high_arr  = arrs["high"]
    low_arr   = arrs["low"]
    close_arr = arrs["close"]
    atr_arr   = arrs["atr"]
    date_arr  = arrs["date_int"]
    time_arr  = arrs["time_int"]
    n         = arrs["n"]

    cash      = INITIAL_CAPITAL
    positions = []

    for i in range(n):
        op  = open_arr[i]
        hi  = high_arr[i]
        lo  = low_arr[i]
        cl  = close_arr[i]
        atr = atr_arr[i]
        d   = date_arr[i]
        t   = time_arr[i]

        # Entry (PG=True: only if no open position)
        if i in sm and not positions:
            ep, touch_idx, bounce_idx = sm[i]
            entry    = ep + _TICK
            sd       = atr * ATR_MULT_STOP
            if sd <= 0:
                sd = entry * 0.01

            eq       = cash   # CP=True: use current equity
            risk_amt = eq * RISK_PER_TRADE
            per_cap  = eq / NUM_STOCKS
            qty      = max(min(int(per_cap / entry), int(risk_amt / sd)), 1)

            positions.append([
                i,                        # 0 entry_idx
                d,                        # 1 entry_date
                entry,                    # 2 entry_price
                qty,                      # 3 qty
                entry - sd,               # 4 stop  (SL=A: fixed)
                entry + sd * RR_TARGET,   # 5 target
                touch_idx,                # 6 touch_idx
                bounce_idx,               # 7 bounce_idx
                risk_amt,                 # 8 risk_amt (for winner label)
            ])

        if not positions:
            continue

        is_bull = cl > op
        kept    = []

        for pos in positions:
            if pos[0] == i:     # skip entry candle
                kept.append(pos)
                continue

            # EOD forced close
            if d == pos[1] and t >= _EOD_INT:
                pnl        = (op - pos[2]) * pos[3]
                cash      += pnl
                total_pnl += pnl
                all_trades.append({
                    "stock":       stock,
                    "entry_date":  pos[1],
                    "entry_price": pos[2],
                    "qty":         pos[3],
                    "stop":        pos[4],
                    "target":      pos[5],
                    "touch_idx":   pos[6],
                    "bounce_idx":  pos[7],
                    "risk_amt":    pos[8],
                    "exit_price":  op,
                    "exit_reason": "eod",
                    "pnl":         pnl,
                    "year":        int(str(pos[1])[:4]),
                })
                continue

            # Candle-direction exit priority (SL=A: fixed stop/target)
            stop   = pos[4]
            target = pos[5]
            exit_p      = None
            exit_reason = None

            if is_bull:
                if lo <= stop:
                    exit_p      = stop - _TICK
                    exit_reason = "sl"
                elif hi >= target:
                    exit_p      = target
                    exit_reason = "target"
            else:
                if hi >= target:
                    exit_p      = target
                    exit_reason = "target"
                elif lo <= stop:
                    exit_p      = stop - _TICK
                    exit_reason = "sl"

            if exit_p is not None:
                pnl        = (exit_p - pos[2]) * pos[3]
                cash      += pnl
                total_pnl += pnl
                all_trades.append({
                    "stock":       stock,
                    "entry_date":  pos[1],
                    "entry_price": pos[2],
                    "qty":         pos[3],
                    "stop":        pos[4],
                    "target":      pos[5],
                    "touch_idx":   pos[6],
                    "bounce_idx":  pos[7],
                    "risk_amt":    pos[8],
                    "exit_price":  exit_p,
                    "exit_reason": exit_reason,
                    "pnl":         pnl,
                    "year":        int(str(pos[1])[:4]),
                })
            else:
                kept.append(pos)

        positions = kept

elapsed_bt = time.time() - t1

# Quick sanity check — must match run_winner.py baseline
n_trades  = len(all_trades)
pnl_total = sum(r["pnl"] for r in all_trades)
final_eq  = INITIAL_CAPITAL + pnl_total
cagr      = ((final_eq / INITIAL_CAPITAL) ** (1 / YEARS) - 1) * 100
match_str = "OK" if abs(cagr - (-8.62)) < 0.15 else "MISMATCH — investigate"

print(f"  {n_trades:,} trades  |  CAGR {cagr:+.2f}%  |  {match_str}", flush=True)
print(f"  Expected: ~28,085 trades, ~-8.62% CAGR", flush=True)
print(f"  Backtest done in {elapsed_bt:.1f}s", flush=True)


# ── HELPER ──────────────────────────────────────────────────────────────────────
def time_int_to_mins(t_int):
    """Convert HHMM int (e.g. 935) to minutes from midnight (e.g. 575)."""
    return (t_int // 100) * 60 + (t_int % 100)


def _charges_vec(entry, exit_price, qty, bkr_rate):
    """Vectorized round-trip NSE intraday charges (from core/portfolio.py)."""
    buy_val   = entry      * qty
    sell_val  = exit_price * qty
    brokerage = np.minimum(buy_val * bkr_rate, 20.0) + np.minimum(sell_val * bkr_rate, 20.0)
    stt       = sell_val * 0.00025
    exchange  = (buy_val + sell_val) * 0.0000345
    sebi      = (buy_val + sell_val) * 0.000001
    gst       = (brokerage + exchange + sebi) * 0.18
    stamp     = buy_val * 0.00003
    return brokerage + stt + exchange + sebi + gst + stamp


# ── STEP 4: COMPUTE BQS METRICS ─────────────────────────────────────────────────
print("Step 4: Computing BQS metrics...", flush=True)

rows = []
for rec in all_trades:
    stock = rec["stock"]
    ti    = rec["touch_idx"]     # touch candle index in stock_arrays
    bi    = rec["bounce_idx"]    # bounce candle index
    arrs  = stock_arrays[stock]

    # Touch candle
    t_open  = arrs["open"][ti]
    t_low   = arrs["low"][ti]
    t_close = arrs["close"][ti]
    t_ma20  = arrs["ma20"][ti]
    t_time  = arrs["time_int"][ti]
    t_date  = arrs["date_int"][ti]

    # Bounce candle
    b_open  = arrs["open"][bi]
    b_close = arrs["close"][bi]
    b_vol   = arrs["volume"][bi]
    b_avg   = arrs["avg_vol"][bi]
    b_time  = arrs["time_int"][bi]

    # Entry candle (for M5)
    # entry_idx not stored separately — derive from touch + bounce + 1
    # Actually we stored entry_price but not entry_idx. Re-derive entry time
    # from signal map: entry candle = bounce_idx + 1 (always).
    # Note: bounce_idx + 1 is guaranteed valid by signal generation.
    e_idx  = bi + 1
    e_time = arrs["time_int"][e_idx]

    # ── M1: volume_ratio = bounce_bar_volume / avg_vol_20d ──────────────────────
    m1 = (b_vol / b_avg) if (not np.isnan(b_avg) and b_avg > 0) else np.nan

    # ── M2: bounce_strength_pct = (bounce_close - touch_low) / touch_low × 100 ──
    m2 = ((b_close - t_low) / t_low * 100) if t_low > 0 else np.nan

    # ── M3: wick_ratio = (touch_open - touch_low) / |touch_close - touch_open| ──
    body = abs(t_close - t_open)
    m3   = ((t_open - t_low) / body) if body > 1e-8 else np.nan

    # ── M4: candle_color = 1 if bounce_close > bounce_open else 0 ───────────────
    m4 = 1 if b_close > b_open else 0

    # ── M5: hours_until_close = (15:30 - entry_time) in decimal hours ───────────
    e_mins = time_int_to_mins(e_time)
    m5     = (_CLOSE_MINS - e_mins) / 60.0

    # ── M6: touch_candle_index = (touch_time - 09:15) / 5 mins ─────────────────
    t_mins = time_int_to_mins(t_time)
    m6     = (t_mins - _OPEN_MINS) / 5.0

    # ── M7: bounce_candle_index_gap = bounce_candle_index - touch_candle_index ──
    b_mins = time_int_to_mins(b_time)
    m7     = int(round((b_mins - t_mins) / 5.0))   # discrete: 0, 1, 2, or 3

    # ── M8: ma20_distance_pct = (ma20 - touch_low) / ma20 × 100 ────────────────
    m8 = ((t_ma20 - t_low) / t_ma20 * 100) if t_ma20 > 0 else np.nan

    # ── M9: prev_candle_dir = 1 if prev_open < prev_close else 0 ────────────────
    # Only valid if previous candle exists and is on the same trading day.
    if ti > 0:
        p_open  = arrs["open"][ti - 1]
        p_close = arrs["close"][ti - 1]
        p_date  = arrs["date_int"][ti - 1]
        if p_date == t_date:
            m9 = 1 if p_open < p_close else 0
        else:
            m9 = np.nan   # first candle of session — no valid prev candle
    else:
        m9 = np.nan

    # ── Winner label ─────────────────────────────────────────────────────────────
    # winner = 1 if hit target OR (eod exit AND pnl > 0.5 × risk_per_trade)
    winner = 1 if (
        rec["exit_reason"] == "target" or
        (rec["exit_reason"] == "eod" and rec["pnl"] > 0.5 * rec["risk_amt"])
    ) else 0

    rows.append({
        **rec,
        "m1_volume_ratio":        m1,
        "m2_bounce_strength_pct": m2,
        "m3_wick_ratio":          m3,
        "m4_candle_color":        int(m4),
        "m5_hours_until_close":   m5,
        "m6_touch_candle_index":  m6,
        "m7_bounce_gap":          m7,
        "m8_ma20_distance_pct":   m8,
        "m9_prev_candle_dir":     m9,
        "winner":                 winner,
    })

df_bqs = pd.DataFrame(rows)
df_bqs = df_bqs.rename(columns={
    "touch_idx":  "raw_touch_idx",
    "bounce_idx": "raw_bounce_idx",
})

print(f"  {len(df_bqs):,} trades enriched with BQS metrics", flush=True)


# ── STEP 4.5: COMPUTE CHARGES + w2/w3 ───────────────────────────────────────────
print("Step 4.5: Computing charges and winner labels (w2/w3)...", flush=True)

ep_arr  = df_bqs["entry_price"].to_numpy()
xp_arr  = df_bqs["exit_price"].to_numpy()
qty_arr = df_bqs["qty"].to_numpy()
pnl_arr = df_bqs["pnl"].to_numpy()

charges_upstox = _charges_vec(ep_arr, xp_arr, qty_arr, 0.0005)
charges_kite   = _charges_vec(ep_arr, xp_arr, qty_arr, 0.0003)

df_bqs["net_pnl_upstox"] = pnl_arr - charges_upstox
df_bqs["net_pnl_kite"]   = pnl_arr - charges_kite
df_bqs["w2"]             = (df_bqs["net_pnl_upstox"] > 0).astype(int)
df_bqs["w3"]             = (df_bqs["net_pnl_kite"]   > 0).astype(int)

n_total  = len(df_bqs)
w1_count = int(df_bqs["winner"].sum())
w2_count = int(df_bqs["w2"].sum())
w3_count = int(df_bqs["w3"].sum())

print(f"  w1 (target hit)  : {w1_count:,}  ({w1_count/n_total*100:.1f}%)", flush=True)
print(f"  w2 (net upstox)  : {w2_count:,}  ({w2_count/n_total*100:.1f}%)", flush=True)
print(f"  w3 (net kite)    : {w3_count:,}  ({w3_count/n_total*100:.1f}%)", flush=True)


# ── STEP 5: EXPORT ───────────────────────────────────────────────────────────────
print("Step 5: Exporting...", flush=True)
parquet_path = OUT_DIR / "bqs_trades.parquet"
csv_path     = OUT_DIR / "bqs_trades.csv"

df_bqs.to_parquet(parquet_path, index=False)
df_bqs.to_csv(csv_path, index=False)
print(f"  {parquet_path}", flush=True)
print(f"  {csv_path}", flush=True)

# Mobile copies
for dst in [MOBILE_DIR / "bqs_trades.parquet", MOBILE_DIR / "bqs_trades.csv"]:
    if dst.suffix == ".parquet":
        df_bqs.to_parquet(dst, index=False)
    else:
        df_bqs.to_csv(dst, index=False)
print(f"  Mobile: {MOBILE_DIR}", flush=True)


# ── STEP 6: WINNER vs LOSER ANALYSIS ────────────────────────────────────────────
print(f"\n{'='*70}", flush=True)
print("  WINNER vs LOSER ANALYSIS", flush=True)
print(f"{'='*70}", flush=True)

w = df_bqs[df_bqs["winner"] == 1]
l = df_bqs[df_bqs["winner"] == 0]
n_total    = len(df_bqs)
n_win      = len(w)
n_los      = len(l)
overall_wr = n_win / n_total * 100 if n_total else 0.0

print(f"\n  Total trades: {n_total:,}  |  Winners: {n_win:,} ({overall_wr:.1f}%)  |  Losers: {n_los:,}", flush=True)

sep_board = {}   # name -> separation score (Cohen's d for continuous, prop gap for binary, wr-range for C/D)


# ── GROUP A: Standard mean/std/gap — M1, M2, M3, M5, M6 ────────────────────────
print(f"\n{'─'*70}", flush=True)
print("  GROUP A — Mean / Std / Gap  (M1, M2, M3, M5, M6)", flush=True)
print(f"{'─'*70}", flush=True)

group_a = [
    ("m1_volume_ratio",        "M1  Volume Ratio"),
    ("m2_bounce_strength_pct", "M2  Bounce Strength %"),
    ("m3_wick_ratio",          "M3  Wick Ratio"),
    ("m5_hours_until_close",   "M5  Hours Until Close"),
    ("m6_touch_candle_index",  "M6  Touch Candle Index"),
]

for col, label in group_a:
    wv = w[col].dropna()
    lv = l[col].dropna()
    if len(wv) < 2 or len(lv) < 2:
        print(f"\n  {label}: insufficient data", flush=True)
        continue

    w_mean = wv.mean()
    w_std  = wv.std()
    l_mean = lv.mean()
    l_std  = lv.std()
    gap    = w_mean - l_mean
    mid    = (w_mean + l_mean) / 2

    pooled_std = np.sqrt((w_std**2 + l_std**2) / 2)
    cohen_d    = abs(gap) / pooled_std if pooled_std > 1e-9 else 0.0
    sep_board[label] = cohen_d

    print(f"\n  {label}", flush=True)
    print(f"    Winner : mean={w_mean:+.4f}  std={w_std:.4f}", flush=True)
    print(f"    Loser  : mean={l_mean:+.4f}  std={l_std:.4f}", flush=True)
    print(f"    Gap    : {gap:+.4f}  |  Suggested threshold: {mid:.4f}  |  Cohen's d: {cohen_d:.4f}", flush=True)


# ── GROUP B: Binary proportion — M4, M9 ─────────────────────────────────────────
print(f"\n{'─'*70}", flush=True)
print("  GROUP B — Binary Proportion  (M4, M9)", flush=True)
print(f"{'─'*70}", flush=True)

group_b = [
    ("m4_candle_color",    "M4  Candle Color (1=Bullish)"),
    ("m9_prev_candle_dir", "M9  Prev Candle Dir (1=Bullish)"),
]

for col, label in group_b:
    wv = w[col].dropna()
    lv = l[col].dropna()
    if len(wv) == 0 or len(lv) == 0:
        print(f"\n  {label}: insufficient data", flush=True)
        continue

    w_bull = wv.mean()
    l_bull = lv.mean()
    gap    = w_bull - l_bull
    sep_board[label] = abs(gap)

    print(f"\n  {label}", flush=True)
    print(f"    Winner bullish: {w_bull*100:.1f}%  ({int(wv.sum())}/{len(wv)})", flush=True)
    print(f"    Loser  bullish: {l_bull*100:.1f}%  ({int(lv.sum())}/{len(lv)})", flush=True)
    print(f"    Gap: {gap:+.4f}", flush=True)


# ── GROUP C: Discrete win rate per gap value — M7 ───────────────────────────────
print(f"\n{'─'*70}", flush=True)
print("  GROUP C — Win Rate per Gap Value  (M7: bounce_candle_gap 0-3)", flush=True)
print(f"{'─'*70}", flush=True)

m7_wrs = []
for gap_val in [0, 1, 2, 3]:
    sub = df_bqs[df_bqs["m7_bounce_gap"] == gap_val]
    cnt = len(sub)
    wr  = sub["winner"].mean() * 100 if cnt > 0 else np.nan
    m7_wrs.append((gap_val, cnt, wr))
    print(f"  Gap={gap_val}: {cnt:7,} trades  |  Win Rate: {wr:.2f}%", flush=True)

valid_m7_wrs = [v[2] for v in m7_wrs if not np.isnan(v[2])]
m7_sep = (max(valid_m7_wrs) - min(valid_m7_wrs)) / 100 if len(valid_m7_wrs) > 1 else 0.0
sep_board["M7  Bounce Gap"] = m7_sep
print(f"  Win rate range: {max(valid_m7_wrs):.2f}% - {min(valid_m7_wrs):.2f}% = {m7_sep*100:.2f}pp", flush=True)


# ── GROUP D: Binned win rate — M8 ───────────────────────────────────────────────
print(f"\n{'─'*70}", flush=True)
print("  GROUP D — Win Rate per Distance Bin  (M8: MA20 Distance %)", flush=True)
print(f"{'─'*70}", flush=True)

bins      = [float("-inf"), 0.3, 0.8, 1.5, 2.5, 3.5, float("inf")]
bin_labels = ["< 0.3%", "0.3–0.8%", "0.8–1.5%", "1.5–2.5%", "2.5–3.5%", "> 3.5%"]

df_bqs["m8_bin"] = pd.cut(df_bqs["m8_ma20_distance_pct"], bins=bins, labels=bin_labels)

m8_wrs = []
for lbl in bin_labels:
    sub = df_bqs[df_bqs["m8_bin"] == lbl]
    cnt = len(sub)
    wr  = sub["winner"].mean() * 100 if cnt > 0 else np.nan
    m8_wrs.append(wr)
    print(f"  {lbl:>12}: {cnt:7,} trades  |  Win Rate: {wr:.2f}%", flush=True)

valid_m8_wrs = [v for v in m8_wrs if not np.isnan(v)]
m8_sep = (max(valid_m8_wrs) - min(valid_m8_wrs)) / 100 if len(valid_m8_wrs) > 1 else 0.0
sep_board["M8  MA20 Distance"] = m8_sep
print(f"  Win rate range: {max(valid_m8_wrs):.2f}% - {min(valid_m8_wrs):.2f}% = {m8_sep*100:.2f}pp", flush=True)


# ── STEP 7: LEADERBOARD ──────────────────────────────────────────────────────────
print(f"\n{'='*70}", flush=True)
print("  LEADERBOARD — Separation Strength", flush=True)
print(f"{'='*70}", flush=True)
print(
    "  Score: Cohen's d for Group A | proportion gap for Group B | "
    "win-rate-range/100 for C/D",
    flush=True
)
print(
    "  Verdict thresholds: HIGH >= 0.10 | LOW >= 0.03 | EXCLUDE < 0.03",
    flush=True
)
print(f"\n  {'Rank':<5} {'Metric':<35} {'Score':>8}  Verdict", flush=True)
print(f"  {'─'*65}", flush=True)

sorted_board = sorted(sep_board.items(), key=lambda x: x[1], reverse=True)

for rank, (name, score) in enumerate(sorted_board, 1):
    if score >= 0.10:
        verdict = "HIGH    — strong BQS weight candidate"
    elif score >= 0.03:
        verdict = "LOW     — weak signal"
    else:
        verdict = "EXCLUDE — no meaningful separation"
    print(f"  {rank:<5} {name:<35} {score:>8.4f}  {verdict}", flush=True)

print(f"\n{'='*70}", flush=True)
print(f"  Total run time: {time.time()-t0:.1f}s", flush=True)
print(f"{'='*70}", flush=True)
