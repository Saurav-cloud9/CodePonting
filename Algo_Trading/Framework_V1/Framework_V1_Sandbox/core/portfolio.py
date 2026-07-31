"""
PORTFOLIO MODULE

Responsibility:
- Track positions, cash, exposure, and PnL.
- Enforce risk constraints.
- Maintain trading state.

Rules:
- No market data access.
- No strategy decisions.
- No broker or order placement logic.

Pure state management.
"""

import pandas as pd
from datetime import time as _time

_EOD_TIME = _time(15, 0)
_TICK     = 0.05    # NSE minimum tick — applied to SL exit fills


def _compute_charges(entry, exit_price, qty, broker):
    """
    Round-trip transaction charges for NSE equity intraday.
    broker: 'upstox' (0.05% brokerage) or 'kite' (0.03% brokerage)
    """
    buy_val  = entry      * qty
    sell_val = exit_price * qty

    bkr_rate  = 0.0005 if broker == "upstox" else 0.0003
    brokerage = min(buy_val * bkr_rate, 20.0) + min(sell_val * bkr_rate, 20.0)
    stt       = sell_val * 0.00025                          # 0.025% sell-side only
    exchange  = (buy_val + sell_val) * 0.0000345            # 0.00345% per side
    sebi      = (buy_val + sell_val) * 0.000001             # 0.0001% per side
    gst       = (brokerage + exchange + sebi) * 0.18        # 18% on fees
    stamp     = buy_val * 0.00003                           # 0.003% buy-side only
    return brokerage + stt + exchange + sebi + gst + stamp


