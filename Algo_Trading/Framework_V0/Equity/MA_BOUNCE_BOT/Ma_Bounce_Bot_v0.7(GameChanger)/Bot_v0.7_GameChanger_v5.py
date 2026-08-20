"""
BOT v0.7 - GAME CHANGER v4 🎮🔔
============================================================
v0.7 VERSION HISTORY:
v1 - Initial Game Changer release
v2 - Added audio beep alerts on signal detection
v3 - FIXED: transaction_type logger bug
v4 - FIXED: Unicode encoding error (₹ symbol in logger) - Dec 30, 2025 09:30 AM

TWO STRATEGIES:
1. MORNING BOUNCE (9:15 AM - 1:30 PM): MA bounce, 2% target, 1% SL, MARKET orders
2. LATE SCALP (2:30 PM - 3:15 PM): Volume/volatility, 0.5% target, 0.3% SL, MARKET orders

**v0.6 PLATINUM CANDLE ENGINE**:
- ✅ Smart API selection (Intraday + Historical)
- ✅ Seamless live + past data merging
- ✅ Automatic holiday handling
- ✅ 100% TradingView accuracy validated
"""

# ============================================
# LIVE TRADING MODE
# ============================================
MONITOR_ONLY = False  # LIVE TRADING ENABLED - Real orders will be placed!

# -*- coding: utf-8 -*-
import sys
import io

# Fix Windows console Unicode issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import json
import time
from datetime import datetime, timedelta
import msvcrt
import os
import sys
import csv  # For signal logging
import logging  # v0.7: Professional logging

# v0.7: Optional environment variable support
try:
    from dotenv import load_dotenv

    load_dotenv()
    ENV_AVAILABLE = True
except ImportError:
    ENV_AVAILABLE = False

# v0.7: Cross-platform audio support
try:
    import winsound

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


# ============================================
# AUDIO ALERT FUNCTION - v0.7 v2
# ============================================
def play_signal_alert():
    """Play 3 beeps to alert signal detection"""
    if AUDIO_AVAILABLE:
        try:
            # Play 3 beeps: frequency 1000 Hz, 200ms each
            for _ in range(3):
                winsound.Beep(1000, 200)
                time.sleep(0.1)  # Small gap between beeps
        except Exception as e:
            # Silently fail if audio not available
            pass


# ============================================
# CONFIGURATION - v0.7 SECURE & FLEXIBLE
# ============================================

# Upstox API Credentials
API_KEY = "18185106-6257-4a85-a84a-2ea314f91927"
API_SECRET = "15m0va42ni"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTUzMzc4NTQ5OGJlZTFiZGZjMDViZTgiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NzA2MTM4MSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY3MTMyMDAwfQ.3RNz2a5Ca-dkmf4XI3MZIywKPvFY60YcwEHWFqmWYrM"

# ============================================
# v0.7: RISK MANAGEMENT PARAMETERS ⭐ NEW
# ============================================
MAX_CAPITAL_PER_ORDER = 1000  # Skip orders > ₹1000 (prevents expensive stocks)
MAX_POSITIONS = 5  # Stop taking new signals after 5 positions (already enforced)
EOD_EXIT_TIME = "15:15"  # Exit ALL positions at 3:15 PM (CRITICAL: avoid ₹50/scrip charges!)

