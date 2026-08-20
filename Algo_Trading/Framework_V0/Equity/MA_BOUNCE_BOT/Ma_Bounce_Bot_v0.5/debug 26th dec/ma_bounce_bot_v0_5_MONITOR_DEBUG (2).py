"""
MA BOUNCE BOT v0.5 - MONITOR-ONLY MODE
============================================================
Two trading strategies based on time of day:
1. MORNING BOUNCE (9:15 AM - 1:30 PM): MA bounce with LIMIT orders
2. LATE SCALP (2:30 PM - 3:15 PM): Volume/volatility scalping with MARKET orders

**MONITOR-ONLY MODE**: 
- Detects and logs signals WITHOUT placing orders
- Logs signals to CSV file for Excel validation
- Cross-check MA20 accuracy with TradingView charts
"""

# ============================================
# MONITOR-ONLY MODE FLAG
# ============================================
MONITOR_ONLY = True  # Set to False to enable actual trading

import requests
import json
import time
from datetime import datetime, timedelta
import winsound  # For audio alerts
import msvcrt
import os
import sys
import csv  # For signal logging

# ============================================
# CONFIGURATION
# ============================================

# Upstox API Credentials
API_KEY = "18185106-6257-4a85-a84a-2ea314f91927"
API_SECRET = "15m0va42ni"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTRkY2ZmYzNlZDdhNDU2NmM3NGE0ODIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NjcwNzE5NiwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY2Nzg2NDAwfQ.gvlbJFWY94keKrs6AABK4EITgTQ7sFXx-PPiDnoBCio"

# Watchlist
WATCHLIST = {
    "YESBANK": "NSE_EQ|INE528G01035",
    "SUZLON": "NSE_EQ|INE040H01021",
    "RPOWER": "NSE_EQ|INE614G01033",
    "IRFC": "NSE_EQ|INE053F01010",
    "IDFC": "NSE_EQ|INE092T01019",
    "IDFCFIRSTB": "NSE_EQ|INE092T01019",  # Same as IDFC (Upstox symbol)
    "SAIL": "NSE_EQ|INE114A01011",
    "PNB": "NSE_EQ|INE160A01022",
    "NATIONALUM": "NSE_EQ|INE139A01034",
    "TATASTEEL": "NSE_EQ|INE081A01020",
    "IDEA": "NSE_EQ|INE669E01016",
    "ZEEL": "NSE_EQ|INE256A01028",
    "JPASSOCIAT": "NSE_EQ|INE455F01025",
    "CANBK": "NSE_EQ|INE476A01022",
    "NMDC": "NSE_EQ|INE584A01023",
    "IOC": "NSE_EQ|INE242A01010",
    "MANAPPURAM": "NSE_EQ|INE522D01027",
    "SOUTHBANK": "NSE_EQ|INE683A01023",
    "PCJEWELLER": "NSE_EQ|INE785M01013",
    "RCOM": "NSE_EQ|INE330H01018",
}

# Bot parameters
QUANTITY = 5
BOUNCE_THRESHOLD_PCT = 0.5
MA_PERIOD = 20

# API Base
BASE_URL = "https://api.upstox.com/v2"

# Signal logging file
SIGNAL_LOG_FILE = "signal_log.csv"

# ============================================
# NSE TRADING HOLIDAYS 2024-2025
# ============================================
NSE_HOLIDAYS = [
    # 2024
    "2024-01-26",  # Republic Day
    "2024-03-08",  # Mahashivratri
    "2024-03-25",  # Holi
    "2024-03-29",  # Good Friday
    "2024-04-11",  # Id-Ul-Fitr
    "2024-04-17",  # Ram Navami
    "2024-04-21",  # Mahavir Jayanti
    "2024-05-01",  # Maharashtra Day
    "2024-05-23",  # Buddha Purnima
    "2024-06-17",  # Bakri Id
    "2024-07-17",  # Muharram
    "2024-08-15",  # Independence Day
    "2024-08-26",  # Janmashtami
    "2024-10-02",  # Gandhi Jayanti
    "2024-10-12",  # Dussehra
    "2024-11-01",  # Diwali
    "2024-11-15",  # Guru Nanak Jayanti
    "2024-12-25",  # Christmas
    
    # 2025
    "2025-01-26",  # Republic Day
    "2025-02-26",  # Mahashivratri
    "2025-03-14",  # Holi
    "2025-03-31",  # Id-Ul-Fitr
    "2025-04-10",  # Mahavir Jayanti
    "2025-04-14",  # Dr. Ambedkar Jayanti
    "2025-04-18",  # Good Friday
    "2025-05-01",  # Maharashtra Day
    "2025-05-12",  # Buddha Purnima
    "2025-06-07",  # Bakri Id
    "2025-08-15",  # Independence Day
    "2025-08-27",  # Janmashtami
    "2025-10-02",  # Gandhi Jayanti
    "2025-10-21",  # Dussehra
    "2025-11-05",  # Diwali (Laxmi Pujan)
    "2025-11-24",  # Guru Nanak Jayanti
    "2025-12-25",  # Christmas
]

