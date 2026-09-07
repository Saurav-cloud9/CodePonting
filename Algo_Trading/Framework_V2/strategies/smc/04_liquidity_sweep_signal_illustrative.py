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


# ─── STEP 4: PLUG INTO BACKTEST LOOP ───────────────────
# Basic usage example — swap df with your real OHLCV data

def run_backtest(df, N=2, lookback=20, target_pct=0.02, sl_pct=0.01):
    """
    df         : OHLCV DataFrame (columns: open, high, low, close, volume)
    N          : swing low sensitivity (2 or 3 recommended)
    lookback   : candles to look back for swing low
    target_pct : take profit % above entry (e.g. 0.02 = 2%)
    sl_pct     : stop loss % below entry  (e.g. 0.01 = 1%)
    """
    # detect swing lows
    df['is_swing_low'] = find_swing_lows(df, N=N)

    # detect sweeps
    df['is_sweep'] = find_liquidity_sweeps(
        df, df['is_swing_low'], lookback=lookback
    )

    # detect buy signals
    df['is_buy_signal'] = find_buy_signals(
        df, df['is_sweep'], df['is_swing_low'], lookback=lookback
    )

    # simulate trades
    trades = []
    for i in range(len(df)):
        if not df['is_buy_signal'].iloc[i]:
            continue

        entry  = df.iloc[i]['close']
        target = entry * (1 + target_pct)
        sl     = entry * (1 - sl_pct)
        result = None

        # check forward candles for outcome
        for j in range(i + 1, min(i + 50, len(df))):
            high = df.iloc[j]['high']
            low  = df.iloc[j]['low']
            if high >= target:
                result = 'WIN'
                break
            if low <= sl:
                result = 'LOSS'
                break

        if result:
            trades.append({
                'entry_time' : df.index[i],
                'entry_price': entry,
                'target'     : target,
                'sl'         : sl,
                'result'     : result
            })

    # print summary
    trades_df  = pd.DataFrame(trades)
    if trades_df.empty:
        print("No trades found.")
        return trades_df

    wins       = (trades_df['result'] == 'WIN').sum()
    losses     = (trades_df['result'] == 'LOSS').sum()
    win_rate   = wins / len(trades_df) * 100
    pf         = (wins * target_pct) / (losses * sl_pct) if losses > 0 else float('inf')

    print(f"Total Trades : {len(trades_df)}")
    print(f"Wins         : {wins}  |  Losses: {losses}")
    print(f"Win Rate     : {win_rate:.1f}%")
    print(f"Profit Factor: {pf:.2f}")

    return trades_df


# ─── USAGE ─────────────────────────────────────────────
# df = pd.read_parquet('BHARTIARTL_5min.parquet')
# df.columns = [c.lower() for c in df.columns]
# results = run_backtest(df, N=2, lookback=20,
#                        target_pct=0.02, sl_pct=0.01)
# print(results.head(20))