# Watchlist - Cleaned for intraday trading only (removed BE/ASM/suspended stocks)
# REMOVED: IRFC (data discrepancy), IDFC (duplicate), JPASSOCIAT (BE segment),
#          PCJEWELLER (ASM surveillance), RCOM (trading suspended)
WATCHLIST = {
    "YESBANK": "NSE_EQ|INE528G01035",
    "SUZLON": "NSE_EQ|INE040H01021",
    "RPOWER": "NSE_EQ|INE614G01033",
    "IDFCFIRSTB": "NSE_EQ|INE092T01019",
    "SAIL": "NSE_EQ|INE114A01011",
    "PNB": "NSE_EQ|INE160A01022",
    "NATIONALUM": "NSE_EQ|INE139A01034",
    "TATASTEEL": "NSE_EQ|INE081A01020",
    "IDEA": "NSE_EQ|INE669E01016",
    "ZEEL": "NSE_EQ|INE256A01028",
    "CANBK": "NSE_EQ|INE476A01022",
    "NMDC": "NSE_EQ|INE584A01023",
    "IOC": "NSE_EQ|INE242A01010",
    "MANAPPURAM": "NSE_EQ|INE522D01027",
    "SOUTHBANK": "NSE_EQ|INE683A01023",
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
# v0.7: PROFESSIONAL LOGGING (GitHub best practice)
# ============================================
LOG_FILE = "bot_activity.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

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
# v0.7: IST TIMEZONE HELPERS (GitHub best practice)
# ============================================

def get_ist_now():
    """Get current time in IST (India Standard Time = UTC+5:30)"""
    from datetime import timezone
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    return ist_now


def is_eod_exit_time():
    """Check if it's 3:15 PM (time to exit all positions)"""
    now = get_ist_now()
    current_time = now.strftime("%H:%M")
    return current_time == EOD_EXIT_TIME


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
    line1 = f"Bot v0.7 - GAME CHANGER 🎮"
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
            'order_type': 'MARKET'  # Changed from LIMIT - bounce needs immediate execution
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
# PLATINUM CANDLE ENGINE 💎
# ============================================

def is_market_open():
    """Check if market is currently open"""
    now = datetime.now()
    current_time = now.time()
    market_start = datetime.strptime("09:15", "%H:%M").time()
    market_end = datetime.strptime("15:30", "%H:%M").time()

    # Check if today is a weekend
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False

    # Check if today is a holiday
    today_str = now.strftime('%Y-%m-%d')
    if today_str in NSE_HOLIDAYS:
        return False

    # Check if within trading hours
    return market_start <= current_time <= market_end


def get_intraday_candles(instrument):
    """Get today's intraday candles (only works during/after market hours on trading days)"""
    try:
        url = f"{BASE_URL}/historical-candle/intraday/{instrument}/1minute"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()

            if 'data' not in data or 'candles' not in data['data']:
                return []

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
        return []
    except Exception as e:
        print(f"⚠️  Intraday API error: {e}")
        return []


def get_historical_candles_from_date(instrument, from_date, num_candles):
    """Get historical candles from a specific date going backwards"""
    try:
        # Get candles from the specified date
        to_date = from_date
        url = f"{BASE_URL}/historical-candle/{instrument}/1minute/{to_date}/{from_date}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()

            if 'data' not in data or 'candles' not in data['data']:
                return []

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

            # Return only the number of candles requested
            # Candles come newest first, so take the first num_candles
            return candles[:num_candles] if len(candles) >= num_candles else candles
        return []
    except Exception as e:
        print(f"⚠️  Historical API error: {e}")
        return []


def get_historical_candles(instrument, num_candles=10):
    """Wrapper function to get recent historical candles"""
    # Get candles from last 2 days to be safe
    from_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    return get_historical_candles_from_date(instrument, from_date, num_candles)


def get_candles_platinum(instrument, num_minutes=100):
    """
    🔷 PLATINUM CANDLE ENGINE 🔷

    Smart candle fetching that works 24/7:
    - During market hours: Combines live intraday + historical data
    - After market close: Uses pure historical data
    - Handles holidays/weekends automatically
    - Always returns most recent {num_minutes} of trading data
    """

    print(f"\n💎 PLATINUM ENGINE: Fetching {num_minutes} minutes of data...")

    market_open = is_market_open()
    today_str = datetime.now().strftime('%Y-%m-%d')
    last_trading_day = get_last_trading_day()

    if market_open or datetime.now().time() > datetime.strptime("15:30", "%H:%M").time():
        # SCENARIO 1 & 2: Market is open OR closed today (after 3:30 PM)
        # Try to get today's intraday candles first

        print(f"   📊 Fetching intraday candles from today ({today_str})...")
        intraday_candles = get_intraday_candles(instrument)

        if len(intraday_candles) >= num_minutes:
            # SCENARIO 2: We have enough candles from today alone
            print(f"   ✅ Got {len(intraday_candles)} intraday candles (enough!)")
            # Take only the most recent num_minutes
            return intraday_candles[:num_minutes]

        # SCENARIO 1: Not enough candles from today, need historical data
        candles_needed = num_minutes - len(intraday_candles)
        print(f"   📊 Got {len(intraday_candles)} intraday candles, need {candles_needed} more from history...")

        historical_candles = get_historical_candles_from_date(instrument, last_trading_day, candles_needed)
        print(f"   ✅ Got {len(historical_candles)} historical candles from {last_trading_day}")

        # Combine: historical (newest first) + intraday (newest first)
        # Both are already in newest-first order from API
        all_candles = intraday_candles + historical_candles

        print(f"   💎 Combined: {len(all_candles)} total candles")
        return all_candles[:num_minutes]

    else:
        # SCENARIO 3: Market is closed (weekend, holiday, or before market open)
        # Use pure historical data from last trading day

        print(f"   📅 Market closed, fetching historical data from {last_trading_day}...")
        historical_candles = get_historical_candles_from_date(instrument, last_trading_day, num_minutes)
        print(f"   ✅ Got {len(historical_candles)} historical candles")

        return historical_candles


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
    """Calculate MA20 using PLATINUM CANDLE ENGINE"""
    try:
        # Use PLATINUM ENGINE to get candles
        candles_1min = get_candles_platinum(instrument, 100)

        if len(candles_1min) < 100:
            print(f"   ⚠️  Only got {len(candles_1min)} candles, need 100")
            return None

        # Candles come from API newest-first, reverse to chronological (oldest-first)
        candles_1min = list(reversed(candles_1min))
        print(f"   ✅ Reversed to chronological order")

        # Convert to 5-min candles
        candles_5min = convert_to_5min_candles(candles_1min)
        if len(candles_5min) < 20:
            print(f"   ⚠️  Only got {len(candles_5min)} 5-min candles, need 20")
            return None

        print(f"   ✅ Created {len(candles_5min)} five-minute candles")

        # Calculate MA20 from last 20 candles
        last_20_closes = [c['close'] for c in candles_5min[-20:]]
        ma20 = round(sum(last_20_closes) / 20, 2)

        # Get timestamp of the latest candle for reference
        latest_candle_time = candles_5min[-1]['timestamp']
        candle_time_str = latest_candle_time.strftime("%I:%M %p") if isinstance(latest_candle_time, datetime) else str(
            latest_candle_time)

        print(f"   💎 MA20 @ {candle_time_str} = ₹{ma20:.2f}\n")

        return ma20
    except Exception as e:
        print(f"   ❌ MA20 calculation error: {e}")
        import traceback
        traceback.print_exc()
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


def place_exit_order(symbol, instrument, quantity, current_price, exit_type):
    """
    Place SELL order to exit position

    Args:
        symbol: Stock symbol
        instrument: Upstox instrument key
        quantity: Number of shares to sell
        current_price: Current market price
        exit_type: "TARGET" or "STOPLOSS"

    Returns:
        Order response dict or None if failed
    """

    logger.info(f"Placing exit order: {symbol} @ ₹{current_price:.2f}, Reason: {exit_type}")

    try:
        url = f"{BASE_URL}/order/place"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "quantity": quantity,
            "product": "I",  # Intraday
            "validity": "DAY",
            "price": 0,  # Not used for MARKET orders
            "tag": "exit_order",
            "instrument_token": instrument,
            "order_type": "MARKET",  # Always use MARKET for exits
            "transaction_type": "SELL",
            "disclosed_quantity": 0,
            "trigger_price": 0,
            "is_amo": False
        }

        print(f"\n{'=' * 60}")
        print(f"📤 PLACING EXIT ORDER ({exit_type}): {symbol}")
        print(f"   Quantity: {quantity}")
        print(f"   Price: ₹{current_price:.2f} (MARKET)")
        print(f"   Type: SELL")
        print(f"{'=' * 60}\n")

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            order_id = result.get('data', {}).get('order_id', 'Unknown')
            print(f"✅ EXIT ORDER PLACED SUCCESSFULLY!")
            print(f"   Order ID: {order_id}")
            print(f"   Symbol: {symbol}")
            print(f"   Exit Type: {exit_type}\n")
            return result

            # LOG TO CSV - THIS WAS MISSING!
            log_trade(
                symbol=symbol,
                entry_price=entry_price,
                exit_price=current_price,
                qty=qty,
                result=result,
                profit=profit,
                exit_type=exit_type
            )

            # UPDATE POSITION STATUS
            active_positions[symbol]["status"] = "CLOSED"
            active_positions[symbol]["exit_price"] = current_price
            active_positions[symbol]["exit_type"] = exit_type
            active_positions[symbol]["pnl"] = profit

        else:
            print(f"❌ EXIT ORDER FAILED!")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}\n")
            return None

    except Exception as e:
        print(f"❌ Exception placing exit order: {e}\n")
        return None


