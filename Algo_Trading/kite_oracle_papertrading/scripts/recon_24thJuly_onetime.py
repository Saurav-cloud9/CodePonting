"""
One-time reconciliation for 2026-07-24 — combines the two real runs of that day
(iteration1_4 = pre-restart 09:15-13:00, iteration1_5 = post-restart 13:10-14:55)
into single bars/trades inputs, then runs the same bar-level + trade-level
recon logic as ma_rejection_v1_reconcile.py (with the session_end off-by-one
fix already applied). Not part of the live pipeline - throwaway script for
this one investigation.
"""
import os
from datetime import timedelta
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from kiteconnect import KiteConnect

from ma_rejection_v1_core import StockState, process_bar, update_indicators

env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path, override=True)

API_KEY = os.getenv('KITE_API_KEY')
ACCESS_TOKEN = os.getenv('KITE_ACCESS_TOKEN')

DAY_DIR = Path(__file__).resolve().parent.parent / 'data' / 'trades' / 'daily data' / '24thJuly' / 'iteration1'
RUN1 = DAY_DIR / 'iteration1_4'   # pre-restart, 09:15-13:00
RUN2 = DAY_DIR / 'iteration1_5'   # post-restart, 13:10-14:55

SYMBOL_MAP = {'TATAMOTORS': 'TMPV'}

log_lines = []


def log(msg=''):
    print(msg)
    log_lines.append(str(msg))


def kite_symbol(display_symbol):
    return SYMBOL_MAP.get(display_symbol, display_symbol)


kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

# ── Combine the two runs ──────────────────────────────────────────────────
bars1 = pd.read_csv(RUN1 / 'live_bars.csv', parse_dates=['datetime'])
bars2 = pd.read_csv(RUN2 / 'live_bars.csv', parse_dates=['datetime'])
live_bars = pd.concat([bars1, bars2], ignore_index=True).drop_duplicates(subset=['symbol', 'datetime'])

trades1 = pd.read_csv(RUN1 / 'live_trades.csv', parse_dates=['entry_dt'])
trades2 = pd.read_csv(RUN2 / 'live_trades.csv', parse_dates=['entry_dt'])
live_trades = pd.concat([trades1, trades2], ignore_index=True).drop_duplicates(subset=['symbol', 'entry_dt'])

symbols = sorted(live_bars['symbol'].unique())
session_start = live_bars['datetime'].min()
session_end = live_bars['datetime'].max() + timedelta(minutes=5)
session_date = session_start.date()
log(f'Combined bars: {len(live_bars):,} rows   Combined trades: {len(live_trades)}')
log(f'Reconciling {len(symbols)} symbols, session window {session_start} to {session_end}')

official_bars_rows = []
official_trades = []

for sym in symbols:
    ksym = kite_symbol(sym)
    quote = kite.ltp([f'NSE:{ksym}'])
    token = quote[f'NSE:{ksym}']['instrument_token']
    candles = kite.historical_data(
        token, from_date=session_start - timedelta(days=10),
        to_date=session_end + timedelta(minutes=10), interval='5minute')

    state = StockState()
    for c in candles:
        dt = c['date'].replace(tzinfo=None)
        bar = {'datetime': dt, 'open': c['open'], 'high': c['high'],
               'low': c['low'], 'close': c['close'], 'date': dt.date(), 'hour': dt.hour}
        if dt < session_start:
            update_indicators(bar, state)
            continue
        if dt > session_end:
            continue
        official_bars_rows.append({'symbol': sym, **bar})
        process_bar(sym, bar, state, official_trades)

official_bars = pd.DataFrame(official_bars_rows)
official_trades_df = pd.DataFrame(official_trades)

log(f'\nOfficial bars fetched: {len(official_bars):,}   Live bars: {len(live_bars):,}')
log(f'Official-replay trades: {len(official_trades_df):,}')

# ── Bar-level check ─────────────────────────────────────────────────────────
merged = pd.merge(
    live_bars[['symbol', 'datetime', 'open', 'high', 'low', 'close']],
    official_bars[['symbol', 'datetime', 'open', 'high', 'low', 'close']],
    on=['symbol', 'datetime'], suffixes=('_live', '_official'), how='outer', indicator=True)

only_live = merged[merged['_merge'] == 'left_only']
only_official = merged[merged['_merge'] == 'right_only']
both = merged[merged['_merge'] == 'both'].copy()

for col in ['open', 'high', 'low', 'close']:
    both[f'{col}_diff'] = (both[f'{col}_live'] - both[f'{col}_official']).abs()
max_diff = both[[f'{c}_diff' for c in ['open', 'high', 'low', 'close']]].max().max()
mismatched = both[(both[[f'{c}_diff' for c in ['open', 'high', 'low', 'close']]] > 0.01).any(axis=1)]

log(f'\n--- Bar-level ---')
log(f'Matched bars (both sources): {len(both):,}')
log(f'Only in live (missing from official): {len(only_live)}')
if len(only_live) > 0:
    log(only_live[['symbol', 'datetime']].sort_values(['symbol', 'datetime']).to_string(index=False))
log(f'Only in official (missing from live): {len(only_official)}')
if len(only_official) > 0:
    log(only_official[['symbol', 'datetime']].sort_values(['symbol', 'datetime']).to_string(index=False))
log(f'Max abs OHLC diff on matched bars: {max_diff:.4f}')
log(f'Bars with OHLC diff > 0.01: {len(mismatched)}')
if len(mismatched) > 0:
    log(mismatched[['symbol', 'datetime', 'open_diff', 'high_diff', 'low_diff', 'close_diff']].to_string(index=False))

# ── Trade-level check ───────────────────────────────────────────────────────
log(f'\n--- Trade-level ---')
log(f'Live trades: {len(live_trades)}   Official-replay trades: {len(official_trades_df)}')
live_keys = set(zip(live_trades['symbol'], live_trades['entry_dt']))
if len(official_trades_df) > 0:
    off_keys = set(zip(official_trades_df['symbol'], official_trades_df['entry_dt']))
else:
    off_keys = set()
log(f'Matched (same symbol+entry_dt): {len(live_keys & off_keys)}')
only_in_live = live_keys - off_keys
only_in_official = off_keys - live_keys
log(f'Only in live: {len(only_in_live)}')
if only_in_live:
    for s, dt in sorted(only_in_live):
        log(f'  {s}  {dt}')
log(f'Only in official-replay: {len(only_in_official)}')
if only_in_official:
    for s, dt in sorted(only_in_official):
        log(f'  {s}  {dt}')

# ── Save outputs ─────────────────────────────────────────────────────────────
RECON_DIR = Path(__file__).resolve().parent.parent / 'data' / 'recon'
RECON_DIR.mkdir(parents=True, exist_ok=True)
official_bars_path = RECON_DIR / f'official_bars_{session_date}_onetime.csv'
findings_path = RECON_DIR / f'recon_{session_date}_onetime.md'

official_bars.to_csv(official_bars_path, index=False)
findings_path.write_text('\n'.join(log_lines), encoding='utf-8')

print(f'\nSaved official bars to {official_bars_path}')
print(f'Saved findings to {findings_path}')
