"""
Diagnostic run for ACT15 best combo:
  SL=D, activation_threshold=3.0, trailing_dist=0.5
  use_compounding=True, use_entry_cutoff=True (14:45)
  use_auction_filter=True (09:45), use_position_guard=False
  use_fixed_fractional=False

Key question: what % of trades actually triggered the trailing stop?
If < 5%, the +0.6pp improvement over SL=A is driven by a handful of trades.
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from core.indicators import add_intraday_indicators, add_atr

INITIAL_CAPITAL    = 1_000_000
YEARS              = 4
NUM_STOCKS         = 30
EXCLUDE            = {"NIFTY50", "VI"}
ATR_MULT_STOP      = 2.5
RR_TARGET          = 4.5 / 2.5   # 1.8
RISK_PER_TRADE     = 0.01
VOL_MULT           = 1.2
LOOKAHEAD          = 3
TRAILING_DIST      = 0.5
ACTIVATION_THRESH  = 3.0          # trail only after +3.0×ATR profit
USE_COMPOUNDING    = True
_EOD_INT           = 1500
_CUTOFF            = 1445         # entry cutoff 14:45
_AUCTION_INT       = 945          # skip before 09:45

FV1_DIR  = Path(__file__).resolve().parent.parent.parent
DS3_DIR  = FV1_DIR / "data/historical/intraday_5min_DS3"

# ─── LOAD DATA ─────────────────────────────────────────────────────────────────
stock_files = sorted(f for f in DS3_DIR.glob("*.parquet") if f.stem not in EXCLUDE)
print(f"Loading {len(stock_files)} stocks...", flush=True)

stock_arrays = {}
stock_dfs    = {}
for sp in stock_files:
    df = pd.read_parquet(sp)
    df["datetime"] = pd.to_datetime(df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S"))
    df = df.sort_values("datetime").reset_index(drop=True)
    _t = df["datetime"].dt.time
    df = df[_t.between(pd.Timestamp("09:15").time(), pd.Timestamp("15:30").time())]
    df = df.reset_index(drop=True)
    df = add_intraday_indicators(df)
    df = add_atr(df)
    stock_dfs[sp.stem] = df
    dti = pd.DatetimeIndex(df["datetime"])
    stock_arrays[sp.stem] = {
        "datetime": df["datetime"].to_numpy(),
        "open":     df["open"].to_numpy(dtype=float),
        "high":     df["high"].to_numpy(dtype=float),
        "low":      df["low"].to_numpy(dtype=float),
        "close":    df["close"].to_numpy(dtype=float),
        "atr":      df["atr_14"].to_numpy(dtype=float),
        "date_int": (dti.year * 10000 + dti.month * 100 + dti.day).to_numpy(),
        "time_int": (dti.hour * 100 + dti.minute).to_numpy(),
        "n":        len(df),
    }

# ─── GENERATE SIGNALS ──────────────────────────────────────────────────────────
print("Generating signals...", flush=True)
signal_maps = {}
for stock, df in stock_dfs.items():
    arrs     = stock_arrays[stock]
    n        = arrs["n"]
    ma20     = df["ma20"].to_numpy()
    avg_vol  = df["avg_volume"].to_numpy()
    vol      = df["volume"].to_numpy()
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
            mt = ma20[i]
            for j in range(i, min(i + LOOKAHEAD + 1, n)):
                if close[j] > mt:
                    nxt = j + 1
                    if nxt >= n:
                        break
                    t_nxt = time_int[nxt]
                    if t_nxt >= _CUTOFF:
                        break
                    if t_nxt < _AUCTION_INT:
                        break
                    raw.append((nxt, open_[nxt], mt))
                    break
    seen = set()
    sm   = {}
    for nxt, ep, mt in raw:
        if nxt not in seen:
            seen.add(nxt)
            sm[nxt] = {"entry_price": ep, "ma20": mt}
    signal_maps[stock] = sm

# ─── RUN BEST COMBO ─────────────────────────────────────────────────────────────
print("Running ACT15 best combo: SL=D, ACT=3.0, TR=0.5, compounding, cutoff=14:45, auction filter...", flush=True)
all_trades = []

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
    # pos: [entry_idx, entry_date, entry_price, qty, stop, target, atr, trailing_stop]

    for i in range(n):
        op  = open_arr[i]; hi = high_arr[i]
        lo  = low_arr[i];  cl = close_arr[i]
        atr = atr_arr[i];  d  = date_arr[i]; t = time_arr[i]

        if i in sm:
            sig   = sm[i]
            entry = sig["entry_price"]
            sd    = atr * ATR_MULT_STOP
            if sd <= 0:
                sd = entry * 0.01
            eq          = cash if USE_COMPOUNDING else INITIAL_CAPITAL
            risk_amt    = eq * RISK_PER_TRADE
            per_stk_cap = eq / NUM_STOCKS
            qty = max(min(int(per_stk_cap / entry), int(risk_amt / sd)), 1)
            positions.append([i, d, entry, qty, entry - sd, entry + sd * RR_TARGET, atr, None])

        if not positions:
            continue

        is_bull = cl > op
        kept    = []
        for pos in positions:
            if pos[0] == i:
                kept.append(pos)
                continue

            # EOD exit
            if d == pos[1] and t >= _EOD_INT:
                pnl = (op - pos[2]) * pos[3]
                cash += pnl
                all_trades.append({
                    "stock": stock, "entry": pos[2], "exit": op,
                    "qty": pos[3], "pnl": pnl, "reason": "time",
                    "atr_entry": pos[6], "trail_activated": pos[7] is not None,
                })
                continue

            # Variant D with activation threshold
            activation_price = pos[2] + ACTIVATION_THRESH * pos[6]
            if hi >= activation_price:
                new_trail = hi - TRAILING_DIST * pos[6]
                if pos[7] is None or new_trail > pos[7]:
                    pos[7] = new_trail
                pos[4] = pos[7]
            # Before activation: pos[4] stays at original stop

            stop   = pos[4]
            target = pos[5]

            exit_p = None
            if is_bull:
                if lo <= stop:      exit_p = stop
                elif hi >= target:  exit_p = target
            else:
                if hi >= target:    exit_p = target
                elif lo <= stop:    exit_p = stop

            if exit_p is not None:
                pnl    = (exit_p - pos[2]) * pos[3]
                cash  += pnl
                reason = "target" if exit_p >= target else "stop"
                all_trades.append({
                    "stock": stock, "entry": pos[2], "exit": exit_p,
                    "qty": pos[3], "pnl": pnl, "reason": reason,
                    "atr_entry": pos[6], "trail_activated": pos[7] is not None,
                })
            else:
                kept.append(pos)

        positions = kept

# ─── DIAGNOSTICS ───────────────────────────────────────────────────────────────
trades_df = pd.DataFrame(all_trades)
n_trades  = len(trades_df)
total_pnl = trades_df["pnl"].sum()
final_eq  = INITIAL_CAPITAL + total_pnl
cagr      = ((final_eq / INITIAL_CAPITAL) ** (1 / YEARS) - 1) * 100

eq_curve  = (INITIAL_CAPITAL + trades_df["pnl"].cumsum()).to_numpy()
roll_max  = np.maximum.accumulate(eq_curve)
drawdowns = (eq_curve - roll_max) / roll_max * 100
max_dd    = drawdowns.min()

trades_df["risk_amt"] = trades_df["atr_entry"] * ATR_MULT_STOP * trades_df["qty"]

n_trail_activated = trades_df["trail_activated"].sum()
pct_activated     = n_trail_activated / n_trades * 100

print()
print("=" * 65)
print("ACT15 BEST COMBO DEEP DIVE: SL=D, ACT=3.0, TR=0.5")
print("  compounding=True, cutoff=14:45, auction_filter=True")
print("=" * 65)
print(f"  Total trades        : {n_trades:,}")
print(f"  Total PnL           : {total_pnl:>14,.0f}")
print(f"  CAGR                : {cagr:.2f}%")
print(f"  Max drawdown        : {max_dd:.2f}%")
print()
print(f"  Avg qty / trade     : {trades_df['qty'].mean():.1f}")
print(f"  Max qty (any trade) : {trades_df['qty'].max():,}")
print(f"  Median PnL / trade  : {trades_df['pnl'].median():.2f}")
print()

# ─── KEY DIAGNOSTIC: TRAIL ACTIVATION RATE ────────────────────────────────────
print("  TRAIL ACTIVATION RATE:")
print(f"    Trail activated     : {n_trail_activated:,}  ({pct_activated:.1f}% of all trades)")
print(f"    Trail NOT activated : {n_trades - n_trail_activated:,}  ({100 - pct_activated:.1f}% of all trades)")
print()

# PnL split by trail activation
trail_on  = trades_df[trades_df["trail_activated"]]
trail_off = trades_df[~trades_df["trail_activated"]]
print(f"    PnL — trail activated    : {trail_on['pnl'].sum():>12,.0f}  "
      f"(avg {trail_on['pnl'].mean():>8.2f} / trade)")
print(f"    PnL — trail NOT activated: {trail_off['pnl'].sum():>12,.0f}  "
      f"(avg {trail_off['pnl'].mean():>8.2f} / trade)")
print()

# ─── QTY DISTRIBUTION ─────────────────────────────────────────────────────────
q = trades_df["qty"]
print("  QTY DISTRIBUTION (shares):")
print(f"    Min         : {q.min()}")
print(f"    25th pct    : {q.quantile(0.25):.0f}")
print(f"    Median      : {q.median():.0f}")
print(f"    75th pct    : {q.quantile(0.75):.0f}")
print(f"    Max         : {q.max():,}")
print(f"    Mean        : {q.mean():.1f}")
if q.mean() > 500:
    print("    *** FLAG: mean qty > 500 — UNREALISTIC SIZING ***")
else:
    print("    OK: mean qty within realistic range (<= 500)")
print()

# ─── RISK AMOUNT ──────────────────────────────────────────────────────────────
print("  RISK AMOUNT PER TRADE (stop_dist x qty)  [expected ~10,000]:")
print(f"    Min         : {trades_df['risk_amt'].min():>10,.0f}")
print(f"    25th pct    : {trades_df['risk_amt'].quantile(0.25):>10,.0f}")
print(f"    Median      : {trades_df['risk_amt'].median():>10,.0f}")
print(f"    75th pct    : {trades_df['risk_amt'].quantile(0.75):>10,.0f}")
print(f"    Max         : {trades_df['risk_amt'].max():>10,.0f}")
print(f"    Mean        : {trades_df['risk_amt'].mean():>10,.0f}")
print(f"    Expected    : {INITIAL_CAPITAL * RISK_PER_TRADE:>10,.0f}  (1% of capital)")
print()

# ─── TOP 10 WINS ──────────────────────────────────────────────────────────────
print("  TOP 10 BIGGEST WINNING TRADES:")
top10 = trades_df.nlargest(10, "pnl")[
    ["stock", "entry", "exit", "qty", "pnl", "atr_entry", "reason", "risk_amt", "trail_activated"]
]
print(f"  {'Stock':<12} {'Entry':>8} {'Exit':>8} {'Qty':>8} {'PnL':>12} "
      f"{'ATR':>7} {'Risk':>10}  Reason   Trail")
for _, r in top10.iterrows():
    trail_flag = "YES" if r["trail_activated"] else "no"
    print(f"  {r['stock']:<12} {r['entry']:>8.2f} {r['exit']:>8.2f} {int(r['qty']):>8,}"
          f" {r['pnl']:>12,.0f} {r['atr_entry']:>7.3f} {r['risk_amt']:>10,.0f}"
          f"  {r['reason']:<8} {trail_flag}")

# ─── WIN / STOP / TIME BREAKDOWN ──────────────────────────────────────────────
print()
print("  EXIT REASON BREAKDOWN:")
rc = trades_df["reason"].value_counts()
for reason, cnt in rc.items():
    pct     = cnt / n_trades * 100
    avg_pnl = trades_df.loc[trades_df["reason"] == reason, "pnl"].mean()
    print(f"    {reason:<8}: {cnt:>6,}  ({pct:.1f}%)  avg PnL = {avg_pnl:>8.2f}")

print()
print("  EXIT REASON — TRAIL ACTIVATED ONLY:")
if len(trail_on) > 0:
    rc_trail = trail_on["reason"].value_counts()
    for reason, cnt in rc_trail.items():
        pct     = cnt / len(trail_on) * 100
        avg_pnl = trail_on.loc[trail_on["reason"] == reason, "pnl"].mean()
        print(f"    {reason:<8}: {cnt:>6,}  ({pct:.1f}%)  avg PnL = {avg_pnl:>8.2f}")
else:
    print("    (no trades with trail activated)")