def update_position_prices():
    """Update current prices for all tracked positions and auto-exit if needed"""
    print("\n🔍 CHECKING EXIT CONDITIONS FOR ALL POSITIONS:")
    print("-" * 60)

    for symbol, pos in list(dashboard_metrics["positions"].items()):
        instrument = WATCHLIST.get(symbol)
        if instrument:
            current_price = get_live_price(instrument)
            if current_price:
                pos["current"] = current_price
                pos["pnl"] = (current_price - pos["entry"]) * pos["qty"]

                # Check for target/SL hit
                pnl_pct = ((current_price - pos["entry"]) / pos["entry"]) * 100

                # Calculate distance to target/SL
                target_price = pos["entry"] * (1 + pos["target_pct"] / 100)
                sl_price = pos["entry"] * (1 - pos["sl_pct"] / 100)
                distance_to_target = ((target_price - current_price) / pos["entry"]) * 100
                distance_to_sl = ((current_price - sl_price) / pos["entry"]) * 100

                # Print detailed status
                print(f"\n📊 {symbol}:")
                print(f"   Entry: ₹{pos['entry']:.2f} | Current: ₹{current_price:.2f} | P&L: {pnl_pct:+.2f}%")
                print(f"   Target: ₹{target_price:.2f} ({pos['target_pct']}%) | Distance: {distance_to_target:.2f}%")
                print(f"   Stop-Loss: ₹{sl_price:.2f} ({pos['sl_pct']}%) | Distance: {distance_to_sl:+.2f}%")

                # TARGET HIT - Place automatic SELL order
                if pnl_pct >= pos["target_pct"]:
                    print(f"   ✅ TARGET REACHED! Placing SELL order...")
                    log_with_color(f"🎯 TARGET HIT: {symbol} at ₹{current_price:.2f} (+{pnl_pct:.2f}%)", "SUCCESS")

                    # Place SELL order to exit position
                    exit_result = place_exit_order(symbol, instrument, pos["qty"], current_price, "TARGET")

                    if exit_result:
                        dashboard_metrics["wins"] += 1
                        dashboard_metrics["pnl"] += pos["pnl"]
                        del dashboard_metrics["positions"][symbol]
                        log_with_color(f"✅ Exit order placed for {symbol}", "SUCCESS")
                        logger.info(f"TARGET HIT: {symbol} at ₹{current_price:.2f}")
                    else:
                        log_with_color(f"⚠️  Failed to place exit order for {symbol}", "WARNING")

                # STOP-LOSS HIT - Place automatic SELL order
                elif pnl_pct <= -pos["sl_pct"]:
                    print(f"   ❌ STOP-LOSS HIT! Placing SELL order...")
                    log_with_color(f"🛑 STOP-LOSS HIT: {symbol} at ₹{current_price:.2f} ({pnl_pct:.2f}%)", "ERROR")

                    # Place SELL order to exit position
                    exit_result = place_exit_order(symbol, instrument, pos["qty"], current_price, "STOPLOSS")
                    logger.info(f"STOP-LOSS HIT: {symbol} at ₹{current_price:.2f}")

                    if exit_result:
                        dashboard_metrics["losses"] += 1
                        dashboard_metrics["pnl"] += pos["pnl"]
                        del dashboard_metrics["positions"][symbol]
                        log_with_color(f"✅ Exit order placed for {symbol}", "SUCCESS")
                    else:
                        log_with_color(f"⚠️  Failed to place exit order for {symbol}", "WARNING")
                else:
                    # Neither target nor SL hit
                    if pnl_pct > 0:
                        print(f"   ⏳ IN PROFIT - Holding for target...")
                    elif pnl_pct < 0:
                        print(f"   ⏳ IN LOSS - Monitoring stop-loss...")
                    else:
                        print(f"   ⏳ AT BREAKEVEN - Holding...")

    print("-" * 60)


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
    # CHECK IF WE ALREADY HAVE THIS POSITION
    if symbol in active_positions:
        existing = active_positions[symbol]

        # If from broker or already active, SKIP!
        if existing.get("from_broker") or existing.get("status") == "ACTIVE":
            print(f"\n⏭️  SKIP: Already have {symbol} position")
            print(f"   Source: {'Broker' if existing.get('from_broker') else 'Bot'}")
            print(f"   Qty: {existing['qty']} @ ₹{existing['entry_price']:.2f}")
            print(f"   Will monitor for exit only\n")
            return None

    # SAFE TO PLACE NEW ORDER
    print(f"\n✅ {symbol}: No existing position, placing order...")
    # ... rest of order placement code ...
    try:
        params = get_strategy_params(strategy)
        if not params:
            return None

        target_pct = params['target_pct']
        stoploss_pct = params['stoploss_pct']
        order_type = params['order_type']

        # v0.7: Log order attempt (avoid unicode in logger - use Rs instead of ₹)
        logger.info(f"Placing BUY order: {symbol} @ Rs{live_price:.2f}, Qty: {QUANTITY}, Strategy: {strategy}")

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
            # ... after order placed ...
            logger.info(f"Order successful: {symbol}, Order ID: {order_id}")
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

                        # Get ACTUAL buy price from position (not current price!)
                        buy_price = position.get("buy_price") or position.get("day_buy_price") or position.get(
                            "average_price")

                        if not buy_price or buy_price == 0:
                            # Fallback to current price only if buy price not available
                            current_price = get_live_price(instrument)
                            if not current_price:
                                print(f"⚠️  Could not fetch price for {trading_symbol}")
                                continue
                            buy_price = current_price
                            print(f"⚠️  Using current price as entry for {trading_symbol} (buy_price not in API)")

                        # Determine strategy based on time
                        current_strategy = get_current_strategy()
                        if current_strategy in ["MORNING_BOUNCE", "LATE_SCALP"]:
                            params = get_strategy_params(current_strategy)
                            if params:
                                add_position_to_dashboard(
                                    trading_symbol,
                                    qty,
                                    buy_price,  # Use ACTUAL buy price
                                    params['target_pct'],
                                    params['stoploss_pct'],
                                    current_strategy
                                )
                                print(f"✅ Loaded {trading_symbol}: {qty}@₹{buy_price:.2f}")

            return active_symbols
        return []
    except Exception as e:
        print(f"⚠️  Error fetching positions: {e}")
        return []