# ============================================
# DASHBOARD STATE
# ============================================

dashboard_metrics = {
    "signals_today": 0,
    "trades_today": 0,
    "wins": 0,
    "losses": 0,
    "pnl": 0.0,
    "positions": {},  # {symbol: {qty, entry, current, pnl, target_pct, sl_pct, strategy}}
    "last_scan": None,
    "current_strategy": "WAITING"
}

# ============================================
# DASHBOARD DISPLAY FUNCTIONS
# ============================================

def move_cursor_to_top():
    """Move cursor to top of terminal"""
    sys.stdout.write('\033[H')
    sys.stdout.flush()


def draw_dashboard_header():
    """Draw live dashboard header"""
    now = datetime.now()
    time_str = now.strftime("%I:%M:%S %p")

    # Next scan countdown
    next_scan = "..."
    if dashboard_metrics["last_scan"]:
        elapsed = (now - dashboard_metrics["last_scan"]).total_seconds()
        remaining = max(0, 60 - int(elapsed))
        next_scan = f"{remaining}s"

    strategy = dashboard_metrics["current_strategy"]
    num_positions = len(dashboard_metrics["positions"])
    total_pnl = dashboard_metrics["pnl"]
    pnl_color = "\033[92m" if total_pnl >= 0 else "\033[91m"

    # Colors
    RESET = '\033[0m'
    RED = '\033[91m'
    BLUE = '\033[38;5;33m'
    WHITE = '\033[97m'

    # Build lines with exact character counts
    line1 = f"MA Bounce Bot v0.5 - LIVE TRADING"
    line2 = f"{time_str} | {strategy:17s} | Next scan: {next_scan:5s}"
    line3 = f"TODAY: Signals: {dashboard_metrics['signals_today']:2d} | Trades: {dashboard_metrics['trades_today']:2d} | Win: {dashboard_metrics['wins']:2d} | Loss: {dashboard_metrics['losses']:2d} | P&L: {pnl_color}₹{total_pnl:+.2f}{WHITE}"
    line4 = f"POSITIONS: {num_positions} active"

    header = f"""{RED}╔══════════════════════════════════════════════════════════════════════════╗{RESET}
{RED}║{RESET} {BLUE}{line1:<72s}{RESET} {RED}║{RESET}
{RED}║{RESET} {BLUE}{line2:<72s}{RESET} {RED}║{RESET}
{RED}╠══════════════════════════════════════════════════════════════════════════╣{RESET}
{RED}║{RESET} {WHITE}{line3:<82s}{RESET} {RED}║{RESET}
{RED}║{RESET} {WHITE}{line4:<72s}{RESET} {RED}║{RESET}
"""

    if dashboard_metrics["positions"]:
        for symbol, pos in dashboard_metrics["positions"].items():
            if pos['entry'] <= 0:
                continue

            pnl_pct = ((pos['current'] - pos['entry']) / pos['entry']) * 100
            pnl_amt = (pos['current'] - pos['entry']) * pos['qty']
            pnl_sign = "+" if pnl_amt >= 0 else ""

            if pnl_pct >= pos['target_pct']:
                status = f"\033[92m[T]{RESET}"
            elif pnl_pct <= -pos['sl_pct']:
                status = "\033[91m[SL]\033[0m"
            else:
                status = "   "

            pos_line = f"└─ {symbol:10s} {pos['qty']:2d}@₹{pos['entry']:.2f} → ₹{pos['current']:.2f} ({pnl_sign}{pnl_pct:+.2f}%) {status}"
            header += f"{RED}║{RESET}  {WHITE}{pos_line:<72s}{RESET} {RED}║{RESET}\n"

    header += f"{RED}╚══════════════════════════════════════════════════════════════════════════╝{RESET}\n"
    return header

