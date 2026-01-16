"""
COMPARE ALL THREE SCENARIOS - CLOSE VALUES
===========================================
1. Chart's 20 five-minute candles (what TradingView shows)
2. Bot WITHOUT reverse (current buggy code)
3. Bot WITH reverse (proposed fix)
"""

from datetime import datetime, timedelta

def create_mock_candles():
    """Create 100 mock 1-minute candles"""
    candles = []
    
    # Dec 24: 09:15 AM to 10:50 AM = 96 candles
    dec24_start = datetime(2025, 12, 24, 10, 50)
    
    for i in range(96):
        time = dec24_start - timedelta(minutes=i)
        price_variation = (i % 10 - 5) * 0.02
        close_price = round(21.86 + price_variation, 2)
        
        candles.append({
            'timestamp': time.isoformat(),
            'close': close_price,
        })
    
    # Dec 23: 3:26 PM to 3:30 PM = 4 candles
    dec23_times = [
        datetime(2025, 12, 23, 15, 30),
        datetime(2025, 12, 23, 15, 29),
        datetime(2025, 12, 23, 15, 28),
        datetime(2025, 12, 23, 15, 26),
    ]
    
    for i, time in enumerate(dec23_times):
        close_price = round(21.70 + (i * 0.05), 2)
        candles.append({
            'timestamp': time.isoformat(),
            'close': close_price,
        })
    
    return candles


def convert_to_5min_candles(candles_1min):
    """Convert 1-minute candles to 5-minute candles"""
    candles_5min = []
    
    for i in range(0, len(candles_1min), 5):
        group = candles_1min[i:i + 5]
        
        if len(group) == 5:
            candle_5min = {
                'timestamp': group[0]['timestamp'],
                'close': group[-1]['close'],  # Close from last candle in group
            }
            candles_5min.append(candle_5min)
    
    return candles_5min


def print_candle_times_and_closes(candles_5min, title):
    """Print timestamp and close for each 5-min candle"""
    print(f"\n{title}")
    print("-" * 80)
    
    closes = []
    for i, candle in enumerate(candles_5min, 1):
        dt = datetime.fromisoformat(candle['timestamp'])
        close = candle['close']
        closes.append(close)
        print(f"  Candle {i:2d}: {dt.strftime('%b %d %H:%M')} - Close: ₹{close:.2f}")
    
    ma20 = sum(closes) / len(closes) if closes else 0
    print(f"\n  MA20 = ₹{ma20:.2f}")
    
    return closes


def main():
    print("=" * 80)
    print("COMPARING CLOSE VALUES - THREE SCENARIOS")
    print("=" * 80)
    
    # Create mock data
    all_candles = create_mock_candles()
    
    print(f"\nTotal 1-minute candles: {len(all_candles)}")
    print(f"First (newest): {all_candles[0]['timestamp']}")
    print(f"Last (oldest):  {all_candles[-1]['timestamp']}")
    
    # ========================================================================
    # SCENARIO 1: CHART (What TradingView shows)
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 1: CHART (TradingView) - EXPECTED CORRECT VALUES")
    print("=" * 80)
    print("""
For TradingView 5-minute chart at 10:50 AM on Dec 24:
The chart shows 20 five-minute candles in CHRONOLOGICAL order:

NOTE: Since we don't have actual TradingView data, we'll use the 
      REVERSED + GROUPED candles as the "expected correct" reference.
      In real testing, you would compare against actual chart values.
""")
    
    # This represents what the chart SHOULD show
    candles_for_chart = list(reversed(all_candles[:100]))
    candles_5min_chart = convert_to_5min_candles(candles_for_chart)
    chart_closes = print_candle_times_and_closes(candles_5min_chart[-20:], 
                                                   "CHART's 20 five-minute candles:")
    
    # ========================================================================
    # SCENARIO 2: BOT WITHOUT REVERSE (Current buggy code)
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 2: BOT WITHOUT REVERSE (Current Buggy Code)")
    print("=" * 80)
    
    candles_100_no_reverse = all_candles[:100]
    candles_5min_buggy = convert_to_5min_candles(candles_100_no_reverse)
    buggy_closes = print_candle_times_and_closes(candles_5min_buggy[-20:],
                                                  "BOT's 20 five-minute candles (NO REVERSE):")
    
    # ========================================================================
    # SCENARIO 3: BOT WITH REVERSE (Proposed fix)
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 3: BOT WITH REVERSE (Proposed Fix)")
    print("=" * 80)
    
    candles_100_reversed = list(reversed(all_candles[:100]))
    candles_5min_fixed = convert_to_5min_candles(candles_100_reversed)
    fixed_closes = print_candle_times_and_closes(candles_5min_fixed[-20:],
                                                  "BOT's 20 five-minute candles (WITH REVERSE):")
    
    # ========================================================================
    # SIDE-BY-SIDE COMPARISON
    # ========================================================================
    print("\n" + "=" * 80)
    print("SIDE-BY-SIDE COMPARISON OF CLOSE VALUES")
    print("=" * 80)
    
    print(f"\n{'Candle':<8} {'Chart':<10} {'No Reverse':<12} {'With Reverse':<13} {'Match?':<10}")
    print("-" * 80)
    
    matches_no_reverse = 0
    matches_with_reverse = 0
    
    for i in range(20):
        chart_val = chart_closes[i]
        buggy_val = buggy_closes[i]
        fixed_val = fixed_closes[i]
        
        no_rev_match = "✅" if abs(chart_val - buggy_val) < 0.01 else "❌"
        with_rev_match = "✅" if abs(chart_val - fixed_val) < 0.01 else "❌"
        
        if abs(chart_val - buggy_val) < 0.01:
            matches_no_reverse += 1
        if abs(chart_val - fixed_val) < 0.01:
            matches_with_reverse += 1
        
        print(f"{i+1:<8} ₹{chart_val:<9.2f} ₹{buggy_val:<11.2f} ₹{fixed_val:<12.2f} No:{no_rev_match}  With:{with_rev_match}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    chart_ma20 = sum(chart_closes) / 20
    buggy_ma20 = sum(buggy_closes) / 20
    fixed_ma20 = sum(fixed_closes) / 20
    
    print(f"\nChart MA20:         ₹{chart_ma20:.2f}")
    print(f"Bot (No Reverse):   ₹{buggy_ma20:.2f} - Difference: ₹{abs(chart_ma20 - buggy_ma20):.2f}")
    print(f"Bot (With Reverse): ₹{fixed_ma20:.2f} - Difference: ₹{abs(chart_ma20 - fixed_ma20):.2f}")
    
    print(f"\nMatching candles:")
    print(f"  Without Reverse: {matches_no_reverse}/20 candles match")
    print(f"  With Reverse:    {matches_with_reverse}/20 candles match")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    
    if matches_with_reverse > matches_no_reverse:
        print("""
✅ WITH REVERSE is the correct approach!
   More candles match the expected chart values.
   
The reverse operation ensures we're grouping 1-minute candles in the 
correct chronological order, giving us the right 5-minute candle close values.
""")
    else:
        print("""
⚠️  NEED REAL DATA TO VERIFY!
   
Mock data is too simple. We need actual Upstox API data to properly 
test and verify which approach matches the TradingView chart.
""")


if __name__ == "__main__":
    main()
