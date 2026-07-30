"""
MA Rejection v1 (SHORT) — live paper-trading engine.
Ticks only: KiteTicker builds 5-min bars in real time, feeds the shared core
logic (ma_rejection_v1_core.py) for signal/entry, and monitors open positions
tick-by-tick for SL/TP (real-time, not bar-close-only). historical_data is
used only for startup warm-up and reconnect gap-patching — never for live
signal detection.
"""
import json
import os
import threading
import time
from datetime import date, datetime, timedelta
from pathlib import Path

CATCHUP_DELAY_MIN = 5  # how long after connect-time bucket to fetch its now-closed candle
MARKET_OPEN = (9, 15)  # (hour, minute) - ticks before this are pre-open auction noise, not real candles

import pandas as pd
from dotenv import load_dotenv
from kiteconnect import KiteConnect, KiteTicker

from ma_rejection_v1_core import StockState, process_bar, update_indicators, EOD_HOUR, _log_trade, zerodha_short

env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path, override=True)

API_KEY = os.getenv('KITE_API_KEY')
ACCESS_TOKEN = os.getenv('KITE_ACCESS_TOKEN')

DATA_DIR = Path(__file__).resolve().parent.parent / 'data' / 'trades'
TRADE_LOG = DATA_DIR / 'live_trades.csv'
BAR_LOG = DATA_DIR / 'live_bars.csv'
WARMUP_LOG = DATA_DIR / 'warmup_bars.csv'
POSITIONS_FILE = DATA_DIR / 'open_positions.json'

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
quotes = kite.ltp([f'NSE:{kite_symbol(sym)}' for sym in UNIVERSE])  # one batched call, not 30
for sym in UNIVERSE:
    ksym = kite_symbol(sym)
    token = quotes[f'NSE:{ksym}']['instrument_token']
    token_to_symbol[token] = sym
    symbol_to_token[sym] = token
print(f'Resolved {len(symbol_to_token)} instruments.')

states = {sym: StockState() for sym in UNIVERSE}
trades = []
bar_log_rows = []
warmup_bar_rows = []
forming_bar = {}
lock = threading.Lock()
eod_reached = threading.Event()
last_summary_bucket = None
bucket_stocks_seen = set()  # tracks which stocks have finalized a bar for last_summary_bucket
current_bucket = None  # set by warmup() - the bucket excluded from warm-up (not yet closed at connect time)
market_open_bucket = None  # today's 09:15 bucket - always historical_data-sourced (see catchup_bucket),
                            # never tick-built: it's the day's densest tick window, where KiteTicker's
                            # throttled/snapshot ticks can miss the true opening trade or an early high wick
                            # that Kite's official 5-min candle (built from the full trade tape) would catch.
peak_capital = 0.0  # highest concurrent capital (sum of open positions' entry prices) seen all day -
                    # updated on every position open/close (see update_peak_capital()), not just at
                    # print time, since ticks can open+close a position within a single 5-min bucket.


def warmup():
    global current_bucket, market_open_bucket
    print('Warming up MA20/ATR14 from historical_data (last 19 closed candles)...')
    to_date = datetime.now()
    from_date = to_date - timedelta(days=10)
    fetched = {}
    for sym in UNIVERSE:
        token = symbol_to_token[sym]
        candles = kite.historical_data(token, from_date=from_date, to_date=to_date, interval='5minute')
        fetched[sym] = candles
        time.sleep(0.34)  # stay under Kite's ~3 req/sec rate limit - historical_data can't be batched

    # Decide the "currently forming" bucket as late as possible - right before we connect
    # and ticks start flowing - so it matches what the live engine will actually build first.
    # Only 19 bars are seeded here (indicators only, no touch-check - these are already-old
    # bars). The currently-forming bucket itself is deliberately excluded (may still be
    # incomplete/unsettled in historical_data) - catchup_bucket() picks it up once
    # it has genuinely closed, running it through the FULL signal logic (not just indicators).
    current_bucket = bucket_start(datetime.now())
    if market_open_bucket is None:
        market_open_bucket = datetime.now().replace(hour=MARKET_OPEN[0], minute=MARKET_OPEN[1],
                                                      second=0, microsecond=0)
    for sym in UNIVERSE:
        candles = [c for c in fetched[sym] if bucket_start(c['date'].replace(tzinfo=None)) < current_bucket]
        for c in candles[-19:]:
            dt = c['date'].replace(tzinfo=None)
            bar = {'datetime': dt, 'open': c['open'], 'high': c['high'],
                   'low': c['low'], 'close': c['close'], 'date': dt.date(), 'hour': dt.hour}
            update_indicators(bar, states[sym])
            warmup_bar_rows.append({'symbol': sym, 'warmup_run_at': to_date, **bar})
    if warmup_bar_rows:
        pd.DataFrame(warmup_bar_rows).to_csv(WARMUP_LOG, index=False)
        print(f'Warm-up bars saved to {WARMUP_LOG}')
    print(f'Warm-up complete. Excluded bucket (still forming at connect time): {current_bucket}')


