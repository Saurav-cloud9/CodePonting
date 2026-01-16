"""
TEST BOUNCE LOGIC - BHARTIARTL JAN 2022
Manually verify TRUE bounce detection with real data
"""

import upstox_client
import pandas as pd
from datetime import datetime

# ============================================
# CONFIG
# ============================================
ACCESS_TOKEN = "YOUR_TOKEN_HERE"  # Update this!

BHARTIARTL = "NSE_EQ|INE397D01024"
TEST_DATE = "2022-01-10"  # Random trading day in Jan 2022

# ============================================
# FETCH DATA
# ============================================
config = upstox_client.Configuration()
config.access_token = ACCESS_TOKEN

api = upstox_client.HistoryV3Api(upstox_client.ApiClient(config))

print("=" * 80)
print(f"FETCHING BHARTIARTL DATA - {TEST_DATE}")
print("=" * 80)

response = api.get_historical_candle_data1(
    instrument_key=BHARTIARTL,
    unit="minutes",
    interval="5",
    to_date=TEST_DATE,
    from_date=TEST_DATE
)

candles = response.data.candles
df = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])

# CRITICAL: Reverse to chronological order
df = df[::-1].reset_index(drop=True)

print(f"✅ Got {len(df)} 5-minute candles")
print(f"✅ Time range: {df.iloc[0]['datetime']} to {df.iloc[-1]['datetime']}")

# ============================================
# CALCULATE MA20
# ============================================
df['ma20'] = df['close'].rolling(20).mean()

# ============================================
# TRACE BOUNCE DETECTION
# ============================================
print("\n" + "=" * 80)
print("BOUNCE DETECTION TEST (TRUE LOGIC)")
print("=" * 80)

bounce_count = 0

for i in range(20, len(df)):
    row = df.iloc[i]
    
    if pd.isna(row['ma20']):
        continue
    
    # STEP 1: TOUCH CHECK
    if row['low'] <= row['ma20']:
        print(f"\n🔍 CANDLE {i} ({row['datetime']}):")
        print(f"   Low: ₹{row['low']:.2f} | MA20: ₹{row['ma20']:.2f}")
        print(f"   ✅ TOUCH DETECTED (low <= MA20)")
        
        # STEP 2: BOUNCE CHECK (current + next 3)
        ma20_at_touch = row['ma20']
        bounced = False
        
        for j in range(i, min(i + 4, len(df))):
            bounce_candle = df.iloc[j]
            
            print(f"\n   Checking candle {j} for bounce:")
            print(f"      Close: ₹{bounce_candle['close']:.2f} vs MA20: ₹{ma20_at_touch:.2f}")
            
            if bounce_candle['close'] > ma20_at_touch:
                print(f"      🎯 BOUNCE CONFIRMED!")
                print(f"      Entry Time: {bounce_candle['datetime']}")
                print(f"      Entry Price: ₹{bounce_candle['close']:.2f}")
                print(f"      Distance from MA20: +{((bounce_candle['close'] - ma20_at_touch) / ma20_at_touch * 100):.3f}%")
                
                # Calculate targets
                target = bounce_candle['close'] * 1.015  # 1.5%
                sl = bounce_candle['close'] * 0.995     # 0.5%
                print(f"      Target: ₹{target:.2f} (+1.5%)")
                print(f"      Stop Loss: ₹{sl:.2f} (-0.5%)")
                
                bounce_count += 1
                bounced = True
                break
        
        if not bounced:
            print(f"   ❌ NO BOUNCE - All 4 candles stayed below/at MA20")
        
        # Only show first 3 bounces to avoid spam
        if bounce_count >= 3:
            print(f"\n... (showing first 3 bounces only)")
            break

# ============================================
# SUMMARY
# ============================================
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total bounces detected: {bounce_count}")
print(f"Date tested: {TEST_DATE}")
print(f"Stock: BHARTIARTL")
print("=" * 80)

print("\n✅ TEST COMPLETE!")
print("This shows how TRUE bounce logic works on real data.")
