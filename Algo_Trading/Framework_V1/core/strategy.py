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

class BounceStrategy:
    def __init__(self, volume_multiplier=1.0, lookahead_candles=3):
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
        for i in range(20, n - 3):

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

        return signals
