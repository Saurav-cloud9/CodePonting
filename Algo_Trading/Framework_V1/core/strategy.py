"""
STRATEGY MODULE

Responsibility:
- Define pure signal logic.
- Input: data up to current time + parameters.
- Output: trading signals (buy/sell/hold).

Rules:
- NO data loading.
- NO indicator computation.
- NO execution, PnL, or portfolio state.
- NO environment awareness (backtest/paper/live).

This code must run identically in all environments.
"""

import numpy as np
import pandas as pd
from datetime import time as _time

_ENTRY_CUTOFF = _time(14, 30)

class BounceStrategy:
    def __init__(self, volume_multiplier=1.2, lookahead_candles=3):
        self.volume_multiplier = volume_multiplier
        self.lookahead_candles = lookahead_candles

    def generate_signals(self, df, filter_mas=None):
        """
        Framework-compatible port of v1.4.5 detect_bounce()
        Returns list[dict] signals identical in structure to original
        """

        signals = []

        n = len(df)

        ma20 = df["ma20"].to_numpy()
        avg_vol = df["avg_volume"].to_numpy()
        vol = df["volume"].to_numpy()
        low = df["low"].to_numpy()
        close_arr = df["close"].to_numpy()
        open_arr = df["open"].to_numpy()
        datetime_arr = df["datetime"].to_numpy()

        # --- Trend filter mask (Daily MAs) ---
        if filter_mas:
            filter_mask = np.ones(n, dtype=bool)
            for ma_col in filter_mas:
                if ma_col in df.columns:
                    ma_vals = df[ma_col].to_numpy()
                    filter_mask &= (close_arr > ma_vals) & ~np.isnan(ma_vals)
        else:
            filter_mask = np.ones(n, dtype=bool)

        # --- Bounce detection loop ---
        # Start from 0: indicators must be pre-computed on full continuous dataset
        for i in range(0, n - 3):

            if np.isnan(ma20[i]) or not filter_mask[i]:
                continue

            # Volume filter
            if not np.isnan(avg_vol[i]):
                if vol[i] < avg_vol[i] * self.volume_multiplier:
                    continue

            # Touch MA20
            if low[i] <= ma20[i]:

                ma_touch = ma20[i]

                # Look ahead up to 3 candles for reclaim
                for j in range(i, min(i + self.lookahead_candles + 1, n)):

                    if close_arr[j] > ma_touch:

                        next_idx = j + 1
                        if next_idx >= n:
                            break

                        # Discard cross-month signals: v1.4.5 processes data
                        # month-by-month, so it can never use a touch candle (i)
                        # from month M to generate an entry in month M+1.
                        # Checking i vs next_idx is strictly stronger than j vs
                        # next_idx and also covers the lookahead-crosses-month
                        # case where touch is in M-1, reclaim crosses into M, and
                        # entry lands in M (j-vs-entry check would miss those).
                        if (datetime_arr[i].year, datetime_arr[i].month) != \
                           (datetime_arr[next_idx].year, datetime_arr[next_idx].month):
                            break

                        # No new entries at or after 14:30
                        if pd.Timestamp(datetime_arr[next_idx]).time() >= _ENTRY_CUTOFF:
                            break

                        signals.append({
                            "datetime": datetime_arr[next_idx],
                            "entry_price": open_arr[next_idx],
                            "ma20": ma_touch,
                            "volume": vol[i],
                            "avg_volume": avg_vol[i],
                        })
                        break

        # In strategy.py, at the end of generate_signals()
        # Before: return signals

        # Deduplicate by entry time (keep first occurrence)
        seen_times = set()
        unique_signals = []
        for sig in signals:
            if sig["datetime"] not in seen_times:
                unique_signals.append(sig)
                seen_times.add(sig["datetime"])

        return unique_signals
