"""
Export candle windows for each H5 signal.
Window: T0-20 bars to exit bar+3. bar_index=0 at T0.
"""
import pandas as pd
import numpy as np
import os

SIGNALS_FILE = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\powergrid_2022_h5_signals.csv"
CSV_PATH     = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min\POWERGRID_5min.csv"
OUTPUT_FILE  = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\powergrid_2022_h5_candles.csv"

# Load OHLCV
df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip()
df['datetime'] = pd.to_datetime(df['datetime'])
df['date'] = df['datetime'].dt.date

# Compute ATR14, vol_ma20
prev_close = df['close'].shift(1)
df['tr'] = np.maximum(df['high'] - df['low'],
           np.maximum(abs(df['high'] - prev_close), abs(df['low'] - prev_close)))
df['atr14'] = df['tr'].rolling(14, min_periods=14).mean()

# Load signals
sigs = pd.read_csv(SIGNALS_FILE)
sigs.columns = sigs.columns.str.strip()
sigs['datetime'] = pd.to_datetime(sigs['datetime'])

rows = []

for _, sig in sigs.iterrows():
    sid = sig['signal_id']
    t0_dt = sig['datetime']

    # Find T0 index in full df
    matches = df.index[df['datetime'] == t0_dt].tolist()
    if not matches:
        print(f"  {sid}: T0 not found — {t0_dt}")
        continue
    T0 = matches[0]
    t0_date = df.iloc[T0]['date']

    # Recompute entry, SL, target
    atr = df.iloc[T0]['atr14']
    if pd.isna(atr):
        print(f"  {sid}: ATR NaN at T0")
        continue

    # Find bounce bar (first bar from T0 where close > ma20, same day)
    bounce_bar = None
    for j in range(T0, min(T0 + 10, len(df) - 1)):
        brow = df.iloc[j]
        if brow['date'] != t0_date:
            break
        if brow['close'] > brow['ma20']:
            bounce_bar = j
            break
    if bounce_bar is None or bounce_bar + 1 >= len(df):
        continue

    entry_bar = bounce_bar + 1
    if df.iloc[entry_bar]['date'] != t0_date:
        continue

    entry_price = df.iloc[entry_bar]['open']
    sl     = entry_price - (2.5 * atr)
    target = entry_price + (4.5 * atr)

    # Find exit bar
    exit_bar = None
    for j in range(entry_bar, len(df)):
        bar = df.iloc[j]
        if bar['date'] != t0_date:
            exit_bar = j - 1
            break
        if bar['low'] <= sl or bar['high'] >= target:
            exit_bar = j
            break
    else:
        exit_bar = len(df) - 1
    if exit_bar is None:
        exit_bar = entry_bar

    # Window: T0-20 to exit+3
    start = max(0, T0 - 10)
    end   = min(len(df) - 1, exit_bar + 3)

    for idx in range(start, end + 1):
        bar = df.iloc[idx]
        rows.append({
            'signal_id': sid,
            'bar_index':  idx - T0,
            'datetime':   bar['datetime'],
            'open':       bar['open'],
            'high':       bar['high'],
            'low':        bar['low'],
            'close':      bar['close'],
            'volume':     bar['volume'],
            'ma20':       bar['ma20'],
        })

out = pd.DataFrame(rows)
out.columns = out.columns.str.strip()
out.to_csv(OUTPUT_FILE, index=False, encoding='utf-8', lineterminator='\n')
print(f"Exported {len(out)} candle rows for {sigs.shape[0]} signals -> {OUTPUT_FILE}")
print(f"Avg candles per signal: {len(out)/sigs.shape[0]:.1f}")
