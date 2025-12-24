"""
MA BOUNCE BOT v0.3 - WITH ORDER PLACEMENT
==========================================
Scans watchlist for MA bounce signals and places automatic orders via Upstox API

Features:
- Live price fetching
- Historical data & MA calculation
- Bounce signal detection
- Automatic order placement (LIMIT orders)
- Target & Stop Loss calculation
"""

import requests
import json
import time
from datetime import datetime, timedelta

# ============================================
# CONFIGURATION
# ============================================

# Upstox API Credentials
API_KEY = "18185106-6257-4a85-a84a-2ea314f91927"
API_SECRET = "15m0va42ni"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTQwZDFhY2IwMTU5MjMwZjUyNzdjOGEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NTg1NTY2MCwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY1OTIyNDAwfQ.ZHiMlWfaJYLRSHLSTzrnJEim2WoVMUtd0dwb_FAVEGI"

# Watchlist - NSE symbols (correct format)
# Watchlist - NSE symbols (ISIN format)
WATCHLIST = {
    'YESBANK': 'NSE_EQ|INE528G01035',
    'SUZLON': 'NSE_EQ|INE040H01021',
    'RPOWER': 'NSE_EQ|INE614G01033',
    'IRFC': 'NSE_EQ|INE053F01010',
    'IDFC': 'NSE_EQ|INE092T01019'  # IDFC First Bank
}

# Bot parameters (CONFIGURATION - change here to affect all trades)
QUANTITY = 5  # shares per trade
TARGET_PCT = 2.0  # 2% profit target
STOPLOSS_PCT = 1.0  # 1% stop loss
BOUNCE_THRESHOLD = 0.30  # ±₹0.30 from MA to trigger signal
MA_PERIOD = 20  # Moving Average period

# API Base
BASE_URL = "https://api.upstox.com/v2"


