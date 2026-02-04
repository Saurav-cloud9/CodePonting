"""
MA20 CALCULATION TEST - WITH PROPER TIME FILTERING
===================================================
Fixes the time filtering logic to grab candles UP TO entry time.
Tests if this makes the MA20 calculation match chart values.
"""

import requests
from datetime import datetime, timedelta, timezone

# Same credentials as v0.5
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTRiNmJhNTE3ZDE3NzU2N2ViYTViODAiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NjU1MDQzNywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY2NjEzNjAwfQ.HOR8lgVnIL0BZSLZO2YUriRYy5ECT1U3ZJmrMGf61n8"
BASE_URL = "https://api.upstox.com/v2"

# Test stocks with their entry times
TEST_STOCKS = {
    "YESBANK": {
        "instrument": "NSE_EQ|INE528G01035",
        "entry_time": "10:50:00"
    },
    "TATASTEEL": {
        "instrument": "NSE_EQ|INE081A01020",
        "entry_time": "11:49:00"
    },
    "ZEEL": {
        "instrument": "NSE_EQ|INE256A01028",
        "entry_time": "11:49:00"
    }
}

# Chart MA20 values (ground truth from Upstox charts)
CHART_MA20 = {
    "YESBANK": 21.91,
    "TATASTEEL": 170.64,
    "ZEEL": 92.22
}

# ============================================
# DATA FETCHING - FIXED VERSION
# ============================================

def get_historical_candles_fixed(instrument, num_minutes=100, up_to_time=None):
    """
    Fetch historical candles from Upstox API.
    If up_to_time is provided, filter candles to only include those UP TO that time.
    
    FIXED: Properly handles IST timezone and filters correctly.
    """
    try:
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        url = f"{BASE_URL}/historical-candle/{instrument}/1minute/{to_date}/{from_date}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            candles_raw = data['data']['candles']

            # Convert to list of dicts (API returns newest first!)
            candles = []
            for candle in candles_raw:
                candles.append({
                    'timestamp': candle[0],
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                })

            # FIXED: Proper time filtering
            if up_to_time:
                # Parse the entry time
                entry_hour = int(up_to_time.split(':')[0])
                entry_minute = int(up_to_time.split(':')[1])
                entry_second = int(up_to_time.split(':')[2])
                
                print(f"  [DEBUG] Filtering candles up to: {entry_hour:02d}:{entry_minute:02d}:{entry_second:02d}")
                print(f"  [DEBUG] Total candles from API: {len(candles)}")
                
                # Filter candles that are at or before entry time
                # Upstox timestamps come in ISO format with timezone: "2024-12-24T10:50:00+05:30"
                filtered_candles = []
                for candle in candles:
                    # Parse candle timestamp
                    candle_dt = datetime.fromisoformat(candle['timestamp'].replace('Z', '+00:00'))
                    
                    # Extract just the TIME part (ignore date and timezone for comparison)
                    candle_hour = candle_dt.hour
                    candle_minute = candle_dt.minute
                    candle_second = candle_dt.second
                    
                    # Convert both to total seconds since midnight for easy comparison
                    candle_time_seconds = candle_hour * 3600 + candle_minute * 60 + candle_second
                    entry_time_seconds = entry_hour * 3600 + entry_minute * 60 + entry_second
                    
                    # Only include candles at or before entry time
                    if candle_time_seconds <= entry_time_seconds:
                        filtered_candles.append(candle)
                
                print(f"  [DEBUG] Candles after time filter: {len(filtered_candles)}")
                
                candles = filtered_candles
            
            # Take first num_minutes candles (newest, since API returns newest-first)
            result = candles[:num_minutes] if len(candles) >= num_minutes else candles
            
            if result:
                first_ts = datetime.fromisoformat(result[0]['timestamp'].replace('Z', '+00:00'))
                last_ts = datetime.fromisoformat(result[-1]['timestamp'].replace('Z', '+00:00'))
                print(f"  [DEBUG] Final candles range: {first_ts.strftime('%I:%M %p')} to {last_ts.strftime('%I:%M %p')}")
            
            return result
        else:
            print(f"  [ERROR] API returned status {response.status_code}")
            return []
            
    except Exception as e:
        print(f"  [ERROR] Exception in get_historical_candles: {e}")
        import traceback
        traceback.print_exc()
        return []


def convert_to_5min_candles(candles_1min):
    """Convert 1-minute candles to 5-minute candles"""
    candles_5min = []
    for i in range(0, len(candles_1min), 5):
        group = candles_1min[i:i + 5]
        if len(group) == 5:
            candles_5min.append({
                'timestamp': group[0]['timestamp'],
                'open': group[0]['open'],
                'high': max(c['high'] for c in group),
                'low': min(c['low'] for c in group),
                'close': group[-1]['close'],
                'volume': sum(c['volume'] for c in group)
            })
    return candles_5min


# ============================================
# MA20 CALCULATION - FIXED VERSION
# ============================================

