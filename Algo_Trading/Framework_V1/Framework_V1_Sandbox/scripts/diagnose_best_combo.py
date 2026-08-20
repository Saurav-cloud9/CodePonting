"""
Diagnostic run for best Optuna combo (FF excluded run):
  SL=D, trailing_dist=0.5
  use_compounding=True, use_entry_cutoff=True (14:45)
  use_position_guard=False, use_auction_filter=False, FF=False

Prints qty distribution, max drawdown, top 10 wins to verify
sizing is realistic with standard capital_and_risk mode.
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from core.indicators import add_intraday_indicators, add_atr

INITIAL_CAPITAL = 1_000_000
YEARS           = 4
NUM_STOCKS      = 30
EXCLUDE         = {"NIFTY50", "VI"}
ATR_MULT_STOP   = 2.5
RR_TARGET       = 4.5 / 2.5
RISK_PER_TRADE  = 0.01
VOL_MULT        = 1.2
LOOKAHEAD       = 3
TRAILING_DIST   = 0.5
USE_COMPOUNDING = True    # Change 5: use current cash equity for sizing
_EOD_INT        = 1500
_CUTOFF         = 1445    # Change 9: entry cutoff 14:45 (was 14:30)

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
    arrs    = stock_arrays[stock]
    n       = arrs["n"]
    ma20    = df["ma20"].to_numpy()
    avg_vol = df["avg_volume"].to_numpy()
    vol     = df["volume"].to_numpy()
    low     = arrs["low"]
    close   = arrs["close"]
    open_   = arrs["open"]
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
                    if time_int[nxt] >= _CUTOFF:
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
# SL=D (trailing), trailing_dist=0.5, fixed_fractional=True
# All other flags OFF
print("Running best combo: SL=D, trailing_dist=0.5, compounding=True, cutoff=14:45...", flush=True)
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

    for i in range(n):
        op  = open_arr[i]; hi = high_arr[i]; lo = low_arr[i]
        cl  = close_arr[i]; atr = atr_arr[i]
        d   = date_arr[i];  t   = time_arr[i]

        # Open position
        if i in sm:
            entry = sm[i]["entry_price"]
            sd    = atr * ATR_MULT_STOP
            if sd <= 0:
                sd = entry * 0.01
            # Capital-and-risk sizing (compounding: use current cash)
            eq           = cash if USE_COMPOUNDING else INITIAL_CAPITAL
            risk_amt     = eq * RISK_PER_TRADE
            per_stk_cap  = eq / NUM_STOCKS
            qty = max(min(int(per_stk_cap / entry), int(risk_amt / sd)), 1)
            # pos layout: [entry_idx, entry_date, entry_price, qty, stop, target, atr, trailing_stop]
            positions.append([i, d, entry, qty, entry - sd, entry + sd * RR_TARGET, atr, None])

        if not positions:
            continue

        is_bull = cl > op
        kept    = []
        for pos in positions:
            if pos[0] == i:          # skip entry candle
                kept.append(pos)
                continue

            # EOD exit
            if d == pos[1] and t >= _EOD_INT:
                pnl = (op - pos[2]) * pos[3]
                cash += pnl
                all_trades.append({
                    "stock": stock, "entry": pos[2], "exit": op,
                    "qty": pos[3], "pnl": pnl, "reason": "time", "atr_entry": pos[6],
                })
                continue

            # Trailing SL update
            new_trail = hi - TRAILING_DIST * pos[6]
            if pos[7] is None or new_trail > pos[7]:
                pos[7] = new_trail
            pos[4] = pos[7]

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
                    "qty": pos[3], "pnl": pnl, "reason": reason, "atr_entry": pos[6],
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

# Max drawdown (trade-by-trade)
eq_curve  = (INITIAL_CAPITAL + trades_df["pnl"].cumsum()).to_numpy()
roll_max  = np.maximum.accumulate(eq_curve)
drawdowns = (eq_curve - roll_max) / roll_max * 100
max_dd    = drawdowns.min()

# Risk per trade (actual stop_dist * qty)
trades_df["risk_amt"] = trades_df["atr_entry"] * ATR_MULT_STOP * trades_df["qty"]

print()
print("=" * 65)
print("BEST COMBO DEEP DIVE: SL=D, TR=0.5, compounding=True, cutoff=14:45")
print("=" * 65)
print(f"  Total trades        : {n_trades:,}")
print(f"  Total PnL           : {total_pnl:>14,.0f}")
print(f"  CAGR                : {cagr:.2f}%")
print()
print(f"  Avg qty / trade     : {trades_df['qty'].mean():.1f}")
print(f"  Max qty (any trade) : {trades_df['qty'].max():,}")
print(f"  Median PnL / trade  : {trades_df['pnl'].median():.2f}")
print(f"  Max drawdown        : {max_dd:.2f}%")
print()

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

print("  RISK AMOUNT PER TRADE (stop_dist * qty)  [expected ~10,000]:")
print(f"    Min         : {trades_df['risk_amt'].min():>10,.0f}")
print(f"    25th pct    : {trades_df['risk_amt'].quantile(0.25):>10,.0f}")
print(f"    Median      : {trades_df['risk_amt'].median():>10,.0f}")
print(f"    75th pct    : {trades_df['risk_amt'].quantile(0.75):>10,.0f}")
print(f"    Max         : {trades_df['risk_amt'].max():>10,.0f}")
print(f"    Mean        : {trades_df['risk_amt'].mean():>10,.0f}")
print(f"    Expected    : {INITIAL_CAPITAL * RISK_PER_TRADE:>10,.0f}  (1% of capital)")
print()

print("  TOP 10 BIGGEST WINNING TRADES:")
top10 = trades_df.nlargest(10, "pnl")[["stock", "entry", "exit", "qty", "pnl", "atr_entry", "reason", "risk_amt"]]
print(f"  {'Stock':<12} {'Entry':>8} {'Exit':>8} {'Qty':>8} {'PnL':>12} {'ATR':>7} {'Risk':>10}  Reason")
for _, r in top10.iterrows():
    print(f"  {r['stock']:<12} {r['entry']:>8.2f} {r['exit']:>8.2f} {int(r['qty']):>8,}"
          f" {r['pnl']:>12,.0f} {r['atr_entry']:>7.3f} {r['risk_amt']:>10,.0f}  {r['reason']}")

print()
print("  WIN / STOP / TIME BREAKDOWN:")
rc = trades_df["reason"].value_counts()
for reason, cnt in rc.items():
    pct = cnt / n_trades * 100
    avg_pnl = trades_df.loc[trades_df["reason"] == reason, "pnl"].mean()
    print(f"    {reason:<8}: {cnt:>6,}  ({pct:.1f}%)  avg PnL = {avg_pnl:>8.2f}")