def get_live_price(instrument):
    """Fetch current market price"""
    url = f"{BASE_URL}/market-quote/quotes"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }
    params = {'instrument_key': instrument}

    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")  # Print full response


        if response.status_code == 200:
            data = response.json()
            # Get the first (and only) key from the data dict
            first_key = list(data['data'].keys())[0]
            ltp = data['data'][first_key]['last_price']
            return ltp
        else:
            print(f"Error fetching price: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None


def get_historical_candles(instrument, interval='5minute', count=20):
    """Fetch historical candle data"""

    # For intraday data, use the special intraday endpoint (no dates needed!)
    url = f"{BASE_URL}/historical-candle/intraday/{instrument}/{interval}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            candles = data['data']['candles'][:count]  # Get last 20 candles
            return candles
        else:
            print(f"Error fetching candles: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

"""
PROPER MA 20 CALCULATION ON 5-MINUTE TIMEFRAME
================================================
Converts 1-minute candles to 5-minute candles, then calculates MA 20
This matches what traders see on standard 5-minute charts!
"""


def convert_1min_to_5min_candles(one_min_candles):
    """
    Convert 1-minute candles to 5-minute candles

    Args:
        one_min_candles: List of 1-min candles from API
                        Format: [timestamp, open, high, low, close, volume]

    Returns:
        List of 5-min candles with same format
    """
    if not one_min_candles or len(one_min_candles) < 5:
        return None

    five_min_candles = []

    # Process in groups of 5 (5 x 1-min = 1 x 5-min)
    for i in range(0, len(one_min_candles), 5):
        # Get next 5 candles (or remaining if less than 5)
        chunk = one_min_candles[i:i + 5]

        if len(chunk) < 5:
            # Skip incomplete 5-min period at the end
            break

        # Create 5-minute candle from 5 one-minute candles
        # timestamp: Use the first candle's timestamp
        # open: First candle's open
        # high: Highest high among all 5 candles
        # low: Lowest low among all 5 candles
        # close: Last candle's close
        # volume: Sum of all 5 volumes

        five_min_candle = [
            chunk[0][0],  # timestamp (first candle)
            chunk[0][1],  # open (first candle)
            max(c[2] for c in chunk),  # high (max of all highs)
            min(c[3] for c in chunk),  # low (min of all lows)
            chunk[-1][4],  # close (last candle)
            sum(c[5] for c in chunk)  # volume (sum of all volumes)
        ]

        five_min_candles.append(five_min_candle)

    return five_min_candles


def calculate_ma20_from_5min(one_min_candles):
    """
    Calculate MA 20 on 5-minute timeframe

    Args:
        one_min_candles: List of 100 one-minute candles from API

    Returns:
        MA 20 value (float) or None if insufficient data
    """
    # Convert to 5-minute candles
    five_min_candles = convert_1min_to_5min_candles(one_min_candles)
    print(f"DEBUG TIME CHECK:")
    print(f"  First 5-min candle timestamp: {five_min_candles[0][0]}")
    print(f"  Last 5-min candle timestamp: {five_min_candles[-1][0]}")

    if not five_min_candles:
        print("❌ Unable to convert to 5-min candles")
        return None

    print(f"\n=== 5-MIN CONVERSION DEBUG ===")
    print(f"1-min candles received: {len(one_min_candles)}")
    print(f"5-min candles created: {len(five_min_candles)}")

    # We need at least 20 five-minute candles for MA 20
    if len(five_min_candles) < 20:
        print(f"❌ Need 20 five-min candles, only have {len(five_min_candles)}")
        print(f"   (Fetch at least 100 one-min candles to get 20 five-min candles)")
        return None

    # Take the most recent 20 five-minute candles
    recent_20_candles = five_min_candles[-20:]

    # Extract close prices (index 4)
    close_prices = [candle[4] for candle in recent_20_candles]

    # Calculate MA 20
    ma20 = sum(close_prices) / len(close_prices)

    print(f"Most recent 5-min candle close: ₹{close_prices[-1]}")
    print(f"Oldest 5-min candle close: ₹{close_prices[0]}")
    print(f"MA 20 (5-min): ₹{round(ma20, 2)}")
    print(f"==============================\n")

    return round(ma20, 2)


# ============================================
# UPDATED get_ma20() FUNCTION FOR YOUR BOT
# ============================================

def get_ma20(instrument):
    """
    Calculate PROPER MA 20 from 5-minute candles
    (Converted from 1-minute data since API doesn't support 5-min)
    """
    # Fetch 100 one-minute candles (= 20 five-minute candles)
    candles = get_historical_candles(instrument, interval='1minute', count=100)

    if not candles:
        return None

    # Convert to 5-min candles and calculate MA 20
    ma20 = calculate_ma20_from_5min(candles)

    return ma20


# ============================================
# EXAMPLE USAGE / TEST
# ============================================

if __name__ == "__main__":
    # Example: Simulating 100 one-minute candles
    # In reality, these come from get_historical_candles()

    print("Testing 5-minute MA 20 calculation...")
    print("=" * 50)

    # Simulate 100 candles with prices gradually decreasing
    test_candles = []
    base_price = 52.00

    for i in range(100):
        candle = [
            f"2025-12-16 10:{i:02d}:00",  # timestamp
            base_price + (i * 0.01),  # open
            base_price + (i * 0.01) + 0.05,  # high
            base_price + (i * 0.01) - 0.05,  # low
            base_price + (i * 0.01) + 0.02,  # close
            100000  # volume
        ]
        test_candles.append(candle)

    # Test the conversion
    five_min = convert_1min_to_5min_candles(test_candles)
    print(f"\n✅ Converted {len(test_candles)} one-min candles")
    print(f"✅ Into {len(five_min)} five-min candles")

    # Test MA calculation
    ma_value = calculate_ma20_from_5min(test_candles)
    print(f"\n✅ MA 20 (5-min timeframe): ₹{ma_value}")

    print("\n" + "=" * 50)
    print("Integration instructions:")
    print("=" * 50)
    print("1. Copy the convert_1min_to_5min_candles() function")
    print("2. Copy the calculate_ma20_from_5min() function")
    print("3. Replace your get_ma20() function with the new one above")
    print("4. Run your bot - MA will now match 5-min charts!")



def check_bounce_signal(instrument):
    """Check if MA bounce condition is met"""
    # Get current data
    live_price = get_live_price(instrument)
    ma20 = get_ma20(instrument)

    if not live_price or not ma20:
        return False, "Unable to fetch data"

    # Calculate difference
    diff = live_price - ma20

    print(f"\n=== BOUNCE CHECK ===")
    print(f"Live Price: ₹{live_price}")
    print(f"MA 20: ₹{ma20}")
    print(f"Difference: ₹{diff:.2f}")

    # Check if price is touching or just crossed above MA
    if -0.10 <= diff <= BOUNCE_THRESHOLD:
        print("✅ BOUNCE SIGNAL: Price is touching MA 20!")
        return True, "BUY"
    elif diff > BOUNCE_THRESHOLD:
        print(f"⏳ WAIT: Price too far above MA (₹{diff:.2f})")
        return False, "WAIT - Price above MA"
    else:
        print(f"⏳ WAIT: Price below MA (₹{diff:.2f})")
        return False, "WAIT - Price below MA"


def place_order(symbol, instrument, live_price):
    """
    Place LIMIT BUY order via Upstox API
    Returns: order response or None if error
    """
    # Use configuration parameters from top of file
    quantity = QUANTITY  # ← lowercase 'quantity', gets value from UPPERCASE 'QUANTITY' at top
    target_pct = TARGET_PCT
    stoploss_pct = STOPLOSS_PCT

    # Calculate target and stop loss prices
    target_price = round(live_price * (1 + target_pct / 100), 2)
    stop_loss = round(live_price * (1 - stoploss_pct / 100), 2)

    # For LIMIT order, set slightly below current price for better fill
    limit_price = round(live_price - 0.05, 2)

    print(f"\n{'=' * 50}")
    print(f"🎯 PLACING ORDER: {symbol}")
    print(f"{'=' * 50}")
    print(f"   Entry Price (Limit): ₹{limit_price}")
    print(f"   Quantity: {quantity} shares")
    print(f"   Capital Required: ₹{limit_price * quantity:.2f}")
    print(f"   Target: ₹{target_price} (+{target_pct}% = +₹{(target_price - live_price) * quantity:.2f})")
    print(f"   Stop Loss: ₹{stop_loss} (-{stoploss_pct}% = -₹{(live_price - stop_loss) * quantity:.2f})")
    print(f"{'=' * 50}\n")

    # Order payload
    order_data = {
        "quantity": quantity,
        "product": "I",  # I = Intraday (MIS)
        "validity": "DAY",
        "price": limit_price,
        "tag": "MA_BOUNCE_BOT",
        "instrument_token": instrument,
        "order_type": "LIMIT",
        "transaction_type": "BUY",
        "disclosed_quantity": 0,
        "trigger_price": 0,
        "is_amo": False
    }

    try:
        # SAFETY CHECK: Confirm before placing order
        print("⚠️  ABOUT TO PLACE REAL ORDER!")
        confirm = input("Type 'YES' to confirm order placement: ")

        if confirm.upper() != "YES":
            print("❌ Order cancelled by user\n")
            return None

        # Place the order
        url = f"{BASE_URL}/order/place"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, json=order_data)

        print(f"\n📤 Order Response Status: {response.status_code}")
        print(f"Response: {response.text}\n")

        if response.status_code == 200:
            order_response = response.json()
            order_id = order_response.get("data", {}).get("order_id")
            print(f"✅ ORDER PLACED SUCCESSFULLY!")
            print(f"   Order ID: {order_id}")
            print(f"   Track in Upstox app\n")
            return order_response
        else:
            print(f"❌ Order placement failed: {response.text}\n")
            return None

    except Exception as e:
        print(f"❌ Exception placing order: {str(e)}\n")
        return None


# Replace your current loop with this:
for symbol, instrument in WATCHLIST.items():
    print(f"\n📊 Checking {symbol}...")
    signal, message = check_bounce_signal(instrument)
    print(f"🤖 {symbol}: {message}")

    # NEW: If BUY signal, place order
    if message == "BUY":
        live_price = get_live_price(instrument)
        if live_price:
            place_order(symbol, instrument, live_price)

    time.sleep(1)