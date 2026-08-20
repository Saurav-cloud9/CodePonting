"""
BOT v0.8 - GAME CHANGER - REPORT FOCUSED 📊
============================================================
v0.8 CHANGES (Dec 31, 2025):
✅ REMOVED late scalp strategy (9:15-1:30 PM ONLY)
✅ Date-based logging (bot_activity_YYYYMMDD.log)
✅ Append mode (survives restarts)
✅ Enhanced CSV columns for ML analysis:
   - Target_Hit (Yes/No)
   - Entry_Source (Bot/Manual/Synced)
   - Exit_Source (Bot_Target/Bot_SL/Bot_EOD/Manual)
   - Entry_Time_Category (Early/Mid/Late)
   - Distance_to_Target (%)
   - MA20_Distance (%)
   - Hold_Duration_Minutes
✅ Daily CSV: trades_log_YYYYMMDD.csv
✅ Master CSV: trades_log_master.csv (cumulative, never overwrites)
✅ All files in Downloads folder (same as bot.py)

STRATEGY:
- MORNING BOUNCE ONLY (9:15 AM - 1:30 PM)
- MA bounce, 2% target, 1% SL, MARKET orders
- EOD exit at 3:15 PM
============================================================
"""

# ============================================
# LIVE TRADING MODE
# ============================================
MONITOR_ONLY = False  # LIVE TRADING ENABLED

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
import csv
import logging

# Cross-platform audio support
try:
    import winsound
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# ============================================
# v0.8: DATE-BASED LOGGING SETUP
# ============================================
today = datetime.now().strftime("%Y%m%d")
LOG_FILE = f"bot_activity_{today}.log"
TRADES_LOG_FILE = f"trades_log_{today}.csv"
TRADES_MASTER_FILE = "trades_log_master.csv"

