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
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================

# Upstox API Credentials
API_KEY = "18185106-6257-4a85-a84a-2ea314f91927"
API_SECRET = "15m0va42ni"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTQwZDFhY2IwMTU5MjMwZjUyNzdjOGEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NTg1NTY2MCwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY1OTIyNDAwfQ.ZHiMlWfaJYLRSHLSTzrnJEim2WoVMUtd0dwb_FAVEGI"

# API Endpoints
BASE_URL = "https://api.upstox.com/v2"
MARKET_QUOTE_URL = f"{BASE_URL}/market-quote/quotes"
HISTORICAL_URL = f"{BASE_URL}/historical-candle"
ORDER_PLACE_URL = f"{BASE_URL}/order/place"

# Trading Parameters
QUANTITY = 10  # Number of shares per trade
MA_PERIOD = 20  # Moving Average period
BOUNCE_THRESHOLD = 0.30  # ±₹0.30 from MA to trigger signal
TARGET_PCT = 2.0  # 2% profit target
STOPLOSS_PCT = 1.0  # 1% stop loss

# Watchlist with ISINs
WATCHLIST = {
    "YESBANK": "INE528G01035",
    "SUZLON": "INE040H01021",
    "RPOWER": "INE614G01033",
    "IRFC": "INE053F01010",
    "IDFC": "INE092T01019",
}


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_headers():
    """Return API headers with authentication"""
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }


