"""
TEST SCRIPT: YESBANK MA20 Calculation with Mock Data
=====================================================
Since we can't fetch live data, we'll create realistic mock data
that simulates what the API would return for Dec 24, 10:50 AM
"""

from datetime import datetime, timedelta

print("=" * 80)
print("YESBANK MA20 CALCULATION TEST - MOCK DATA")
print("=" * 80)

# Create mock candles that simulate API response
# API returns in REVERSE chronological order (newest first)
def create_mock_candles():
    """
    Create 100 mock 1-minute candles for YESBANK
    Simulating Dec 24, 10:50 AM scenario:
    
    API returns NEWEST FIRST, so:
    [0] = 10:50 AM Dec 24
    [1] = 10:49 AM Dec 24
    [2] = 10:48 AM Dec 24
    ...
    [95] = 09:16 AM Dec 24 (96th candle from Dec 24)
    [96] = 03:30 PM Dec 23 (need 4 more from previous day)
    [97] = 03:29 PM Dec 23
    [98] = 03:28 PM Dec 23
    [99] = 03:26 PM Dec 23 (100th candle - oldest)
    
    Note: Market closes at 3:30 PM, so last candle of Dec 23 is 3:30 PM
    """
    candles = []
    
    print("\nCreating mock candles for YESBANK...")
    print("Simulating API response (newest first, oldest last)")
    print("\nScenario: Dec 24, 10:50 AM")
    print("Need 100 candles:")
    
    # Dec 24: 09:15 AM to 10:50 AM = 96 candles
    # Start from 10:50 AM and go backwards
    dec24_start = datetime(2025, 12, 24, 10, 50)
    
    print(f"  - Dec 24: 09:15 AM to 10:50 AM = 96 candles")
    
    for i in range(96):
        time = dec24_start - timedelta(minutes=i)
        # Simulate realistic price movement
        price_variation = (i % 10 - 5) * 0.02  # Small variations
        close_price = round(21.86 + price_variation, 2)
        
        candles.append({
            'timestamp': time.isoformat(),
            'open': round(close_price - 0.01, 2),
            'high': round(close_price + 0.02, 2),
            'low': round(close_price - 0.02, 2),
            'close': close_price,
            'volume': 100000 + (i * 1000)
        })
    
    # Dec 23: Need 4 more candles from end of previous day
    # Market closes at 3:30 PM, so: 3:30, 3:29, 3:28, 3:26 PM
    # (Note: 3:27 would be the 4th candle but let's use 3:26 to make it exactly 100)
    
    print(f"  - Dec 23: 03:26 PM to 03:30 PM = 4 candles")
    
    dec23_times = [
        datetime(2025, 12, 23, 15, 30),  # 3:30 PM
        datetime(2025, 12, 23, 15, 29),  # 3:29 PM
        datetime(2025, 12, 23, 15, 28),  # 3:28 PM
        datetime(2025, 12, 23, 15, 26),  # 3:26 PM (skipping 3:27 for exactly 100)
    ]
    
    for i, time in enumerate(dec23_times):
        close_price = round(21.70 + (i * 0.05), 2)
        
        candles.append({
            'timestamp': time.isoformat(),
            'open': round(close_price - 0.01, 2),
            'high': round(close_price + 0.02, 2),
            'low': round(close_price - 0.02, 2),
            'close': close_price,
            'volume': 100000
        })
    
    print(f"\nCreated {len(candles)} mock candles total")
    print(f"  First candle (newest): {candles[0]['timestamp']}")
    print(f"  Last candle (oldest):  {candles[-1]['timestamp']}")
    
    return candles


def convert_to_5min_candles(candles_1min):
    """Convert 1-minute candles to 5-minute candles"""
    candles_5min = []
    
    for i in range(0, len(candles_1min), 5):
        group = candles_1min[i:i + 5]
        
        if len(group) == 5:
            candle_5min = {
                'timestamp': group[0]['timestamp'],
                'open': group[0]['open'],
                'high': max(c['high'] for c in group),
                'low': min(c['low'] for c in group),
                'close': group[-1]['close'],
                'volume': sum(c['volume'] for c in group)
            }
            candles_5min.append(candle_5min)
    
    return candles_5min


def calculate_ma20(candles_5min):
    """Calculate MA20 from 5-minute candles"""
    if len(candles_5min) < 20:
        return None
    
    last_20 = candles_5min[-20:]
    closes = [c['close'] for c in last_20]
    ma20 = sum(closes) / 20
    
    return round(ma20, 2)


