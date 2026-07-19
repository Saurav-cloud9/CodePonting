"""
MA Rejection v1 (SHORT) — offline paper-trading engine
Structurally shaped like the live engine: one bar at a time, explicit per-stock
state, indicators computed incrementally (not read from precomputed columns),
all 30 stocks processed in strict chronological order (not stock-by-stock).
Reference logic: ma_30_rejection_v1_reference.py (array/batch backtest).
"""
import os
import glob
from collections import deque

import numpy as np
import pandas as pd

DATA_DIR  = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3'
TRADE_LOG = r'C:\Users\saurav\CodePonting\Algo_Trading\kite_oracle_papertrading\data\trades\offline_trades.csv'

SL_MULT    = 2.0
TP_MULT    = 4.5
EOD_HOUR   = 15
MA_PERIOD  = 20
ATR_PERIOD = 14


class StockState:
    def __init__(self):
        self.closes = deque(maxlen=MA_PERIOD)
        self.trs = deque(maxlen=ATR_PERIOD)
        self.prev_close = None
        self.position = None        # {'entry','sl','tp','entry_date','entry_dt'}
        self.pending_entry = None   # {'touch_date','atr'}

    def ma20(self):
        return sum(self.closes) / len(self.closes) if len(self.closes) == MA_PERIOD else None

    def atr14(self):
        return sum(self.trs) / len(self.trs) if len(self.trs) == ATR_PERIOD else None


def is_shortable(symbol):
    # Offline replay: always allowed. Live engine replaces this with a real
    # MIS/ASM-GSM check before firing an entry.
    return True


def process_bar(symbol, bar, state, trades):
    """One bar-close event for one stock. Mirrors the reference script's exit
    priority (date-change -> hour>=EOD -> SL -> TP) and position-guard rule
    (a bar where a trade closes is never itself checked for a new touch)."""
    just_exited = False

    if state.position is not None:
        pos = state.position
        if bar['date'] != pos['entry_date']:
            exit_price = state.prev_close
            outcome = 'EOD+' if pos['entry'] - exit_price > 0 else 'EOD-'
            _log_trade(trades, symbol, pos, exit_price, outcome, state.prev_dt)
            state.position = None
            just_exited = True
        elif bar['hour'] >= EOD_HOUR:
            exit_price = bar['open']
            outcome = 'EOD+' if pos['entry'] - exit_price > 0 else 'EOD-'
            _log_trade(trades, symbol, pos, exit_price, outcome, bar['datetime'])
            state.position = None
            just_exited = True
        elif bar['high'] >= pos['sl']:
            _log_trade(trades, symbol, pos, pos['sl'], 'L', bar['datetime'])
            state.position = None
            just_exited = True
        elif bar['low'] <= pos['tp']:
            _log_trade(trades, symbol, pos, pos['tp'], 'W', bar['datetime'])
            state.position = None
            just_exited = True

    # Indicators updated after exit-check (uses raw incoming bar), before signal check
    if state.prev_close is not None:
        tr = max(bar['high'] - bar['low'],
                  abs(bar['high'] - state.prev_close),
                  abs(bar['low'] - state.prev_close))
        state.trs.append(tr)
    state.closes.append(bar['close'])
    ma20, atr14 = state.ma20(), state.atr14()

    if state.pending_entry is not None:
        pend = state.pending_entry
        if bar['date'] != pend['touch_date']:
            state.pending_entry = None  # cancelled - same bar re-checked for touch below
        else:
            entry = bar['open']
            sl = entry + SL_MULT * pend['atr']
            tp = entry - TP_MULT * pend['atr']
            state.position = {'entry': entry, 'sl': sl, 'tp': tp,
                               'entry_date': bar['date'], 'entry_dt': bar['datetime']}
            state.pending_entry = None
            # entry bar is itself checked for exit, per reference script (k starts at ei)
            pos = state.position
            if bar['hour'] >= EOD_HOUR:
                _log_trade(trades, symbol, pos, bar['open'], 'EOD-', bar['datetime'])
                state.position = None
                just_exited = True
            elif bar['high'] >= sl:
                _log_trade(trades, symbol, pos, sl, 'L', bar['datetime'])
                state.position = None
                just_exited = True
            elif bar['low'] <= tp:
                _log_trade(trades, symbol, pos, tp, 'W', bar['datetime'])
                state.position = None
                just_exited = True

    if (state.position is None and state.pending_entry is None and not just_exited
            and ma20 is not None and atr14 is not None
            and bar['high'] >= ma20 and bar['open'] < ma20 and bar['close'] < ma20
            and bar['hour'] < EOD_HOUR):
        state.pending_entry = {'touch_date': bar['date'], 'atr': atr14}

    state.prev_close = bar['close']
    state.prev_dt = bar['datetime']


def _log_trade(trades, symbol, pos, exit_price, outcome, exit_dt):
    pnl = pos['entry'] - exit_price
    trades.append({
        'symbol': symbol, 'entry_dt': pos['entry_dt'], 'entry': pos['entry'],
        'sl': pos['sl'], 'tp': pos['tp'], 'exit_dt': exit_dt,
        'exit_price': exit_price, 'outcome': outcome, 'pnl': pnl,
    })


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
