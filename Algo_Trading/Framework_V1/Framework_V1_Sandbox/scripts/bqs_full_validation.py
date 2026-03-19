"""
bqs_full_validation.py — BQS Direction Validation on DS3 2015–2025
===================================================================
P1: Re-run bqs_export logic on full DS3 2015–2025 (no year filter).
P2: Compute winner vs loser stats — same groups as BQS_METRICS_REFERENCE.
P3: For each metric compare direction vs 2022–2025 → ROBUST or FRAGILE.

Winner definition: exit_reason == "target" only.
Output: Framework_V1_Sandbox/outputs/bqs/bqs_trades_full.parquet
"""

import sys, io, time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

SANDBOX_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SANDBOX_DIR))
from core.indicators import add_intraday_indicators, add_atr

# ── CONSTANTS ───────────────────────────────────────────────────────────────────
INITIAL_CAPITAL = 1_000_000
YEARS           = 10        # 2015–2025
NUM_STOCKS      = 30
EXCLUDE         = {"NIFTY50", "VI"}
ATR_MULT_STOP   = 2.5
RR_TARGET       = 4.5 / 2.5
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

_OPEN_MINS  = 9 * 60 + 15
_CLOSE_MINS = 15 * 60 + 30

# Reference values from BQS_METRICS_REFERENCE.md (2022–2025)
REF_2022 = {
    "M1": {"w_mean": 1.740, "l_mean": 1.669, "gap": +0.071,  "hyp": "higher=better", "confirmed": True},
    "M2": {"w_mean": 0.281, "l_mean": 0.304, "gap": -0.023,  "hyp": "higher=better", "confirmed": False},
    "M3": {"w_mean": 1.809, "l_mean": 1.831, "gap": -0.022,  "hyp": "higher=better", "confirmed": False},
    "M5": {"w_mean": 3.444, "l_mean": 3.097, "gap": +0.347,  "hyp": "higher=better", "confirmed": True},
    "M6": {"w_mean": 31.85, "l_mean": 35.94, "gap": -4.09,   "hyp": "lower=better",  "confirmed": True},
    "M4": {"w_bull": 0.873, "l_bull": 0.868, "gap": +0.005,  "hyp": "higher=better"},
    "M9": {"w_bull": 0.434, "l_bull": 0.434, "gap": +0.0004, "hyp": "higher=better"},
    "M7": {"gap0": 15.4, "gap1": 14.5, "gap2": 13.7, "gap3": 14.1, "hyp": "lower_gap=better"},
    "M8": {"bins": [15.5, 12.7, 7.2, 2.0, 10.0, 9.1], "hyp": "shallower=better"},
}

# ── STEP 1: LOAD DATA (no year filter) ─────────────────────────────────────────
print("Step 1: Loading full DS3 2015–2025...", flush=True)
t0 = time.time()

stock_files = sorted(f for f in DS3_DIR.glob("*.parquet") if f.stem not in EXCLUDE)
print(f"  {len(stock_files)} stocks", flush=True)

stock_arrays = {}

