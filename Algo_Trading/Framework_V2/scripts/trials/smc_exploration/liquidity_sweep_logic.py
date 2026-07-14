import pandas as pd
import numpy as np

# ─── STEP 1: IDENTIFY SWING LOWS ───────────────────────
# A candle is a swing low if its low is lower than
# N candles on both left AND right side.
# N is a tunable parameter (recommend N=2 or N=3 for fv2)

def find_swing_lows(df, N=2):
    """
    df   : DataFrame with at least a 'low' column
    N    : number of candles to check on each side
    returns: Series of booleans (True = swing low at that index)
    """
    lows = df['low'].values
    swing_low = np.zeros(len(lows), dtype=bool)

    for i in range(N, len(lows) - N):
        left  = lows[i - N : i]       # N candles to the left
        right = lows[i + 1 : i + N + 1]  # N candles to the right
        if lows[i] < left.min() and lows[i] < right.min():
            swing_low[i] = True

    return pd.Series(swing_low, index=df.index)


# ─── STEP 2: DETECT LIQUIDITY SWEEP ────────────────────
# A sweep happens when:
#   - Price wicks BELOW a recent confirmed swing low
#   - But the candle CLOSES back ABOVE that swing low
# This means stops were triggered but buyers stepped in.

def find_liquidity_sweeps(df, swing_low_series, lookback=20):
    """
    df                : DataFrame with OHLC columns
    swing_low_series  : boolean Series from find_swing_lows()
    lookback          : how many candles back to look for a
                        recent swing low (default 20)
    returns: Series of booleans (True = sweep candle at index)
    """
    sweep = np.zeros(len(df), dtype=bool)
    swing_low_indices = df.index[swing_low_series].tolist()

    for i in range(len(df)):
        current = df.iloc[i]

        # find the most recent swing low within lookback window
        recent_swings = [
            idx for idx in swing_low_indices
            if 0 < (i - df.index.get_loc(idx)) <= lookback
        ]
        if not recent_swings:
            continue

        # get the most recent swing low level
        latest_swing_idx  = recent_swings[-1]
        swing_low_level   = df.loc[latest_swing_idx, 'low']

        # sweep condition:
        # wick goes BELOW swing low but candle CLOSES above it
        wick_below  = current['low']   < swing_low_level
        close_above = current['close'] > swing_low_level

        if wick_below and close_above:
            sweep[i] = True

    return pd.Series(sweep, index=df.index)


# ─── STEP 3: GENERATE BUY SIGNAL ───────────────────────
# Buy signal fires on the candle AFTER the sweep candle,
# if that candle also closes above the swing low level.
# (two-candle confirmation: sweep + follow-through)

def find_buy_signals(df, sweep_series, swing_low_series, lookback=20):
    """
    returns: Series of booleans (True = buy signal at index)
    """
    buy_signal = np.zeros(len(df), dtype=bool)
    swing_low_indices = df.index[swing_low_series].tolist()

    for i in range(1, len(df)):
        # previous candle must be a sweep
        if not sweep_series.iloc[i - 1]:
            continue

        # find the swing low level again
        recent_swings = [
            idx for idx in swing_low_indices
            if 0 < (i - df.index.get_loc(idx)) <= lookback
        ]
        if not recent_swings:
            continue

        swing_low_level = df.loc[recent_swings[-1], 'low']

        # current candle must close above the swing low
        if df.iloc[i]['close'] > swing_low_level:
            buy_signal[i] = True

    return pd.Series(buy_signal, index=df.index)


def identify_signals(df, N=2, lookback=20):
    """
    Runs the full pipeline and returns df with is_swing_low,
    is_sweep, is_buy_signal columns, plus the swing_low_level
    used for each sweep/buy signal (for drawing purposes).
    """
    df = df.copy()
    df['is_swing_low'] = find_swing_lows(df, N=N)
    df['is_sweep'] = find_liquidity_sweeps(df, df['is_swing_low'], lookback=lookback)
    df['is_buy_signal'] = find_buy_signals(df, df['is_sweep'], df['is_swing_low'], lookback=lookback)

    # attach the swing_low_level each sweep/buy signal referenced (for chart drawing)
    swing_low_indices = df.index[df['is_swing_low']].tolist()
    ref_level = [None] * len(df)
    for i in range(len(df)):
        recent_swings = [
            idx for idx in swing_low_indices
            if 0 < (i - df.index.get_loc(idx)) <= lookback
        ]
        if recent_swings:
            ref_level[i] = df.loc[recent_swings[-1], 'low']
    df['ref_swing_low_level'] = ref_level

    return df