def catchup_bucket(target_bucket):
    """Runs once, ~CATCHUP_DELAY_MIN after target_bucket started - by then that bucket has
    genuinely closed, so it's safe to fetch. Feeds it through the FULL process_bar() (not
    just update_indicators()) so it gets a real touch-check too, not just silently seeded -
    sourced from historical_data instead of ticks, so it's evaluated exactly like the
    official backtest would see it. Used both for warm-up's excluded (still-forming-at-
    connect-time) bucket and for the market-open bucket (see market_open_bucket)."""
    print(f'Catch-up: fetching now-closed bucket {target_bucket} for all 30 stocks...')
    for sym in UNIVERSE:
        token = symbol_to_token[sym]
        candles = kite.historical_data(token, from_date=target_bucket,
                                        to_date=target_bucket + timedelta(minutes=5), interval='5minute')
        match = next((c for c in candles if bucket_start(c['date'].replace(tzinfo=None)) == target_bucket), None)
        if match is not None:
            dt = match['date'].replace(tzinfo=None)
            bar = {'datetime': dt, 'open': match['open'], 'high': match['high'],
                   'low': match['low'], 'close': match['close'], 'date': dt.date(), 'hour': dt.hour}
            with lock:
                bar_log_rows.append({'symbol': sym, 'datetime': bar['datetime'], 'open': bar['open'],
                                      'high': bar['high'], 'low': bar['low'], 'close': bar['close']})
                process_bar(sym, bar, states[sym], trades)
                save_positions()
                save_trades()
                update_peak_capital()
            pos = states[sym].position
            tag = f"OPEN sl={pos['sl']:.2f} tp={pos['tp']:.2f}" if pos else 'flat'
            print(f"{bar['datetime']}  {sym:12s}  O={bar['open']:.2f} H={bar['high']:.2f} "
                  f"L={bar['low']:.2f} C={bar['close']:.2f}  -> {tag}  [catch-up]")
        time.sleep(0.34)  # same rate-limit courtesy as warmup()
    print('Catch-up complete.')
    print_pnl_summary(target_bucket)


