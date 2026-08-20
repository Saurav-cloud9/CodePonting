"""
MA20 CALCULATION TEST - BUGGY vs FIXED
=======================================
Compares the buggy candles[-100:] vs fixed candles[:100]
to verify which one matches chart values.
"""

import requests
from datetime import datetime, timedelta

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
# DATA FETCHING
# ============================================

def get_historical_candles(instrument, num_minutes=100, up_to_time=None):
    """Fetch historical candles from Upstox API, optionally filtered up to a specific time"""
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

            # Filter candles up to entry time if specified
            if up_to_time:
                # Parse entry time (format: "HH:MM:SS")
                entry_dt = datetime.strptime(f"{to_date} {up_to_time}", "%Y-%m-%d %H:%M:%S")
                
                # Filter candles that are at or before entry time
                filtered_candles = []
                for candle in candles:
                    candle_dt = datetime.fromisoformat(candle['timestamp'].replace('Z', '+00:00'))
                    if candle_dt <= entry_dt:
                        filtered_candles.append(candle)
                
                candles = filtered_candles

            # Return BOTH versions for testing
            return candles, num_minutes
        else:
            print(f"Error getting candles: {response.status_code}")
            return None, num_minutes

    except Exception as e:
        print(f"Error in get_historical_candles: {e}")
        return None, num_minutes


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
# MA20 CALCULATION - BUGGY VERSION
# ============================================

def get_ma20_buggy(instrument, entry_time=None):
    """Calculate MA20 using BUGGY code (candles[-100:])"""
    try:
        all_candles, num_minutes = get_historical_candles(instrument, 100, up_to_time=entry_time)
        
        if all_candles is None or len(all_candles) < 100:
            print(f"Insufficient data: Only {len(all_candles) if all_candles else 0} candles")
            return None, None

        # BUGGY: Take last 100 (oldest candles due to reverse chronological order)
        candles_1min = all_candles[-num_minutes:]  # ❌ WRONG!

        candles_5min = convert_to_5min_candles(candles_1min)
        
        if len(candles_5min) < 20:
            return None, None

        last_20_closes = [c['close'] for c in candles_5min[-20:]]
        ma20 = sum(last_20_closes) / 20

        # Return MA20 and timestamps for verification
        first_timestamp = candles_1min[0]['timestamp']
        last_timestamp = candles_1min[-1]['timestamp']
        
        return round(ma20, 2), (first_timestamp, last_timestamp)

    except Exception as e:
        print(f"Error: {e}")
        return None, None


# ============================================
# MA20 CALCULATION - FIXED VERSION
# ============================================

def get_ma20_fixed(instrument, entry_time=None):
    """Calculate MA20 using FIXED code (candles[:100])"""
    try:
        all_candles, num_minutes = get_historical_candles(instrument, 100, up_to_time=entry_time)
        
        if all_candles is None or len(all_candles) < 100:
            print(f"Insufficient data: Only {len(all_candles) if all_candles else 0} candles")
            return None, None

        # FIXED: Take first 100 (newest candles since API returns newest first)
        candles_1min = all_candles[:num_minutes]  # ✅ CORRECT!

        candles_1min.reverse()

        candles_5min = convert_to_5min_candles(candles_1min)
        
        if len(candles_5min) < 20:
            return None, None

        last_20_closes = [c['close'] for c in candles_5min[-20:]]
        ma20 = sum(last_20_closes) / 20

        # Return MA20 and timestamps for verification
        first_timestamp = candles_1min[0]['timestamp']
        last_timestamp = candles_1min[-1]['timestamp']
        
        return round(ma20, 2), (first_timestamp, last_timestamp)

    except Exception as e:
        print(f"Error: {e}")
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