def get_live_price(symbol, isin):
    """
    Fetch current live price for a stock
    Returns: float (live price) or None if error
    """
    instrument_key = f"NSE_EQ|{isin}"

    try:
        response = requests.get(
            MARKET_QUOTE_URL,
            headers=get_headers(),
            params={"instrument_key": instrument_key}
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")  # First 500 chars

        if response.status_code == 200:
            data = response.json()
            # Navigate through nested structure
            quote_data = data.get("data", {}).get(instrument_key, {})
            live_price = quote_data.get("last_price")
            return live_price
        else:
            print(f"❌ Error fetching price for {symbol}: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Exception for {symbol}: {str(e)}")
        return None


def get_historical_data(isin, interval="1minute", days=5):
    """
    Fetch historical candle data for MA calculation
    Returns: list of candles or None if error
    """
    instrument_key = f"NSE_EQ|{isin}"
    to_date = datetime.now().strftime("%Y-%m-%d")

    url = f"{HISTORICAL_URL}/{instrument_key}/{interval}/2024-12-01/{to_date}"

    try:
        response = requests.get(url, headers=get_headers())

        if response.status_code == 200:
            data = response.json()
            candles = data.get("data", {}).get("candles", [])
            return candles
        else:
            print(f"❌ Error fetching historical data: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Exception fetching historical data: {str(e)}")
        return None


def calculate_ma(candles, period=20):
    """
    Calculate Moving Average from candle data
    Returns: float (MA value) or None if insufficient data
    """
    if not candles or len(candles) < period:
        return None

    # Get most recent 'period' candles
    recent_candles = candles[-period:]

    # Extract close prices (index 4 in candle data)
    close_prices = [candle[4] for candle in recent_candles]

    # Calculate average
    ma_value = sum(close_prices) / len(close_prices)

    # Debug info
    print(f"\n=== DEBUG INFO ===")
    print(f"Total candles fetched: {len(candles)}")
    print(f"Most recent candle close: ₹{close_prices[-1]}")
    print(f"Oldest candle close: ₹{close_prices[0]}")
    print(f"==================\n")

    return round(ma_value, 2)


def check_bounce_signal(live_price, ma_value, threshold=0.30):
    """
    Check if price is bouncing off MA (within threshold)
    Returns: "BUY", "WAIT", or error message
    """
    if live_price is None or ma_value is None:
        return "ERROR"

    difference = live_price - ma_value

    print(f"\n=== BOUNCE CHECK ===")
    print(f"Live Price: ₹{live_price}")
    print(f"MA {MA_PERIOD}: ₹{ma_value}")
    print(f"Difference: ₹{difference:.2f}")

    # Check if within bounce threshold
    if abs(difference) <= threshold:
        print(f"✅ BOUNCE SIGNAL: Price is touching MA {MA_PERIOD}!")
        return "BUY"
    elif difference > threshold:
        print(f"⏳ WAIT: Price too far above MA (₹{difference:.2f})")
        return "WAIT - Price above MA"
    else:
        print(f"⏳ WAIT: Price below MA (₹{difference:.2f})")
        return "WAIT - Price below MA"


def place_order(symbol, isin, live_price, quantity=QUANTITY):
    """
    Place LIMIT BUY order via Upstox API
    Returns: order response or None if error
    """
    # Calculate target and stop loss prices
    target_price = round(live_price * (1 + TARGET_PCT / 100), 2)
    stop_loss = round(live_price * (1 - STOPLOSS_PCT / 100), 2)

    # For LIMIT order, set slightly below current price for better fill
    limit_price = round(live_price - 0.05, 2)

    print(f"\n{'=' * 50}")
    print(f"🎯 PLACING ORDER: {symbol}")
    print(f"{'=' * 50}")
    print(f"   Entry Price (Limit): ₹{limit_price}")
    print(f"   Quantity: {quantity} shares")
    print(f"   Capital Required: ₹{limit_price * quantity:.2f}")
    print(f"   Target: ₹{target_price} (+{TARGET_PCT}% = +₹{(target_price - live_price) * quantity:.2f})")
    print(f"   Stop Loss: ₹{stop_loss} (-{STOPLOSS_PCT}% = -₹{(live_price - stop_loss) * quantity:.2f})")
    print(f"{'=' * 50}\n")

    # Order payload
    order_data = {
        "quantity": quantity,
        "product": "I",  # I = Intraday (MIS)
        "validity": "DAY",
        "price": limit_price,
        "tag": "MA_BOUNCE_BOT",
        "instrument_token": f"NSE_EQ|{isin}",
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
            print("❌ Order cancelled by user")
            return None

        # Place the order
        response = requests.post(
            ORDER_PLACE_URL,
            headers={**get_headers(), "Content-Type": "application/json"},
            json=order_data
        )

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
            print(f"❌ Order placement failed: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Exception placing order: {str(e)}")
        return None


def scan_watchlist():
    """
    Main function: Scan all stocks in watchlist for bounce signals
    """
    print("\n" + "=" * 50)
    print("SCANNING WATCHLIST FOR BOUNCE SIGNALS")
    print("=" * 50 + "\n")

    signals = []

    for symbol, isin in WATCHLIST.items():
        print(f"📊 Checking {symbol}...")

        # Step 1: Get live price
        live_price = get_live_price(symbol, isin)
        if live_price is None:
            print(f"⚠️  Skipping {symbol} - couldn't fetch price\n")
            continue

        # Step 2: Get historical data
        candles = get_historical_data(isin)
        if candles is None:
            print(f"⚠️  Skipping {symbol} - couldn't fetch historical data\n")
            continue

        # Step 3: Calculate MA
        ma_value = calculate_ma(candles, MA_PERIOD)
        if ma_value is None:
            print(f"⚠️  Skipping {symbol} - insufficient data for MA\n")
            continue

        # Step 4: Check bounce signal
        signal = check_bounce_signal(live_price, ma_value, BOUNCE_THRESHOLD)

        print(f"🤖 {symbol}: {signal}\n")

        # Step 5: If BUY signal, place order
        if signal == "BUY":
            order_result = place_order(symbol, isin, live_price)
            signals.append({
                "symbol": symbol,
                "signal": signal,
                "live_price": live_price,
                "ma_value": ma_value,
                "order_placed": order_result is not None
            })
        else:
            signals.append({
                "symbol": symbol,
                "signal": signal,
                "live_price": live_price,
                "ma_value": ma_value,
                "order_placed": False
            })

    return signals


# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("\n🚀 MA BOUNCE BOT v0.2 - Starting...\n")
    print(f"Configuration:")
    print(f"  - MA Period: {MA_PERIOD}")
    print(f"  - Bounce Threshold: ±₹{BOUNCE_THRESHOLD}")
    print(f"  - Quantity per trade: {QUANTITY} shares")
    print(f"  - Target: +{TARGET_PCT}%")
    print(f"  - Stop Loss: -{STOPLOSS_PCT}%")
    print(f"  - Product Type: INTRADAY (MIS)")
    print(f"  - Order Type: LIMIT\n")

    # Run the scan
    results = scan_watchlist()

    # Summary
    print("\n" + "=" * 50)
    print("SCAN COMPLETE - SUMMARY")
    print("=" * 50)

    buy_signals = [r for r in results if r["signal"] == "BUY"]
    orders_placed = [r for r in results if r.get("order_placed")]

    print(f"\n📊 Total stocks scanned: {len(results)}")
    print(f"✅ BUY signals detected: {len(buy_signals)}")
    print(f"📤 Orders placed: {len(orders_placed)}")

    if orders_placed:
        print(f"\n💰 Positions opened:")
        for order in orders_placed:
            print(f"   - {order['symbol']} @ ₹{order['live_price']}")

    print("\n🎯 Bot execution complete!")