def bucket_start(dt):
    minute = (dt.minute // 5) * 5
    return dt.replace(minute=minute, second=0, microsecond=0)


def load_existing_logs():
    """Load any existing live_trades.csv/live_bars.csv/warmup_bars.csv from a
    previous run today into the in-memory lists, so the periodic save cycle
    (and each fresh warmup() write) accumulates old+new data instead of
    starting empty and overwriting whatever was already there. warmup_bars.csv
    in particular is the only real audit trail of what the bot's indicators
    were actually seeded from at each restart - useful since we've seen Kite's
    own historical_data can read differently depending on when it's fetched."""
    if TRADE_LOG.exists():
        existing = pd.read_csv(TRADE_LOG).to_dict('records')
        for t in existing:
            if 'zpnl' not in t or pd.isna(t['zpnl']):
                t['zpnl'] = t['pnl'] - zerodha_short(t['entry'], t['exit_price'])
        trades.extend(existing)
        print(f'Loaded {len(existing)} existing trade(s) from {TRADE_LOG}')
    if BAR_LOG.exists():
        existing = pd.read_csv(BAR_LOG).to_dict('records')
        bar_log_rows.extend(existing)
        print(f'Loaded {len(existing)} existing bar(s) from {BAR_LOG}')
    if WARMUP_LOG.exists():
        existing = pd.read_csv(WARMUP_LOG).to_dict('records')
        warmup_bar_rows.extend(existing)
        print(f'Loaded {len(existing)} existing warm-up bar(s) from {WARMUP_LOG}')


def archive_daily_logs():
    """Move today's log files into a dated 'daily data/<Nth><Month>' folder, right
    after a genuine EOD auto-stop - so tomorrow's load_existing_logs() starts fresh
    without needing a manual archive step first."""
    today = date.today()
    suffix = 'th' if 11 <= today.day % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(today.day % 10, 'th')
    archive_dir = DATA_DIR / 'daily data' / f'{today.day}{suffix}{today.strftime("%B")}'
    archive_dir.mkdir(parents=True, exist_ok=True)
    for f in (TRADE_LOG, BAR_LOG, WARMUP_LOG, POSITIONS_FILE):
        if f.exists():
            f.rename(archive_dir / f.name)
    print(f'Archived today\'s logs to {archive_dir}')


def save_positions():
    """Snapshot all currently-open positions AND pending touches to disk. Called
    under `lock`, right after any state.position/pending_entry change, so a
    crash/power-cut never loses more than the one change that was mid-write
    (event-driven, not polled). pending_entry must be persisted too - otherwise
    a restart landing between a touch bar and its entry bar silently drops that
    entry (state.position alone doesn't capture a touch still awaiting fill)."""
    snapshot = {}
    for sym, st in states.items():
        entry = {}
        if st.position is not None:
            pos = st.position
            entry['position'] = {
                'entry': pos['entry'], 'sl': pos['sl'], 'tp': pos['tp'],
                'entry_date': pos['entry_date'].isoformat(),
                'entry_dt': pos['entry_dt'].isoformat(),
            }
        if st.pending_entry is not None:
            pend = st.pending_entry
            entry['pending_entry'] = {
                'touch_date': pend['touch_date'].isoformat(),
                'atr': pend['atr'],
            }
        if entry:
            snapshot[sym] = entry
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(snapshot, f, indent=2)
    except PermissionError:
        print('Positions snapshot save skipped - file open elsewhere.')


def load_positions():
    if not POSITIONS_FILE.exists():
        return
    with open(POSITIONS_FILE) as f:
        snapshot = json.load(f)
    n_pos, n_pend = 0, 0
    for sym, entry in snapshot.items():
        if sym not in states:
            continue
        pos = entry.get('position')
        if pos is not None:
            states[sym].position = {
                'entry': pos['entry'], 'sl': pos['sl'], 'tp': pos['tp'],
                'entry_date': date.fromisoformat(pos['entry_date']),
                'entry_dt': datetime.fromisoformat(pos['entry_dt']),
            }
            n_pos += 1
        pend = entry.get('pending_entry')
        if pend is not None:
            touch_date = date.fromisoformat(pend['touch_date'])
            if touch_date == date.today():
                states[sym].pending_entry = {'touch_date': touch_date, 'atr': pend['atr']}
                n_pend += 1
            # else: stale (from a previous day) - dropped, same as process_bar's own
            # date-change cancellation logic (ma_rejection_v1_core.py process_bar()).
    if n_pos:
        print(f'Restored {n_pos} open position(s) from {POSITIONS_FILE}')
    if n_pend:
        print(f'Restored {n_pend} pending touch(es) from {POSITIONS_FILE}')


def save_trades():
    """Write the full trades list to disk immediately. Called under `lock` right
    after any trade closes, same event-driven pattern as save_positions() - the
    30s periodic save alone isn't enough, since a trade closing seconds before a
    crash/restart was previously invisible until the next periodic flush, which
    might never come (this is exactly how a real RELIANCE trade - entered and
    exited correctly - went missing from live_trades.csv on 2026-07-28)."""
    try:
        pd.DataFrame(trades).to_csv(TRADE_LOG, index=False)
    except PermissionError:
        print('Trade log save skipped - file open elsewhere.')


def update_peak_capital():
    """Recompute current concurrent capital (sum of open positions' entry prices)
    and roll peak_capital forward if it's a new high. Called under `lock` right
    after any position open/close, same event-driven pattern as save_positions() -
    a print-time-only snapshot would miss a peak that opened and closed again
    within a single 5-min bucket via ticks."""
    global peak_capital
    current_capital = sum(st.position['entry'] for st in states.values() if st.position is not None)
    peak_capital = max(peak_capital, current_capital)


def reconcile_gap_positions():
    """For any position just restored via load_positions(), replay
    historical_data since entry to check whether SL/TP was actually hit while
    the bot was down. SL/TP are fixed at entry - no indicator dependency, so
    this only needs raw OHLC bars, not MA20/ATR14. Exit-only: does not scan
    for new signals during the gap, only resolves the restored position."""
    for sym in UNIVERSE:
        pos = states[sym].position
        if pos is None:
            continue
        token = symbol_to_token[sym]
        candles = kite.historical_data(token, from_date=pos['entry_dt'],
                                        to_date=datetime.now(), interval='5minute')
        prev_close = pos['entry']
        resolved = False
        for c in candles:
            dt = c['date'].replace(tzinfo=None)
            if dt <= pos['entry_dt']:
                continue
            if dt.date() != pos['entry_date']:
                exit_price = prev_close
                outcome = 'EOD+' if pos['entry'] - exit_price > 0 else 'EOD-'
                _log_trade(trades, sym, pos, exit_price, outcome, dt)
                resolved = True
            elif dt.hour >= EOD_HOUR:
                exit_price = c['open']
                outcome = 'EOD+' if pos['entry'] - exit_price > 0 else 'EOD-'
                _log_trade(trades, sym, pos, exit_price, outcome, dt)
                resolved = True
            elif c['high'] >= pos['sl']:
                _log_trade(trades, sym, pos, pos['sl'], 'L', dt)
                resolved = True
            elif c['low'] <= pos['tp']:
                _log_trade(trades, sym, pos, pos['tp'], 'W', dt)
                resolved = True
            if resolved:
                states[sym].position = None
                print(f'{sym}: gap-check found SL/TP hit during downtime - closed retroactively.')
                break
            prev_close = c['close']
        if not resolved:
            print(f'{sym}: gap-check found no SL/TP hit - position remains open.')
    save_positions()
    save_trades()
    update_peak_capital()


def print_pnl_summary(bucket_dt):
    """Trailing footer: Trades = total positions taken today (closed + still-open),
    Closed = just the closed count, Open = still-open count. Pcap = peak concurrent
    capital seen all day (see update_peak_capital()), Tcap = total capital committed
    across every trade opened today, closed or still open (sum of entry prices -
    reused capital from closed trades is NOT subtracted out, unlike Pcap)."""
    with lock:
        n_open = sum(1 for s in states.values() if s.position is not None)
        n_closed = len(trades)
        wins = sum(1 for t in trades if t['pnl'] > 0)
        losses = n_closed - wins
        total_pnl = sum(t['pnl'] for t in trades)
        total_zpnl = sum(t['zpnl'] for t in trades)
        total_capital = sum(t['entry'] for t in trades) + sum(
            st.position['entry'] for st in states.values() if st.position is not None)
    print(f"  === [{bucket_dt}] PnL Summary===")
    print(f"  === Trades={n_closed + n_open}  Closed={n_closed}  Open={n_open}  "
          f"Wins={wins}  Losses={losses}  PnL={total_pnl:+.2f}  ZPnL={total_zpnl:+.2f}  "
          f"Pcap={peak_capital:.2f}  Tcap={total_capital:.2f} ===")


def finalize_bar(sym, bar):
    global last_summary_bucket, bucket_stocks_seen
    with lock:
        bar_log_rows.append({'symbol': sym, 'datetime': bar['datetime'], 'open': bar['open'],
                              'high': bar['high'], 'low': bar['low'], 'close': bar['close']})
        process_bar(sym, bar, states[sym], trades)
        save_positions()
        save_trades()
        update_peak_capital()
    pos = states[sym].position
    tag = f"OPEN sl={pos['sl']:.2f} tp={pos['tp']:.2f}" if pos else 'flat'
    print(f"{bar['datetime']}  {sym:12s}  O={bar['open']:.2f} H={bar['high']:.2f} "
          f"L={bar['low']:.2f} C={bar['close']:.2f}  -> {tag}")

    # PnL summary, printed once as a trailing footer after every stock in UNIVERSE has
    # finalized its bar for this bucket - not per-stock, to keep the log readable, and
    # not on the first stock (which buried it at the top of each bucket's block).
    if bar['datetime'] != last_summary_bucket:
        last_summary_bucket = bar['datetime']
        bucket_stocks_seen = set()
    bucket_stocks_seen.add(sym)

    if len(bucket_stocks_seen) >= len(UNIVERSE):
        print_pnl_summary(bar['datetime'])


def on_ticks(ws, ticks):
    for t in ticks:
        sym = token_to_symbol.get(t['instrument_token'])
        if sym is None:
            continue
        price = t['last_price']
        ts = t.get('exchange_timestamp') or datetime.now()

        # Discard pre-open auction ticks (~09:00-09:08) - they aren't real candles and
        # don't exist in historical_data, so letting them into forming_bar/process_bar
        # would pollute MA20/ATR14 with bars the backtest never sees.
        if (ts.hour, ts.minute) < MARKET_OPEN:
            continue

        b = bucket_start(ts)

        # Discard any tick still belonging to (or older than) the bucket that was
        # forming at connect time - that bucket is handled by catchup_bucket()
        # once it genuinely closes, not by live ticks (avoids building a partial bar
        # from incomplete tick coverage, and avoids double-counting it).
        if current_bucket is not None and b <= current_bucket:
            continue

        # Also always discard ticks for the market-open bucket itself, regardless of
        # connect time - it's the day's densest tick window, where a throttled/snapshot
        # WebSocket feed can miss the true opening trade or an early high wick that Kite's
        # official candle (full trade tape) would catch. catchup_bucket() sources it from
        # historical_data instead, once it closes (scheduled in __main__).
        if market_open_bucket is not None and b == market_open_bucket:
            continue

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
            if not eod_reached.is_set():
                eod_reached.set()
                print(f"{ts}  EOD_HOUR reached ({EOD_HOUR}:00) - no more entries, bot will stop once positions are flat.")
            pos = state.position
            if pos is not None:
                pnl = pos['entry'] - price
                zpnl = pnl - zerodha_short(pos['entry'], price)
                outcome = 'EOD+' if pnl > 0 else 'EOD-'
                with lock:
                    trades.append({'symbol': sym, 'entry_dt': pos['entry_dt'], 'entry': pos['entry'],
                                    'sl': pos['sl'], 'tp': pos['tp'], 'exit_dt': ts,
                                    'exit_price': price, 'outcome': outcome, 'pnl': pnl, 'zpnl': zpnl})
                    state.position = None
                    state.tick_exit_pending_bar = b
                    save_positions()
                    save_trades()
                    update_peak_capital()
                print(f"{ts}  {sym:12s}  TICK EXIT ({outcome}) @ {price:.2f}  pnl={pnl:.2f}  zpnl={zpnl:.2f}")
            state.pending_entry = None  # no new entries once EOD hour is reached

        # Real-time exit monitoring - ticks, not waiting for bar close
        pos = state.position
        if pos is not None:
            if price >= pos['sl']:
                pnl = pos['entry'] - pos['sl']
                zpnl = pnl - zerodha_short(pos['entry'], pos['sl'])
                with lock:
                    trades.append({'symbol': sym, 'entry_dt': pos['entry_dt'], 'entry': pos['entry'],
                                    'sl': pos['sl'], 'tp': pos['tp'], 'exit_dt': ts,
                                    'exit_price': pos['sl'], 'outcome': 'L', 'pnl': pnl, 'zpnl': zpnl})
                    state.position = None
                    state.tick_exit_pending_bar = forming_bar[sym]['bucket']
                    save_positions()
                    save_trades()
                    update_peak_capital()
                print(f"{ts}  {sym:12s}  TICK EXIT (SL) @ {pos['sl']:.2f}  pnl={pnl:.2f}  zpnl={zpnl:.2f}")
            elif price <= pos['tp']:
                pnl = pos['entry'] - pos['tp']
                zpnl = pnl - zerodha_short(pos['entry'], pos['tp'])
                with lock:
                    trades.append({'symbol': sym, 'entry_dt': pos['entry_dt'], 'entry': pos['entry'],
                                    'sl': pos['sl'], 'tp': pos['tp'], 'exit_dt': ts,
                                    'exit_price': pos['tp'], 'outcome': 'W', 'pnl': pnl, 'zpnl': zpnl})
                    state.position = None
                    state.tick_exit_pending_bar = forming_bar[sym]['bucket']
                    save_positions()
                    save_trades()
                    update_peak_capital()
                print(f"{ts}  {sym:12s}  TICK EXIT (TP) @ {pos['tp']:.2f}  pnl={pnl:.2f}  zpnl={zpnl:.2f}")


def on_connect(ws, response):
    print('Connected. Subscribing...')
    tokens = list(symbol_to_token.values())
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_FULL, tokens)


