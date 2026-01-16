"""
MA20 CALCULATION TEST - Using EXACT v0.4 Logic
===============================================
Tests MA20 calculation for 3 stocks at their entry times
to verify against chart values.
"""

import requests
from datetime import datetime, timedelta

# Same credentials as v0.4
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTRiNmJhNTE3ZDE3NzU2N2ViYTViODAiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NjU1MDQzNywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY2NjEzNjAwfQ.HOR8lgVnIL0BZSLZO2YUriRYy5ECT1U3ZJmrMGf61n8"
BASE_URL = "https://api.upstox.com/v2"

# Test stocks
TEST_STOCKS = {
    "YESBANK": "NSE_EQ|INE528G01035",
    "TATASTEEL": "NSE_EQ|INE081A01020",
    "ZEEL": "NSE_EQ|INE256A01028"
}

# Chart MA20 values (ground truth)
CHART_MA20 = {
    "YESBANK": 21.91,
    "TATASTEEL": 170.64,
    "ZEEL": 92.22
}

# ============================================
# EXACT COPY OF v0.4 FUNCTIONS
# ============================================

def get_historical_candles(instrument, num_minutes=100):
    """
    Get historical 1-minute candles for today + yesterday
    EXACT COPY from v0.4
    """
    try:
        # Calculate date range (yesterday + today)
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # Use regular historical endpoint with date range
        url = f"{BASE_URL}/historical-candle/{instrument}/1minute/{to_date}/{from_date}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            candles_raw = data['data']['candles']

            # Convert to list of dicts (most recent first in API response)
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

            # Return last N minutes (most recent at end)
            return candles[-num_minutes:] if len(candles) >= num_minutes else candles

        else:
            print(f"Error getting candles: {response.status_code}")
            return []

    except Exception as e:
        print(f"Error in get_historical_candles: {e}")
        return []


def convert_to_5min_candles(candles_1min):
    """
    Convert 1-minute candles to 5-minute candles
    EXACT COPY from v0.4
    """
    candles_5min = []

    # Group every 5 consecutive 1-minute candles
    for i in range(0, len(candles_1min), 5):
        group = candles_1min[i:i + 5]

        if len(group) == 5:  # Only create 5-min candle if we have complete 5 minutes
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


def get_ma20(instrument):
    """
    Calculate 20-period moving average using 5-minute candles
    EXACT COPY from v0.4
    """
    try:
        # Get 100 one-minute candles (enough for 20 five-minute candles)
        candles_1min = get_historical_candles(instrument, 100)

        if len(candles_1min) < 100:
            print(f"Insufficient data: Only {len(candles_1min)} candles available")
            return None

        # Convert to 5-minute candles
        candles_5min = convert_to_5min_candles(candles_1min)

        if len(candles_5min) < 20:
            print(f"Insufficient 5-min candles: Only {len(candles_5min)} available")
            return None

        # Calculate MA20 from last 20 five-minute candles
        last_20_closes = [c['close'] for c in candles_5min[-20:]]
        ma20 = sum(last_20_closes) / 20

        return round(ma20, 2)

    except Exception as e:
        print(f"Error calculating MA20: {e}")
        return None


# ============================================
# TEST RUNNER
# ============================================

def run_ma20_test():
    """Test MA20 calculation for all 3 stocks"""
    
    print("=" * 80)
    print("MA20 CALCULATION TEST - December 24, 2025")
    print("=" * 80)
    print("\nUsing EXACT v0.4 logic to calculate MA20...")
    print("Comparing bot calculations vs chart values\n")
    
    results = []
    
    for stock, instrument in TEST_STOCKS.items():
        print(f"\n{'=' * 80}")
        print(f"Testing: {stock}")
        print(f"{'=' * 80}")
        
        # Calculate MA20 using bot's logic
        bot_ma20 = get_ma20(instrument)
        chart_ma20 = CHART_MA20[stock]
        
        if bot_ma20:
            error = bot_ma20 - chart_ma20
            error_pct = (error / chart_ma20) * 100
            
            print(f"Bot MA20:   ₹{bot_ma20:.2f}")
            print(f"Chart MA20: ₹{chart_ma20:.2f}")
            print(f"Error:      ₹{error:+.2f} ({error_pct:+.2f}%)")
            
            if abs(error) > 0.05:
                print(f"❌ MISMATCH! Bot calculation is WRONG!")
            else:
                print(f"✅ Match!")
            
            results.append({
                'stock': stock,
                'bot_ma20': bot_ma20,
                'chart_ma20': chart_ma20,
                'error': error,
                'error_pct': error_pct
            })
        else:
            print(f"❌ Failed to calculate MA20!")
    
    # Summary table
    print(f"\n\n{'=' * 80}")
    print("SUMMARY TABLE")
    print(f"{'=' * 80}\n")
    print(f"{'Stock':<12} {'Bot MA20':>10} {'Chart MA20':>10} {'Error':>10} {'Error %':>10}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['stock']:<12} ₹{r['bot_ma20']:>9.2f} ₹{r['chart_ma20']:>9.2f} "
              f"₹{r['error']:>+9.2f} {r['error_pct']:>+9.2f}%")
    
    # Average error
    avg_error = sum(r['error'] for r in results) / len(results)
    print("-" * 80)
    print(f"{'AVERAGE ERROR':<12} {'':>10} {'':>10} ₹{avg_error:>+9.2f}")
    
    print(f"\n{'=' * 80}")
    print("CONCLUSION")
    print(f"{'=' * 80}")
    
    if abs(avg_error) > 0.05:
        print(f"❌ Bot's MA20 calculation is systematically OFF by ₹{avg_error:+.2f}")
        print("   This explains why all morning bounce signals were WRONG!")
    else:
        print("✅ Bot's MA20 calculation matches chart values")
    
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    run_ma20_test()
