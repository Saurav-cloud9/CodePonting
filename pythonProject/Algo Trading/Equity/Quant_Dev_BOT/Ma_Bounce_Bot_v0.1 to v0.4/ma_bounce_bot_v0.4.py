"""
MA BOUNCE BOT v0.4 - DYNAMIC STRATEGIES
=========================================
Two trading strategies based on time of day:
1. MORNING BOUNCE (9:15 AM - 1:30 PM): MA bounce with LIMIT orders
2. LATE SCALP (2:30 PM - 3:15 PM): Volume/volatility scalping with MARKET orders

New Features in v0.4:
- Time-based strategy switching
- Volume spike detection (2x multiplier)
- Volatility detection (1.5x multiplier)
- Dynamic order types (LIMIT morning, MARKET late)
- Dynamic targets (2% morning, 0.5% late)
- Force exit at 3:15 PM
"""

import requests
import json
import time
from datetime import datetime, timedelta
import winsound  # For audio alerts
import msvcrt

# ============================================
# CONFIGURATION
# ============================================

# Upstox API Credentials
API_KEY = "18185106-6257-4a85-a84a-2ea314f91927"
API_SECRET = "15m0va42ni"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTRiNmJhNTE3ZDE3NzU2N2ViYTViODAiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NjU1MDQzNywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY2NjEzNjAwfQ.HOR8lgVnIL0BZSLZO2YUriRYy5ECT1U3ZJmrMGf61n8"

# Watchlist
WATCHLIST = {
    "YESBANK": "NSE_EQ|INE528G01035",
    "SUZLON": "NSE_EQ|INE040H01021",
    "RPOWER": "NSE_EQ|INE614G01033",
    "IRFC": "NSE_EQ|INE053F01010",
    "IDFCFIRSTB": "NSE_EQ|INE092T01019",
    "SAIL": "NSE_EQ|INE114A01011",       # ₹133
    "PNB": "NSE_EQ|INE160A01022",        # ₹120
    "NATIONALUM": "NSE_EQ|INE139A01034", # ₹278
    "TATASTEEL": "NSE_EQ|INE081A01020",  # ₹170
    "IDEA": "NSE_EQ|INE669E01016",       # ₹9
    "ZEEL": "NSE_EQ|INE256A01028",       # ₹92
    "JPASSOCIAT": "NSE_EQ|INE455F01025", # ₹4
# New 7 AFFORDABLE stocks
    "CANBK": "NSE_EQ|INE476A01022",       # ₹100
    "NMDC": "NSE_EQ|INE584A01023",        # ₹72
    "IOC": "NSE_EQ|INE242A01010",         # ₹130
    "MANAPPURAM": "NSE_EQ|INE522D01027",  # ₹155
    "SOUTHBANK": "NSE_EQ|INE683A01023",   # ₹13
    "PCJEWELLER": "NSE_EQ|INE785M01013",  # ₹9
    "RCOM": "NSE_EQ|INE330H01018",        # ₹15-18
}

# Bot parameters
QUANTITY = 5
BOUNCE_THRESHOLD_PCT = 0.5  # 0.5% of stock price (flexible for all price ranges)
MA_PERIOD = 20

# API Base
BASE_URL = "https://api.upstox.com/v2"


# ============================================
# v0.4 NEW FUNCTIONS - STRATEGY SELECTION
# ============================================

def get_current_strategy():
    """
    Determine which trading strategy to use based on current time

    Returns:
        str: "MORNING_BOUNCE" or "LATE_SCALP" or "NO_TRADE" or "MARKET_CLOSED"
    """
    now = datetime.now().time()

    # Convert to comparable time objects
    morning_end = datetime.strptime("13:30", "%H:%M").time()  # 1:30 PM
    late_start = datetime.strptime("14:30", "%H:%M").time()  # 2:30 PM
    market_close = datetime.strptime("15:15", "%H:%M").time()  # 3:15 PM

    if now < morning_end:
        return "MORNING_BOUNCE"
    elif morning_end <= now < late_start:
        return "NO_TRADE"  # Transition period
    elif late_start <= now < market_close:
        return "LATE_SCALP"
    else:
        return "MARKET_CLOSED"


def get_strategy_params(strategy):
    """
    Get trading parameters based on strategy

    Args:
        strategy: "MORNING_BOUNCE" or "LATE_SCALP"

    Returns:
        dict: {target_pct, stoploss_pct, order_type}
    """
    if strategy == "MORNING_BOUNCE":
        return {
            'target_pct': 2.0,  # 2% target
            'stoploss_pct': 1.0,  # 1% stop loss
            'order_type': 'LIMIT'  # Use limit orders
        }
    elif strategy == "LATE_SCALP":
        return {
            'target_pct': 0.5,  # 0.5% target (quick scalp)
            'stoploss_pct': 0.3,  # 0.3% stop loss (tight)
            'order_type': 'MARKET'  # Use market orders for speed
        }
    else:
        return None


