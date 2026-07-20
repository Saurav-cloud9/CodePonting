"""
MA Rejection v1 (SHORT) — live paper-trading engine.
Ticks only: KiteTicker builds 5-min bars in real time, feeds the shared core
logic (ma_rejection_v1_core.py) for signal/entry, and monitors open positions
tick-by-tick for SL/TP (real-time, not bar-close-only). historical_data is
used only for startup warm-up and reconnect gap-patching — never for live
signal detection.
"""
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from kiteconnect import KiteConnect, KiteTicker

from ma_rejection_v1_core import StockState, process_bar, update_indicators, EOD_HOUR

env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path, override=True)

API_KEY = os.getenv('KITE_API_KEY')
ACCESS_TOKEN = os.getenv('KITE_ACCESS_TOKEN')

DATA_DIR = Path(__file__).resolve().parent.parent / 'data' / 'trades'
TRADE_LOG = DATA_DIR / 'live_trades.csv'
BAR_LOG = DATA_DIR / 'live_bars.csv'

UNIVERSE = ['ADANIPORTS', 'ASHOKLEY', 'AXISBANK', 'BAJFINANCE', 'BANDHANBNK', 'BHARTIARTL',
            'CIPLA', 'COALINDIA', 'DABUR', 'DIVISLAB', 'HDFCBANK', 'HINDALCO', 'ICICIBANK',
            'INDUSINDBK', 'INFY', 'ITC', 'JSWSTEEL', 'NATIONALUM', 'NTPC', 'ONGC', 'PNB',
            'POWERGRID', 'RELIANCE', 'SBIN', 'SUNPHARMA', 'TATAMOTORS', 'TATASTEEL',
            'TECHM', 'VEDL', 'WIPRO']

# TATAMOTORS demerged Nov 2025 -> TMPV is the continuing entity (same instrument_token)
SYMBOL_MAP = {'TATAMOTORS': 'TMPV'}


def kite_symbol(display_symbol):
    return SYMBOL_MAP.get(display_symbol, display_symbol)


kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

print('Resolving instrument tokens...')
token_to_symbol = {}
symbol_to_token = {}
for sym in UNIVERSE:
    ksym = kite_symbol(sym)
    quote = kite.ltp([f'NSE:{ksym}'])
    token = quote[f'NSE:{ksym}']['instrument_token']
    token_to_symbol[token] = sym
    symbol_to_token[sym] = token
print(f'Resolved {len(symbol_to_token)} instruments.')

states = {sym: StockState() for sym in UNIVERSE}
trades = []
bar_log_rows = []
forming_bar = {}
lock = threading.Lock()


def warmup():
    print('Warming up MA20/ATR14 from historical_data (last 20 candles, wide window)...')
    to_date = datetime.now()
    from_date = to_date - timedelta(days=10)
    for sym in UNIVERSE:
        token = symbol_to_token[sym]
        candles = kite.historical_data(token, from_date=from_date, to_date=to_date, interval='5minute')
        for c in candles[-20:]:
            dt = c['date'].replace(tzinfo=None)
            bar = {'datetime': dt, 'open': c['open'], 'high': c['high'],
                   'low': c['low'], 'close': c['close'], 'date': dt.date(), 'hour': dt.hour}
            update_indicators(bar, states[sym])
    print('Warm-up complete.')


