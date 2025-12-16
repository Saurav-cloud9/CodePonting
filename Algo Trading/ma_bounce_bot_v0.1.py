import requests
import time
from datetime import datetime

# Configuration
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

# Bot parameters
QUANTITY = 25  # shares per trade
STOP_LOSS = 0.20  # Rs below entry
TARGET = 0.50  # Rs above entry

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
    url = f"{BASE_URL}/historical-candle/{instrument}/{interval}/2025-12-12"
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

    # Bounce conditions
    TOUCH_THRESHOLD = 0.30  # Price within ₹0.30 of MA is "touching"

    print(f"\n=== BOUNCE CHECK ===")
    print(f"Live Price: ₹{live_price}")
    print(f"MA 20: ₹{ma20}")
    print(f"Difference: ₹{diff:.2f}")

    # Check if price is touching or just crossed above MA
    if -0.10 <= diff <= TOUCH_THRESHOLD:
        print("✅ BOUNCE SIGNAL: Price is touching MA 20!")
        return True, "BUY"
    elif diff > TOUCH_THRESHOLD:
        print(f"⏳ WAIT: Price too far above MA (₹{diff:.2f})")
        return False, "WAIT - Price above MA"
    else:
        print(f"⏳ WAIT: Price below MA (₹{diff:.2f})")
        return False, "WAIT - Price below MA"


def place_order(symbol, signal, live_price):
    """
    Place buy order when bounce signal detected
    """
    if signal != "BUY":
        return

    # Order parameters
    quantity = 10  # Start small
    order_type = "MARKET"  # Or "LIMIT"
    product = "DELIVERY"  # Or "INTRADAY"

    # Calculate targets
    target_price = round(live_price * 1.02, 2)  # +2%
    stop_loss = round(live_price * 0.99, 2)  # -1%

    print(f"\n🎯 PLACING ORDER: {symbol}")
    print(f"   Entry: ₹{live_price}")
    print(f"   Quantity: {quantity}")
    print(f"   Target: ₹{target_price} (+2%)")
    print(f"   Stop Loss: ₹{stop_loss} (-1%)")

    # TODO: Add actual Upstox API order placement here

    return True

# Test all stocks in watchlist
print("\n" + "="*50)
print("SCANNING WATCHLIST FOR BOUNCE SIGNALS")
print("="*50)

for symbol, instrument in WATCHLIST.items():
    print(f"\n📊 Checking {symbol}...")
    signal, message = check_bounce_signal(instrument)
    print(f"🤖 {symbol}: {message}")
    time.sleep(1)  # Small delay to avoid API rate limits