def update_dashboard():
    """Update dashboard in-place"""
    move_cursor_to_top()
    print(draw_dashboard_header(), end='', flush=True)

def log_with_color(message, level="INFO"):
    """Colored logging that works with dashboard"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "SIGNAL": "\033[95m"
    }
    reset = "\033[0m"
    color = colors.get(level, "")
    print(f"{color}[{timestamp}] {message}{reset}", flush=True)

def clear_screen():
    """Clear screen once at startup"""
    os.system('cls' if os.name == 'nt' else 'clear')

# ============================================
# STRATEGY SELECTION
# ============================================

def get_current_strategy():
    """Determine trading strategy based on time"""
    now = datetime.now().time()
    morning_end = datetime.strptime("13:30", "%H:%M").time()
    late_start = datetime.strptime("14:30", "%H:%M").time()
    market_close = datetime.strptime("15:15", "%H:%M").time()

    if now < morning_end:
        return "MORNING_BOUNCE"
    elif morning_end <= now < late_start:
        return "NO_TRADE"
    elif late_start <= now < market_close:
        return "LATE_SCALP"
    else:
        return "MARKET_CLOSED"

def get_strategy_params(strategy):
    """Get parameters for strategy"""
    if strategy == "MORNING_BOUNCE":
        return {
            'target_pct': 2.0,
            'stoploss_pct': 1.0,
            'order_type': 'LIMIT'
        }
    elif strategy == "LATE_SCALP":
        return {
            'target_pct': 0.5,
            'stoploss_pct': 0.3,
            'order_type': 'MARKET'
        }
    return None

# ============================================
# TRADING DAY DETECTION
# ============================================

def get_last_trading_day():
    """Get the last trading day (skip weekends and holidays)"""
    current_date = datetime.now().date()
    days_back = 1
    
    while days_back < 10:  # Look back max 10 days
        check_date = current_date - timedelta(days=days_back)
        
        # Skip weekends (Saturday=5, Sunday=6)
        if check_date.weekday() >= 5:
            days_back += 1
            continue
        
        # Skip NSE holidays
        date_str = check_date.strftime('%Y-%m-%d')
        if date_str in NSE_HOLIDAYS:
            days_back += 1
            continue
        
        # Found a valid trading day!
        return date_str
    
    # Fallback: just return yesterday if we can't find anything
    return (current_date - timedelta(days=1)).strftime('%Y-%m-%d')

# ============================================
# VOLUME & VOLATILITY DETECTION
# ============================================

def detect_volume_spike(instrument):
    """Detect volume spike"""
    try:
        candles = get_historical_candles(instrument, 10)
        if len(candles) < 5:
            return False

        current_volume = candles[-1]['volume']
        avg_volume = sum(c['volume'] for c in candles[-6:-1]) / 5
        return current_volume >= (avg_volume * 2)
    except:
        return False

def detect_high_volatility(instrument):
    """Detect high volatility"""
    try:
        candles = get_historical_candles(instrument, 10)
        if len(candles) < 5:
            return False

        current_range = candles[-1]['high'] - candles[-1]['low']
        avg_range = sum(c['high'] - c['low'] for c in candles[-6:-1]) / 5
        return current_range >= (avg_range * 1.5)
    except:
        return False

# ============================================
# API FUNCTIONS
# ============================================

def get_live_price(instrument):
    """Get real-time price"""
    try:
        url = f"{BASE_URL}/market-quote/quotes"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }
        params = {"instrument_key": instrument}

        response = requests.get(url, headers=headers, params=params)
        
        print(f"DEBUG Live Price: Status={response.status_code}")  # Debug
        
        if response.status_code != 200:
            print(f"DEBUG Live Price Error: {response.text[:200]}")  # Debug
            return None

        if response.status_code == 200:
            data = response.json()
            if 'data' not in data or not data['data']:
                print(f"DEBUG: No data in response")  # Debug
                return None
            first_key = list(data['data'].keys())[0]
            price = data['data'][first_key]['last_price']
            print(f"DEBUG: Got price={price}")  # Debug
            return price
        return None
    except Exception as e:
        print(f"DEBUG Live Price Exception: {e}")  # Debug
        return None

def get_historical_candles(instrument, num_minutes=100):
    """Get historical candles from today and last trading day"""
    try:
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = get_last_trading_day()  # ✨ Get last trading day (skip holidays/weekends)
        
        url = f"{BASE_URL}/historical-candle/{instrument}/1minute/{from_date}/{to_date}"
        
        print(f"DEBUG: API URL - from {from_date} to {to_date}")

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

            return candles[:num_minutes] if len(candles) >= num_minutes else candles
        return []
    except:
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

def get_ma20(instrument):
    """Calculate MA20"""
    try:
        candles_1min = get_historical_candles(instrument, 100)
        if len(candles_1min) < 100:
            return None

        # DEBUG: Print first and last few candles BEFORE reversing
        print(f"\n🔍 DEBUG MA20 - BEFORE reverse (API order - newest first):")
        print(f"   Total 1-min candles: {len(candles_1min)}")
        print(f"   First 3 (newest): {[(c['timestamp'], c['close']) for c in candles_1min[:3]]}")
        print(f"   Last 3 (oldest): {[(c['timestamp'], c['close']) for c in candles_1min[-3:]]}")

        # ✨ FIX: REVERSE to chronological order (oldest first, newest last)
        # API returns candles newest-first, but we need to group them chronologically
        candles_1min = list(reversed(candles_1min))

        # DEBUG: Print first and last few candles AFTER reversing
        print(f"\n🔍 DEBUG MA20 - AFTER reverse (chronological - oldest first):")
        print(f"   First 3 (oldest): {[(c['timestamp'], c['close']) for c in candles_1min[:3]]}")
        print(f"   Last 3 (newest): {[(c['timestamp'], c['close']) for c in candles_1min[-3:]]}")

        candles_5min = convert_to_5min_candles(candles_1min)
        if len(candles_5min) < 20:
            return None

        # DEBUG: Print the 20 five-minute candles used for MA20
        print(f"\n🔍 DEBUG MA20 - 5-min candles created:")
        print(f"   Total 5-min candles: {len(candles_5min)}")
        print(f"   Using last 20 candles for MA20:")
        for i, c in enumerate(candles_5min[-20:], 1):
            print(f"   {i:2d}. {c['timestamp']} Close: ₹{c['close']:.2f}")

        last_20_closes = [c['close'] for c in candles_5min[-20:]]
        ma20 = round(sum(last_20_closes) / 20, 2)
        
        print(f"\n   Sum: ₹{sum(last_20_closes):.2f}")
        print(f"   MA20: ₹{ma20:.2f}")
        
        return ma20
    except Exception as e:
        print(f"DEBUG MA20 Exception: {e}")
        return None

def check_signal(instrument, strategy):
    """Check for trading signal"""
    try:
        live_price = get_live_price(instrument)
        if live_price is None:
            return False, "Could not get live price"

        if strategy == "MORNING_BOUNCE":
            ma20 = get_ma20(instrument)
            if ma20 is None:
                return False, "Could not calculate MA20"

            # Safety check for division by zero
            if ma20 <= 0:
                return False, "Invalid MA20 value"

            if live_price >= ma20:
                dynamic_threshold = live_price * (BOUNCE_THRESHOLD_PCT / 100)
                distance = abs(live_price - ma20)

                if distance <= dynamic_threshold:
                    return True, f"BUY - Bounce detected! Price: ₹{live_price:.2f}, MA20: ₹{ma20:.2f}, Distance: ₹{distance:.2f}"
                else:
                    return False, f"WAIT - Price too far above MA (Distance: ₹{distance:.2f}, Threshold: ₹{dynamic_threshold:.2f})"
            else:
                return False, f"WAIT - Price below MA (₹{live_price:.2f} < ₹{ma20:.2f})"

        elif strategy == "LATE_SCALP":
            has_volume_spike = detect_volume_spike(instrument)
            has_volatility = detect_high_volatility(instrument)
            candles = get_historical_candles(instrument, 5)

            if len(candles) < 2:
                return False, "Insufficient data for trend check"

            is_uptrend = candles[-1]['close'] > candles[-2]['close']

            if (has_volume_spike or has_volatility) and is_uptrend:
                conditions = []
                if has_volume_spike:
                    conditions.append("Volume spike")
                if has_volatility:
                    conditions.append("High volatility")
                return True, f"BUY - Scalp signal! {', '.join(conditions)}, Price: ₹{live_price:.2f}, Trending UP"
            else:
                return False, f"WAIT - No scalp signal (Vol: {has_volume_spike}, Volatility: {has_volatility}, Uptrend: {is_uptrend})"

        return False, "Unknown strategy"
    except ZeroDivisionError:
        return False, "Math error (division by zero)"
    except Exception as e:
        return False, f"Error: {e}"

# ============================================
# POSITION TRACKING
# ============================================

def add_position_to_dashboard(symbol, qty, entry_price, target_pct, sl_pct, strategy):
    """Add position to dashboard tracking"""
    dashboard_metrics["positions"][symbol] = {
        "qty": qty,
        "entry": entry_price,
        "current": entry_price,
        "pnl": 0.0,
        "target_pct": target_pct,
        "sl_pct": sl_pct,
        "strategy": strategy
    }
    dashboard_metrics["trades_today"] += 1

def update_position_prices():
    """Update current prices for all tracked positions"""
    for symbol, pos in list(dashboard_metrics["positions"].items()):
        instrument = WATCHLIST.get(symbol)
        if instrument:
            current_price = get_live_price(instrument)
            if current_price:
                pos["current"] = current_price
                pos["pnl"] = (current_price - pos["entry"]) * pos["qty"]

                # Check for target/SL hit
                pnl_pct = ((current_price - pos["entry"]) / pos["entry"]) * 100
                if pnl_pct >= pos["target_pct"]:
                    log_with_color(f"🎯 TARGET HIT: {symbol} at ₹{current_price:.2f} (+{pnl_pct:.2f}%)", "SUCCESS")
                    dashboard_metrics["wins"] += 1
                    dashboard_metrics["pnl"] += pos["pnl"]
                    del dashboard_metrics["positions"][symbol]
                elif pnl_pct <= -pos["sl_pct"]:
                    log_with_color(f"🛑 STOP-LOSS HIT: {symbol} at ₹{current_price:.2f} ({pnl_pct:.2f}%)", "ERROR")
                    dashboard_metrics["losses"] += 1
                    dashboard_metrics["pnl"] += pos["pnl"]
                    del dashboard_metrics["positions"][symbol]

# ============================================
# SIGNAL LOGGING
# ============================================

def log_signal_to_csv(symbol, strategy, live_price, ma20, bounce_pct, target_pct, stoploss_pct):
    """Log detected signals to CSV file for validation"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if file exists to write headers
    file_exists = os.path.isfile(SIGNAL_LOG_FILE)
    
    with open(SIGNAL_LOG_FILE, 'a', newline='') as csvfile:
        fieldnames = ['Timestamp', 'Symbol', 'Strategy', 'Live_Price', 'MA20', 'Bounce_Pct', 
                      'Target_Pct', 'Stoploss_Pct', 'Target_Price', 'SL_Price']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        target_price = round(live_price * (1 + target_pct / 100), 2)
        sl_price = round(live_price * (1 - stoploss_pct / 100), 2)
        
        writer.writerow({
            'Timestamp': timestamp,
            'Symbol': symbol,
            'Strategy': strategy,
            'Live_Price': f"{live_price:.2f}",
            'MA20': f"{ma20:.2f}",
            'Bounce_Pct': f"{bounce_pct:.2f}",
            'Target_Pct': f"{target_pct:.1f}",
            'Stoploss_Pct': f"{stoploss_pct:.1f}",
            'Target_Price': f"{target_price:.2f}",
            'SL_Price': f"{sl_price:.2f}"
        })
    
    print(f"📝 Signal logged to {SIGNAL_LOG_FILE}")

