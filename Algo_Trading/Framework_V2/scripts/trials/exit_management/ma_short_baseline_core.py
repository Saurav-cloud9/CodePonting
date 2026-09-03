"""
MA Rejection v1 (SHORT) — shared core logic, exit_management baseline.
Unmodified copy of the live bot's ma_rejection_v1_core.py (synced 2026-09-02).
Data-source agnostic: both the offline engine (DS3 replay) and the live engine
(KiteTicker) feed bars into process_bar(). Nothing here knows or cares where a
bar came from. This file is the baseline every exit-management variant in this
folder branches from.
"""
from collections import deque
from datetime import time as _time

SL_MULT    = 2.0
TP_MULT    = 4.5
EOD_HOUR   = 15
MA_PERIOD  = 20
ATR_PERIOD = 14
LAST_TOUCH_TIME = _time(14, 45)  # last bar allowed to register a NEW touch - blocks 14:50
                                  # onward, so no entry can fire at 14:55 with only ~5min
                                  # before the hard EOD square-off. The old bar['hour'] <
                                  # EOD_HOUR check only had hour granularity, so it treated
                                  # all of 14:00-14:55 as equally "not yet EOD".
ENTRY_CUTOFF_TIME = _time(14, 50)  # latest bar a pending touch may convert into a real
                                    # entry on. Normally unreachable (LAST_TOUCH_TIME=14:45
                                    # caps touches, so the very next bar is always 14:50) -
                                    # this guards the edge case where a bucket gets silently
                                    # skipped (e.g. a live tick gap with no bot restart, so
                                    # catchup_range() never gets a chance to backfill it),
                                    # which would otherwise let the entry land later than
                                    # intended with even less runway before EOD. Cancels
                                    # outright (no trade, no charges) rather than entering
                                    # and immediately exiting like the EOD_HOUR>=15 branch
                                    # below does (that one still logs a charges-only-loss
                                    # "wash" trade - a separate, pre-existing behavior).


def zerodha_short(entry, exit_price):
    """Full Zerodha intraday SHORT charges: brokerage (capped 20/side) + STT (sell
    side, i.e. entry here) + transaction + SEBI + stamp (buy side, i.e. exit here)
    + GST on brokerage/txn/sebi. Same formula used throughout recon/MemLabs."""
    brok = min(0.0003 * entry, 20) + min(0.0003 * exit_price, 20)
    stt = entry * 0.00025
    txn = (entry + exit_price) * 0.0000307
    sebi = (entry + exit_price) * 0.000001
    stamp = exit_price * 0.000003
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


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
        elif bar['datetime'].time() > ENTRY_CUTOFF_TIME:
            state.pending_entry = None  # cancelled - entry bar skipped past the intended
                                         # cutoff (bucket gap); no trade, no charges, same
                                         # bar re-checked for touch below (won't re-qualify,
                                         # already past LAST_TOUCH_TIME anyway)
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
            and bar['datetime'].time() <= LAST_TOUCH_TIME):
        state.pending_entry = {'touch_date': bar['date'], 'atr': atr14}


def _log_trade(trades, symbol, pos, exit_price, outcome, exit_dt):
    pnl = pos['entry'] - exit_price
    zpnl = pnl - zerodha_short(pos['entry'], exit_price)
    trades.append({
        'symbol': symbol, 'entry_dt': pos['entry_dt'], 'entry': pos['entry'],
        'sl': pos['sl'], 'tp': pos['tp'], 'exit_dt': exit_dt,
        'exit_price': exit_price, 'outcome': outcome, 'pnl': pnl, 'zpnl': zpnl,
    })