# ============================================
# v0.4 NEW FUNCTIONS - VOLUME & VOLATILITY
# ============================================

def detect_volume_spike(instrument):
    """
    Detect if current volume is significantly higher than average

    Args:
        instrument: Instrument key (e.g., 'NSE_EQ|INE528G01035')

    Returns:
        bool: True if volume spike detected
    """
    try:
        # Get last 10 minutes of 1-minute candles
        candles = get_historical_candles(instrument, 10)

        if len(candles) < 5:
            return False

        # Get current minute volume (last candle)
        current_volume = candles[-1]['volume']

        # Calculate average of previous 5 minutes
        avg_volume = sum(c['volume'] for c in candles[-6:-1]) / 5

        # Check if current volume is 2x average
        if current_volume >= (avg_volume * 2):
            return True

        return False

    except Exception as e:
        print(f"Error detecting volume spike: {e}")
        return False


def detect_high_volatility(instrument):
    """
    Detect if current volatility is higher than normal

    Args:
        instrument: Instrument key

    Returns:
        bool: True if high volatility detected
    """
    try:
        # Get last 10 minutes of 1-minute candles
        candles = get_historical_candles(instrument, 10)

        if len(candles) < 5:
            return False

        # Calculate price range for current minute
        current_range = candles[-1]['high'] - candles[-1]['low']

        # Calculate average range of previous 5 minutes
        avg_range = sum(c['high'] - c['low'] for c in candles[-6:-1]) / 5

        # Check if current range is 1.5x average
        if current_range >= (avg_range * 1.5):
            return True

        return False

    except Exception as e:
        print(f"Error detecting volatility: {e}")
        return False


# ============================================
# EXISTING FUNCTIONS (Enhanced for v0.4)
# ============================================

def get_live_price(instrument):
    """Get real-time price for an instrument"""
    try:
        url = f"{BASE_URL}/market-quote/quotes"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }
        params = {"instrument_key": instrument}

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()

            # Check if data exists
            if 'data' not in data or not data['data']:
                print(f"  ⏭️  Skipped - stock might be suspended/halted")
                return None

            # Get the first (and only) key from the data dict
            first_key = list(data['data'].keys())[0]
            ltp = data['data'][first_key]['last_price']
            return ltp
        else:
            print(f"Error getting price: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error in get_live_price: {e}")
        return None


def get_historical_candles(instrument, num_minutes=100):
    """
    Get historical 1-minute candles for today + yesterday

    Args:
        instrument: Instrument key
        num_minutes: Number of 1-minute candles to fetch (default 100 for MA20 calculation)

    Returns:
        list: List of candle dicts with keys: open, high, low, close, volume
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

    Args:
        candles_1min: List of 1-minute candle dicts

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


def get_ma20(instrument):
    """
    Calculate 20-period moving average using 5-minute candles

    Args:
        instrument: Instrument key

    Returns:
        float: MA20 value or None if insufficient data
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


def check_signal(instrument, strategy):
    """
    Check for trading signal based on current strategy

    Args:
        instrument: Instrument key
        strategy: "MORNING_BOUNCE" or "LATE_SCALP"

    Returns:
        tuple: (has_signal: bool, message: str)
    """
    try:
        live_price = get_live_price(instrument)

        if live_price is None:
            return False, "Could not get live price"

        # MORNING BOUNCE STRATEGY
        if strategy == "MORNING_BOUNCE":
            ma20 = get_ma20(instrument)

            if ma20 is None:
                return False, "Could not calculate MA20"

            # EFFICIENT LOGIC: Check position FIRST, then proximity
            if live_price >= ma20:
                # Calculate dynamic threshold based on current price
                dynamic_threshold = live_price * (BOUNCE_THRESHOLD_PCT / 100)
                distance = abs(live_price - ma20)

                if distance <= dynamic_threshold:
                    return True, f"BUY - Bounce detected! Price: ₹{live_price:.2f}, MA20: ₹{ma20:.2f}, Distance: ₹{distance:.2f}"
                else:
                    return False, f"WAIT - Price too far above MA (Distance: ₹{distance:.2f}, Threshold: ₹{dynamic_threshold:.2f})"
            else:
                return False, f"WAIT - Price below MA (₹{live_price:.2f} < ₹{ma20:.2f})"

        # LATE SCALP STRATEGY (keep as is)
        elif strategy == "LATE_SCALP":
            # Check for volume spike
            has_volume_spike = detect_volume_spike(instrument)

            # Check for high volatility
            has_volatility = detect_high_volatility(instrument)

            # Get recent candles to check trend
            candles = get_historical_candles(instrument, 5)

            if len(candles) < 2:
                return False, "Insufficient data for trend check"

            # Check if price is trending UP (last 2 candles)
            is_uptrend = candles[-1]['close'] > candles[-2]['close']

            # Signal conditions:
            # 1. Volume spike OR high volatility
            # 2. AND price trending up
            if (has_volume_spike or has_volatility) and is_uptrend:
                conditions = []
                if has_volume_spike:
                    conditions.append("Volume spike")
                if has_volatility:
                    conditions.append("High volatility")

                return True, f"BUY - Scalp signal! {', '.join(conditions)}, Price: ₹{live_price:.2f}, Trending UP"
            else:
                return False, f"WAIT - No scalp signal (Vol: {has_volume_spike}, Volatility: {has_volatility}, Uptrend: {is_uptrend})"

        else:
            return False, "Unknown strategy"

    except Exception as e:
        print(f"Error checking signal: {e}")
        return False, f"Error: {e}"


