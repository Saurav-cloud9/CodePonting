"""
run_winner.py -- Step 3.2 Winner Confirmation
=============================================
Runs the Optuna Step 3.2 winner combo and confirms CAGR.

Winner: SL=A [PG|CP|--|AF|--]
  sl_variant=A, position_guard=True, compounding=True,
  auction_filter=True, entry_cutoff=False, fixed_fractional=False

Expected: CAGR ~ -8.62%, 28,085 trades  (DS3, 2022-2025, +0.05 tick slippage)
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

# -- CONSTANTS -----------------------------------------------------------------
INITIAL_CAPITAL = 1_000_000
YEARS           = 4
NUM_STOCKS      = 30
EXCLUDE         = {"NIFTY50", "VI"}
ATR_MULT_STOP   = 2.5
RR_TARGET       = 4.5 / 2.5   # Extreme-2
RISK_PER_TRADE  = 0.01
VOL_MULT        = 1.2
LOOKAHEAD       = 3
_EOD_INT        = 1500         # 15:00
_CUTOFF_DEFAULT = 1430         # 14:30 (entry_cutoff=False)
_AUCTION_INT    = 945          # 09:45 (auction_filter=True)
_TICK           = 0.05         # entry slippage + SL exit slippage

FV1_DIR  = SANDBOX_DIR.parent
DS3_DIR  = FV1_DIR / "data/historical/intraday_5min_DS3"

# -- STEP 1: LOAD DATA ---------------------------------------------------------
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
        "atr":      df["atr_14"].to_numpy(dtype=float),
        "date_int": date_int,
        "time_int": time_int,
        "n":        len(df),
    }

print(f"  Done in {time.time()-t0:.1f}s", flush=True)

# -- STEP 2: GENERATE SIGNAL MAP -----------------------------------------------
# Winner: auction_filter=True, entry_cutoff=False (14:30 cutoff)
print("Step 2: Generating signal map (AF=True, EC=False)...", flush=True)


def gen_signals(stock):
    df       = stock_dfs[stock]
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
            ma_touch = ma20[i]
            for j in range(i, min(i + LOOKAHEAD + 1, n)):
                if close[j] > ma_touch:
                    nxt   = j + 1
                    if nxt >= n:
                        break
                    t_nxt = time_int[nxt]
                    if t_nxt >= _CUTOFF_DEFAULT:   # EC=False: use 14:30
                        break
                    if t_nxt < _AUCTION_INT:        # AF=True: skip before 09:45
                        break
                    raw.append((nxt, open_[nxt]))
                    break

    seen = set()
    sm   = {}
    for nxt, ep in raw:
        if nxt not in seen:
            seen.add(nxt)
            sm[nxt] = ep
    return sm


signal_maps = {stock: gen_signals(stock) for stock in stock_arrays}
total_sigs  = sum(len(v) for v in signal_maps.values())
print(f"  {total_sigs:,} signals across {len(signal_maps)} stocks", flush=True)

# -- STEP 3: RUN WINNER BACKTEST -----------------------------------------------
# SL=A, PG=True, CP=True, FF=False
print("Step 3: Running winner params...", flush=True)
t1 = time.time()

all_trades = []   # list of (year, pnl)
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
    positions = []   # [entry_idx, entry_date, entry_price, qty, stop, target]

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
            entry = sm[i] + _TICK    # +1 tick entry slippage
            sd    = atr * ATR_MULT_STOP
            if sd <= 0:
                sd = entry * 0.01

            eq          = cash   # CP=True: use current equity
            risk_amt    = eq * RISK_PER_TRADE
            per_stk_cap = eq / NUM_STOCKS

            qty = max(min(int(per_stk_cap / entry), int(risk_amt / sd)), 1)

            positions.append([
                i,                        # 0 entry_idx
                d,                        # 1 entry_date
                entry,                    # 2 entry_price
                qty,                      # 3 qty
                entry - sd,               # 4 stop  (SL=A: fixed)
                entry + sd * RR_TARGET,   # 5 target
            ])

        if not positions:
            continue

        is_bull = cl > op
        kept    = []

        for pos in positions:
            if pos[0] == i:              # skip entry candle
                kept.append(pos)
                continue

            # EOD forced close
            if d == pos[1] and t >= _EOD_INT:
                pnl = (op - pos[2]) * pos[3]
                cash      += pnl
                total_pnl += pnl
                all_trades.append((int(str(pos[1])[:4]), pnl))
                continue

            # Candle-direction exit priority (SL=A: fixed stop/target)
            stop   = pos[4]
            target = pos[5]
            exit_p = None

            if is_bull:
                if lo <= stop:      exit_p = stop - _TICK   # SL slip
                elif hi >= target:  exit_p = target
            else:
                if hi >= target:    exit_p = target
                elif lo <= stop:    exit_p = stop - _TICK   # SL slip

            if exit_p is not None:
                pnl = (exit_p - pos[2]) * pos[3]
                cash      += pnl
                total_pnl += pnl
                all_trades.append((int(str(pos[1])[:4]), pnl))
            else:
                kept.append(pos)

        positions = kept

elapsed = time.time() - t1

# -- RESULTS -------------------------------------------------------------------
final_equity = INITIAL_CAPITAL + total_pnl
cagr         = ((final_equity / INITIAL_CAPITAL) ** (1 / YEARS) - 1) * 100

pnl_arr  = np.array([p for _, p in all_trades])
n_trades = len(pnl_arr)
n_wins   = int((pnl_arr > 0).sum())
win_pct  = n_wins / n_trades * 100 if n_trades else 0

print(f"\n{'='*60}")
print(f"  STEP 3.2 WINNER CONFIRMATION")
print(f"{'='*60}")
print(f"  Config    : Extreme-2  (sl=2.5 ATR, tp=1.8R)")
print(f"  Features  : SL=A  PG=True  CP=True  AF=True  EC=False  FF=False")
print(f"  Stocks    : {len(stock_arrays)}")
print(f"  Period    : 2022-2025  ({YEARS} yr)")
print()
print(f"  Total Trades   : {n_trades:,}")
print(f"  Win Rate       : {win_pct:.1f}%")
print(f"  Initial Equity : Rs {INITIAL_CAPITAL:,}")
print(f"  Final Equity   : Rs {final_equity:,.2f}")
print(f"  4yr CAGR       : {cagr:+.2f}%   (expected: -2.08%)")

print(f"\n  {'YEAR':<6}  {'PnL (Rs)':>13}  {'Return %':>9}")
running = INITIAL_CAPITAL
for year in [2022, 2023, 2024, 2025]:
    yr_pnl = sum(p for y, p in all_trades if y == year)
    yr_ret  = yr_pnl / running * 100
    running += yr_pnl
    print(f"  {year}    {yr_pnl:>+13,.2f}  {yr_ret:>+8.2f}%")

match = "CONFIRMED" if abs(cagr - (-8.62)) < 0.10 else "MISMATCH -- investigate"
print(f"\n  Status   : {match}  (DS3 + slippage baseline: -8.62%, 28,085 trades)")
print(f"  Run time : {elapsed:.1f}s")
print(f"{'='*60}")