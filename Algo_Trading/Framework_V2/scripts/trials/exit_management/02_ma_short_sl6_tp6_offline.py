"""
MA Rejection v1 (SHORT) — SL=6.0/TP=6.0 variant offline engine, exit_management #02.
Structurally shaped like the live engine: one bar at a time, explicit per-stock
state (ma_short_sl6_tp6_core.py, branched from ma_short_v1_core.py with only
SL_MULT/TP_MULT changed). Compare its PF/Sh(D)/ZPF/ZSh(D) against #01's v1 numbers.
"""
import os
import glob

import numpy as np
import pandas as pd

from ma_short_sl6_tp6_core import StockState, process_bar

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.normpath(os.path.join(_THIS_DIR, '..', '..', '..', 'data', 'historical', 'intraday_5min_DS3'))
TRADE_LOG = os.path.join(_THIS_DIR, '02_ma_short_sl6_tp6_trades.csv')


def load_arrays(f):
    """Per-stock plain numpy arrays (known-good memory pattern from
    baseline_explorations/baseline_reserve_lock/sl_tp_sweep_baseline_short.py) —
    never concatenated into one giant DataFrame, never .to_dict('records')."""
    df = pd.read_parquet(f, columns=['datetime', 'open', 'high', 'low', 'close'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].apply(lambda x: x.replace(tzinfo=None))
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return {
        'datetime': df['datetime'].values, 'open': df['open'].values,
        'high': df['high'].values, 'low': df['low'].values, 'close': df['close'].values,
        'date': df['datetime'].dt.date.values, 'hour': df['datetime'].dt.hour.values,
        'n': len(df),
    }


files = sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet')))
print(f'Loading {len(files)} stocks...')
symbols = [os.path.basename(f).replace('.parquet', '') for f in files]
stock_arrays = [load_arrays(f) for f in files]

# Lightweight (datetime, stock_idx, row_idx) index only — no OHLC duplication —
# to replay all 30 stocks in strict global chronological order (matches the live
# engine), same stable-sort tie-break as the original (mergesort on datetime,
# ties broken by stock order == symbol order, since files are pre-sorted by name).
total_n = sum(a['n'] for a in stock_arrays)
print(f'Loaded {total_n:,} bars. Building chronological index...')
all_dt = np.concatenate([a['datetime'] for a in stock_arrays])
stock_idx = np.concatenate([np.full(a['n'], si, dtype=np.int32) for si, a in enumerate(stock_arrays)])
row_idx = np.concatenate([np.arange(a['n'], dtype=np.int64) for a in stock_arrays])
order = np.argsort(all_dt, kind='mergesort')
del all_dt  # only the sort order is needed past this point

print('Replaying in chronological order...')
states = {}
trades = []
for si, ri in zip(stock_idx[order], row_idx[order]):
    symbol = symbols[si]
    arr = stock_arrays[si]
    bar = {'datetime': pd.Timestamp(arr['datetime'][ri]), 'open': arr['open'][ri], 'high': arr['high'][ri],
           'low': arr['low'][ri], 'close': arr['close'][ri], 'date': arr['date'][ri], 'hour': arr['hour'][ri]}
    state = states.setdefault(symbol, StockState())
    process_bar(symbol, bar, state, trades)

trades_df = pd.DataFrame(trades)
trades_df.to_csv(TRADE_LOG, index=False)
print(f'\n{len(trades_df):,} trades written to {TRADE_LOG}')

# --- Raw PF (pre-charge, reference only per backtesting_rules.md) ---
gp = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
gl = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
pf = gp / gl if gl > 0 else 0.0

# --- ZPF (Zerodha Profit Factor) — the actual viability metric ---
zgp = trades_df[trades_df['zpnl'] > 0]['zpnl'].sum()
zgl = abs(trades_df[trades_df['zpnl'] < 0]['zpnl'].sum())
zpf = zgp / zgl if zgl > 0 else 0.0

# --- Sh(D) / ZSh(D) — daily-resampled annualised Sharpe (per backtesting_rules.md,
# NOT monthly — daily_pnl[date] = sum of all trade pnl on that date, x sqrt(252)) ---
tdf = trades_df.copy()
tdf['exit_dt'] = pd.to_datetime(tdf['exit_dt'])
daily = tdf.resample('D', on='exit_dt')[['pnl', 'zpnl']].sum()
daily = daily[(daily['pnl'] != 0) | (daily['zpnl'] != 0)]  # drop no-trade days
sh_d = round((daily['pnl'].mean() / daily['pnl'].std()) * np.sqrt(252), 3) if daily['pnl'].std() > 0 else 0.0
zsh_d = round((daily['zpnl'].mean() / daily['zpnl'].std()) * np.sqrt(252), 3) if daily['zpnl'].std() > 0 else 0.0

print(f'N={len(trades_df):,}  PF={pf:.3f}  Sh(D)={sh_d:.3f}  ZPF={zpf:.3f}  ZSh(D)={zsh_d:.3f}')