# ============================================
# ORDER PLACEMENT WITH BRACKET ORDERS
# ============================================

def place_order(symbol, instrument, live_price, strategy):
    """
    Place BRACKET order via Upstox API
    (BUY + automatic target + automatic stop-loss in ONE order)

    Args:
        symbol: Stock symbol (e.g., 'YESBANK')
        instrument: Instrument key for API
        live_price: Current market price
        strategy: "MORNING_BOUNCE" or "LATE_SCALP"

    Returns:
        order response dict or None if failed
    """
    try:
        # Get strategy-specific parameters
        params = get_strategy_params(strategy)

        if not params:
            print(f"❌ Invalid strategy: {strategy}")
            return None

        # Extract parameters
        quantity = QUANTITY
        target_pct = params['target_pct']
        stoploss_pct = params['stoploss_pct']
        order_type = params['order_type']

        # Calculate target and stop-loss prices
        target_price = round(live_price * (1 + target_pct / 100), 2)
        stoploss_price = round(live_price * (1 - stoploss_pct / 100), 2)

        # Calculate absolute differences for bracket order
        # (Upstox bracket orders need DIFFERENCE from entry, not absolute price)
        square_off_value = round(target_price - live_price, 2)
        stoploss_value = round(live_price - stoploss_price, 2)

        # Determine entry order price based on order type
        if order_type == "LIMIT":
            # For LIMIT: place slightly below current for better fill
            entry_price = round(live_price - 0.01, 2)
        else:  # MARKET
            # For MARKET: use current price as reference (actual execution at best price)
            entry_price = live_price

        # Display order details
        print(f"\n{'=' * 60}")
        print(f"🎯 PLACING BRACKET ORDER: {symbol} ({strategy})")
        print(f"{'=' * 60}")
        print(f"   Order Type: {order_type}")
        if order_type == "LIMIT":
            print(f"   Entry Price: ₹{entry_price} (LIMIT)")
        else:
            print(f"   Entry Price: ₹{entry_price} (MARKET - best available)")
        print(f"   Quantity: {quantity} shares")
        print(f"   Capital Required: ₹{entry_price * quantity:.2f}")
        print(f"")
        print(f"   📈 TARGET: ₹{target_price} (+{target_pct}% = +₹{square_off_value * quantity:.2f} profit)")
        print(f"   📉 STOP LOSS: ₹{stoploss_price} (-{stoploss_pct}% = -₹{stoploss_value * quantity:.2f} loss)")
        print(f"")
        print(f"   ✅ Bracket order: Broker will AUTO-SELL at target or stop-loss!")
        print(f"{'=' * 60}\n")

        # Prepare BRACKET order payload for Upstox API
        order_data = {
            "quantity": quantity,
            "product": "I",  # I = Intraday (MIS with bracket support)
            "validity": "DAY",
            "price": entry_price if order_type == "LIMIT" else 0,
            "tag": f"v0.4_bracket_{strategy}",
            "instrument_token": instrument,
            "order_type": order_type,
            "transaction_type": "BUY",
            "disclosed_quantity": 0,
            "trigger_price": 0,
            "is_amo": False,
            # BRACKET ORDER PARAMETERS:
            "square_off": square_off_value,  # Auto-sell when profit = this amount
            "stop_loss": stoploss_value  # Auto-sell when loss = this amount
        }

        # SAFETY CHECK: Manual confirmation before placing order
        print("⚠️  ABOUT TO PLACE REAL BRACKET ORDER!")
        print("    (Broker will automatically handle exits)")
        confirm = input("\nType 'YES' to confirm: ")

        if confirm.upper() != "YES":
            print("❌ Order cancelled by user\n")
            return None

        # Place the bracket order via Upstox API
        url = f"{BASE_URL}/order/place"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, json=order_data)

        print(f"\n📤 Order Response Status: {response.status_code}")

        if response.status_code == 200:
            order_response = response.json()
            order_id = order_response.get("data", {}).get("order_id")
            print(f"✅ BRACKET ORDER PLACED SUCCESSFULLY!")
            print(f"   Order ID: {order_id}")
            print(f"   Entry + Target + Stop-Loss all active!")
            print(f"   Track in Upstox app\n")
            return order_response
        else:
            print(f"❌ Order placement failed!")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            print(f"\n   NOTE: If bracket orders not supported, we'll need to use simple orders")
            print(f"         and handle exits separately in v0.5\n")
            return None

    except Exception as e:
        print(f"❌ Exception placing order: {str(e)}\n")
        return None