def main():
    # Create mock data
    all_candles = create_mock_candles()
    
    # Show order of candles as received
    print("\n" + "=" * 80)
    print("CANDLES AS RECEIVED FROM API (newest first)")
    print("=" * 80)
    
    print("\nFirst 5 candles (newest):")
    for i in range(5):
        dt = datetime.fromisoformat(all_candles[i]['timestamp'])
        print(f"  [{i:2d}] {dt.strftime('%b %d %H:%M')} - Close: ₹{all_candles[i]['close']:.2f}")
    
    print("\nLast 5 candles (oldest):")
    for i in range(len(all_candles) - 5, len(all_candles)):
        dt = datetime.fromisoformat(all_candles[i]['timestamp'])
        print(f"  [{i:2d}] {dt.strftime('%b %d %H:%M')} - Close: ₹{all_candles[i]['close']:.2f}")
    
    # SCENARIO 1: WITHOUT REVERSING (current buggy code)
    print("\n" + "=" * 80)
    print("SCENARIO 1: WITHOUT REVERSING (CURRENT BUGGY CODE)")
    print("=" * 80)
    
    candles_5min_buggy = convert_to_5min_candles(all_candles[:100])
    
    print(f"\nCreated {len(candles_5min_buggy)} five-minute candles")
    print("\nFirst 5-min candle (from newest 5 one-min candles):")
    dt = datetime.fromisoformat(candles_5min_buggy[0]['timestamp'])
    print(f"  Timestamp: {dt.strftime('%b %d %H:%M')}")
    print(f"  Open:  ₹{candles_5min_buggy[0]['open']:.2f}")
    print(f"  Close: ₹{candles_5min_buggy[0]['close']:.2f}")
    print(f"  ❌ Problem: Open is from newest candle, Close is from 5th newest")
    print(f"  ❌ This is BACKWARDS! Should be: Open from oldest, Close from newest")
    
    ma20_buggy = calculate_ma20(candles_5min_buggy)
    print(f"\n❌ Buggy MA20 = ₹{ma20_buggy:.2f}")
    
    # SCENARIO 2: WITH REVERSING (fixed code)
    print("\n" + "=" * 80)
    print("SCENARIO 2: WITH REVERSING (FIXED CODE)")
    print("=" * 80)
    
    candles_reversed = list(reversed(all_candles[:100]))
    
    print("\nAfter reversing - First 5 candles (now oldest):")
    for i in range(5):
        dt = datetime.fromisoformat(candles_reversed[i]['timestamp'])
        print(f"  [{i:2d}] {dt.strftime('%b %d %H:%M')} - Close: ₹{candles_reversed[i]['close']:.2f}")
    
    print("\nAfter reversing - Last 5 candles (now newest):")
    for i in range(len(candles_reversed) - 5, len(candles_reversed)):
        dt = datetime.fromisoformat(candles_reversed[i]['timestamp'])
        print(f"  [{i:2d}] {dt.strftime('%b %d %H:%M')} - Close: ₹{candles_reversed[i]['close']:.2f}")
    
    candles_5min_fixed = convert_to_5min_candles(candles_reversed)
    
    print(f"\nCreated {len(candles_5min_fixed)} five-minute candles")
    print("\nFirst 5-min candle (from oldest 5 one-min candles):")
    dt = datetime.fromisoformat(candles_5min_fixed[0]['timestamp'])
    print(f"  Timestamp: {dt.strftime('%b %d %H:%M')}")
    print(f"  Open:  ₹{candles_5min_fixed[0]['open']:.2f}")
    print(f"  Close: ₹{candles_5min_fixed[0]['close']:.2f}")
    print(f"  ✅ Correct! Open from oldest candle, Close from 5th candle")
    
    ma20_fixed = calculate_ma20(candles_5min_fixed)
    print(f"\n✅ Fixed MA20 = ₹{ma20_fixed:.2f}")
    
    # COMPARISON
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print(f"\nBuggy MA20 (no reverse):  ₹{ma20_buggy:.2f}")
    print(f"Fixed MA20 (with reverse): ₹{ma20_fixed:.2f}")
    print(f"Difference:                ₹{abs(ma20_fixed - ma20_buggy):.2f}")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("""
The REVERSE operation is CRITICAL because:

1. API returns candles newest-first: [10:50, 10:49, 10:48, ...]
2. WITHOUT reverse: Groups [10:50-10:46] into first 5-min candle
   → Open = 10:50's open (WRONG - this is the END)
   → Close = 10:46's close (WRONG - this is the START)
   
3. WITH reverse: First reverse to [10:46, 10:47, 10:48, 10:49, 10:50]
   → Then groups into first 5-min candle
   → Open = 10:46's open (CORRECT - this is the START)
   → Close = 10:50's close (CORRECT - this is the END)

This is why the MA20 calculation was wrong!
    """)


if __name__ == "__main__":
    main()
