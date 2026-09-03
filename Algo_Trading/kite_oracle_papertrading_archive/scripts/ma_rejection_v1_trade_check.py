"""
Trade-level check — validates trades in a live_trades.csv against an
official-replay of the core logic, for an explicit custom time window.
Unlike ma_rejection_v1_reconcile.py (which auto-derives its window from
live_bars.csv and also does a bar-level check), this only does trade-level
validation, over whatever [--start, --end] window you give it. Useful when
live_bars.csv doesn't span the window you actually want to check (e.g. after
a bot restart overwrote it) but live_trades.csv still has the trades.

Usage:
    python ma_rejection_v1_trade_check.py --start "2026-07-23 13:00" --end "2026-07-23 15:00"
    python ma_rejection_v1_trade_check.py --start "2026-07-23 09:15" --end "2026-07-23 15:30" --trades-file path/to/live_trades.csv
"""
import argparse
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

DEFAULT_TRADES_FILE = Path(__file__).resolve().parent.parent / 'data' / 'trades' / 'live_trades.csv'
RECON_DIR = Path(__file__).resolve().parent.parent / 'data' / 'recon'

SYMBOL_MAP = {'TATAMOTORS': 'TMPV'}

UNIVERSE = ['ADANIPORTS', 'ASHOKLEY', 'AXISBANK', 'BAJFINANCE', 'BANDHANBNK', 'BHARTIARTL',
            'CIPLA', 'COALINDIA', 'DABUR', 'DIVISLAB', 'HDFCBANK', 'HINDALCO', 'ICICIBANK',
            'INDUSINDBK', 'INFY', 'ITC', 'JSWSTEEL', 'NATIONALUM', 'NTPC', 'ONGC', 'PNB',
            'POWERGRID', 'RELIANCE', 'SBIN', 'SUNPHARMA', 'TATAMOTORS', 'TATASTEEL',
            'TECHM', 'VEDL', 'WIPRO']


def kite_symbol(display_symbol):
    return SYMBOL_MAP.get(display_symbol, display_symbol)


def main():
    parser = argparse.ArgumentParser(description='Trade-level check for a custom time window.')
    parser.add_argument('--start', required=True, help='Window start, e.g. "2026-07-23 13:00"')
    parser.add_argument('--end', required=True, help='Window end, e.g. "2026-07-23 15:00"')
    parser.add_argument('--trades-file', default=str(DEFAULT_TRADES_FILE),
                         help='Path to a live_trades.csv (default: data/trades/live_trades.csv)')
    args = parser.parse_args()

    session_start = pd.Timestamp(args.start)
    session_end = pd.Timestamp(args.end)

    kite = KiteConnect(api_key=API_KEY)
    kite.set_access_token(ACCESS_TOKEN)

    trades_path = Path(args.trades_file)
    live_trades = pd.read_csv(trades_path, parse_dates=['entry_dt'])
    live_trades_in_window = live_trades[
        (live_trades['entry_dt'] >= session_start) & (live_trades['entry_dt'] < session_end)
    ]

    symbols = UNIVERSE  # full universe - catches signals live missed entirely, not just symbols live traded
    log_lines = []

    def log(msg=''):
        print(msg)
        log_lines.append(str(msg))

    log(f'Trade-level check, window {session_start} to {session_end}')
    log(f'Trades file: {trades_path}')
    log(f'Live trades in window: {len(live_trades_in_window)}   Replaying full universe: {len(symbols)} symbols')

    official_trades = []
    # Replay every symbol present in the window's live trades, plus nothing else -
    # if you want to also catch signals live entirely missed on OTHER symbols,
    # widen this to the full UNIVERSE instead.
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
            process_bar(sym, bar, state, official_trades)

    official_trades_df = pd.DataFrame(official_trades)
    log(f'Official-replay trades: {len(official_trades_df)}')

    log('\n--- Trade-level ---')
    if len(official_trades_df) > 0 or len(live_trades_in_window) > 0:
        live_keys = set(zip(live_trades_in_window['symbol'], live_trades_in_window['entry_dt']))
        off_keys = set(zip(official_trades_df['symbol'], official_trades_df['entry_dt'])) if len(official_trades_df) else set()
        log(f'Matched (same symbol+entry_dt): {len(live_keys & off_keys)}')
        log(f'Only in live: {len(live_keys - off_keys)}')
        log(f'Only in official-replay: {len(off_keys - live_keys)}')
        if live_keys - off_keys:
            log('\nOnly in live:')
            for k in sorted(live_keys - off_keys):
                log(f'  {k}')
        if off_keys - live_keys:
            log('\nOnly in official-replay:')
            for k in sorted(off_keys - live_keys):
                log(f'  {k}')
        if live_keys & off_keys:
            log('\nMatched:')
            for k in sorted(live_keys & off_keys):
                log(f'  {k}')
    else:
        log('No trades in window on either side.')

    RECON_DIR.mkdir(parents=True, exist_ok=True)
    findings_path = RECON_DIR / f'trade_check_{session_start.date()}_{session_start.strftime("%H%M")}_{session_end.strftime("%H%M")}.md'
    findings_path.write_text('\n'.join(log_lines), encoding='utf-8')
    print(f'\nSaved findings to {findings_path}')


if __name__ == '__main__':
    main()