# ============================================
# ORDER PLACEMENT
# ============================================

def place_order(symbol, instrument, live_price, strategy):
    """Place bracket order OR log signal in monitor-only mode"""
    try:
        params = get_strategy_params(strategy)
        if not params:
            return None

        target_pct = params['target_pct']
        stoploss_pct = params['stoploss_pct']
        order_type = params['order_type']

        # ============================================
        # MONITOR-ONLY MODE: Just log the signal
        # ============================================
        if MONITOR_ONLY:
            # Get MA20 for logging
            ma20 = get_ma20(instrument)
            if not ma20:
                ma20 = 0.0
            
            bounce_pct = ((live_price - ma20) / ma20 * 100) if ma20 > 0 else 0.0
            
            target_price = round(live_price * (1 + target_pct / 100), 2)
            stoploss_price = round(live_price * (1 - stoploss_pct / 100), 2)
            
            print(f"\n{'=' * 60}")
            print(f"📊 SIGNAL DETECTED (MONITOR-ONLY): {symbol} ({strategy})")
            print(f"{'=' * 60}")
            print(f"   Live Price: ₹{live_price:.2f}")
            print(f"   MA20: ₹{ma20:.2f}")
            print(f"   Bounce: {bounce_pct:+.2f}%")
            print(f"")
            print(f"   📈 Would TARGET: ₹{target_price} (+{target_pct}%)")
            print(f"   📉 Would STOP-LOSS: ₹{stoploss_price} (-{stoploss_pct}%)")
            print(f"   Order Type: {order_type}")
            print(f"")
            print(f"   ✅ Signal logged to CSV for validation")
            print(f"   🔍 Cross-check MA20 value with TradingView chart")
            print(f"{'=' * 60}\n")
            
            # Log to CSV
            log_signal_to_csv(symbol, strategy, live_price, ma20, bounce_pct, target_pct, stoploss_pct)
            
            return {"monitor_only": True, "symbol": symbol}

        # ============================================
        # LIVE TRADING MODE: Place actual order
        # ============================================
        quantity = QUANTITY

        target_price = round(live_price * (1 + target_pct / 100), 2)
        stoploss_price = round(live_price * (1 - stoploss_pct / 100), 2)
        square_off_value = round(target_price - live_price, 2)
        stoploss_value = round(live_price - stoploss_price, 2)

        entry_price = round(live_price - 0.01, 2) if order_type == "LIMIT" else live_price

        print(f"\n{'=' * 60}")
        print(f"🎯 PLACING BRACKET ORDER: {symbol} ({strategy})")
        print(f"{'=' * 60}")
        print(f"   Order Type: {order_type}")
        print(f"   Entry Price: ₹{entry_price} ({'LIMIT' if order_type == 'LIMIT' else 'MARKET - best available'})")
        print(f"   Quantity: {quantity} shares")
        print(f"   Capital Required: ₹{entry_price * quantity:.2f}")
        print(f"")
        print(f"   📈 TARGET: ₹{target_price} (+{target_pct}% = +₹{square_off_value * quantity:.2f} profit)")
        print(f"   📉 STOP LOSS: ₹{stoploss_price} (-{stoploss_pct}% = -₹{stoploss_value * quantity:.2f} loss)")
        print(f"")
        print(f"   ✅ Bracket order: Broker will AUTO-SELL at target or stop-loss!")
        print(f"{'=' * 60}\n")

        order_data = {
            "quantity": quantity,
            "product": "I",
            "validity": "DAY",
            "price": entry_price if order_type == "LIMIT" else 0,
            "tag": f"v0.4_bracket_{strategy}",
            "instrument_token": instrument,
            "order_type": order_type,
            "transaction_type": "BUY",
            "disclosed_quantity": 0,
            "trigger_price": 0,
            "is_amo": False,
            "square_off": square_off_value,
            "stop_loss": stoploss_value
        }

        print("⚠️  ABOUT TO PLACE REAL BRACKET ORDER!")
        print("    (Broker will automatically handle exits)")
        confirm = input("\nType 'YES' to confirm: ")

        if confirm.upper() != "YES":
            print("❌ Order cancelled by user\n")
            return None

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

            # Add to dashboard tracking
            add_position_to_dashboard(symbol, quantity, entry_price, target_pct, stoploss_pct, strategy)

            return order_response
        else:
            print(f"❌ Order placement failed: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Exception: {str(e)}\n")
        return None