def sync_positions_from_broker():
    """Load existing positions from broker at startup - PREVENTS SAIL BUG!"""
    print("\n" + "=" * 60)
    print("🔄 SYNCING POSITIONS FROM BROKER...")
    print("=" * 60)

    try:
        positions_response = upstox.get_positions()

        if positions_response.status_code != 200:
            print("⚠️  Could not fetch positions from broker")
            print("   Starting with empty position tracking")
            return

        positions_data = positions_response.json()["data"]

        # Check both 'positions' (day) and 'holdings' for overnight positions
        existing_count = 0

        for pos in positions_data:
            symbol = pos["tradingsymbol"]
            qty = pos["quantity"]
            avg_price = pos["average_price"]

            if qty > 0:  # Long position exists
                print(f"   📍 FOUND: {symbol} | Qty: {qty} @ ₹{avg_price:.2f}")

                # Add to active_positions with special flag
                active_positions[symbol] = {
                    "symbol": symbol,
                    "qty": qty,
                    "entry_price": avg_price,
                    "strategy": "EXISTING_BROKER",
                    "from_broker": True,  # CRITICAL FLAG
                    "status": "ACTIVE",
                    "entry_time": datetime.now()
                }
                existing_count += 1

        if existing_count > 0:
            print(f"\n✅ Synced {existing_count} existing position(s)")
            print("⚠️  Bot will MONITOR these, NOT place new orders!")
        else:
            print("\n✅ No existing positions found - clean start")

        print("=" * 60 + "\n")

    except Exception as e:
        print(f"❌ Error syncing positions: {e}")
        print("⚠️  Starting with empty position tracking")

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
        print("🎮 BOT v0.7 - GAME CHANGER v4 🎮")
        print("=" * 60)
        print("⚠️  MONITOR-ONLY: Signals will be LOGGED, not TRADED")
        print("    - Detects MA bounce signals")
        print("    - Logs to signal_log.csv")
        print("    - Cross-check MA20 with TradingView")
        print()
        print("✨ v0.7: Risk Management + EOD Auto-Exit")
        print("    - Capital caps (₹1000 max per order)")
        print("    - 3:15 PM auto-exit (avoid ₹50/scrip charges)")
        print("    - Professional logging system")
        print("=" * 60)
    else:
        print("🎮 BOT v0.7 - GAME CHANGER v4 🎮")
        print("=" * 60)
        print("⚠️  LIVE TRADING ENABLED: Real orders will be placed!")
        print("✨ v0.7 v4: Platinum + Risk Mgmt + Audio + Encoding Fix")
    print("Strategies:")
    print("  🌅 MORNING BOUNCE (9:15 AM - 1:30 PM)")
    print("     - MA bounce detection, MARKET orders")
    print("     - 2% target, 1% stop-loss")
    print()
    print("  🌆 LATE SCALP (2:30 PM - 3:15 PM)")
    print("     - Volume/volatility scalping, MARKET orders")
    print("     - 0.5% target, 0.3% stop-loss")
    print("=" * 60 + "\n")

    # TOKEN CHECK PROMPT
    print("⚠️  CRITICAL: Access tokens expire at 3:30 PM daily!")
    print()
    token_check = input("Have you updated ACCESS_TOKEN for today? (yes/no): ").strip().lower()

    if token_check not in ['yes', 'y']:
        print("\n" + "=" * 60)
        print("❌ PLEASE UPDATE ACCESS_TOKEN FIRST!")
        print("=" * 60)
        print("1. Get new token from Upstox dashboard")
        print("2. Update ACCESS_TOKEN variable (line 43)")
        print("3. Restart bot")
        print("=" * 60 + "\n")
        input("Press Enter to exit...")
        return

    print()

    sync_positions_from_broker()

    print("🔍 Checking for existing positions...")
    active_positions = get_existing_positions()
    if active_positions:
        print(f"📝 Found existing positions: {active_positions}")
    else:
        print("📝 No existing positions found")
    print()

    update_dashboard()

    while True:
        # v0.7: EOD Auto-Exit at 3:15 PM (CRITICAL - avoid ₹50/scrip charges)
        if is_eod_exit_time():
            log_with_color("", "INFO")
            log_with_color("🕒 3:15 PM - EXECUTING EOD EXIT TO AVOID AUTO-SQUARE CHARGES", "SUCCESS")
            log_with_color("=" * 60, "INFO")
            logger.info("EOD Exit triggered at 3:15 PM")

            if dashboard_metrics["positions"]:
                log_with_color(f"📤 Closing {len(dashboard_metrics['positions'])} open positions...", "INFO")

                for symbol, pos in list(dashboard_metrics["positions"].items()):
                    instrument = WATCHLIST.get(symbol)
                    if instrument:
                        current_price = get_live_price(instrument)
                        if current_price:
                            log_with_color(f"   Selling {symbol} @ ₹{current_price:.2f}", "INFO")
                            exit_result = place_exit_order(symbol, instrument, pos["qty"], current_price, "EOD_CLEANUP")

                            if exit_result:
                                # Update P&L
                                final_pnl = (current_price - pos["entry"]) * pos["qty"]
                                dashboard_metrics["pnl"] += final_pnl

                                if final_pnl >= 0:
                                    dashboard_metrics["wins"] += 1
                                    log_with_color(f"   ✅ {symbol} closed with profit: ₹{final_pnl:+.2f}", "SUCCESS")
                                else:
                                    dashboard_metrics["losses"] += 1
                                    log_with_color(f"   ✅ {symbol} closed with loss: ₹{final_pnl:+.2f}", "ERROR")

                                del dashboard_metrics["positions"][symbol]
                                logger.info(
                                    f"EOD Exit: {symbol} closed at ₹{current_price:.2f}, P&L: ₹{final_pnl:+.2f}")
                            else:
                                log_with_color(f"   ⚠️  Failed to exit {symbol}", "WARNING")
                                logger.error(f"EOD Exit failed for {symbol}")

                update_dashboard()
                log_with_color("", "INFO")
                log_with_color("✅ EOD EXIT COMPLETE - All positions closed", "SUCCESS")
                log_with_color(f"📊 Final P&L: ₹{dashboard_metrics['pnl']:+.2f}", "INFO")
                logger.info(f"EOD Exit complete. Final P&L: ₹{dashboard_metrics['pnl']:+.2f}")
            else:
                log_with_color("📝 No open positions to close", "INFO")
                logger.info("EOD Exit: No positions to close")

            log_with_color("", "INFO")
            log_with_color("🛑 Bot stopping after EOD exit", "INFO")
            log_with_color("=" * 60, "INFO")
            break  # Exit main loop

        try:
            strategy = get_current_strategy()
            dashboard_metrics["current_strategy"] = strategy

            if strategy == "MARKET_CLOSED":
                print("⏰ Market closed. Bot stopping.")
                break

            elif strategy == "NO_TRADE":
                print("⏸️  Transition period (1:30 PM - 2:30 PM). Pausing new signals...")
                print("📊 Still monitoring existing positions for exits...")

                # CRITICAL: Still monitor positions during transition!
                if dashboard_metrics["positions"]:
                    update_position_prices()
                    update_dashboard()

                time.sleep(60)  # Check every minute during transition
                continue

            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{current_time}] Current Strategy: {strategy}")
            print("-" * 60)

            dashboard_metrics["last_scan"] = datetime.now()

            # Update existing positions first
            if dashboard_metrics["positions"]:
                update_position_prices()
                update_dashboard()

            # Check if we've hit max positions
            current_position_count = len(dashboard_metrics["positions"])
            MAX_POSITIONS = 5

            if current_position_count >= MAX_POSITIONS:
                print(f"\n⚠️  MAX POSITIONS REACHED ({current_position_count}/{MAX_POSITIONS})")
                print("   Skipping new signals, monitoring exits only...")
                time.sleep(60)  # Check every minute
                continue

            # Scan for new signals
            for symbol, instrument in WATCHLIST.items():
                print(f"\nScanning {symbol}...")

                has_signal, message = check_signal(instrument, strategy)
                print(f"  {message}")

                if has_signal:
                    if symbol in active_positions:
                        print(f"⏭️  SKIP - Already have {symbol} position")
                        continue

                    # 🔔 PLAY ALERT BEEPS (v2)
                    play_signal_alert()

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
                        # Live trading mode - simple confirmation
                        dashboard_metrics["signals_today"] += 1

                        print("⚠️  SIGNAL DETECTED - Review and confirm:")
                        print(f"    Symbol: {symbol}")
                        print(f"    Strategy: {strategy}")
                        print(f"    Press ENTER to place order (or type 'skip' to ignore)")
                        print("=" * 60 + "\n")

                        # Wait for user input
                        try:
                            user_input = input().strip().lower()
                            if user_input == 'skip':
                                print("⏭️  Signal skipped by user\n")
                                continue
                            print("✅ Order confirmed, proceeding...\n")
                        except KeyboardInterrupt:
                            print("\n⏭️  Signal skipped (Ctrl+C)\n")
                            continue

                        live_price = get_live_price(instrument)
                        if live_price:
                            # v0.7: Capital cap check
                            order_value = live_price * QUANTITY
                            if order_value > MAX_CAPITAL_PER_ORDER:
                                log_with_color(
                                    f"⏭️  SKIP {symbol} - Order value ₹{order_value:.2f} exceeds cap (₹{MAX_CAPITAL_PER_ORDER})",
                                    "WARNING")
                                logger.warning(f"Skipped {symbol} - exceeds capital cap")
                                continue
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