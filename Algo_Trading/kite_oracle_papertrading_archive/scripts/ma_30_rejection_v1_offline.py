"""
MA Rejection v1 (SHORT) — offline paper-trading engine
Structurally shaped like the live engine: one bar at a time, explicit per-stock
state (ma_rejection_v1_core.py), all 30 stocks processed in strict chronological
order (not stock-by-stock). Reference logic: ma_30_rejection_v1_reference.py
(array/batch backtest) — validated against it, see grok_review.md / SESSION_SUMMARY.md.
"""
import os
import glob

import numpy as np
import pandas as pd

from ma_rejection_v1_core import StockState, process_bar

DATA_DIR  = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3'
TRADE_LOG = r'C:\Users\saurav\CodePonting\Algo_Trading\kite_oracle_papertrading\data\trades\offline_trades.csv'


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

gp = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
gl = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
pf = gp / gl if gl > 0 else 0.0
tdf = trades_df.copy()
tdf['exit_dt'] = pd.to_datetime(tdf['exit_dt'])
m = tdf.resample('ME', on='exit_dt')['pnl'].sum()
sharpe = round((m.mean() / m.std()) * np.sqrt(12), 3) if m.std() > 0 else 0.0
print(f'N={len(trades_df):,}  PF={pf:.3f}  Sharpe={sharpe:.3f}')
