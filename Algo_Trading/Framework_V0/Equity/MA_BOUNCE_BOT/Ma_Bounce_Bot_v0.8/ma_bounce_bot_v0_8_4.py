"""
MA BOUNCE BOT v0.8 - REPORT MASTER 📊
============================================================
v0.8 (Dec 31, 2025) - LOGGING ENHANCEMENTS ONLY:
     ✅ Date-based logging: bot_activity_YYYYMMDD.log
     ✅ Append mode: Survives restarts, no data loss
     ✅ Enhanced CSV with ML columns (Target_Hit, Entry_Source, Exit_Source, etc.)
     ✅ Dual CSV: Daily (trades_log_YYYYMMDD.csv) + Master (trades_log_master.csv)

v0.7 - PRODUCTION READY (Dec 30, 2025):
     ✅ Upstox position sync, Unicode fixes, CSV logging, LATE_SCALP disabled
============================================================
TWO STRATEGIES:
1. MORNING BOUNCE (9:15 AM - 1:30 PM): MA bounce, 2% target, 1% SL
2. LATE SCALP (2:30 PM - 3:15 PM): Volume/volatility, 0.5% target, 0.3% SL

**PLATINUM CANDLE ENGINE**: Smart API, Holiday handling, TradingView validated
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
# ANSI COLOR CODES FOR TERMINAL
# ============================================
CYAN = '\033[96m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


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
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTU0YjJjMzQ2NmZiMjEyODM2NjM3YWEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NzE1ODQ2NywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY3MjE4NDAwfQ.gEBs0gQ-MjidyOfVi61OhdUHBaAc3LlHxQCpVell_DE"

# ============================================
# v0.7: RISK MANAGEMENT PARAMETERS ⭐ NEW
# ============================================
MAX_CAPITAL_PER_ORDER = 1000  # Skip orders > ₹1000 (prevents expensive stocks)
MAX_POSITIONS = 10  # ML Optimizer: 10 stocks = faster pattern recognition (v6)
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

# ============================================
# v0.8: DATE-BASED LOGGING SETUP
# ============================================
today = datetime.now().strftime("%Y%m%d")
LOG_FILE = f"bot_activity_{today}.log"
TRADES_LOG_FILE = f"trades_log_{today}.csv"
TRADES_MASTER_FILE = "trades_log_master.csv"

# v0.8: Professional logging with append mode
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),  # APPEND mode!
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info(f"MA BOUNCE BOT v0.8 STARTED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("="  * 80)

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
    "current_strategy": "WAITING",
    "traded_symbols_today": set()  # NEW: Track which stocks already traded today
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

    # v0.8: Check if in EXIT MODE (10/10 trades)
    trades_today = len(dashboard_metrics.get("traded_symbols_today", set()))
    MAX_TRADES_PER_DAY = 10
    
    if trades_today >= MAX_TRADES_PER_DAY:
        bot_mode = "Bot v0.8 - EXIT MODE 🎯"
        strategy_display = "MONITORING EXITS"
        scan_label = "Next check:"
    else:
        bot_mode = "Bot v0.8 - GAME CHANGER 🎮"
        strategy_display = dashboard_metrics["current_strategy"]
        scan_label = "Next scan:"

    num_positions = len(dashboard_metrics["positions"])
    total_pnl = dashboard_metrics["pnl"]
    pnl_color = "\033[92m" if total_pnl >= 0 else "\033[91m"

    # Colors
    RESET = '\033[0m'
    RED = '\033[91m'
    BLUE = '\033[38;5;33m'
    WHITE = '\033[97m'

    # Build lines with exact character counts
    line1 = bot_mode
    line2 = f"{time_str} | {strategy_display:17s} | {scan_label} {next_scan:5s}"
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
        # v6 FIX: LATE_SCALP disabled - insufficient volume data from Upstox API
        # MORNING_BOUNCE works perfectly, focus on that! Still monitors exits.
        return "NO_TRADE"  # Changed from "LATE_SCALP"
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
    """Check for trading signal - v0.8: Returns (has_signal, message, ma20_distance)"""
    try:
        live_price = get_live_price(instrument)
        if live_price is None:
            return False, "Could not get live price", 0

        if strategy == "MORNING_BOUNCE":
            ma20 = get_ma20(instrument)
            if ma20 is None:
                return False, "Could not calculate MA20", 0

            # Safety check for division by zero
            if ma20 <= 0:
                return False, "Invalid MA20 value", 0

            # v0.8: Calculate MA20 distance for logging
            ma20_distance_pct = ((live_price - ma20) / ma20) * 100

            if live_price >= ma20:
                dynamic_threshold = live_price * (BOUNCE_THRESHOLD_PCT / 100)
                distance = abs(live_price - ma20)

                if distance <= dynamic_threshold:
                    return True, f"BUY - Bounce detected! Price: ₹{live_price:.2f}, MA20: ₹{ma20:.2f}, Distance: ₹{distance:.2f}", ma20_distance_pct
                else:
                    return False, f"WAIT - Price too far above MA (Distance: ₹{distance:.2f}, Threshold: ₹{dynamic_threshold:.2f})", ma20_distance_pct
            else:
                return False, f"WAIT - Price below MA (₹{live_price:.2f} < ₹{ma20:.2f})", ma20_distance_pct


        elif strategy == "LATE_SCALP":

            # Try volume/volatility detection first
            has_volume_spike = detect_volume_spike(instrument)
            has_volatility = detect_high_volatility(instrument)
            candles = get_historical_candles(instrument, 5)

            # If insufficient historical data, use simple price movement
            if len(candles) < 2:
                # Fallback: Use recent price momentum (if price moved >0.3% in last minute)
                # This is acceptable for LATE_SCALP since we have tight 0.3% stop-loss
                return False, "LATE_SCALP: Using price-only mode (no volume data available)", 0
                # Note: For now, just skip. Can enable simple scalping later if needed.

            is_uptrend = candles[-1]['close'] > candles[-2]['close']

            if (has_volume_spike or has_volatility) and is_uptrend:
                conditions = []
                if has_volume_spike:
                    conditions.append("Volume spike")
                if has_volatility:
                    conditions.append("High volatility")
                return True, f"BUY - Scalp signal! {', '.join(conditions)}, Price: ₹{live_price:.2f}, Trending UP", 0
            else:
                return False, f"WAIT - No scalp signal (Vol: {has_volume_spike}, Volatility: {has_volatility}, Uptrend: {is_uptrend})", 0

        return False, "Unknown strategy", 0
    except ZeroDivisionError:
        return False, "Math error (division by zero)", 0
    except Exception as e:
        return False, f"Error: {e}"


# ============================================
# POSITION TRACKING
# ============================================

def add_position_to_dashboard(symbol, qty, entry_price, target_pct, sl_pct, strategy, entry_source="Bot", ma20_distance=0):
    """Add position to dashboard tracking with v0.8 enhanced fields"""
    entry_time = datetime.now().strftime("%H:%M:%S")
    
    dashboard_metrics["positions"][symbol] = {
        "qty": qty,
        "entry": entry_price,
        "current": entry_price,
        "pnl": 0.0,
        "target_pct": target_pct,
        "sl_pct": sl_pct,
        "strategy": strategy,
        "entry_time": entry_time,          # v0.8: Track entry time
        "entry_source": entry_source,      # v0.8: Bot/Manual/Synced
        "ma20_distance": ma20_distance     # v0.8: Distance from MA20 at entry
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

    logger.info(f"Placing exit order: {symbol} @ Rs{current_price:.2f}, Reason: {exit_type}")

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
            
            # v0.8: ENHANCED CSV LOGGING WITH ML COLUMNS
            entry_price = dashboard_metrics["positions"][symbol]["entry"]
            profit = (current_price - entry_price) * quantity
            profit_pct = (profit / (entry_price * quantity)) * 100
            
            # Determine result
            result_status = "WIN" if profit >= 0 else "LOSS"
            
            # Enhanced logging
            try:
                pos = dashboard_metrics["positions"][symbol]
                
                # Calculate enhanced fields
                target_price = pos.get("entry") * (1 + pos.get("target_pct", 2) / 100)
                sl_price = pos.get("entry") * (1 - pos.get("sl_pct", 1) / 100)
                
                # Target hit check
                target_hit = "Yes" if current_price >= target_price else "No"
                
                # Entry time category
                entry_time_str = pos.get("entry_time", datetime.now().strftime("%H:%M:%S"))
                try:
                    entry_hour = int(entry_time_str.split(':')[0])
                    if entry_hour < 11:
                        entry_category = 'Early'
                    elif entry_hour < 13:
                        entry_category = 'Mid'
                    else:
                        entry_category = 'Late'
                except:
                    entry_category = 'Unknown'
                
                # Distance to target
                distance_to_target = ((target_price - current_price) / target_price) * 100 if target_price else 0
                
                # Hold duration
                try:
                    entry_dt = datetime.strptime(entry_time_str, "%H:%M:%S")
                    exit_dt = datetime.now()
                    hold_duration = int((exit_dt - entry_dt).total_seconds() / 60)
                except:
                    hold_duration = 0
                
                # Exit source mapping
                exit_source_map = {
                    "TARGET": "Bot_Target",
                    "STOPLOSS": "Bot_SL",
                    "EOD_CLEANUP": "Bot_EOD",
                    "MANUAL": "Manual"
                }
                exit_source = exit_source_map.get(exit_type, exit_type)
                
                # Enhanced CSV headers
                headers = [
                    'Date', 'Entry_Time', 'Exit_Time', 'Symbol',
                    'Entry_Price', 'Exit_Price', 'Qty', 'P&L', 'P&L%',
                    'Target_Price', 'SL_Price', 'Target_Hit',
                    'Entry_Source', 'Exit_Source',
                    'Hold_Duration_Minutes',
                    'MA20_Distance_%',
                    'Distance_to_Target_%',
                    'Entry_Time_Category'
                ]
                
                now = datetime.now()
                row_data = [
                    now.strftime('%Y-%m-%d'),
                    entry_time_str,
                    now.strftime('%H:%M:%S'),
                    symbol,
                    f"{entry_price:.2f}",
                    f"{current_price:.2f}",
                    quantity,
                    f"{profit:.2f}",
                    f"{profit_pct:.2f}",
                    f"{target_price:.2f}",
                    f"{sl_price:.2f}",
                    target_hit,
                    pos.get('entry_source', 'Bot'),
                    exit_source,
                    hold_duration,
                    f"{pos.get('ma20_distance', 0):.2f}",
                    f"{distance_to_target:.2f}",
                    entry_category
                ]
                
                # Write to DAILY CSV
                file_exists = os.path.isfile(TRADES_LOG_FILE)
                with open(TRADES_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(headers)
                        logger.info(f"Created daily trades log: {TRADES_LOG_FILE}")
                    writer.writerow(row_data)
                
                # Write to MASTER CSV (cumulative)
                file_exists = os.path.isfile(TRADES_MASTER_FILE)
                with open(TRADES_MASTER_FILE, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(headers)
                        logger.info(f"Created master trades log: {TRADES_MASTER_FILE}")
                    writer.writerow(row_data)
                
                print(f"✅ Trade logged: {symbol} {result_status} ₹{profit:+.2f} | Target Hit: {target_hit}")
                logger.info(f"CSV logged: {symbol} | P&L: Rs{profit:.2f} | Exit: {exit_source}")
                
            except Exception as log_error:
                print(f"⚠️  Could not log trade: {log_error}")
                logger.error(f"CSV logging failed: {log_error}")

            logger.info(f"Exit {exit_type}: {symbol} @ Rs{current_price:.2f}, P&L: Rs{profit:+.2f}")

            return result

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
                        logger.info(f"TARGET HIT: {symbol} at Rs{current_price:.2f}")
                    else:
                        log_with_color(f"⚠️  Failed to place exit order for {symbol}", "WARNING")

                # STOP-LOSS HIT - Place automatic SELL order
                elif pnl_pct <= -pos["sl_pct"]:
                    print(f"   ❌ STOP-LOSS HIT! Placing SELL order...")
                    log_with_color(f"🛑 STOP-LOSS HIT: {symbol} at ₹{current_price:.2f} ({pnl_pct:.2f}%)", "ERROR")

                    # Place SELL order to exit position
                    exit_result = place_exit_order(symbol, instrument, pos["qty"], current_price, "STOPLOSS")
                    logger.info(f"STOP-LOSS HIT: {symbol} at Rs{current_price:.2f}")

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
    # CHECK IF WE ALREADY HAVE THIS POSITION (v0.7 v5 FIX)
    if symbol in dashboard_metrics["positions"]:
        existing = dashboard_metrics["positions"][symbol]

        # If from broker or already active, SKIP!
        if existing.get("from_upstox") or existing.get("qty", 0) > 0:
            print(f"\n⏭️  SKIP: Already have {symbol} position")
            print(f"   Source: {'Upstox' if existing.get('from_upstox') else 'Bot'}")
            print(f"   Qty: {existing['qty']} @ ₹{existing['entry']:.2f}")
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
        print(f"   ✅ Bracket order: Upstox will AUTO-SELL at target or stop-loss!")
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
        print("    (Upstox will automatically handle exits)")
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

            # Add position to dashboard
            add_position_to_dashboard(symbol, quantity, entry_price, target_pct, stoploss_pct, strategy)

            # v6 ML: Mark this stock as traded today (one stock trades once)
            dashboard_metrics["traded_symbols_today"].add(symbol)
            print(f"✅ Position added to dashboard")
            print(f"📊 Stocks traded today: {len(dashboard_metrics['traded_symbols_today'])}/10")
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
                # v0.8 FIX: Check if position is dict (sometimes API returns floats in array)
                if not isinstance(position, dict):
                    print(f"   ⚠️  Skipping non-dict position: {type(position)}")
                    continue
                    
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
                        # v6 DEBUG: Why isn't position loading?
                        print(f"🔍 DEBUG {trading_symbol}: qty={qty}, instrument={'✅ FOUND' if instrument else '❌ NOT IN WATCHLIST'}")
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
                                    buy_price,
                                    params['target_pct'],
                                    params['stoploss_pct'],
                                    current_strategy
                                )
                                print(f"✅ Loaded {trading_symbol}: {qty}@₹{buy_price:.2f}")

                                # v6 ML: Mark as traded today
                                dashboard_metrics["traded_symbols_today"].add(trading_symbol)
                                print(
                                    f"   📊 Marked {trading_symbol} as traded (total: {len(dashboard_metrics['traded_symbols_today'])}/10)")

            return active_symbols
        return []
    except Exception as e:
        print(f"⚠️  Error fetching positions: {e}")
        return []


def sync_positions_from_upstox():
    """
    v0.7 v5 FIX: Load existing positions from broker at startup
    CRITICAL: PREVENTS SAIL BUG - No duplicate orders on existing positions!
    """
    print("\n" + "=" * 60)
    print("🔄 SYNCING POSITIONS FROM UPSTOX...")
    print("=" * 60)

    try:
        url = f"{BASE_URL}/portfolio/short-term-positions"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print("⚠️  Could not fetch positions from broker")
            print("   Starting with empty position tracking")
            print("=" * 60 + "\n")
            return

        data = response.json()
        positions_data = data.get("data", [])
        
        # v7 FIX: Safety check - ensure positions_data is a list
        if not isinstance(positions_data, list):
            print(f"⚠️  Unexpected data type from Upstox: {type(positions_data)}")
            print("   Starting with empty position tracking")
            print("=" * 60 + "\n")
            return

        # Check for overnight/existing positions
        existing_count = 0

        for pos in positions_data:
            try:
                # v6 FIX: Skip if not a dict (Upstox sometimes returns floats/nulls)
                if not isinstance(pos, dict):
                    print(f"   ⚠️  Skipping non-dict item: {type(pos)}")
                    continue

                symbol = pos.get("tradingsymbol", "")
                qty = pos.get("quantity", 0)
                # v6 FIX: Use buy_average (more reliable than average_price)
                # NEW:
                avg_price = pos.get("average_price", 0)
                if avg_price == 0:
                    avg_price = pos.get("buy_avg", pos.get("sell_avg", 0))
                if avg_price == 0:
                    avg_price = pos.get("pnl", {}).get("average_price", 0)
            
                # Fallback: If still 0, get current LTP as estimate
                if avg_price == 0:
                    instrument = WATCHLIST.get(symbol)
                    if instrument:
                        current_price = get_live_price(instrument)
                        if current_price:
                            avg_price = current_price
                            print(f"   ⚠️  Using LTP as entry estimate for {symbol}")

                if qty > 0 and symbol in WATCHLIST:  # Long position exists in our watchlist
                    print(f"   📍 FOUND: {symbol} | Qty: {qty} @ ₹{avg_price:.2f}")

                    # Add to dashboard_metrics with special flag
                    dashboard_metrics["positions"][symbol] = {
                        "symbol": symbol,
                        "qty": qty,
                        "entry": avg_price,
                        "current": avg_price,
                        "pnl": 0.0,
                        "target_pct": 2.0,
                        "sl_pct": 1.0,
                        "strategy": "EXISTING_UPSTOX",
                        "from_upstox": True
                    }
                    # v6 ML: Mark as already traded today
                    dashboard_metrics["traded_symbols_today"].add(symbol)
                    print(f"✅ Marked {symbol} as traded today")
                    existing_count += 1
            
            except Exception as pos_error:
                print(f"   ⚠️  Error processing position: {pos_error}")
                continue

        if existing_count > 0:
            print(f"\n✅ Synced {existing_count} existing position(s)")
            print("⚠️  Bot will MONITOR these, NOT place new orders!")
        else:
            print("\n✅ No existing positions found - clean start")

        print("=" * 60 + "\n")

    except Exception as e:
        print(f"❌ Error syncing positions: {e}")
        print("⚠️  Starting with empty position tracking")
        print("=" * 60 + "\n")


def get_active_position_count():
    """
    v0.7 v5 FIX: Count ONLY active positions (not closed ones)
    CRITICAL: Prevents exceeding MAX_POSITIONS limit
    """
    count = 0
    for symbol, pos in dashboard_metrics["positions"].items():
        # Only count if position is truly active (has qty > 0)
        if pos.get("qty", 0) > 0:
            count += 1
    return count

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
        print("🎮 BOT v0.7 - GAME CHANGER v7 🎮")
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
        print("🎮 BOT v0.7 - GAME CHANGER v7 🎮")
        print("=" * 60)
        print("⚠️  LIVE TRADING ENABLED: Real orders will be placed!")
        print("✨ v0.7 v7: All Fixes Applied + Clean Logging")
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

    sync_positions_from_upstox()

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
                logger.info(f"EOD Exit complete. Final P&L: Rs{dashboard_metrics['pnl']:+.2f}")
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

                # v6 ML: Check if hit max TRADES per day (not positions!)
                MAX_TRADES_PER_DAY = 10
                trades_today = len(dashboard_metrics["traded_symbols_today"])

                if trades_today >= MAX_TRADES_PER_DAY:
                    # Calculate current stats
                    total_pnl = sum(pos['pnl'] for pos in dashboard_metrics['positions'].values())
                    win_count = sum(1 for pos in dashboard_metrics['positions'].values() if pos['pnl'] > 0)
                    loss_count = sum(1 for pos in dashboard_metrics['positions'].values() if pos['pnl'] < 0)
                    breakeven_count = sum(1 for pos in dashboard_metrics['positions'].values() if pos['pnl'] == 0)
                    
                    print(f"\n{CYAN}{'=' * 70}{RESET}")
                    print("🏁 MAX TRADES REACHED FOR TODAY!")
                    print(f"{CYAN}{'=' * 70}{RESET}")
                    print(f"📊 TRADES TODAY: {trades_today}/{MAX_TRADES_PER_DAY}")
                    print(f"✅ WINS: {win_count} | ❌ LOSSES: {loss_count} | ⚖️  BREAKEVEN: {breakeven_count}")
                    print(f"💰 TOTAL P&L: ₹{total_pnl:+.2f}")
                    print(f"📈 OPEN POSITIONS: {len(dashboard_metrics['positions'])}")
                    print(f"\n⏸️  NO MORE NEW TRADES - Monitoring exits only...")
                    print(f"{CYAN}{'=' * 70}{RESET}\n")
                    
                    time.sleep(60)
                    continue

                # Also check current open positions (for safety)
                current_position_count = get_active_position_count()
                if current_position_count >= 10:
                    print(f"\n⚠️  MAX OPEN POSITIONS ({current_position_count}/10)")
                    print("   Waiting for exits before new trades...")
                    time.sleep(60)
                    continue

            # Scan for new signals
            for symbol, instrument in WATCHLIST.items():
                print(f"\nScanning {symbol}...")

                has_signal, message, ma20_distance = check_signal(instrument, strategy)  # v0.8: Capture MA20 distance
                print(f"  {message}")

                if has_signal:
                    # Check if already have open position
                    if symbol in dashboard_metrics["positions"]:
                        print(f"⏭️  SKIP - Already have {symbol} position")
                        continue

                    # v6 ML: Check if already traded today (one stock trades once)
                    if symbol in dashboard_metrics["traded_symbols_today"]:
                        print(f"⏭️  SKIP - {symbol} already traded today")
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
                                # Position already added to dashboard_metrics in add_position_to_dashboard()
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

            # v0.8: Live countdown timer
            print(f"\n⏳ Next scan at {next_scan_time.strftime('%H:%M:%S')}")
            logger.info(f"Next scan at {next_scan_time.strftime('%H:%M:%S')} (in {int(sleep_seconds)}s)")
            
            # Countdown timer with dashboard refresh
            while sleep_seconds > 0:
                mins, secs = divmod(int(sleep_seconds), 60)
                timer = f"{mins:02d}:{secs:02d}"
                
                # Update dashboard with countdown
                update_dashboard()
                print(f"\r⏱️  Next scan: {timer}   ", end='', flush=True)
                
                time.sleep(1)
                sleep_seconds -= 1

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