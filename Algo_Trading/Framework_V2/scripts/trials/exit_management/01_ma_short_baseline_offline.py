"""
MA Rejection v1 (SHORT) — baseline offline engine, exit_management #01.
Structurally shaped like the live engine: one bar at a time, explicit per-stock
state (ma_short_baseline_core.py, a copy of the live bot's ma_rejection_v1_core.py),
all 30 stocks processed in strict chronological order (not stock-by-stock). This is
the unmodified reference — every future exit-management variant here gets compared
against its PF/Sharpe.
"""
import os
import glob

import numpy as np
import pandas as pd

from ma_short_baseline_core import StockState, process_bar

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.normpath(os.path.join(_THIS_DIR, '..', '..', '..', 'data', 'historical', 'intraday_5min_DS3'))
TRADE_LOG = os.path.join(_THIS_DIR, '01_ma_short_baseline_trades.csv')


def load(f):
    df = pd.read_parquet(f, columns=['datetime', 'open', 'high', 'low', 'close'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].apply(lambda x: x.replace(tzinfo=None))
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df['symbol'] = os.path.basename(f).replace('.parquet', '')
    return df


files = sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet')))
print(f'Loading {len(files)} stocks...')
all_bars = pd.concat([load(f) for f in files], ignore_index=True)
all_bars.sort_values(['datetime', 'symbol'], inplace=True, kind='mergesort')
print(f'Loaded {len(all_bars):,} bars. Replaying in chronological order...')

states = {}
trades = []
for symbol, bar in zip(all_bars['symbol'].values, all_bars.to_dict('records')):
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
