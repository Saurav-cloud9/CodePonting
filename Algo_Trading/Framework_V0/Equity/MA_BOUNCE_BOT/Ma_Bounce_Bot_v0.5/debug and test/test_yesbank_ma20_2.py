"""
TEST SCRIPT: YESBANK MA20 Calculation Debug
============================================
Fetch 100 candles as of 10:50 AM on Dec 24, 2025
Calculate MA20 and verify against chart value (21.91)
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTRkY2ZmYzNlZDdhNDU2NmM3NGE0ODIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NjcwNzE5NiwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY2Nzg2NDAwfQ.gvlbJFWY94keKrs6AABK4EITgTQ7sFXx-PPiDnoBCio"
BASE_URL = "https://api.upstox.com/v2"
YESBANK_INSTRUMENT = "NSE_EQ|INE528G01035"

# Target scenario: Dec 24, 10:50 AM
# We need candles from Dec 23 and Dec 24 to get 100 candles

def get_historical_candles(instrument, to_date, from_date):
    """
    Get historical 1-minute candles
    
    Args:
        instrument: Instrument key
        to_date: End date (YYYY-MM-DD format)
        from_date: Start date (YYYY-MM-DD format)
    
    Returns:
        list: List of candle dicts
    """
    try:
        url = f"{BASE_URL}/historical-candle/{instrument}/1minute/{to_date}/{from_date}"
        
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }
        
        print(f"Fetching candles from API...")
        print(f"URL: {url}")
        
        response = requests.get(url, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            candles_raw = data['data']['candles']
            
            print(f"Total candles received: {len(candles_raw)}")
            
            # Convert to list of dicts
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
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            return []
    
    except Exception as e:
        print(f"Exception: {e}")
        return []


def convert_to_5min_candles(candles_1min):
    """
    Convert 1-minute candles to 5-minute candles
    
    Args:
        candles_1min: List of 1-minute candle dicts (should be in chronological order)
    
    Returns:
        list: List of 5-minute candle dicts
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


def calculate_ma20(candles_5min):
    """
    Calculate MA20 from 5-minute candles
    
    Args:
        candles_5min: List of 5-minute candles
    
    Returns:
        float: MA20 value
    """
    if len(candles_5min) < 20:
        print(f"ERROR: Need 20 five-minute candles, only have {len(candles_5min)}")
        return None
    
    # Take last 20 candles
    last_20 = candles_5min[-20:]
    
    # Get close prices
    closes = [c['close'] for c in last_20]
    
    # Calculate average
    ma20 = sum(closes) / 20
    
    return round(ma20, 2)