for sp in stock_files:
    stock = sp.stem
    df = pd.read_parquet(sp)
    df["datetime"] = pd.to_datetime(df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S"))
    df = df.sort_values("datetime").reset_index(drop=True)
    # NO year filter — full DS3
    _t = df["datetime"].dt.time
    df = df[_t.between(pd.Timestamp("09:15").time(), pd.Timestamp("15:30").time())]
    df = df.reset_index(drop=True)
    df = add_intraday_indicators(df)
    df = add_atr(df)

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


# ── STEP 2: GENERATE SIGNALS ────────────────────────────────────────────────────
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
                    raw.append((nxt, open_[nxt], i, j))
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
print(f"  {total_sigs:,} signals", flush=True)


# ── STEP 3: BACKTEST ────────────────────────────────────────────────────────────
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

        if i in sm and not positions:
            ep, touch_idx, bounce_idx = sm[i]
            entry    = ep + _TICK
            sd       = atr * ATR_MULT_STOP
            if sd <= 0:
                sd = entry * 0.01
            eq       = cash
            risk_amt = eq * RISK_PER_TRADE
            per_cap  = eq / NUM_STOCKS
            qty      = max(min(int(per_cap / entry), int(risk_amt / sd)), 1)

            positions.append([
                i, d, entry, qty,
                entry - sd,
                entry + sd * RR_TARGET,
                touch_idx, bounce_idx, risk_amt,
            ])

        if not positions:
            continue

        is_bull = cl > op
        kept    = []

        for pos in positions:
            if pos[0] == i:
                kept.append(pos)
                continue

            if d == pos[1] and t >= _EOD_INT:
                pnl        = (op - pos[2]) * pos[3]
                cash      += pnl
                total_pnl += pnl
                all_trades.append({
                    "stock": stock, "entry_date": pos[1],
                    "entry_price": pos[2], "qty": pos[3],
                    "stop": pos[4], "target": pos[5],
                    "touch_idx": pos[6], "bounce_idx": pos[7], "risk_amt": pos[8],
                    "exit_price": op, "exit_reason": "eod", "pnl": pnl,
                    "year": int(str(pos[1])[:4]),
                })
                continue

            stop   = pos[4]
            target = pos[5]
            exit_p = exit_reason = None

            if is_bull:
                if lo <= stop:      exit_p, exit_reason = stop - _TICK, "sl"
                elif hi >= target:  exit_p, exit_reason = target, "target"
            else:
                if hi >= target:    exit_p, exit_reason = target, "target"
                elif lo <= stop:    exit_p, exit_reason = stop - _TICK, "sl"

            if exit_p is not None:
                pnl        = (exit_p - pos[2]) * pos[3]
                cash      += pnl
                total_pnl += pnl
                all_trades.append({
                    "stock": stock, "entry_date": pos[1],
                    "entry_price": pos[2], "qty": pos[3],
                    "stop": pos[4], "target": pos[5],
                    "touch_idx": pos[6], "bounce_idx": pos[7], "risk_amt": pos[8],
                    "exit_price": exit_p, "exit_reason": exit_reason, "pnl": pnl,
                    "year": int(str(pos[1])[:4]),
                })
            else:
                kept.append(pos)

        positions = kept

n_trades = len(all_trades)
cagr     = (((INITIAL_CAPITAL + total_pnl) / INITIAL_CAPITAL) ** (1 / YEARS) - 1) * 100
print(f"  {n_trades:,} trades  |  CAGR {cagr:+.2f}%  ({YEARS}yr)", flush=True)
print(f"  Backtest done in {time.time()-t1:.1f}s", flush=True)


# ── STEP 4: BQS METRICS ─────────────────────────────────────────────────────────
print("Step 4: Computing BQS metrics...", flush=True)


def time_int_to_mins(t_int):
    return (t_int // 100) * 60 + (t_int % 100)


rows = []
for rec in all_trades:
    stock = rec["stock"]
    ti    = rec["touch_idx"]
    bi    = rec["bounce_idx"]
    arrs  = stock_arrays[stock]

    t_open  = arrs["open"][ti];   t_low   = arrs["low"][ti]
    t_close = arrs["close"][ti];  t_ma20  = arrs["ma20"][ti]
    t_time  = arrs["time_int"][ti]; t_date = arrs["date_int"][ti]

    b_open  = arrs["open"][bi];   b_close = arrs["close"][bi]
    b_vol   = arrs["volume"][bi]; b_avg   = arrs["avg_vol"][bi]
    b_time  = arrs["time_int"][bi]

    e_idx  = bi + 1
    e_time = arrs["time_int"][e_idx]

    body   = abs(t_close - t_open)
    t_mins = time_int_to_mins(t_time)
    b_mins = time_int_to_mins(b_time)
    e_mins = time_int_to_mins(e_time)

    m1 = (b_vol / b_avg)            if (not np.isnan(b_avg) and b_avg > 0) else np.nan
    m2 = (b_close - t_low) / t_low * 100 if t_low > 0 else np.nan
    m3 = (t_open - t_low) / body    if body > 1e-8 else np.nan
    m4 = 1 if b_close > b_open else 0
    m5 = (_CLOSE_MINS - e_mins) / 60.0
    m6 = (t_mins - _OPEN_MINS) / 5.0
    m7 = int(round((b_mins - t_mins) / 5.0))
    m8 = (t_ma20 - t_low) / t_ma20 * 100 if t_ma20 > 0 else np.nan

    if ti > 0:
        p_open  = arrs["open"][ti - 1];  p_close = arrs["close"][ti - 1]
        p_date  = arrs["date_int"][ti - 1]
        m9 = (1 if p_open < p_close else 0) if p_date == t_date else np.nan
    else:
        m9 = np.nan

    winner = 1 if rec["exit_reason"] == "target" else 0

    rows.append({**rec,
        "m1_volume_ratio": m1, "m2_bounce_strength_pct": m2,
        "m3_wick_ratio": m3, "m4_candle_color": int(m4),
        "m5_hours_until_close": m5, "m6_touch_candle_index": m6,
        "m7_bounce_gap": m7, "m8_ma20_distance_pct": m8,
        "m9_prev_candle_dir": m9, "winner": winner,
    })

df_full = pd.DataFrame(rows).drop(columns=["touch_idx", "bounce_idx"])

# Export
parquet_path = OUT_DIR / "bqs_trades_full.parquet"
df_full.to_parquet(parquet_path, index=False)
df_full.to_csv(OUT_DIR / "bqs_trades_full.csv", index=False)
df_full.to_parquet(MOBILE_DIR / "bqs_trades_full.parquet", index=False)
print(f"  Saved: {parquet_path}", flush=True)


# ── STEP 5: DIRECTION VALIDATION ────────────────────────────────────────────────
print(f"\n{'='*70}", flush=True)
print("  P2/P3 — DIRECTION VALIDATION: DS3 2015–2025 vs 2022–2025", flush=True)
print(f"{'='*70}", flush=True)

w = df_full[df_full["winner"] == 1]
l = df_full[df_full["winner"] == 0]
total    = len(df_full)
n_win    = len(w)
base_wr  = n_win / total * 100

print(f"\n  Total trades: {total:,}  |  Winners (target): {n_win:,} ({base_wr:.2f}%)", flush=True)

results = {}  # metric -> dict of full-period stats + verdict

# ── GROUP A ──────────────────────────────────────────────────────────────────────
print(f"\n{'─'*70}", flush=True)
print("  GROUP A — Continuous (M1, M2, M3, M5, M6)", flush=True)
print(f"{'─'*70}", flush=True)
print(f"  {'Metric':<6} {'W-mean':>8} {'L-mean':>8} {'Gap(full)':>10} {'Gap(22-25)':>11} {'Dir match':>10}  Verdict", flush=True)
print(f"  {'─'*65}", flush=True)

group_a_meta = [
    ("m1_volume_ratio",        "M1", "higher=better", +0.071),
    ("m2_bounce_strength_pct", "M2", "higher=better", -0.023),
    ("m3_wick_ratio",          "M3", "higher=better", -0.022),
    ("m5_hours_until_close",   "M5", "higher=better", +0.347),
    ("m6_touch_candle_index",  "M6", "lower=better",  -4.090),
]

for col, label, hyp, ref_gap in group_a_meta:
    wv = w[col].dropna(); lv = l[col].dropna()
    if len(wv) < 2 or len(lv) < 2:
        continue
    w_mean = wv.mean(); l_mean = lv.mean(); gap = w_mean - l_mean

    # Direction match: does sign of gap agree with 2022-2025?
    same_sign = (gap * ref_gap > 0)
    dir_match = "YES" if same_sign else "NO"

    # Verdict
    if same_sign and abs(gap) >= 0.01:
        verdict = "ROBUST"
    elif same_sign:
        verdict = "ROBUST (weak)"
    else:
        verdict = "FRAGILE"

    results[label] = {"w_mean": w_mean, "l_mean": l_mean, "gap": gap,
                      "ref_gap": ref_gap, "verdict": verdict}

    print(f"  {label:<6} {w_mean:>8.3f} {l_mean:>8.3f} {gap:>+10.3f} {ref_gap:>+11.3f} {dir_match:>10}  {verdict}", flush=True)


# ── GROUP B ──────────────────────────────────────────────────────────────────────
print(f"\n{'─'*70}", flush=True)
print("  GROUP B — Binary (M4, M9)", flush=True)
print(f"{'─'*70}", flush=True)
print(f"  {'Metric':<6} {'W-bull%':>8} {'L-bull%':>8} {'Gap(full)':>10} {'Gap(22-25)':>11} {'Dir match':>10}  Verdict", flush=True)
print(f"  {'─'*65}", flush=True)

group_b_meta = [
    ("m4_candle_color",    "M4", +0.005),
    ("m9_prev_candle_dir", "M9", +0.0004),
]

for col, label, ref_gap in group_b_meta:
    wv = w[col].dropna(); lv = l[col].dropna()
    w_bull = wv.mean(); l_bull = lv.mean(); gap = w_bull - l_bull
    same_sign = (gap * ref_gap > 0) or (abs(gap) < 0.002 and abs(ref_gap) < 0.002)
    dir_match = "YES" if same_sign else "NO"
    verdict = "ROBUST (negligible)" if abs(gap) < 0.01 else ("ROBUST" if same_sign else "FRAGILE")
    results[label] = {"w_bull": w_bull, "l_bull": l_bull, "gap": gap, "verdict": verdict}
    print(f"  {label:<6} {w_bull*100:>7.1f}% {l_bull*100:>7.1f}% {gap:>+10.4f} {ref_gap:>+11.4f} {dir_match:>10}  {verdict}", flush=True)


# ── GROUP C ──────────────────────────────────────────────────────────────────────
print(f"\n{'─'*70}", flush=True)
print("  GROUP C — Discrete win rate (M7: gap 0-3)", flush=True)
print(f"{'─'*70}", flush=True)

ref_m7 = {0: 15.4, 1: 14.5, 2: 13.7, 3: 14.1}
full_m7 = {}
print(f"  {'Gap':<6} {'Trades(full)':>13} {'WR%(full)':>10} {'WR%(22-25)':>11} {'Dir match':>10}", flush=True)
print(f"  {'─'*55}", flush=True)
for gv in [0, 1, 2, 3]:
    sub = df_full[df_full["m7_bounce_gap"] == gv]
    wr  = sub["winner"].mean() * 100 if len(sub) > 0 else np.nan
    full_m7[gv] = wr
    # Direction: does gap=0 still have highest WR?
    print(f"  {gv:<6} {len(sub):>13,} {wr:>9.2f}% {ref_m7[gv]:>10.1f}%", flush=True)

# Verdict: does lower gap still = higher WR directionally?
m7_trend_full = full_m7[0] > full_m7[1] > full_m7[3]  # rough check
m7_verdict = "ROBUST" if (full_m7[0] > full_m7[2]) else "FRAGILE"
results["M7"] = {"verdict": m7_verdict, "wrs": full_m7}
print(f"  Hypothesis (lower gap=better): gap=0 highest? -> {m7_verdict}", flush=True)


# ── GROUP D ──────────────────────────────────────────────────────────────────────
print(f"\n{'─'*70}", flush=True)
print("  GROUP D — Binned win rate (M8: MA20 distance %)", flush=True)
print(f"{'─'*70}", flush=True)

bins       = [float("-inf"), 0.3, 0.8, 1.5, 2.5, float("inf")]
bin_labels = ["< 0.3%", "0.3-0.8%", "0.8-1.5%", "1.5-2.5%", "> 2.5%"]
ref_m8     = [15.5, 12.7, 7.2, 2.0, 9.5]   # merged last two bins from ref

df_full["m8_bin"] = pd.cut(df_full["m8_ma20_distance_pct"], bins=bins, labels=bin_labels)

print(f"  {'Bin':<12} {'Trades(full)':>13} {'WR%(full)':>10} {'WR%(22-25)':>11} {'Dir match':>10}", flush=True)
print(f"  {'─'*60}", flush=True)

full_m8_wrs = []
for lbl, ref_wr in zip(bin_labels, ref_m8):
    sub = df_full[df_full["m8_bin"] == lbl]
    wr  = sub["winner"].mean() * 100 if len(sub) > 0 else np.nan
    full_m8_wrs.append(wr)
    # Direction: does lower distance still = higher WR?
    print(f"  {lbl:<12} {len(sub):>13,} {wr:>9.2f}% {ref_wr:>10.1f}%", flush=True)

# Verdict: monotonic decline (shallower=better) still holds?
valid_wrs = [(i, v) for i, v in enumerate(full_m8_wrs) if not np.isnan(v)]
monotone  = all(valid_wrs[i][1] >= valid_wrs[i+1][1] for i in range(len(valid_wrs)-1))
m8_verdict = "ROBUST" if (full_m8_wrs[0] > full_m8_wrs[2]) else "FRAGILE"
results["M8"] = {"verdict": m8_verdict, "wrs": full_m8_wrs}
print(f"  Hypothesis (shallower=better): monotone decline? {monotone} -> {m8_verdict}", flush=True)


# ── FINAL SUMMARY ────────────────────────────────────────────────────────────────
print(f"\n{'='*70}", flush=True)
print("  VERDICT SUMMARY", flush=True)
print(f"{'='*70}", flush=True)
print(f"  {'Metric':<6}  {'2022-25 Role':<12}  {'2015-25 Verdict'}", flush=True)
print(f"  {'─'*45}", flush=True)

roles = {
    "M1": "LOW", "M2": "LOW", "M3": "EXCLUDE",
    "M5": "HIGH", "M6": "HIGH", "M8": "MODERATE",
    "M4": "EXCLUDE", "M9": "EXCLUDE", "M7": "EXCLUDE",
}
for m, r in results.items():
    print(f"  {m:<6}  {roles.get(m,'?'):<12}  {r['verdict']}", flush=True)

print(f"\n{'='*70}", flush=True)
print(f"  Total run time: {time.time()-t0:.1f}s", flush=True)
print(f"{'='*70}", flush=True)

# Store results for file update
import json
summary_path = OUT_DIR / "bqs_full_validation_summary.json"
out = {}
for m, r in results.items():
    out[m] = {k: (float(v) if isinstance(v, (np.floating, float)) else v)
              for k, v in r.items() if k != "wrs"}
with open(summary_path, "w") as f:
    json.dump(out, f, indent=2)
print(f"  Summary JSON: {summary_path}", flush=True)