def get_existing_positions():
    """Fetch existing positions from Upstox and load them into dashboard"""
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

            active_symbols = []
            for position in positions:
                trading_symbol = position.get("tradingsymbol", "")
                if not trading_symbol:
                    continue

                active_symbols.append(trading_symbol)

                # Add to dashboard if not already there
                if trading_symbol not in dashboard_metrics["positions"]:
                    qty = abs(position.get("quantity", 0))

                    if qty > 0:
                        # Get instrument key for this symbol
                        instrument = WATCHLIST.get(trading_symbol)
                        if not instrument:
                            print(f"⚠️  {trading_symbol} not in watchlist, skipping dashboard tracking")
                            continue

                        # Fetch current live price
                        current_price = get_live_price(instrument)
                        if not current_price:
                            print(f"⚠️  Could not fetch price for {trading_symbol}")
                            continue

                        # Use current price as entry (since API returns 0)
                        # Determine strategy based on time
                        current_strategy = get_current_strategy()
                        if current_strategy in ["MORNING_BOUNCE", "LATE_SCALP"]:
                            params = get_strategy_params(current_strategy)
                            if params:
                                add_position_to_dashboard(
                                    trading_symbol,
                                    qty,
                                    current_price,  # Use current as entry
                                    params['target_pct'],
                                    params['stoploss_pct'],
                                    current_strategy
                                )
                                print(f"✅ Loaded {trading_symbol}: {qty}@₹{current_price:.2f}")

            return active_symbols
        return []
    except Exception as e:
        print(f"⚠️  Error fetching positions: {e}")
        return []

