"""
TEST: v0.5 MA20 Calculation with Fixes Applied
================================================
Tests the EXACT v0.5 bot logic with our fixes:
1. Add .reverse() before grouping
2. Optional: Filter to only today's candles

This simulates what v0.5 will calculate after we apply fixes.
"""

import requests
from datetime import datetime, timedelta

# Same credentials as v0.5
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTRiNmJhNTE3ZDE3NzU2N2ViYTViODAiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NjU1MDQzNywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY2NjEzNjAwfQ.HOR8lgVnIL0BZSLZO2YUriRYy5ECT1U3ZJmrMGf61n8"
BASE_URL = "https://api.upstox.com/v2"

# Test stocks - using Dec 24 entry times from your actual trades
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

# Chart MA20 values (ground truth)
CHART_MA20 = {
    "YESBANK": 21.91,
    "TATASTEEL": 170.64,
    "ZEEL": 92.22
}

# ============================================
# EXACT v0.5 CODE (with fixes applied)
# ============================================

def get_historical_candles(instrument, num_minutes=100):
    """Get historical candles - EXACT v0.5 logic"""
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

            # v0.5 original logic
            return candles[:num_minutes] if len(candles) >= num_minutes else candles
        return []
    except:
        return []


def convert_to_5min_candles(candles_1min):
    """Convert 1-min to 5-min candles - EXACT v0.5 logic"""
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


def get_ma20_original(instrument):
    """ORIGINAL v0.5 code (BUGGY - no reverse)"""
    try:
        candles_1min = get_historical_candles(instrument, 100)
        if len(candles_1min) < 100:
            return None, "Insufficient candles"

        # NO .reverse() here - this is the bug!
        candles_5min = convert_to_5min_candles(candles_1min)
        if len(candles_5min) < 20:
            return None, "Insufficient 5-min candles"

        last_20_closes = [c['close'] for c in candles_5min[-20:]]
        ma20 = round(sum(last_20_closes) / 20, 2)
        
        # Debug info
        first_ts = candles_1min[0]['timestamp']
        last_ts = candles_1min[-1]['timestamp']
        
        return ma20, f"{format_ts(first_ts)} to {format_ts(last_ts)}"
    except Exception as e:
        return None, str(e)


def get_ma20_with_reverse(instrument):
    """FIXED v0.5 code - Add .reverse()"""
    try:
        candles_1min = get_historical_candles(instrument, 100)
        if len(candles_1min) < 100:
            return None, "Insufficient candles"

        # FIX #1: Add .reverse() before grouping
        candles_1min.reverse()
        
        candles_5min = convert_to_5min_candles(candles_1min)
        if len(candles_5min) < 20:
            return None, "Insufficient 5-min candles"

        last_20_closes = [c['close'] for c in candles_5min[-20:]]
        ma20 = round(sum(last_20_closes) / 20, 2)
        
        # Debug info
        first_ts = candles_1min[0]['timestamp']
        last_ts = candles_1min[-1]['timestamp']
        
        return ma20, f"{format_ts(first_ts)} to {format_ts(last_ts)}"
    except Exception as e:
        return None, str(e)


def get_ma20_with_reverse_and_filter(instrument, entry_time):
    """FIXED v0.5 code - Add .reverse() + filter today only"""
    try:
        all_candles = get_historical_candles(instrument, 1000)  # Get more candles
        if not all_candles:
            return None, "No candles from API"

        # FIX #2: Filter to only TODAY's candles
        today_date = datetime.now().date()
        today_candles = []
        
        for candle in all_candles:
            candle_dt = datetime.fromisoformat(candle['timestamp'].replace('Z', '+00:00'))
            if candle_dt.date() == today_date:
                today_candles.append(candle)
        
        # Take first 100 (newest)
        candles_1min = today_candles[:100] if len(today_candles) >= 100 else today_candles
        
        if len(candles_1min) < 100:
            return None, f"Only {len(candles_1min)} candles from today"

        # FIX #1: Add .reverse() before grouping
        candles_1min.reverse()
        
        candles_5min = convert_to_5min_candles(candles_1min)
        if len(candles_5min) < 20:
            return None, "Insufficient 5-min candles"

        last_20_closes = [c['close'] for c in candles_5min[-20:]]
        ma20 = round(sum(last_20_closes) / 20, 2)
        
        # Debug info
        first_ts = candles_1min[0]['timestamp']
        last_ts = candles_1min[-1]['timestamp']
        
        return ma20, f"{format_ts(first_ts)} to {format_ts(last_ts)}"
    except Exception as e:
        return None, str(e)


