"""
MA BOUNCE BOT - VISUAL BACKTEST SYSTEM
========================================
Fetches real Upstox data and runs backtest with visual dashboard
"""

import requests
import json
from datetime import datetime, timedelta
import webbrowser
import os

# Configuration
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTRkY2ZmYzNlZDdhNDU2NmM3NGE0ODIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NjcwNzE5NiwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY2Nzg2NDAwfQ.gvlbJFWY94keKrs6AABK4EITgTQ7sFXx-PPiDnoBCio"  # Update this
BASE_URL = "https://api.upstox.com/v2"

INSTRUMENTS = {
    "YESBANK": "NSE_EQ|INE528G01035",
    "SUZLON": "NSE_EQ|INE040H01021",
    "TATASTEEL": "NSE_EQ|INE081A01020",
}

BOUNCE_THRESHOLD_PCT = 0.5  # 0.5% distance threshold

# ============================================
# CORE BOT FUNCTIONS (FIXED VERSION)
# ============================================

def get_historical_candles(instrument, to_date, from_date):
    """Fetch historical 1-minute candles from Upstox"""
    try:
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
            
            return candles
        else:
            print(f"API Error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception: {e}")
        return []


def convert_to_5min_candles(candles_1min):
    """Convert 1-min to 5-min candles"""
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


def calculate_ma20_at_timestamp(all_candles, target_index):
    """
    Calculate MA20 at a specific candle index
    Uses fixed logic with REVERSE
    """
    try:
        # Get 100 candles ending at target_index
        start_idx = target_index
        end_idx = target_index + 100
        
        if end_idx > len(all_candles):
            return None
        
        candles_100 = all_candles[start_idx:end_idx]
        
        # ✨ FIX: REVERSE to chronological order
        candles_100_reversed = list(reversed(candles_100))
        
        # Convert to 5-min candles
        candles_5min = convert_to_5min_candles(candles_100_reversed)
        
        if len(candles_5min) < 20:
            return None
        
        # Calculate MA20
        last_20_closes = [c['close'] for c in candles_5min[-20:]]
        ma20 = sum(last_20_closes) / 20
        
        return round(ma20, 2)
    except:
        return None


def run_backtest(stock, date, start_time="09:15", end_time="15:30"):
    """
    Run backtest for a specific stock and date
    Returns candles and signals data for visualization
    """
    print(f"\n{'=' * 80}")
    print(f"RUNNING BACKTEST: {stock} on {date}")
    print(f"{'=' * 80}\n")
    
    # Fetch data
    instrument = INSTRUMENTS[stock]
    from_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"Fetching data from {from_date} to {date}...")
    all_candles = get_historical_candles(instrument, date, from_date)
    
    if not all_candles:
        print("❌ Failed to fetch data!")
        return None
    
    print(f"✅ Fetched {len(all_candles)} candles")
    
    # Convert all to 5-min for visualization
    print("\nProcessing candles...")
    
    # Find candles within time range
    candles_in_range = []
    signals = []
    
    for i, candle in enumerate(all_candles):
        dt = datetime.fromisoformat(candle['timestamp'].replace('Z', '+00:00'))
        time_str = dt.strftime('%H:%M')
        date_str = dt.strftime('%Y-%m-%d')
        
        # Only process candles from target date within time range
        if date_str != date:
            continue
        
        if time_str < start_time or time_str > end_time:
            continue
        
        # Calculate MA20 at this timestamp
        ma20 = calculate_ma20_at_timestamp(all_candles, i)
        
        if ma20 is not None:
            candle_data = {
                'timestamp': dt.strftime('%Y-%m-%d %H:%M'),
                'open': candle['open'],
                'high': candle['high'],
                'low': candle['low'],
                'close': candle['close'],
                'ma20': ma20
            }
            candles_in_range.append(candle_data)
            
            # Check for signal
            price = candle['close']
            distance = price - ma20
            dynamic_threshold = price * (BOUNCE_THRESHOLD_PCT / 100)
            
            # Signal conditions: price above MA and within threshold
            if price >= ma20 and abs(distance) <= dynamic_threshold:
                signal = {
                    'timestamp': dt.strftime('%Y-%m-%d %H:%M'),
                    'price': price,
                    'ma20': ma20,
                    'distance': distance,
                    'valid': True  # In backtest, we mark based on conditions
                }
                signals.append(signal)
                print(f"  📊 Signal at {time_str}: Price ₹{price:.2f}, MA20 ₹{ma20:.2f}, Distance ₹{distance:.2f}")
    
    print(f"\n✅ Processed {len(candles_in_range)} candles")
    print(f"✅ Found {len(signals)} signals")
    
    return {
        'stock': stock,
        'date': date,
        'candles': candles_in_range,
        'signals': signals
    }


def generate_dashboard_html(backtest_results):
    """Generate HTML dashboard with real backtest data"""
    
    # Read the template
    template_path = '/home/claude/backtest_dashboard.html'
    with open(template_path, 'r') as f:
        html_template = f.read()
    
    # Convert data to JavaScript format
    js_data = f"""
        const backtestData = {json.dumps(backtest_results)};
        
        window.onload = function() {{
            displayResults(backtestData);
        }};
    """
    
    # Replace the example data generation with real data
    html_with_data = html_template.replace(
        "window.onload = function() {\n            setTimeout(() => runBacktest(), 500);\n        };",
        js_data
    )
    
    # Save to output file
    output_path = '/home/claude/backtest_result.html'
    with open(output_path, 'w') as f:
        f.write(html_with_data)
    
    print(f"\n✅ Dashboard generated: {output_path}")
    return output_path


# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("=" * 80)
    print("MA BOUNCE BOT - VISUAL BACKTEST SYSTEM")
    print("=" * 80)
    
    # Configuration
    STOCK = "YESBANK"
    DATE = "2025-12-24"
    
    print(f"\nConfiguration:")
    print(f"  Stock: {STOCK}")
    print(f"  Date: {DATE}")
    print(f"  Time Range: 09:15 - 15:30")
    
    # Run backtest
    results = run_backtest(STOCK, DATE)
    
    if results:
        # Generate dashboard
        dashboard_path = generate_dashboard_html(results)
        
        print(f"\n{'=' * 80}")
        print("BACKTEST COMPLETE!")
        print(f"{'=' * 80}")
        print(f"\nOpen this file in your browser:")
        print(f"  {dashboard_path}")
        print(f"\nOr run: ")
        print(f"  python -m webbrowser {dashboard_path}")
    else:
        print("\n❌ Backtest failed!")
