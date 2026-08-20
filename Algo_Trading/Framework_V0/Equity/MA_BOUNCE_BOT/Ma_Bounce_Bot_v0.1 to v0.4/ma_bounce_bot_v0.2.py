"""
MA BOUNCE BOT v0.2 - WITH ORDER PLACEMENT
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
from datetime import datetime

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

    to_date = datetime.now().strftime("%Y-%m-%d")
    print(f"DEBUG: Fetching candles up to: {to_date}")
    url = f"{BASE_URL}/historical-candle/{instrument}/{interval}/{to_date}"
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

def get_ma20(instrument):
    """Calculate MA 20 from 1-min candles (equivalent to 20x5min)"""
    candles = get_historical_candles(instrument, interval='1minute', count=100)  # 100 mins = 20x5min

    if candles:
        print(f"\n=== DEBUG INFO ===")
        print(f"Total candles fetched: {len(candles)}")
        print(f"Most recent candle close: ₹{candles[0][4]}")  # First candle is most recent
        print(f"DEBUG: First candle close: ₹{candles[0][4]}, Last candle close: ₹{candles[-1][4]}")
        print(f"Oldest candle close: ₹{candles[-1][4]}")  # Last candle is oldest
        print(f"==================\n")

        close_prices = [candle[4] for candle in candles]
        ma20 = sum(close_prices) / len(close_prices)
        return round(ma20, 2)
    return None



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