# ============================================
# MAIN BOT LOOP
# ============================================

def run_bot():
    """Main bot execution"""

    # Initialize display
    clear_screen()
    print(draw_dashboard_header())

    print("\n" + "=" * 60)
    if MONITOR_ONLY:
        print("MA BOUNCE BOT v0.5 - MONITOR-ONLY MODE")
        print("=" * 60)
        print("⚠️  MONITOR-ONLY: Signals will be LOGGED, not TRADED")
        print("    - Detects MA bounce signals")
        print("    - Logs to signal_log.csv")
        print("    - Cross-check MA20 with TradingView")
        print("=" * 60)
    else:
        print("MA BOUNCE BOT v0.5 - LIVE TRADING MODE")
        print("=" * 60)
        print("⚠️  LIVE TRADING ENABLED: Real orders will be placed!")
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

    update_dashboard()

    while True:
        try:
            strategy = get_current_strategy()
            dashboard_metrics["current_strategy"] = strategy

            if strategy == "MARKET_CLOSED":
                print("⏰ Market closed. Bot stopping.")
                break

            elif strategy == "NO_TRADE":
                print("⏸️  Transition period (1:30 PM - 2:30 PM). Pausing...")
                time.sleep(300)
                continue

            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{current_time}] Current Strategy: {strategy}")
            print("-" * 60)

            dashboard_metrics["last_scan"] = datetime.now()

            # Update existing positions first
            if dashboard_metrics["positions"]:
                update_position_prices()
                update_dashboard()

            # Scan for new signals
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
                    
                    # In monitor-only mode, skip beeping and just log
                    if MONITOR_ONLY:
                        print("📊 MONITOR-ONLY MODE: Logging signal without placing order")
                        print("=" * 60 + "\n")
                        
                        live_price = get_live_price(instrument)
                        if live_price:
                            order_result = place_order(symbol, instrument, live_price, strategy)
                            if order_result:
                                print(f"✅ Signal logged successfully")
                    else:
                        # Live trading mode - beep and confirm
                        dashboard_metrics["signals_today"] += 1
                        
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

                    update_dashboard()

            # ============================================
            # WAIT UNTIL NEXT 5-MINUTE MARK
            # ============================================
            now = datetime.now()
            current_minute = now.minute
            current_second = now.second
            
            # Calculate next 5-minute mark (0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55)
            next_interval = ((current_minute // 5) + 1) * 5
            if next_interval >= 60:
                next_interval = 0
                next_scan_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            else:
                next_scan_time = now.replace(minute=next_interval, second=0, microsecond=0)
            
            sleep_seconds = (next_scan_time - now).total_seconds()
            
            print(f"\n⏳ Next scan at {next_scan_time.strftime('%H:%M:%S')} (in {int(sleep_seconds)} seconds)...")
            update_dashboard()
            time.sleep(sleep_seconds)

        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped by user.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(60)

    print("\n" + "=" * 60)
    print("Bot execution completed.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    run_bot()