def get_ma20_fixed(instrument, entry_time=None):
    """
    Calculate MA20 using FIXED code:
    1. Get candles up to entry time
    2. Take first 100 (newest)
    3. Reverse to chronological order
    4. Group into 5-min candles
    5. Calculate MA20 from last 20 closes
    """
    try:
        print(f"\n  Fetching candles...")
        candles_1min = get_historical_candles_fixed(instrument, 100, up_to_time=entry_time)
        
        if candles_1min is None or len(candles_1min) < 100:
            print(f"  [ERROR] Insufficient data: Only {len(candles_1min) if candles_1min else 0} candles")
            return None, None

        print(f"  [DEBUG] Got {len(candles_1min)} 1-min candles")
        
        # CRITICAL FIX: Reverse to chronological order (oldest-first) before grouping
        candles_1min.reverse()
        print(f"  [DEBUG] Reversed to chronological order")

        # Convert to 5-min candles
        candles_5min = convert_to_5min_candles(candles_1min)
        print(f"  [DEBUG] Converted to {len(candles_5min)} 5-min candles")
        
        if len(candles_5min) < 20:
            print(f"  [ERROR] Only {len(candles_5min)} 5-min candles, need 20")
            return None, None

        # Calculate MA20 from last 20 closes
        last_20_closes = [c['close'] for c in candles_5min[-20:]]
        ma20 = sum(last_20_closes) / 20

        # Get timestamps for verification
        first_timestamp = candles_1min[0]['timestamp']
        last_timestamp = candles_1min[-1]['timestamp']
        
        return round(ma20, 2), (first_timestamp, last_timestamp)

    except Exception as e:
        print(f"  [ERROR] Exception in get_ma20_fixed: {e}")
        import traceback
        traceback.print_exc()
        return None, None


# ============================================
# TEST RUNNER
# ============================================

def format_timestamp(ts):
    """Convert timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime('%I:%M %p')
    except:
        return ts


def run_fixed_test():
    """Test the FIXED MA20 calculation with proper time filtering"""
    
    print("=" * 90)
    print("MA20 CALCULATION TEST - FIXED TIME FILTERING")
    print("=" * 90)
    print("\nThis test uses PROPER time filtering to grab candles UP TO entry time.")
    print("Expected: MA20 should match chart values exactly (error < ₹0.05)\n")
    
    results = []
    
    for stock, stock_info in TEST_STOCKS.items():
        print(f"\n{'=' * 90}")
        print(f"Testing: {stock} (Entry Time: {stock_info['entry_time']})")
        print(f"{'=' * 90}")
        
        chart_ma20 = CHART_MA20[stock]
        instrument = stock_info['instrument']
        entry_time = stock_info['entry_time']
        
        print(f"Chart MA20 (Ground Truth): ₹{chart_ma20:.2f}")
        
        # Calculate with FIXED code
        fixed_ma20, fixed_timestamps = get_ma20_fixed(instrument, entry_time)
        
        if fixed_ma20:
            error = fixed_ma20 - chart_ma20
            error_pct = (error / chart_ma20) * 100
            
            print(f"\n--- FIXED CODE RESULT ---")
            print(f"Calculated MA20:  ₹{fixed_ma20:.2f}")
            print(f"Error:            ₹{error:+.2f} ({error_pct:+.2f}%)")
            
            if fixed_timestamps:
                print(f"Time Range Used:  {format_timestamp(fixed_timestamps[0])} to {format_timestamp(fixed_timestamps[1])}")
            
            if abs(error) < 0.05:
                print(f"Status:           ✅ PERFECT MATCH!")
            elif abs(error) < 0.20:
                print(f"Status:           ⚠️  Close but not perfect")
            else:
                print(f"Status:           ❌ Still has error")
            
            results.append({
                'stock': stock,
                'chart_ma20': chart_ma20,
                'fixed_ma20': fixed_ma20,
                'error': error,
                'error_pct': error_pct
            })
        else:
            print(f"\n❌ Failed to calculate MA20!")
    
    # Summary table
    if results:
        print(f"\n\n{'=' * 90}")
        print("SUMMARY TABLE")
        print(f"{'=' * 90}\n")
        print(f"{'Stock':<12} {'Chart MA20':>12} {'Calc MA20':>12} {'Error':>12} {'Error %':>10} {'Status':>8}")
        print("-" * 90)
        
        for r in results:
            status = "✅" if abs(r['error']) < 0.05 else ("⚠️" if abs(r['error']) < 0.20 else "❌")
            print(f"{r['stock']:<12} ₹{r['chart_ma20']:>11.2f} ₹{r['fixed_ma20']:>11.2f} "
                  f"₹{r['error']:>+10.2f} {r['error_pct']:>+9.2f}% {status:>8}")
        
        # Average error
        avg_error = sum(abs(r['error']) for r in results) / len(results)
        
        print("-" * 90)
        print(f"{'AVERAGE ABSOLUTE ERROR':<12} {'':>12} {'':>12} ₹{avg_error:>11.2f}")
        
        print(f"\n{'=' * 90}")
        print("CONCLUSION")
        print(f"{'=' * 90}")
        
        if avg_error < 0.05:
            print(f"✅ SUCCESS! Time filtering is working perfectly!")
            print(f"   Average error: ₹{avg_error:.2f} (within acceptable range)")
            print(f"\n   ✅ This fix is ready to apply to v0.5!")
            print(f"\n   Changes needed in v0.5:")
            print(f"   1. Add .reverse() after getting candles in get_ma20()")
            print(f"   2. Optionally: Add time filtering (but not critical if trading real-time)")
        elif avg_error < 0.20:
            print(f"⚠️  PARTIAL SUCCESS! Better but not perfect.")
            print(f"   Average error: ₹{avg_error:.2f}")
            print(f"\n   There may be one more issue to investigate.")
        else:
            print(f"❌ STILL HAS ISSUES!")
            print(f"   Average error: ₹{avg_error:.2f}")
            print(f"\n   Need to investigate further - may be timezone or grouping logic.")
        
        print(f"{'=' * 90}\n")
    else:
        print("\n❌ No results - all calculations failed!")


if __name__ == "__main__":
    run_fixed_test()
