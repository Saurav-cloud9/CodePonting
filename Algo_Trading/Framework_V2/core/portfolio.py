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


class Portfolio:
    def __init__(
            self,
            capital=1000000,
            risk_per_trade=0.01,
            atr_mult_stop=1.0,
            rr_target=2.0,
            max_hold_bars=80,
            num_stocks=30
    ):
        self.initial_capital = capital
        self.cash = capital
        self.risk_per_trade = risk_per_trade
        self.atr_mult_stop = atr_mult_stop
        self.rr_target = rr_target
        self.max_hold_bars = max_hold_bars
        self.capital_per_stock = capital / num_stocks
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
        entry = signal["entry_price"]
        entry_time = signal["datetime"]  # matches strategy output

        # Get ATR from bar data (not passed separately)
        atr = bar["atr_14"]

        # Position sizing
        stop_dist = atr * self.atr_mult_stop
        risk_amt = self.initial_capital * self.risk_per_trade
        if stop_dist <= 0:  # Also catches negative ATR (data corruption)
            stop_dist = entry * 0.01  # 1% fallback
        max_qty_by_capital = int(self.capital_per_stock / entry)
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
            "status": "open"
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
                # v1.4.5 intra-bar sequence logic: check SL/TP based on candle direction
                # Bullish candle likely went: Open -> Low -> High -> Close (check SL first)
                # Bearish candle likely went: Open -> High -> Low -> Close (check TP first)
                is_bullish = bar.close > bar.open

                if is_bullish:
                    # Bullish: dipped first, then rallied — check SL first
                    if bar.low <= pos["stop"]:
                        exit_price = pos["stop"]
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
                        exit_price = pos["stop"]
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
        pnl = (exit_price - pos["entry_price"]) * pos["qty"]
        self.cash += pnl

        self.trades.append({
            "entry_time": pos["entry_time"],
            "exit_time": exit_time,
            "entry": pos["entry_price"],
            "exit": exit_price,
            "qty": pos["qty"],
            "pnl": pnl,
            "reason": reason,
            "ma20": pos["ma20"]  # Include for analysis
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