class Portfolio:
    def __init__(
            self,
            capital=1000000,
            risk_per_trade=0.01,
            atr_mult_stop=1.0,
            rr_target=2.0,
            num_stocks=30,
            sl_variant="A",
            breakeven_trigger=None,
            trailing_dist=None,
            position_guard=True,
            compounding=True,
    ):
        self.initial_capital = capital
        self.cash = capital
        self.risk_per_trade = risk_per_trade
        self.atr_mult_stop = atr_mult_stop
        self.rr_target = rr_target
        self.num_stocks = num_stocks
        self.sl_variant = sl_variant
        self.breakeven_trigger = breakeven_trigger
        self.trailing_dist = trailing_dist
        self.position_guard = position_guard
        self.compounding = compounding
        self.positions = []
        self.trades = []
        self.equity_curve = []

    # =========================================================
    # OPEN POSITION
    # =========================================================
    def open_position(self, signal, bar, bar_index):
        """
        Fixed to match strategy.py signal structure and use bar data directly
        signal dict keys: datetime, entry_price, ma20, volume, avg_volume
        bar: DataFrame row (Series) with OHLCV + indicators
        """
        # Position guard: skip if already holding a position for this stock
        if self.position_guard and self.positions:
            return

        entry = signal["entry_price"]
        entry_time = signal["datetime"]  # matches strategy output

        # Get ATR from bar data (not passed separately)
        atr = bar.atr_14

        # 7a: Entry slippage — 1 tick flat above signal open
        entry = entry + 0.05

        # Position sizing (compounding: use current cash equity, not fixed initial)
        eq        = self.cash if self.compounding else self.initial_capital
        stop_dist = atr * self.atr_mult_stop
        risk_amt  = eq * self.risk_per_trade
        if stop_dist <= 0:  # Also catches negative ATR (data corruption)
            stop_dist = entry * 0.01  # 1% fallback
        max_qty_by_capital = int((eq / self.num_stocks) / entry)
        max_qty_by_risk    = int(risk_amt / stop_dist)
        qty                = max(min(max_qty_by_capital, max_qty_by_risk), 1)

        stop = entry - stop_dist
        target = entry + stop_dist * self.rr_target

        position = {
            "entry_time": entry_time,
            "entry_idx": bar_index,
            "entry_price": entry,
            "qty": qty,
            "stop": stop,
            "target": target,
            "ma20": signal["ma20"],  # Track MA20 at entry for analysis
            "status": "open",
            "atr_at_entry": atr,
            "breakeven_moved": False,
            "trailing_stop": None,
        }
        self.positions.append(position)

    # =========================================================
    # BAR UPDATE
    # =========================================================
    def update(self, bar, bar_index):
        """
        bar: DataFrame row (Series) with OHLCV data
        """
        closed = []

        for pos in self.positions:
            if pos["status"] != "open":
                continue

            # Skip the entry candle: cannot exit on the same bar we entered
            if pos["entry_idx"] == bar_index:
                continue

            exit_price = None
            reason = None

            # EOD forced close: first bar at/after 15:00 on the entry date
            bar_dt = bar.datetime.to_pydatetime() if hasattr(bar.datetime, "to_pydatetime") else bar.datetime
            entry_dt = pos["entry_time"].to_pydatetime() if hasattr(pos["entry_time"], "to_pydatetime") else pos["entry_time"]
            if bar_dt.date() == entry_dt.date() and bar_dt.time() >= _EOD_TIME:
                exit_price = bar.open
                reason = "time"
            else:
                # ── SL variant logic: update stop BEFORE exit checks ──────────
                if self.sl_variant in ("B", "C") and not pos["breakeven_moved"]:
                    trigger = pos["entry_price"] + self.breakeven_trigger * pos["atr_at_entry"]
                    if bar.high >= trigger:
                        pos["stop"] = pos["entry_price"]
                        pos["breakeven_moved"] = True

                elif self.sl_variant == "D":
                    new_trail = bar.high - self.trailing_dist * pos["atr_at_entry"]
                    if pos["trailing_stop"] is None or new_trail > pos["trailing_stop"]:
                        pos["trailing_stop"] = new_trail
                    pos["stop"] = pos["trailing_stop"]
                    # target remains fixed (set in open_position) — only stop trails

                # v1.4.5 intra-bar sequence logic: check SL/TP based on candle direction
                # All variants (A, B, C, D) use the same candle-direction priority.
                # B/C: stop value may have changed to entry_price (breakeven), but logic is identical.
                # D: stop trails, target remains fixed — same logic applies.
                # Bullish candle likely went: Open -> Low -> High -> Close (check SL first)
                # Bearish candle likely went: Open -> High -> Low -> Close (check TP first)
                is_bullish = bar.close > bar.open

                if is_bullish:
                    # Bullish: dipped first, then rallied — check SL first
                    if bar.low <= pos["stop"]:
                        exit_price = pos["stop"] - _TICK
                        reason = "stop"
                    elif bar.high >= pos["target"]:
                        exit_price = pos["target"]
                        reason = "target"
                else:
                    # Bearish: rallied first, then dropped — check TP first
                    if bar.high >= pos["target"]:
                        exit_price = pos["target"]
                        reason = "target"
                    elif bar.low <= pos["stop"]:
                        exit_price = pos["stop"] - _TICK
                        reason = "stop"

            if exit_price:
                self._close(pos, bar.datetime, exit_price, reason)
                closed.append(pos)

        for c in closed:
            self.positions.remove(c)

        self._record_equity(bar.close)

    # =========================================================
    # CLOSE POSITION
    # =========================================================
    def _close(self, pos, exit_time, exit_price, reason):
        raw_pnl        = (exit_price - pos["entry_price"]) * pos["qty"]
        charges_upstox = _compute_charges(pos["entry_price"], exit_price, pos["qty"], "upstox")
        charges_kite   = _compute_charges(pos["entry_price"], exit_price, pos["qty"], "kite")
        self.cash += raw_pnl

        self.trades.append({
            "entry_time":     pos["entry_time"],
            "exit_time":      exit_time,
            "entry":          pos["entry_price"],
            "exit":           exit_price,
            "qty":            pos["qty"],
            "pnl":            raw_pnl,              # alias for raw_pnl (backward compat)
            "raw_pnl":        raw_pnl,
            "net_pnl_upstox": raw_pnl - charges_upstox,
            "net_pnl_kite":   raw_pnl - charges_kite,
            "reason":         reason,
            "ma20":           pos["ma20"],
        })

    # =========================================================
    # EQUITY TRACK
    # =========================================================
    def _record_equity(self, mark_price):
        unrealized = sum(
            (mark_price - p["entry_price"]) * p["qty"]
            for p in self.positions if p["status"] == "open"
        )
        self.equity_curve.append(self.cash + unrealized)

    # =========================================================
    # EXPORTS
    # =========================================================
    def trades_df(self):
        return pd.DataFrame(self.trades)

    def equity_series(self):
        return pd.Series(self.equity_curve)