def main():
    print("=" * 80)
    print("YESBANK MA20 CALCULATION TEST - Dec 24, 10:50 AM")
    print("=" * 80)
    
    # Fetch candles from Dec 23 and Dec 24
    to_date = "2025-12-24"
    from_date = "2025-12-23"
    
    print(f"\nFetching data from {from_date} to {to_date}...")
    
    all_candles = get_historical_candles(YESBANK_INSTRUMENT, to_date, from_date)
    
    if not all_candles:
        print("\n❌ Failed to fetch candles!")
        return
    
    print(f"\n✅ Received {len(all_candles)} total candles")
    
    # Show first 5 and last 5 candles to understand order
    print("\n" + "=" * 80)
    print("CANDLE ORDER CHECK (as received from API)")
    print("=" * 80)
    
    print("\nFirst 5 candles:")
    for i in range(min(5, len(all_candles))):
        ts = all_candles[i]['timestamp']
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        print(f"  [{i}] {dt.strftime('%b %d %H:%M')} - Close: ₹{all_candles[i]['close']:.2f}")
    
    print("\nLast 5 candles:")
    for i in range(max(0, len(all_candles) - 5), len(all_candles)):
        ts = all_candles[i]['timestamp']
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        print(f"  [{i}] {dt.strftime('%b %d %H:%M')} - Close: ₹{all_candles[i]['close']:.2f}")
    
    # Find the candle at 10:50 AM on Dec 24
    print("\n" + "=" * 80)
    print("STEP 1: Find candle at 10:50 AM on Dec 24, then take 100 candles")
    print("=" * 80)
    
    target_time = "2025-12-24T10:50"
    target_index = None
    
    for i, candle in enumerate(all_candles):
        if target_time in candle['timestamp']:
            target_index = i
            print(f"\n✅ Found target candle at index {i}")
            dt = datetime.fromisoformat(candle['timestamp'].replace('Z', '+00:00'))
            print(f"   Timestamp: {dt.strftime('%b %d %H:%M')}")
            print(f"   Close: ₹{candle['close']:.2f}")
            break
    
    if target_index is None:
        print("\n❌ Could not find 10:50 AM candle on Dec 24!")
        return
    
    # Take 100 candles starting from target_index (includes the 10:50 candle)
    # Since API returns newest first, we need candles from target_index to target_index+99
    start_idx = target_index
    end_idx = target_index + 100
    
    if end_idx > len(all_candles):
        print(f"\n⚠️  Not enough candles! Need {end_idx}, have {len(all_candles)}")
        candles_100 = all_candles[start_idx:]
    else:
        candles_100 = all_candles[start_idx:end_idx]
    
    print(f"\nExtracted {len(candles_100)} candles from index {start_idx} to {start_idx + len(candles_100) - 1}")
    
    print("\nFirst 3 of these 100:")
    for i in range(min(3, len(candles_100))):
        ts = candles_100[i]['timestamp']
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        print(f"  [{i}] {dt.strftime('%b %d %H:%M')} - Close: ₹{candles_100[i]['close']:.2f}")
    
    print("\nLast 3 of these 100:")
    for i in range(max(0, len(candles_100) - 3), len(candles_100)):
        ts = candles_100[i]['timestamp']
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        print(f"  [{i}] {dt.strftime('%b %d %H:%M')} - Close: ₹{candles_100[i]['close']:.2f}")
    
    # REVERSE the candles (THIS IS THE FIX!)
    print("\n" + "=" * 80)
    print("STEP 2: REVERSE to chronological order")
    print("=" * 80)
    
    candles_100_reversed = list(reversed(candles_100))
    
    print("\nAfter reversing - First 3:")
    for i in range(min(3, len(candles_100_reversed))):
        ts = candles_100_reversed[i]['timestamp']
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        print(f"  [{i}] {dt.strftime('%b %d %H:%M')} - Close: ₹{candles_100_reversed[i]['close']:.2f}")
    
    print("\nAfter reversing - Last 3:")
    for i in range(max(0, len(candles_100_reversed) - 3), len(candles_100_reversed)):
        ts = candles_100_reversed[i]['timestamp']
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        print(f"  [{i}] {dt.strftime('%b %d %H:%M')} - Close: ₹{candles_100_reversed[i]['close']:.2f}")
    
    # Convert to 5-minute candles
    print("\n" + "=" * 80)
    print("STEP 3: Convert to 5-minute candles")
    print("=" * 80)
    
    candles_5min = convert_to_5min_candles(candles_100_reversed)
    
    print(f"\nCreated {len(candles_5min)} five-minute candles")
    
    print("\n" + "=" * 80)
    print("ALL 20 FIVE-MINUTE CANDLES - COMPARE WITH CHART")
    print("=" * 80)
    print("\nPlease compare these CLOSE values with TradingView 5-min chart:")
    print("-" * 80)
    
    for i in range(len(candles_5min)):
        ts = candles_5min[i]['timestamp']
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        close = candles_5min[i]['close']
        print(f"  Candle {i+1:2d}: {dt.strftime('%b %d %H:%M')} - Close: ₹{close:.2f}")
    
    print("-" * 80)
    print("\nINSTRUCTIONS:")
    print("1. Open TradingView with YESBANK on 5-minute chart")
    print("2. Go to Dec 24, 10:50 AM")
    print("3. Check the close value of each 5-min candle above")
    print("4. Note any discrepancies")
    print("-" * 80)
    
    # Calculate MA20
    print("\n" + "=" * 80)
    print("STEP 4: Calculate MA20")
    print("=" * 80)
    
    ma20 = calculate_ma20(candles_5min)
    
    if ma20:
        print(f"\n✅ MA20 = ₹{ma20:.2f}")
        
        print("\n" + "=" * 80)
        print("COMPARISON WITH CHART")
        print("=" * 80)
        
        chart_ma20 = 21.91
        difference = ma20 - chart_ma20
        
        print(f"\nChart MA20:      ₹{chart_ma20:.2f}")
        print(f"Calculated MA20: ₹{ma20:.2f}")
        print(f"Difference:      ₹{difference:+.2f}")
        
        if abs(difference) < 0.05:
            print("\n✅ MATCH! MA20 calculation is correct!")
        else:
            print("\n❌ MISMATCH! MA20 calculation is still wrong!")
    else:
        print("\n❌ Could not calculate MA20!")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
