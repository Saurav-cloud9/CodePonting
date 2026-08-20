"""
ENGINE MODULE

Responsibility:
- Drive the event loop.
- Feed data events to strategy.
- Route signals to the broker adapter.
- Coordinate portfolio updates.

Rules:
- Environment-agnostic.
- No strategy-specific logic.
- No direct data source or broker calls.
- Uses adapters for all external interaction.

This is the system's core runtime.
"""

import pandas as pd

from core.strategy import BounceStrategy
from core.portfolio import Portfolio


class BacktestEngine:

    def __init__(self, data: pd.DataFrame):
        """
        data must contain:
        datetime, open, high, low, close, volume
        + indicator columns
        """
        self.df = data.reset_index(drop=True)

        self.strategy = BounceStrategy()
        self.portfolio = Portfolio()

    # =========================================================
    # MAIN RUN LOOP
    # =========================================================
    def run(self):

        df = self.df

        # -----------------------------------------------------
        # 1️⃣ Pre-compute ALL signals once (Claude fix)
        # -----------------------------------------------------
        signals = self.strategy.generate_signals(df)

        # Map signals by datetime for fast lookup
        signal_map = {}
        for s in signals:
            signal_map.setdefault(s["datetime"], []).append(s)

        # -----------------------------------------------------
        # 2️⃣ Event Loop
        # -----------------------------------------------------
        for i in range(len(df)):

            bar = df.iloc[i]
            dt = bar.datetime

            # Entries
            if dt in signal_map:
                for sig in signal_map[dt]:
                    self.portfolio.open_position(sig, bar, i)

            # Position Updates
            self.portfolio.update(bar, i)

        return self._results()

    # =========================================================
    # RESULTS
    # =========================================================
    def _results(self):

        trades = self.portfolio.trades_df()
        equity = self.portfolio.equity_series()

        stats = {
            "final_equity": equity.iloc[-1] if len(equity) else self.portfolio.cash,
            "total_trades": len(trades),
            "win_rate": (trades.pnl > 0).mean() if len(trades) else 0,
            "net_pnl": trades.pnl.sum() if len(trades) else 0,
        }

        return trades, equity, stats