# Configure logging with FileHandler + StreamHandler
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
logger.info(f"BOT v0.8 STARTED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("=" * 80)

# ============================================
# AUDIO ALERT FUNCTION
# ============================================
def play_signal_alert():
    """Play 3 beeps to alert signal detection"""
    if AUDIO_AVAILABLE:
        try:
            for _ in range(3):
                winsound.Beep(1000, 200)
                time.sleep(0.1)
        except:
            pass

# ============================================
# CONFIGURATION
# ============================================
# Upstox API Credentials
API_KEY = "18185106-6257-4a85-a84a-2ea314f91927"
API_SECRET = "15m0va42ni"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTU0YjJjMzQ2NmZiMjEyODM2NjM3YWEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NzE1ODQ2NywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY3MjE4NDAwfQ.gEBs0gQ-MjidyOfVi61OhdUHBaAc3LlHxQCpVell_DE"

# Risk Management
MAX_CAPITAL_PER_ORDER = 1000
MAX_POSITIONS = 10
EOD_EXIT_TIME = "15:15"

# Watchlist
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
# NSE HOLIDAYS
# ============================================
NSE_HOLIDAYS = [
    "2025-01-26", "2025-02-26", "2025-03-14", "2025-03-31",
    "2025-04-10", "2025-04-14", "2025-04-18", "2025-05-01",
    "2025-05-12", "2025-06-06", "2025-08-15", "2025-08-27",
    "2025-10-02", "2025-10-21", "2025-11-05", "2025-11-24",
    "2025-12-25"
]

def is_trading_day(date_obj):
    """Check if given date is a trading day"""
    if date_obj.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    date_str = date_obj.strftime("%Y-%m-%d")
    return date_str not in NSE_HOLIDAYS

# ============================================
# v0.8: ENHANCED CSV LOGGING
# ============================================
def log_trade_to_csv(trade_data):
    """
    Log trade with ALL enhanced columns for ML analysis
    
    trade_data = {
        'symbol': str,
        'entry_price': float,
        'exit_price': float,
        'qty': int,
        'pnl': float,
        'pnl_pct': float,
        'entry_time': str,
        'exit_time': str,
        'entry_source': str,  # Bot/Manual/Synced
        'exit_source': str,   # Bot_Target/Bot_SL/Bot_EOD/Manual
        'target_price': float,
        'sl_price': float,
        'target_hit': str,    # Yes/No
        'ma20_distance': float,  # Distance from MA20 at entry (%)
        'hold_duration': int,    # Minutes
    }
    """
    
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
    
    # Calculate additional fields
    entry_hour = int(trade_data['entry_time'].split(':')[0])
    if entry_hour < 11:
        entry_category = 'Early'
    elif entry_hour < 13:
        entry_category = 'Mid'
    else:
        entry_category = 'Late'
    
    # Distance to target calculation
    if trade_data.get('target_price'):
        distance_to_target = ((trade_data.get('target_price', 0) - trade_data.get('exit_price', 0)) / 
                             trade_data.get('target_price', 1)) * 100
    else:
        distance_to_target = 0
    
    # Prepare row data
    row_data = {
        'Date': datetime.now().strftime('%Y-%m-%d'),
        'Entry_Time': trade_data.get('entry_time', ''),
        'Exit_Time': trade_data.get('exit_time', ''),
        'Symbol': trade_data.get('symbol', ''),
        'Entry_Price': f"{trade_data.get('entry_price', 0):.2f}",
        'Exit_Price': f"{trade_data.get('exit_price', 0):.2f}",
        'Qty': trade_data.get('qty', 0),
        'P&L': f"{trade_data.get('pnl', 0):.2f}",
        'P&L%': f"{trade_data.get('pnl_pct', 0):.2f}",
        'Target_Price': f"{trade_data.get('target_price', 0):.2f}",
        'SL_Price': f"{trade_data.get('sl_price', 0):.2f}",
        'Target_Hit': trade_data.get('target_hit', 'No'),
        'Entry_Source': trade_data.get('entry_source', 'Bot'),
        'Exit_Source': trade_data.get('exit_source', 'Unknown'),
        'Hold_Duration_Minutes': trade_data.get('hold_duration', 0),
        'MA20_Distance_%': f"{trade_data.get('ma20_distance', 0):.2f}",
        'Distance_to_Target_%': f"{distance_to_target:.2f}",
        'Entry_Time_Category': entry_category
    }
    
    # Write to DAILY CSV
    file_exists = os.path.isfile(TRADES_LOG_FILE)
    with open(TRADES_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
            logger.info(f"Created new daily trades log: {TRADES_LOG_FILE}")
        writer.writerow(row_data)
    
    # Write to MASTER CSV (cumulative)
    file_exists = os.path.isfile(TRADES_MASTER_FILE)
    with open(TRADES_MASTER_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
            logger.info(f"Created new master trades log: {TRADES_MASTER_FILE}")
        writer.writerow(row_data)
    
    logger.info(f"Trade logged to CSV: {trade_data['symbol']} | P&L: Rs{trade_data['pnl']:.2f} | Exit: {trade_data['exit_source']}")

# ============================================
# GLOBAL STATE - Dashboard Metrics
# ============================================
dashboard_metrics = {
    "signals_today": 0,
    "wins": 0,
    "losses": 0,
    "pnl": 0.0,
    "positions": {},  # {symbol: {entry, target, sl, qty, from_upstox}}
    "current_strategy": "UNKNOWN",
    "last_scan": None,
    "traded_symbols_today": set()  # v6: Track symbols already traded
}

active_positions = {}  # For backward compatibility with existing code

# ============================================
# COLOR PRINTING
# ============================================
COLORS = {
    "SUCCESS": "\033[92m",  # Green
    "ERROR": "\033[91m",  # Red
    "WARNING": "\033[93m",  # Yellow
    "INFO": "\033[94m",  # Blue
    "RESET": "\033[0m"
}

def log_with_color(message, level="INFO"):
    """Print with color codes"""
    color = COLORS.get(level, COLORS["INFO"])
    print(f"{color}{message}{COLORS['RESET']}")

# ============================================
# API REQUEST HELPER
# ============================================
def make_api_request(endpoint, method="GET", params=None, data=None, headers_override=None):
    """Unified API request handler with error handling"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json"
    }
    if headers_override:
        headers.update(headers_override)

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API Error {response.status_code}: {response.text}")
            return None

    except requests.exceptions.Timeout:
        logger.error("Request timeout")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None

# ============================================
# GET LIVE PRICE
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

# ============================================
# GET INTRADAY DATA
# ============================================
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

# ============================================
# GET HISTORICAL DATA
# ============================================
def get_historical_data(instrument_key, from_date, to_date, interval="day"):
    """Get historical candles for multiple days"""
    endpoint = "/historical-candle/intraday"
    interval_map = {
        "1minute": "1minute",
        "5minute": "5minute",
        "30minute": "30minute",
        "day": "day"
    }
    
    api_interval = interval_map.get(interval, "5minute")
    url = f"{BASE_URL}/historical-candle/{instrument_key}/{api_interval}/{to_date}/{from_date}"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                candles = result.get("data", {}).get("candles", [])
                return candles
            else:
                logger.error(f"Historical API returned error: {result}")
                return []
        else:
            logger.error(f"Historical API failed: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Historical data fetch failed: {e}")
        return []

# ============================================
# BUILD COMPLETE CANDLES
# ============================================
def build_complete_candles(instrument_key, days_back=20):
    """
    Build complete candle set combining historical + intraday data
    Returns list of [timestamp, open, high, low, close, volume]
    """
    try:
        # Get historical daily candles for MA20 calculation
        today = datetime.now()
        
        # Find previous trading day
        check_date = today - timedelta(days=1)
        while not is_trading_day(check_date):
            check_date -= timedelta(days=1)
        to_date = check_date.strftime("%Y-%m-%d")
        
        # Go back enough days to get 20 trading days
        check_date = today - timedelta(days=days_back + 10)
        while not is_trading_day(check_date):
            check_date -= timedelta(days=1)
        from_date = check_date.strftime("%Y-%m-%d")
        
        # Fetch historical daily data
        historical_candles = get_historical_data(instrument_key, from_date, to_date, interval="day")
        
        # Fetch today's intraday data
        intraday_candles = get_intraday_candles(instrument_key, interval="5minute")
        
        # Combine: historical daily + today's intraday
        all_candles = historical_candles + intraday_candles
        
        return all_candles
        
    except Exception as e:
        logger.error(f"Error building candles: {e}")
        return []

# ============================================
# CALCULATE MA20
# ============================================
def calculate_ma20(candles):
    """Calculate 20-period MA from candle data"""
    if len(candles) < 20:
        return None
    
    # Last 20 candles (daily)
    last_20_closes = [c[4] for c in candles[-20:]]  # Index 4 = close price
    ma20 = sum(last_20_closes) / 20
    return ma20

# ============================================
# v0.8: REMOVED LATE SCALP - MORNING BOUNCE ONLY
# ============================================
def get_current_strategy():
    """Determine current trading strategy based on time"""
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    # Market hours: 9:15 AM - 3:30 PM
    if current_time < "09:15":
        return "PRE_MARKET"
    elif "09:15" <= current_time < "13:30":
        return "MORNING_BOUNCE"  # ONLY strategy now!
    elif current_time >= "15:30":
        return "MARKET_CLOSED"
    else:
        return "NO_TRADE"  # 1:30 PM - 3:30 PM: Monitor exits only

# ============================================
# CHECK SIGNAL
# ============================================
def check_signal(instrument_key, strategy):
    """
    Check if current price action meets entry criteria
    Returns: (has_signal, message)
    """
    try:
        # Build complete candle set
        candles = build_complete_candles(instrument_key, days_back=30)
        
        if not candles or len(candles) < 20:
            return False, "Insufficient candle data"
        
        # Calculate MA20 from daily candles
        ma20 = calculate_ma20(candles[:-1])  # Exclude today's intraday candles
        if not ma20:
            return False, "Could not calculate MA20"
        
        # Get current price (last intraday candle close or LTP)
        current_price = get_live_price(instrument_key)
        if not current_price:
            return False, "Could not fetch current price"
        
        # MORNING BOUNCE logic (only strategy now)
        # Entry: Price bounces off MA20 with 0.5% threshold
        distance_from_ma = ((current_price - ma20) / ma20) * 100
        
        if abs(distance_from_ma) <= BOUNCE_THRESHOLD_PCT and current_price > ma20:
            return True, f"SIGNAL: MA20 bounce (MA20: Rs{ma20:.2f}, LTP: Rs{current_price:.2f}, Distance: {distance_from_ma:.2f}%)"
        else:
            return False, f"No signal (MA20: Rs{ma20:.2f}, LTP: Rs{current_price:.2f}, Distance: {distance_from_ma:.2f}%)"
            
    except Exception as e:
        logger.error(f"Signal check failed: {e}")
        return False, f"Error: {str(e)}"

# ============================================
# PLACE ORDER
# ============================================
def place_order(symbol, instrument, entry_price, strategy):
    """Place BUY order and add to dashboard"""
    global dashboard_metrics, active_positions
    
    try:
        # Set targets based on strategy
        target_pct = 2.0  # 2% target for morning bounce
        sl_pct = 1.0      # 1% stop loss
        
        target_price = entry_price * (1 + target_pct / 100)
        sl_price = entry_price * (1 - sl_pct / 100)
        
        logger.info(f"Attempting to place order: {symbol} @ Rs{entry_price:.2f}")
        logger.info(f"Target: Rs{target_price:.2f} ({target_pct}%), SL: Rs{sl_price:.2f} ({sl_pct}%)")
        
        if MONITOR_ONLY:
            logger.info("MONITOR MODE: Order not placed, just tracking")
            order_id = f"PAPER_{symbol}_{int(time.time())}"
        else:
            # Place actual order via Upstox
            order_data = {
                "quantity": QUANTITY,
                "product": "I",  # Intraday
                "validity": "DAY",
                "price": 0,  # Market order
                "tag": "bot_v08",
                "instrument_token": instrument,
                "order_type": "MARKET",
                "transaction_type": "BUY",
                "disclosed_quantity": 0,
                "trigger_price": 0,
                "is_amo": False
            }
            
            result = make_api_request("/order/place", method="POST", data=order_data)
            if not result or result.get("status") != "success":
                logger.error(f"Order placement failed for {symbol}")
                return None
            
            order_id = result.get("data", {}).get("order_id")
            logger.info(f"Order placed successfully: {order_id}")
        
        # Calculate MA20 distance for logging
        candles = build_complete_candles(instrument, days_back=30)
        ma20 = calculate_ma20(candles[:-1]) if candles else entry_price
        ma20_distance = ((entry_price - ma20) / ma20) * 100 if ma20 else 0
        
        # Add to dashboard
        entry_time = datetime.now().strftime("%H:%M:%S")
        position_data = {
            "entry": entry_price,
            "target": target_price,
            "sl": sl_price,
            "qty": QUANTITY,
            "from_upstox": False,  # Bot-placed order
            "entry_time": entry_time,
            "entry_source": "Bot",
            "ma20_distance": ma20_distance
        }
        
        dashboard_metrics["positions"][symbol] = position_data
        active_positions[symbol] = position_data
        dashboard_metrics["traded_symbols_today"].add(symbol)
        
        log_with_color(f"✅ {symbol} added to positions: Entry Rs{entry_price:.2f}, Target Rs{target_price:.2f}, SL Rs{sl_price:.2f}", "SUCCESS")
        
        return order_id
        
    except Exception as e:
        logger.error(f"Order placement error: {e}")
        return None

# ============================================
# PLACE EXIT ORDER
# ============================================
def place_exit_order(symbol, instrument, qty, exit_price, exit_reason):
    """Place SELL order and log trade to CSV with enhanced data"""
    global dashboard_metrics
    
    try:
        logger.info(f"Exiting {symbol} @ Rs{exit_price:.2f}, Reason: {exit_reason}")
        
        if MONITOR_ONLY:
            logger.info("MONITOR MODE: Exit order not placed")
            success = True
        else:
            # Place actual SELL order
            order_data = {
                "quantity": qty,
                "product": "I",
                "validity": "DAY",
                "price": 0,
                "tag": "bot_v08_exit",
                "instrument_token": instrument,
                "order_type": "MARKET",
                "transaction_type": "SELL",
                "disclosed_quantity": 0,
                "trigger_price": 0,
                "is_amo": False
            }
            
            result = make_api_request("/order/place", method="POST", data=order_data)
            success = result and result.get("status") == "success"
        
        if success:
            # Get position data
            pos = dashboard_metrics["positions"].get(symbol, {})
            entry_price = pos.get("entry", 0)
            entry_time = pos.get("entry_time", "")
            exit_time = datetime.now().strftime("%H:%M:%S")
            
            # Calculate P&L
            pnl = (exit_price - entry_price) * qty
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price else 0
            
            # Calculate hold duration
            if entry_time:
                try:
                    entry_dt = datetime.strptime(entry_time, "%H:%M:%S")
                    exit_dt = datetime.strptime(exit_time, "%H:%M:%S")
                    hold_duration = int((exit_dt - entry_dt).total_seconds() / 60)
                except:
                    hold_duration = 0
            else:
                hold_duration = 0
            
            # Determine exit source
            exit_source_map = {
                "TARGET": "Bot_Target",
                "SL": "Bot_SL",
                "EOD_CLEANUP": "Bot_EOD",
                "MANUAL": "Manual"
            }
            exit_source = exit_source_map.get(exit_reason, exit_reason)
            
            # Check if target was hit
            target_price = pos.get("target", 0)
            target_hit = "Yes" if exit_price >= target_price else "No"
            
            # Prepare trade data for CSV
            trade_data = {
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'qty': qty,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'entry_source': pos.get('entry_source', 'Bot'),
                'exit_source': exit_source,
                'target_price': target_price,
                'sl_price': pos.get('sl', 0),
                'target_hit': target_hit,
                'ma20_distance': pos.get('ma20_distance', 0),
                'hold_duration': hold_duration
            }
            
            # Log to CSV
            log_trade_to_csv(trade_data)
            
            log_with_color(f"✅ Exit logged: {symbol} | P&L: Rs{pnl:+.2f} | Target Hit: {target_hit}", "SUCCESS")
            return True
        else:
            logger.error(f"Exit order failed for {symbol}")
            return False
            
    except Exception as e:
        logger.error(f"Exit order error: {e}")
        return False

# ============================================
# UPDATE POSITION PRICES & CHECK EXITS
# ============================================
def update_position_prices():
    """Update current prices and check for exits"""
    global dashboard_metrics
    
    for symbol, pos in list(dashboard_metrics["positions"].items()):
        instrument = WATCHLIST.get(symbol)
        if not instrument:
            continue
        
        current_price = get_live_price(instrument)
        if not current_price:
            continue
        
        # Update position data
        pos["current"] = current_price
        pos["pnl"] = (current_price - pos["entry"]) * pos["qty"]
        pos["pnl_pct"] = ((current_price - pos["entry"]) / pos["entry"]) * 100
        
        # Check for exits
        if current_price >= pos["target"]:
            # TARGET HIT
            logger.info(f"TARGET HIT: {symbol} @ Rs{current_price:.2f}")
            exit_result = place_exit_order(symbol, instrument, pos["qty"], current_price, "TARGET")
            if exit_result:
                dashboard_metrics["wins"] += 1
                dashboard_metrics["pnl"] += pos["pnl"]
                del dashboard_metrics["positions"][symbol]
                if symbol in active_positions:
                    del active_positions[symbol]
                    
        elif current_price <= pos["sl"]:
            # STOP LOSS HIT
            logger.info(f"STOP LOSS HIT: {symbol} @ Rs{current_price:.2f}")
            exit_result = place_exit_order(symbol, instrument, pos["qty"], current_price, "SL")
            if exit_result:
                dashboard_metrics["losses"] += 1
                dashboard_metrics["pnl"] += pos["pnl"]
                del dashboard_metrics["positions"][symbol]
                if symbol in active_positions:
                    del active_positions[symbol]

# ============================================
# UPDATE DASHBOARD
# ============================================
def update_dashboard():
    """Display real-time dashboard"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 80)
    print("BOT v0.8 - MORNING BOUNCE ONLY - DASHBOARD".center(80))
    print("=" * 80)
    print(f"Strategy: {dashboard_metrics['current_strategy']}")
    print(f"Signals Today: {dashboard_metrics['signals_today']}")
    print(f"Wins: {dashboard_metrics['wins']} | Losses: {dashboard_metrics['losses']}")
    print(f"P&L: Rs{dashboard_metrics['pnl']:+.2f}")
    print(f"Traded Symbols Today: {len(dashboard_metrics['traded_symbols_today'])}/{MAX_POSITIONS}")
    
    if dashboard_metrics["last_scan"]:
        print(f"Last Scan: {dashboard_metrics['last_scan'].strftime('%H:%M:%S')}")
    
    print("-" * 80)
    
    if dashboard_metrics["positions"]:
        print("ACTIVE POSITIONS:")
        print(f"{'Symbol':<12} {'Entry':>8} {'Current':>8} {'Target':>8} {'SL':>8} {'P&L':>10} {'P&L%':>8}")
        print("-" * 80)
        
        for symbol, pos in dashboard_metrics["positions"].items():
            current = pos.get("current", pos["entry"])
            pnl = pos.get("pnl", 0)
            pnl_pct = pos.get("pnl_pct", 0)
            
            color = "SUCCESS" if pnl >= 0 else "ERROR"
            print(f"{COLORS[color]}{symbol:<12} Rs{pos['entry']:>7.2f} Rs{current:>7.2f} Rs{pos['target']:>7.2f} Rs{pos['sl']:>7.2f} Rs{pnl:>9.2f} {pnl_pct:>7.2f}%{COLORS['RESET']}")
    else:
        print("No active positions")
    
    print("=" * 80)

# ============================================
# GET ACTIVE POSITION COUNT
# ============================================
def get_active_position_count():
    """Get count of active positions"""
    return len(dashboard_metrics["positions"])

# ============================================
# SYNC UPSTOX POSITIONS
# ============================================
def sync_upstox_positions():
    """Load existing positions from Upstox at startup"""
    global dashboard_metrics, active_positions
    
    logger.info("Syncing positions from Upstox...")
    
    result = make_api_request("/portfolio/short-term-positions")
    if not result or result.get("status") != "success":
        logger.warning("Could not fetch Upstox positions")
        return
    
    positions_data = result.get("data", [])
    synced_count = 0
    
    for item in positions_data:
        if not isinstance(item, dict):
            continue
        
        symbol = item.get("trading_symbol", "")
        qty = item.get("quantity", 0)
        avg_price = item.get("buy_average", item.get("average_price", 0))
        
        if symbol in WATCHLIST and qty > 0 and avg_price > 0:
            # Add to dashboard
            target_price = avg_price * 1.02  # 2% target
            sl_price = avg_price * 0.99      # 1% SL
            
            position_data = {
                "entry": avg_price,
                "target": target_price,
                "sl": sl_price,
                "qty": qty,
                "from_upstox": True,
                "entry_time": "Synced",
                "entry_source": "Synced",
                "ma20_distance": 0
            }
            
            dashboard_metrics["positions"][symbol] = position_data
            active_positions[symbol] = position_data
            dashboard_metrics["traded_symbols_today"].add(symbol)
            synced_count += 1
            
            logger.info(f"Synced position: {symbol} @ Rs{avg_price:.2f} (Qty: {qty})")
    
    logger.info(f"Position sync complete: {synced_count} positions loaded")

# ============================================
# MAIN BOT LOOP
# ============================================
def run_bot():
    """Main bot execution loop"""
    global dashboard_metrics
    
    logger.info("Bot v0.8 starting...")
    logger.info("Strategy: MORNING BOUNCE ONLY (9:15 AM - 1:30 PM)")
    
    # Sync existing positions from Upstox
    sync_upstox_positions()
    
    # Initial dashboard
    update_dashboard()
    
    while True:
        # EOD Exit check
        current_time = datetime.now().strftime("%H:%M")
        
        if current_time >= EOD_EXIT_TIME:
            logger.info("EOD EXIT TIME REACHED - Closing all positions")
            
            if dashboard_metrics["positions"]:
                for symbol in list(dashboard_metrics["positions"].keys()):
                    pos = dashboard_metrics["positions"][symbol]
                    instrument = WATCHLIST.get(symbol)
                    
                    if instrument:
                        current_price = get_live_price(instrument)
                        if current_price:
                            exit_result = place_exit_order(symbol, instrument, pos["qty"], current_price, "EOD_CLEANUP")
                            
                            if exit_result:
                                final_pnl = (current_price - pos["entry"]) * pos["qty"]
                                dashboard_metrics["pnl"] += final_pnl
                                
                                if final_pnl >= 0:
                                    dashboard_metrics["wins"] += 1
                                else:
                                    dashboard_metrics["losses"] += 1
                                
                                del dashboard_metrics["positions"][symbol]
            
            update_dashboard()
            logger.info(f"EOD Exit complete. Final P&L: Rs{dashboard_metrics['pnl']:+.2f}")
            logger.info("Bot stopping...")
            break
        
        try:
            strategy = get_current_strategy()
            dashboard_metrics["current_strategy"] = strategy
            
            if strategy == "MARKET_CLOSED":
                logger.info("Market closed. Bot stopping.")
                break
            
            elif strategy == "NO_TRADE":
                logger.info("Transition period - monitoring exits only")
                
                if dashboard_metrics["positions"]:
                    update_position_prices()
                    update_dashboard()
                
                time.sleep(60)
                continue
            
            elif strategy == "PRE_MARKET":
                logger.info("Pre-market - waiting for 9:15 AM")
                time.sleep(60)
                continue
            
            # MORNING_BOUNCE strategy active
            dashboard_metrics["last_scan"] = datetime.now()
            
            # Update existing positions
            if dashboard_metrics["positions"]:
                update_position_prices()
                update_dashboard()
            
            # Check trade limits
            trades_today = len(dashboard_metrics["traded_symbols_today"])
            if trades_today >= MAX_POSITIONS:
                logger.info(f"MAX TRADES REACHED ({trades_today}/{MAX_POSITIONS})")
                time.sleep(60)
                continue
            
            # Scan for new signals
            for symbol, instrument in WATCHLIST.items():
                logger.info(f"Scanning {symbol}...")
                
                has_signal, message = check_signal(instrument, strategy)
                logger.info(f"  {message}")
                
                if has_signal:
                    # Check if already have position
                    if symbol in dashboard_metrics["positions"]:
                        logger.info(f"SKIP - Already have {symbol} position")
                        continue
                    
                    # Check if already traded today
                    if symbol in dashboard_metrics["traded_symbols_today"]:
                        logger.info(f"SKIP - {symbol} already traded today")
                        continue
                    
                    # Play alert
                    play_signal_alert()
                    
                    logger.info("=" * 80)
                    logger.info(f"SIGNAL DETECTED FOR {symbol}!")
                    logger.info("=" * 80)
                    
                    if MONITOR_ONLY:
                        logger.info("MONITOR MODE: Logging signal without order")
                    else:
                        dashboard_metrics["signals_today"] += 1
                        
                        # Confirmation prompt
                        logger.info(f"Press ENTER to place order or type 'skip' to ignore")
                        try:
                            user_input = input().strip().lower()
                            if user_input == 'skip':
                                logger.info("Signal skipped by user")
                                continue
                        except KeyboardInterrupt:
                            logger.info("Signal skipped (Ctrl+C)")
                            continue
                    
                    # Place order
                    live_price = get_live_price(instrument)
                    if live_price:
                        order_value = live_price * QUANTITY
                        if order_value > MAX_CAPITAL_PER_ORDER:
                            logger.warning(f"SKIP {symbol} - Order value Rs{order_value:.2f} exceeds cap")
                            continue
                        
                        order_result = place_order(symbol, instrument, live_price, strategy)
                        if order_result:
                            logger.info(f"Order placed successfully: {symbol}")
                    
                    update_dashboard()
            
            # Wait for next scan (5 minutes)
            now = datetime.now()
            next_interval = ((now.minute // 5) + 1) * 5
            if next_interval >= 60:
                next_scan_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            else:
                next_scan_time = now.replace(minute=next_interval, second=0, microsecond=0)
            
            sleep_seconds = (next_scan_time - now).total_seconds()
            logger.info(f"Next scan at {next_scan_time.strftime('%H:%M:%S')} (in {int(sleep_seconds)}s)")
            
            update_dashboard()
            time.sleep(sleep_seconds)
        
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)
    
    logger.info("=" * 80)
    logger.info("Bot execution completed")
    logger.info("=" * 80)

if __name__ == "__main__":
    run_bot()
