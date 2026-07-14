import json
import pandas as pd
from liquidity_sweep_logic import identify_signals

with open('hdfcbank_5min_snapshot.json') as f:
    data = json.load(f)

df = pd.DataFrame(data['bars'])
df = df.set_index('time', drop=False)

result = identify_signals(df, N=2, lookback=20)

sweeps = result[result['is_sweep']]
buys = result[result['is_buy_signal']]

print(f"Total bars       : {len(result)}")
print(f"Swing lows found : {result['is_swing_low'].sum()}")
print(f"Sweeps found     : {len(sweeps)}")
print(f"Buy signals found: {len(buys)}")
print()

print("=== SWEEP CANDLES ===")
for idx, row in sweeps.iterrows():
    print(f"time={int(row['time'])}  low={row['low']}  close={row['close']}  ref_swing_low={row['ref_swing_low_level']}")

print()
print("=== BUY SIGNALS ===")
for idx, row in buys.iterrows():
    print(f"time={int(row['time'])}  close={row['close']}  ref_swing_low={row['ref_swing_low_level']}")

# dump full drawable payload for the draw step
drawable = []
for idx, row in result.iterrows():
    if row['is_sweep'] or row['is_buy_signal']:
        drawable.append({
            'time': int(row['time']),
            'open': row['open'], 'high': row['high'], 'low': row['low'], 'close': row['close'],
            'is_sweep': bool(row['is_sweep']),
            'is_buy_signal': bool(row['is_buy_signal']),
            'ref_swing_low_level': row['ref_swing_low_level'],
        })

with open('drawable_signals.json', 'w') as f:
    json.dump(drawable, f, indent=2)

print(f"\nWrote {len(drawable)} drawable signal bars to drawable_signals.json")
