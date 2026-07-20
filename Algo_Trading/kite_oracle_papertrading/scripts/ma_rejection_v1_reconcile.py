"""
Reconciliation script — run after a live/paper session.
1. Bar-level check: our live-built bars (live_bars.csv) vs Kite's official
   historical_data for the same window.
2. Trade-level check: replay the shared core logic on official bars, compare
   resulting trades against what the live engine actually did (live_trades.csv).
Some divergence is expected (real tick-driven slippage vs clean official-bar
fills) - the goal is catching structural mismatches, not zero difference.
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

DATA_DIR = Path(__file__).resolve().parent.parent / 'data' / 'trades'
LIVE_BARS = DATA_DIR / 'live_bars.csv'
LIVE_TRADES = DATA_DIR / 'live_trades.csv'

SYMBOL_MAP = {'TATAMOTORS': 'TMPV'}


def kite_symbol(display_symbol):
    return SYMBOL_MAP.get(display_symbol, display_symbol)


kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

live_bars = pd.read_csv(LIVE_BARS, parse_dates=['datetime'])
symbols = sorted(live_bars['symbol'].unique())
session_start = live_bars['datetime'].min()
session_end = live_bars['datetime'].max() + timedelta(minutes=5)
print(f'Reconciling {len(symbols)} symbols, session window {session_start} to {session_end}')

official_bars_rows = []
official_trades = []

for sym in symbols:
    ksym = kite_symbol(sym)
    quote = kite.ltp([f'NSE:{ksym}'])
    token = quote[f'NSE:{ksym}']['instrument_token']
    candles = kite.historical_data(
        token, from_date=session_start - timedelta(days=10),
        to_date=session_end, interval='5minute')

    state = StockState()
    for c in candles:
        dt = c['date'].replace(tzinfo=None)
        bar = {'datetime': dt, 'open': c['open'], 'high': c['high'],
               'low': c['low'], 'close': c['close'], 'date': dt.date(), 'hour': dt.hour}
        if dt < session_start:
            update_indicators(bar, state)
            continue
        if dt >= session_end:
            continue
        official_bars_rows.append({'symbol': sym, **bar})
        process_bar(sym, bar, state, official_trades)

official_bars = pd.DataFrame(official_bars_rows)
official_trades_df = pd.DataFrame(official_trades)

print(f'\nOfficial bars fetched: {len(official_bars):,}   Live bars: {len(live_bars):,}')
print(f'Official-replay trades: {len(official_trades_df):,}')

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

print(f'\n--- Bar-level ---')
print(f'Matched bars (both sources): {len(both):,}')
print(f'Only in live (missing from official): {len(only_live)}')
print(f'Only in official (missing from live): {len(only_official)}')
print(f'Max abs OHLC diff on matched bars: {max_diff:.4f}')
print(f'Bars with OHLC diff > 0.01: {len(mismatched)}')
if len(mismatched) > 0:
    print(mismatched[['symbol', 'datetime', 'open_diff', 'high_diff', 'low_diff', 'close_diff']].to_string(index=False))

# ── Trade-level check ───────────────────────────────────────────────────────
print(f'\n--- Trade-level ---')
if LIVE_TRADES.exists():
    live_trades = pd.read_csv(LIVE_TRADES, parse_dates=['entry_dt'])
    print(f'Live trades: {len(live_trades)}   Official-replay trades: {len(official_trades_df)}')
    if len(official_trades_df) > 0:
        live_keys = set(zip(live_trades['symbol'], live_trades['entry_dt']))
        off_keys = set(zip(official_trades_df['symbol'], official_trades_df['entry_dt']))
        print(f'Matched (same symbol+entry_dt): {len(live_keys & off_keys)}')
        print(f'Only in live: {len(live_keys - off_keys)}')
        print(f'Only in official-replay: {len(off_keys - live_keys)}')
    else:
        print('No official-replay trades to compare (no signal fired in this window).')
else:
    print('No live_trades.csv yet - no trade has exited during this session.')