def on_close(ws, code, reason):
    print(f'Connection closed: {code} {reason}')


def on_reconnect(ws, attempts_count):
    print(f'Reconnecting (attempt {attempts_count})... re-warming indicators to patch any gap.')
    warmup()
    catchup_at = current_bucket + timedelta(minutes=CATCHUP_DELAY_MIN)
    catchup_delay = max(0, (catchup_at - datetime.now()).total_seconds())
    print(f'Catch-up for bucket {current_bucket} scheduled at {catchup_at} ({catchup_delay:.0f}s from now).')
    threading.Timer(catchup_delay, catchup_bucket, args=(current_bucket,)).start()


if __name__ == '__main__':
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    load_existing_logs()
    warmup()
    load_positions()
    reconcile_gap_positions()

    catchup_at = current_bucket + timedelta(minutes=CATCHUP_DELAY_MIN)
    catchup_delay = max(0, (catchup_at - datetime.now()).total_seconds())
    print(f'Catch-up for bucket {current_bucket} scheduled at {catchup_at} ({catchup_delay:.0f}s from now).')
    threading.Timer(catchup_delay, catchup_bucket, args=(current_bucket,)).start()

    if market_open_bucket > current_bucket:
        mo_catchup_at = market_open_bucket + timedelta(minutes=CATCHUP_DELAY_MIN)
        mo_catchup_delay = max(0, (mo_catchup_at - datetime.now()).total_seconds())
        print(f'Catch-up for market-open bucket {market_open_bucket} scheduled at '
              f'{mo_catchup_at} ({mo_catchup_delay:.0f}s from now).')
        threading.Timer(mo_catchup_delay, catchup_bucket, args=(market_open_bucket,)).start()

    kws = KiteTicker(API_KEY, ACCESS_TOKEN)
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_close = on_close
    kws.on_reconnect = on_reconnect

    print('Connecting to KiteTicker...')
    kws.connect(threaded=True)

    eod_grace_cycles_left = None  # set once eod_reached fires, counts down before auto-stop
    natural_eod_stop = False  # True only if we exit via the EOD break, not Ctrl+C

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

            if eod_reached.is_set():
                # Grace period: give every symbol a chance to individually cross the
                # EOD bucket and close its own position before we actually stop.
                if eod_grace_cycles_left is None:
                    eod_grace_cycles_left = 2
                elif eod_grace_cycles_left <= 0:
                    print('EOD reached and all positions flat - auto-stopping.')
                    natural_eod_stop = True
                    break
                else:
                    eod_grace_cycles_left -= 1
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

    if natural_eod_stop:
        archive_daily_logs()