def get_existing_positions():
    """
    Fetch current open positions from Upstox

    Returns:
        list: List of stock symbols that have open positions
    """
    try:
        url = f"{BASE_URL}/portfolio/short-term-positions"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            positions = data.get("data", [])

            # Extract symbols from positions
            active_symbols = []
            for position in positions:
                # Get trading symbol (like "YESBANK", "SUZLON")
                trading_symbol = position.get("tradingsymbol", "")
                if trading_symbol:
                    active_symbols.append(trading_symbol)

            return active_symbols
        else:
            print(f"⚠️  Could not fetch positions: {response.status_code}")
            return []

    except Exception as e:
        print(f"⚠️  Error fetching positions: {e}")
        return []


# ============================================
# MAIN BOT LOOP
# ============================================

def run_bot():
    """Main bot execution loop"""

    print("\n" + "=" * 60)
    print("MA BOUNCE BOT v0.4 - DYNAMIC STRATEGIES")
    print("=" * 60)
    print("Strategies:")
    print("  🌅 MORNING BOUNCE (9:15 AM - 1:30 PM)")
    print("     - MA bounce detection, LIMIT orders")
    print("     - 2% target, 1% stop-loss")
    print()
    print("  🌆 LATE SCALP (2:30 PM - 3:15 PM)")
    print("     - Volume/volatility scalping, MARKET orders")
    print("     - 0.5% target, 0.3% stop-loss")
    print("=" * 60 + "\n")

    print("🔍 Checking for existing positions...")
    active_positions = get_existing_positions()
    if active_positions:
        print(f"📝 Found existing positions: {active_positions}")
    else:
        print("📝 No existing positions found")
    print()

    while True:
        try:
            # Check current strategy
            strategy = get_current_strategy()

            if strategy == "MARKET_CLOSED":
                print("⏰ Market is closed. Bot stopping.")
                break

            elif strategy == "NO_TRADE":
                print("⏸️  Transition period (1:30 PM - 2:30 PM). Pausing...")
                time.sleep(300)  # Wait 5 minutes
                continue

            # Display current strategy
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{current_time}] Current Strategy: {strategy}")
            print("-" * 60)

            # Scan watchlist
            for symbol, instrument in WATCHLIST.items():
                print(f"\nScanning {symbol}...")

                has_signal, message = check_signal(instrument, strategy)
                print(f"  {message}")

                if has_signal:
                    if symbol in active_positions:
                        print(f"⏭️  SKIP - Already have {symbol} position")
                        continue

                    print("\n" + "=" * 60)
                    print(f"🔔 SIGNAL DETECTED FOR {symbol}!")
                    print("=" * 60)
                    print("⚠️  Press ENTER to acknowledge and proceed with order")
                    print("    (Auto-stops after 3 beeps / 15 seconds)")
                    print("=" * 60 + "\n")

                    max_beeps = 3
                    acknowledged = False

                    for beep_num in range(1, max_beeps + 1):
                        winsound.Beep(800, 200)
                        time.sleep(0.1)
                        winsound.Beep(1000, 200)
                        time.sleep(0.1)
                        winsound.Beep(1200, 400)

                        print(f"🔔 Alert #{beep_num}/3 - Press ENTER to stop beeping...")

                        for _ in range(50):
                            if msvcrt.kbhit():
                                key = msvcrt.getch()
                                if key in [b'\r', b'\n']:
                                    print("\n✅ Alert acknowledged!\n")
                                    acknowledged = True
                                    break
                            time.sleep(0.1)

                        if acknowledged:
                            break

                    if not acknowledged:
                        print("\n⏰ Auto-acknowledged after 15 seconds\n")

                    live_price = get_live_price(instrument)
                    if live_price:
                        order_result = place_order(symbol, instrument, live_price, strategy)
                        if order_result:
                            active_positions.append(symbol)
                            print(f"📝 Added {symbol} to active positions: {active_positions}")

            # Wait before next scan
            print(f"\n⏳ Waiting 60 seconds before next scan...")
            time.sleep(60)

        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped by user.")
            break
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")
            time.sleep(60)

    print("\n" + "=" * 60)
    print("Bot execution completed.")
    print("=" * 60 + "\n")


# ============================================
# RUN THE BOT
# ============================================

if __name__ == "__main__":
    run_bot()