"""
MA Rejection v1 (SHORT) — shared core logic.
Data-source agnostic: both the offline engine (DS3 replay) and the live engine
(KiteTicker) feed bars into process_bar(). Nothing here knows or cares where a
bar came from.
"""
from collections import deque

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
        self.prev_dt = None
        self.position = None        # {'entry','sl','tp','entry_date','entry_dt'}
        self.pending_entry = None   # {'touch_date','atr'}
        self.tick_exit_pending_bar = None  # bucket datetime of a live tick-triggered exit

    def ma20(self):
        return sum(self.closes) / len(self.closes) if len(self.closes) == MA_PERIOD else None

    def atr14(self):
        return sum(self.trs) / len(self.trs) if len(self.trs) == ATR_PERIOD else None


def is_shortable(symbol):
    # Offline replay / not-yet-wired live check: always allowed.
    # TODO: real MIS/ASM-GSM check before firing a live entry.
    return True


def update_indicators(bar, state):
    """Rolling MA20/ATR14 update only — no signal/position logic. Used both by
    process_bar() and by warm-up (which must not trigger entries on stale bars)."""
    if state.prev_close is not None:
        tr = max(bar['high'] - bar['low'],
                  abs(bar['high'] - state.prev_close),
                  abs(bar['low'] - state.prev_close))
        state.trs.append(tr)
    state.closes.append(bar['close'])
    state.prev_close = bar['close']
    state.prev_dt = bar['datetime']


def process_bar(symbol, bar, state, trades):
    """One bar-close event for one stock. Mirrors the reference backtest's exit
    priority (date-change -> hour>=EOD -> SL -> TP) and position-guard rule
    (a bar where a trade closes is never itself checked for a new touch)."""
    just_exited = False

    if state.tick_exit_pending_bar == bar['datetime']:
        just_exited = True
        state.tick_exit_pending_bar = None

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

    update_indicators(bar, state)
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
            and ma20 is not None and atr14 is not None and is_shortable(symbol)
            and bar['high'] >= ma20 and bar['open'] < ma20 and bar['close'] < ma20
            and bar['hour'] < EOD_HOUR):
        state.pending_entry = {'touch_date': bar['date'], 'atr': atr14}


def _log_trade(trades, symbol, pos, exit_price, outcome, exit_dt):
    pnl = pos['entry'] - exit_price
    trades.append({
        'symbol': symbol, 'entry_dt': pos['entry_dt'], 'entry': pos['entry'],
        'sl': pos['sl'], 'tp': pos['tp'], 'exit_dt': exit_dt,
        'exit_price': exit_price, 'outcome': outcome, 'pnl': pnl,
    })