def run_comparison_test():
    """Compare buggy vs fixed MA20 calculations"""
    
    print("=" * 90)
    print("MA20 CALCULATION TEST - BUGGY vs FIXED COMPARISON")
    print("=" * 90)
    print("\nTesting hypothesis: candles[:100] should match chart MA20")
    print("while candles[-100:] gives wrong (old) data\n")
    
    results = []
    
    for stock, stock_info in TEST_STOCKS.items():
        print(f"\n{'=' * 90}")
        print(f"Testing: {stock} (Entry Time: {stock_info['entry_time']})")
        print(f"{'=' * 90}")
        
        chart_ma20 = CHART_MA20[stock]
        instrument = stock_info['instrument']
        entry_time = stock_info['entry_time']
        
        # Calculate with BUGGY code
        buggy_ma20, buggy_timestamps = get_ma20_buggy(instrument, entry_time)
        
        # Calculate with FIXED code
        fixed_ma20, fixed_timestamps = get_ma20_fixed(instrument, entry_time)
        
        if buggy_ma20 and fixed_ma20:
            buggy_error = buggy_ma20 - chart_ma20
            fixed_error = fixed_ma20 - chart_ma20
            
            print(f"\nChart MA20:  ₹{chart_ma20:.2f} (Ground Truth)")
            print(f"\n--- BUGGY CODE: candles[-100:] ---")
            print(f"MA20:        ₹{buggy_ma20:.2f}")
            print(f"Error:       ₹{buggy_error:+.2f} ({(buggy_error/chart_ma20*100):+.2f}%)")
            if buggy_timestamps:
                print(f"Time Range:  {format_timestamp(buggy_timestamps[0])} to {format_timestamp(buggy_timestamps[1])}")
            if abs(buggy_error) > 0.05:
                print("Status:      ❌ WRONG!")
            else:
                print("Status:      ✅ Matches!")
            
            print(f"\n--- FIXED CODE: candles[:100] ---")
            print(f"MA20:        ₹{fixed_ma20:.2f}")
            print(f"Error:       ₹{fixed_error:+.2f} ({(fixed_error/chart_ma20*100):+.2f}%)")
            if fixed_timestamps:
                print(f"Time Range:  {format_timestamp(fixed_timestamps[0])} to {format_timestamp(fixed_timestamps[1])}")
            if abs(fixed_error) > 0.05:
                print("Status:      ❌ Still wrong!")
            else:
                print("Status:      ✅ MATCHES CHART!")
            
            results.append({
                'stock': stock,
                'chart_ma20': chart_ma20,
                'buggy_ma20': buggy_ma20,
                'fixed_ma20': fixed_ma20,
                'buggy_error': buggy_error,
                'fixed_error': fixed_error
            })
        else:
            print(f"❌ Failed to calculate MA20!")
    
    # Summary table
    print(f"\n\n{'=' * 90}")
    print("SUMMARY TABLE")
    print(f"{'=' * 90}\n")
    print(f"{'Stock':<12} {'Chart':>10} {'Buggy':>10} {'Fixed':>10} {'Buggy Err':>12} {'Fixed Err':>12}")
    print("-" * 90)
    
    for r in results:
        buggy_status = "❌" if abs(r['buggy_error']) > 0.05 else "✅"
        fixed_status = "❌" if abs(r['fixed_error']) > 0.05 else "✅"
        print(f"{r['stock']:<12} ₹{r['chart_ma20']:>9.2f} ₹{r['buggy_ma20']:>9.2f} ₹{r['fixed_ma20']:>9.2f} "
              f"₹{r['buggy_error']:>+10.2f} {buggy_status} ₹{r['fixed_error']:>+10.2f} {fixed_status}")
    
    # Average errors
    avg_buggy = sum(abs(r['buggy_error']) for r in results) / len(results)
    avg_fixed = sum(abs(r['fixed_error']) for r in results) / len(results)
    
    print("-" * 90)
    print(f"{'AVG ABS ERROR':<12} {'':>10} {'':>10} {'':>10} ₹{avg_buggy:>10.2f}    ₹{avg_fixed:>10.2f}")
    
    print(f"\n{'=' * 90}")
    print("CONCLUSION")
    print(f"{'=' * 90}")
    
    if avg_fixed < 0.05:
        print(f"✅ SUCCESS! Fixed code (candles[:100]) matches chart perfectly!")
        print(f"   Average error reduced from ₹{avg_buggy:.2f} to ₹{avg_fixed:.2f}")
        print(f"\n   The fix works! Update v0.5 with: candles[:num_minutes]")
    elif avg_fixed < avg_buggy:
        print(f"⚠️  PARTIAL SUCCESS! Fixed code is better but not perfect.")
        print(f"   Average error reduced from ₹{avg_buggy:.2f} to ₹{avg_fixed:.2f}")
        print(f"\n   There may be another issue in the calculation logic.")
    else:
        print(f"❌ HYPOTHESIS REJECTED! Fixed code doesn't help.")
        print(f"   The bug is somewhere else in the calculation logic.")
    
    print(f"{'=' * 90}\n")


if __name__ == "__main__":
    run_comparison_test()
