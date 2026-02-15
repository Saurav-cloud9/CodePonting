import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, r'C:\Users\saurav\CodePonting\Algo_Trading\Framework_V1')

from core.indicators import add_intraday_indicators

df = pd.read_parquet(
    r'C:\Users\saurav\CodePonting\Algo_Trading\Framework_V1\data\historical\intraday_5min\TATASTEEL.parquet')
df = add_intraday_indicators(df)

# June 28 end-of-day
june28 = df[(df['datetime'] >= '2024-06-28 15:00') &
            (df['datetime'] <= '2024-06-28 15:30')]

print("June 28 closing - checking for MA20 touches:")
for idx, row in june28.iterrows():
    if pd.notna(row['ma20']):
        touch = "✓ TOUCH" if row['low'] <= row['ma20'] else ""
        print(
            f"{row['datetime']} | Low: {row['low']:.2f} | MA20: {row['ma20']:.2f} | Close: {row['close']:.2f} {touch}")

        # If touch, check if close reclaims
        if row['low'] <= row['ma20'] and row['close'] > row['ma20']:
            print(f"  → RECLAIM on same candle! Close {row['close']:.2f} > MA20 {row['ma20']:.2f}")
            print(f"  → Next candle (July 1 09:15) would get entry signal")