# ============================================
# TEST RUNNER
# ============================================

def format_ts(ts):
    """Format timestamp"""
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime('%I:%M %p')
    except:
        return ts


def run_test():
    print("=" * 100)
    print("v0.5 MA20 CALCULATION TEST - COMPARING FIXES")
    print("=" * 100)
    print("\nTesting 3 versions:")
    print("1. ORIGINAL v0.5 (buggy - no reverse)")
    print("2. FIX #1: Add .reverse()")
    print("3. FIX #2: Add .reverse() + filter today only")
    print()

    results = []

    for stock, info in TEST_STOCKS.items():
        print(f"\n{'=' * 100}")
        print(f"Testing: {stock} (Entry: {info['entry_time']})")
        print(f"{'=' * 100}")
        
        chart_ma20 = CHART_MA20[stock]
        instrument = info['instrument']
        entry_time = info['entry_time']
        
        print(f"\nChart MA20 (Ground Truth): ₹{chart_ma20:.2f}")
        
        # Test original (buggy)
        print(f"\n--- ORIGINAL v0.5 (BUGGY) ---")
        orig_ma20, orig_info = get_ma20_original(instrument)
        if orig_ma20:
            orig_error = orig_ma20 - chart_ma20
            print(f"MA20: ₹{orig_ma20:.2f} | Error: ₹{orig_error:+.2f} | Range: {orig_info}")
        else:
            print(f"Failed: {orig_info}")
            orig_error = None
        
        # Test with reverse
        print(f"\n--- FIX #1: With .reverse() ---")
        rev_ma20, rev_info = get_ma20_with_reverse(instrument)
        if rev_ma20:
            rev_error = rev_ma20 - chart_ma20
            print(f"MA20: ₹{rev_ma20:.2f} | Error: ₹{rev_error:+.2f} | Range: {rev_info}")
        else:
            print(f"Failed: {rev_info}")
            rev_error = None
        
        # Test with reverse + filter
        print(f"\n--- FIX #2: With .reverse() + Today Filter ---")
        filt_ma20, filt_info = get_ma20_with_reverse_and_filter(instrument, entry_time)
        if filt_ma20:
            filt_error = filt_ma20 - chart_ma20
            print(f"MA20: ₹{filt_ma20:.2f} | Error: ₹{filt_error:+.2f} | Range: {filt_info}")
        else:
            print(f"Failed: {filt_info}")
            filt_error = None
        
        results.append({
            'stock': stock,
            'chart': chart_ma20,
            'orig': orig_ma20,
            'orig_err': orig_error,
            'rev': rev_ma20,
            'rev_err': rev_error,
            'filt': filt_ma20,
            'filt_err': filt_error
        })

    # Summary
    print(f"\n\n{'=' * 100}")
    print("SUMMARY TABLE")
    print(f"{'=' * 100}\n")
    print(f"{'Stock':<12} {'Chart':>10} {'Original':>10} {'Err':>8} {'+ Reverse':>10} {'Err':>8} {'+ Filter':>10} {'Err':>8}")
    print("-" * 100)
    
    for r in results:
        orig_str = f"₹{r['orig']:.2f}" if r['orig'] else "N/A"
        orig_err_str = f"₹{r['orig_err']:+.2f}" if r['orig_err'] is not None else "N/A"
        rev_str = f"₹{r['rev']:.2f}" if r['rev'] else "N/A"
        rev_err_str = f"₹{r['rev_err']:+.2f}" if r['rev_err'] is not None else "N/A"
        filt_str = f"₹{r['filt']:.2f}" if r['filt'] else "N/A"
        filt_err_str = f"₹{r['filt_err']:+.2f}" if r['filt_err'] is not None else "N/A"
        
        print(f"{r['stock']:<12} ₹{r['chart']:>9.2f} {orig_str:>10} {orig_err_str:>8} {rev_str:>10} {rev_err_str:>8} {filt_str:>10} {filt_err_str:>8}")

    print(f"\n{'=' * 100}")
    print("RECOMMENDATION")
    print(f"{'=' * 100}")
    print("\nBased on results, which fix should we apply to v0.5?")
    print("- If FIX #1 is good enough (error < ₹0.20): Just add .reverse()")
    print("- If FIX #2 is better: Add .reverse() + today filter")
    print(f"{'=' * 100}\n")


if __name__ == "__main__":
    run_test()