def bucket_start(dt):
    minute = (dt.minute // 5) * 5
    return dt.replace(minute=minute, second=0, microsecond=0)


def finalize_bar(sym, bar):
    with lock:
        bar_log_rows.append({'symbol': sym, **bar})
        process_bar(sym, bar, states[sym], trades)
    pos = states[sym].position
    tag = f"OPEN sl={pos['sl']:.2f} tp={pos['tp']:.2f}" if pos else 'flat'
    print(f"{bar['datetime']}  {sym:12s}  O={bar['open']:.2f} H={bar['high']:.2f} "
          f"L={bar['low']:.2f} C={bar['close']:.2f}  -> {tag}")


def on_ticks(ws, ticks):
    for t in ticks:
        sym = token_to_symbol.get(t['instrument_token'])
        if sym is None:
            continue
        price = t['last_price']
        ts = t.get('exchange_timestamp') or datetime.now()
        b = bucket_start(ts)

        state = states[sym]
        fb = forming_bar.get(sym)
        new_bucket_started = fb is None or b != fb['bucket']

        if fb is None:
            forming_bar[sym] = {'bucket': b, 'open': price, 'high': price, 'low': price, 'close': price}
        elif b == fb['bucket']:
            fb['high'] = max(fb['high'], price)
            fb['low'] = min(fb['low'], price)
            fb['close'] = price
        else:
            closed = {'datetime': fb['bucket'], 'open': fb['open'], 'high': fb['high'],
                      'low': fb['low'], 'close': fb['close'],
                      'date': fb['bucket'].date(), 'hour': fb['bucket'].hour}
            finalize_bar(sym, closed)
            forming_bar[sym] = {'bucket': b, 'open': price, 'high': price, 'low': price, 'close': price}

        # Tick-based EOD exit - the instant we cross into an hour>=EOD_HOUR bucket,
        # don't wait for that bar to close (same real-time design as SL/TP below).
        # Exit price = this tick's price, which is that new bucket's open.
        if new_bucket_started and b.hour >= EOD_HOUR:
            pos = state.position
            if pos is not None:
                pnl = pos['entry'] - price
                outcome = 'EOD+' if pnl > 0 else 'EOD-'
                with lock:
                    trades.append({'symbol': sym, 'entry_dt': pos['entry_dt'], 'entry': pos['entry'],
                                    'sl': pos['sl'], 'tp': pos['tp'], 'exit_dt': ts,
                                    'exit_price': price, 'outcome': outcome, 'pnl': pnl})
                    state.position = None
                    state.tick_exit_pending_bar = b
                print(f"{ts}  {sym:12s}  TICK EXIT ({outcome}) @ {price:.2f}  pnl={pnl:.2f}")
            state.pending_entry = None  # no new entries once EOD hour is reached

        # Real-time exit monitoring - ticks, not waiting for bar close
        pos = state.position
        if pos is not None:
            if price >= pos['sl']:
                pnl = pos['entry'] - pos['sl']
                with lock:
                    trades.append({'symbol': sym, 'entry_dt': pos['entry_dt'], 'entry': pos['entry'],
                                    'sl': pos['sl'], 'tp': pos['tp'], 'exit_dt': ts,
                                    'exit_price': pos['sl'], 'outcome': 'L', 'pnl': pnl})
                    state.position = None
                    state.tick_exit_pending_bar = forming_bar[sym]['bucket']
                print(f"{ts}  {sym:12s}  TICK EXIT (SL) @ {pos['sl']:.2f}  pnl={pnl:.2f}")
            elif price <= pos['tp']:
                pnl = pos['entry'] - pos['tp']
                with lock:
                    trades.append({'symbol': sym, 'entry_dt': pos['entry_dt'], 'entry': pos['entry'],
                                    'sl': pos['sl'], 'tp': pos['tp'], 'exit_dt': ts,
                                    'exit_price': pos['tp'], 'outcome': 'W', 'pnl': pnl})
                    state.position = None
                    state.tick_exit_pending_bar = forming_bar[sym]['bucket']
                print(f"{ts}  {sym:12s}  TICK EXIT (TP) @ {pos['tp']:.2f}  pnl={pnl:.2f}")


def on_connect(ws, response):
    print('Connected. Subscribing...')
    tokens = list(symbol_to_token.values())
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_QUOTE, tokens)


def on_close(ws, code, reason):
    print(f'Connection closed: {code} {reason}')


def on_reconnect(ws, attempts_count):
    print(f'Reconnecting (attempt {attempts_count})... re-warming indicators to patch any gap.')
    warmup()


if __name__ == '__main__':
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    warmup()

    kws = KiteTicker(API_KEY, ACCESS_TOKEN)
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_close = on_close
    kws.on_reconnect = on_reconnect

    print('Connecting to KiteTicker...')
    kws.connect(threaded=True)

    try:
        while True:
            time.sleep(30)
            with lock:
                try:
                    if trades:
                        pd.DataFrame(trades).to_csv(TRADE_LOG, index=False)
                    if bar_log_rows:
                        pd.DataFrame(bar_log_rows).to_csv(BAR_LOG, index=False)
                except PermissionError:
                    print('CSV save skipped - file open elsewhere (e.g. Excel). Will retry in 30s.')
    except KeyboardInterrupt:
        print('Stopping...')
        kws.close()
        with lock:
            try:
                pd.DataFrame(trades).to_csv(TRADE_LOG, index=False)
                pd.DataFrame(bar_log_rows).to_csv(BAR_LOG, index=False)
            except PermissionError:
                print('Final CSV save failed - file open elsewhere. Close it and re-save manually if needed.')
        print(f'Saved {len(trades)} trades to {TRADE_LOG}')
