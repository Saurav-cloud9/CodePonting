"""
run_cost_analysis.py -- Step 3.3: Transaction Costs + Slippage
==============================================================
Runs the Step 3.2 winner combo with full cost/slippage modelling
and reports CAGR under three cost regimes:

  Raw      : no costs, no slippage (= -2.08% baseline)
  Upstox   : 0.05% brokerage (capped Rs 20) + all charges
  Kite     : 0.03% brokerage (capped Rs 20) + all charges

  Entry slippage  : +1 tick (Rs 0.05) above signal open (Change 7a)
  SL exit slip    : stop - 1 tick (Rs 0.05) (Change 7b)
  Charges         : STT + exchange + SEBI + GST + stamp (Change 7c)

Config: Extreme-2, SL=A, PG=True, CP=True, AF=True, EC=False
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

from core.indicators  import add_intraday_indicators, add_atr
from core.strategy    import BounceStrategy
from core.portfolio   import Portfolio

# -- CONSTANTS -----------------------------------------------------------------
INITIAL_CAPITAL = 1_000_000
YEARS           = 4
NUM_STOCKS      = 30
EXCLUDE         = {"NIFTY50", "VI"}
ATR_MULT_STOP   = 2.5
RR_TARGET       = 4.5 / 2.5
_AUCTION_INT    = 945
_CUTOFF_DEFAULT = 1430

FV1_DIR  = SANDBOX_DIR.parent
DS3_DIR  = FV1_DIR / "data/historical/intraday_5min_DS3"

# -- STEP 1: LOAD DATA ---------------------------------------------------------
print("Step 1: Loading stock data...", flush=True)
t0 = time.time()

stock_files = sorted(f for f in DS3_DIR.glob("*.parquet") if f.stem not in EXCLUDE)
print(f"  {len(stock_files)} stocks", flush=True)

stock_dfs = {}
for sp in stock_files:
    stock = sp.stem
    df = pd.read_parquet(sp)
    df["datetime"] = pd.to_datetime(df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S"))
    df = df.sort_values("datetime").reset_index(drop=True)
    _t = df["datetime"].dt.time
    df = df[_t.between(pd.Timestamp("09:15").time(), pd.Timestamp("15:30").time())]
    df = df.reset_index(drop=True)
    df = add_intraday_indicators(df)
    df = add_atr(df)
    stock_dfs[stock] = df

print(f"  Done in {time.time()-t0:.1f}s", flush=True)

# -- STEP 2: GENERATE SIGNALS --------------------------------------------------
# auction_filter=True, entry_cutoff=False (14:30)
print("Step 2: Generating signals (auction_filter=True)...", flush=True)

strategy = BounceStrategy(auction_filter=True)

# Suppress per-stock dedup prints for clean output
import io as _io, contextlib as _ctx
signal_maps = {}
for stock, df in stock_dfs.items():
    buf = _io.StringIO()
    with _ctx.redirect_stdout(buf):
        sigs = strategy.generate_signals(df)
    # Convert to bar-index map for fast lookup
    dt_to_idx = {row.datetime: i for i, row in df[["datetime"]].iterrows()}
    sm = {}
    for s in sigs:
        idx = dt_to_idx.get(s["datetime"])
        if idx is not None:
            sm[idx] = s
    signal_maps[stock] = sm

total_sigs = sum(len(v) for v in signal_maps.values())
print(f"  {total_sigs:,} signals across {len(signal_maps)} stocks", flush=True)

# -- STEP 3: RUN BACKTEST WITH PORTFOLIO CLASS ---------------------------------
print("Step 3: Running backtest with costs...", flush=True)
t1 = time.time()

all_trades = []

for stock, df in stock_dfs.items():
    sm = signal_maps[stock]
    if not sm:
        continue

    portfolio = Portfolio(
        capital       = INITIAL_CAPITAL,
        atr_mult_stop = ATR_MULT_STOP,
        rr_target     = RR_TARGET,
        num_stocks    = NUM_STOCKS,
        sl_variant    = "A",
        position_guard = True,
        compounding    = True,
    )

    n = len(df)
    for i in range(n):
        bar = df.iloc[i]

        # Entry
        if i in sm:
            portfolio.open_position(sm[i], bar, i)

        # Update
        portfolio.update(bar, i)

    trades = portfolio.trades_df()
    if not trades.empty:
        trades.insert(0, "stock", stock)
        all_trades.append(trades)

elapsed = time.time() - t1

# -- RESULTS -------------------------------------------------------------------
if not all_trades:
    print("[ERROR] No trades generated.")
    sys.exit(1)

all_df = pd.concat(all_trades, ignore_index=True)
all_df["year"] = pd.to_datetime(all_df["entry_time"]).dt.year


def cagr_pct(total_pnl):
    final = INITIAL_CAPITAL + total_pnl
    if final <= 0:
        return float("nan")
    return ((final / INITIAL_CAPITAL) ** (1 / YEARS) - 1) * 100


n_trades = len(all_df)
n_wins   = int((all_df["raw_pnl"] > 0).sum())
win_pct  = n_wins / n_trades * 100 if n_trades else 0

raw_cagr    = cagr_pct(all_df["raw_pnl"].sum())
upstox_cagr = cagr_pct(all_df["net_pnl_upstox"].sum())
kite_cagr   = cagr_pct(all_df["net_pnl_kite"].sum())

print(f"\n{'='*66}")
print(f"  STEP 3.3 — TRANSACTION COST IMPACT")
print(f"{'='*66}")
print(f"  Config    : Extreme-2  |  SL=A  |  PG+CP+AF  |  Entry slip=Rs 0.05 (1 tick)")
print(f"  Stocks    : {len(stock_dfs)}  |  Period: 2022-2025  ({YEARS} yr)")
print()
print(f"  Total Trades : {n_trades:,}")
print(f"  Win Rate     : {win_pct:.1f}%")
print()
print(f"  {'':25}  {'Raw':>9}  {'Upstox':>9}  {'Kite':>9}")
print(f"  {'':25}  {'-'*9}  {'-'*9}  {'-'*9}")
print(f"  {'4yr CAGR':<25}  {raw_cagr:>+8.2f}%  {upstox_cagr:>+8.2f}%  {kite_cagr:>+8.2f}%")

print(f"\n  {'YEAR':<6}  {'Raw':>9}  {'Upstox':>9}  {'Kite':>9}")
print(f"  {'-'*6}  {'-'*9}  {'-'*9}  {'-'*9}")

running_raw    = INITIAL_CAPITAL
running_upstox = INITIAL_CAPITAL
running_kite   = INITIAL_CAPITAL

for year in [2022, 2023, 2024, 2025]:
    yr = all_df[all_df["year"] == year]
    yr_raw    = yr["raw_pnl"].sum()
    yr_upstox = yr["net_pnl_upstox"].sum()
    yr_kite   = yr["net_pnl_kite"].sum()

    ret_raw    = yr_raw    / running_raw    * 100
    ret_upstox = yr_upstox / running_upstox * 100
    ret_kite   = yr_kite   / running_kite   * 100

    running_raw    += yr_raw
    running_upstox += yr_upstox
    running_kite   += yr_kite

    print(f"  {year}    {ret_raw:>+8.2f}%  {ret_upstox:>+8.2f}%  {ret_kite:>+8.2f}%")

raw_delta    = raw_cagr    - (-2.08)
upstox_delta = upstox_cagr - raw_cagr
kite_delta   = kite_cagr   - raw_cagr

print(f"\n  Cost drag (vs raw):  Upstox {upstox_delta:+.2f}pp  |  Kite {kite_delta:+.2f}pp")
print(f"  Slippage included:   +0.1 ATR entry  +Rs 0.05 SL exit")
print(f"\n  Run time : {elapsed:.1f}s")
print(f"{'='*66}")
