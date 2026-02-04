"""
MA BOUNCE BOT v1.3 PRODUCTION - ENHANCED SIGNAL LOGGING 📊
============================================================
v1.3 (Jan 15, 2026) - ENHANCED SIGNAL DETAILS:
     ✅ Signal details capture (touch/bounce candles)
     ✅ Volume ratio tracking
     ✅ Candles gap measurement
     ✅ Enhanced logging for analysis

v1.2 (Jan 14, 2026) - UPSTOX v3 API MIGRATION:
     ✅ Migrated to Upstox API v3 (BASE_URL: https://api.upstox.com/v3)
     ✅ Fixed order_id → order_ids[0] response handling
     ✅ Updated historical candles: /minutes/5 format
     ✅ All v3 breaking changes addressed
     ✅ TRUE bounce logic + Direct 5-min candles
     ✅ 5 Top stocks: TATAMOTORS, POWERGRID, VEDL, ONGC, BHARTIARTL

v1.1 (Jan 14, 2026) - TRUE BOUNCE FIX:
     ✅ Fixed bounce detection: Touch + Bounce (15-min window)
     ✅ Replaced proximity logic with TRUE bounce validation
     ✅ Same logic as 48-month backtest v1.4

BACKTEST RESULTS (48 MONTHS - TRUE BOUNCE):
- TATAMOTORS: 52.1% consistency (NEW #1!)
- POWERGRID: 47.9% consistency (NEW #2!)
- VEDL: 45.8% consistency
- ONGC: 41.7% consistency
- BHARTIARTL: 41.7% consistency
============================================================
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
import time
from datetime import datetime, timedelta
import os
import csv
import logging
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.text import Text
# NEW
import os
from dotenv import load_dotenv

# Optional environment variable support
try:
    from dotenv import load_dotenv
    load_dotenv()
    ENV_AVAILABLE = True
except ImportError:
    ENV_AVAILABLE = False

# Cross-platform audio support
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
# AUDIO ALERT FUNCTION
# ============================================
def play_signal_alert():
    """Play 3 beeps to alert signal detection"""
    if AUDIO_AVAILABLE:
        try:
            for _ in range(3):
                winsound.Beep(1000, 200)
                time.sleep(0.1)
        except Exception:
            pass

# Load environment variables
load_dotenv()

API_KEY = os.getenv('UPSTOX_API_KEY')
API_SECRET = os.getenv('UPSTOX_API_SECRET')
ACCESS_TOKEN = os.getenv('UPSTOX_ACCESS_TOKEN')

# ============================================
# v1.1: TOP 5 STOCKS (TRUE BOUNCE 48-MONTH VALIDATED)
# ============================================
WATCHLIST = {
    "TATAMOTORS": "NSE_EQ|INE155A01022",    # #1: 52.1% consistency
    "POWERGRID": "NSE_EQ|INE752E01010",     # #2: 47.9% consistency
    "VEDL": "NSE_EQ|INE205A01025",          # #3: 45.8% consistency
    "ONGC": "NSE_EQ|INE213A01029",          # #4: 41.7% consistency
    "BHARTIARTL": "NSE_EQ|INE397D01024",    # #5: 41.7% consistency
}

# Symbol mapping for Upstox ticker differences
SYMBOL_MAPPING = {
    'TMPV': 'TATAMOTORS',  # Upstox uses TMPV ticker
}

# ============================================
# v1.0: UNIFIED CONFIG (NO FILTER + 1.5% + 0.5%)
# ============================================
TARGET_PCT = 0.015  # 1.5% target (backtest winner: 85% of Top 10)
STOP_LOSS_PCT = 0.005  # 0.5% stop loss (1:3 risk/reward)
BOUNCE_THRESHOLD_PCT = 0.5  # Within 0.5% of MA20
MA_PERIOD = 20  # MA20 only (no MA50/100/200 filters)

# Risk Management
MAX_CAPITAL_PER_ORDER = 10000  # ₹10k max per order
MAX_POSITIONS = 5  # Max 5 positions (Top 5 stocks)
MAX_TRADES_PER_DAY = 5  # One trade per stock per day
EOD_EXIT_TIME = "15:00"  # 3:00 PM square-off

# API Base
BASE_URL = "https://api.upstox.com/v3"  # Market data, positions
HFT_URL = "https://api-hft.upstox.com/v3"  # Order placement (lower latency)

# ============================================
# DATE-BASED LOGGING SETUP
# ============================================
today = datetime.now().strftime("%Y%m%d")
LOG_FILE = f"bot_activity_{today}.log"
TRADES_LOG_FILE = f"trades_log_{today}.csv"
TRADES_MASTER_FILE = "trades_log_master.csv"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info(f"MA BOUNCE BOT v1.3 PRODUCTION STARTED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("=" * 80)
logger.info("TOP 5 STOCKS: TATAMOTORS, POWERGRID, VEDL, ONGC, BHARTIARTL")
logger.info("CONFIG: TRUE Bounce + No Filter + 1.5% Target + 0.5% SL")
logger.info("=" * 80)

# ============================================
# NSE TRADING HOLIDAYS 2025-2026
# ============================================
NSE_HOLIDAYS = [
    # 2025
    "2025-01-26", "2025-02-26", "2025-03-14", "2025-03-31",
    "2025-04-10", "2025-04-14", "2025-04-18", "2025-05-01",
    "2025-05-12", "2025-06-07", "2025-08-15", "2025-08-27",
    "2025-10-02", "2025-10-21", "2025-11-05", "2025-11-24",
    "2025-12-25",
    # 2026
    "2026-01-26", "2026-03-03", "2026-03-21", "2026-03-30",
    "2026-04-02", "2026-04-06", "2026-04-14", "2026-04-21",
    "2026-05-01", "2026-05-26", "2026-08-15", "2026-08-16",
    "2026-10-02", "2026-10-10", "2026-10-24", "2026-11-13",
    "2026-11-25", "2026-12-25"
]

def is_trading_day():
    """Check if today is a trading day"""
    today = datetime.now().date()
    
    # Weekend check
    if today.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    
    # Holiday check
    today_str = today.strftime("%Y-%m-%d")
    if today_str in NSE_HOLIDAYS:
        return False
    
    return True

# ============================================
# DASHBOARD METRICS
# ============================================
dashboard_metrics = {
    "positions": {},
    "signals_today": 0,
    "trades_today": 0,
    "traded_symbols_today": set(),
    "total_pnl": 0.0,
    "last_scan": None,
    "current_strategy": "INITIALIZING"
}

# ============================================
# COLOR LOGGING
# ============================================
def log_with_color(message, level="INFO"):
    """Enhanced logging with colors"""
    if level == "SUCCESS":
        print(f"{GREEN}{message}{RESET}")
    elif level == "ERROR":
        print(f"{RED}{message}{RESET}")
    elif level == "WARNING":
        print(f"{YELLOW}{message}{RESET}")
    else:
        print(f"{CYAN}{message}{RESET}")

def load_today_metrics_from_csv():
    """Load today's trade count and traded symbols from CSV on bot startup"""
    try:
        if not os.path.isfile(TRADES_LOG_FILE):
            logger.info("No trades CSV found - starting fresh")
            return

        today_date = datetime.now().strftime('%Y-%m-%d')
        buy_count = 0
        traded_symbols = set()

        with open(TRADES_LOG_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamp = row.get('Timestamp', '')
                # Check if trade is from today
                if timestamp.startswith(today_date):
                    if row.get('Side') == 'BUY':
                        buy_count += 1
                        symbol = row.get('Symbol')
                        if symbol:
                            traded_symbols.add(symbol)

        # Update dashboard metrics
        dashboard_metrics["trades_today"] = buy_count
        dashboard_metrics["traded_symbols_today"] = traded_symbols

        if buy_count > 0:
            logger.info(f"📊 Loaded from CSV: {buy_count} trades today | Symbols: {traded_symbols}")
        else:
            logger.info("📊 No trades found in CSV for today - starting fresh")

    except Exception as e:
        logger.error(f"Error loading today's metrics from CSV: {e}")

# ============================================
# STRATEGY TIMING - v1.0 SINGLE STRATEGY
# ============================================
def get_current_strategy():
    """Determine current trading strategy based on time"""
    now = datetime.now()
    current_time = now.time()
    
    # Market hours: 9:15 AM - 3:30 PM
    market_start = datetime.strptime("09:15", "%H:%M").time()
    market_end = datetime.strptime("15:30", "%H:%M").time()
    
    # Trading window: 9:30 AM - 2:30 PM
    morning_start = datetime.strptime("09:30", "%H:%M").time()
    morning_end = datetime.strptime("14:30", "%H:%M").time()
    
    if current_time < market_start or current_time > market_end:
        return "MARKET_CLOSED"
    
    if morning_start <= current_time <= morning_end:
        return "MORNING_BOUNCE"
    
    # After 2:30 PM: Monitor only, no new trades
    return "NO_TRADE"

# ============================================
# UPSTOX API FUNCTIONS
# ============================================
def get_headers():
    """Get API headers with access token"""
    return {
        'Accept': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

def get_live_price(instrument_key):
    """Get current LTP for instrument"""
    try:
        url = f"{BASE_URL}/market-quote/ltp"
        params = {'instrument_key': instrument_key}
        response = requests.get(url, headers=get_headers(), params=params)

        if response.status_code == 200:
            data = response.json()

            if data['status'] == 'success' and 'data' in data:
                # Response has different key format - get first item
                first_key = list(data['data'].keys())[0]
                return data['data'][first_key]['last_price']

        return None
    except Exception as e:
        logger.error(f"Error fetching LTP: {e}")
        return None

def get_intraday_candles(instrument_key):
    """Get today's 5-minute intraday candles from Upstox"""
    try:
        url = f"{BASE_URL}/historical-candle/intraday/{instrument_key}/minutes/5"
        response = requests.get(url, headers=get_headers())

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
        logger.error(f"Intraday API error: {e}")
        return []



def calculate_ma(candles, period=20):
    """Calculate moving average"""
    if len(candles) < period:
        return None
    
    closes = [c['close'] for c in candles[-period:]]
    return sum(closes) / len(closes)

def check_signal(instrument_key, strategy):
    """Check for MA20 bounce signal - TRUE BOUNCE LOGIC v1.1"""
    try:
        # Get 5-minute intraday candles directly
        candles = get_intraday_candles(instrument_key)
        print(f"  DEBUG: Got {len(candles) if candles else 0} candles")

        if not candles or len(candles) < MA_PERIOD + 3:  # Need extra candles for bounce check
            return False, "Insufficient data", None, None
        
        # Calculate MA20 for all recent candles
        ma20_values = []
        for i in range(len(candles) - 3, len(candles)):  # Last 4 candles
            ma20 = calculate_ma(candles[:i+1], MA_PERIOD)
            ma20_values.append(ma20)
        
        if None in ma20_values:
            return False, "MA20 unavailable", None, None
        
        # TRUE BOUNCE DETECTION (15-min window: current + last 3 candles)
        # Check last 4 candles for touch + bounce pattern
        for i in range(len(candles) - 4, len(candles)):
            if i < MA_PERIOD:
                continue
                
            touch_candle = candles[i]
            ma20_at_touch = calculate_ma(candles[:i+1], MA_PERIOD)
            
            if ma20_at_touch is None:
                continue

            # STEP 1: TOUCH CHECK - Low touches or goes below MA20
            if touch_candle['low'] <= ma20_at_touch:

                # STEP 2: VOLUME CHECK - Must have 1.2x average volume
                avg_volume = sum(c['volume'] for c in candles[-20:]) / 20
                if touch_candle['volume'] < avg_volume * 1.2:
                    continue  # Skip weak volume bounce

                # STEP 3: BOUNCE CHECK - Check current + next candles (up to latest)
                for j in range(i, len(candles)):
                    bounce_candle = candles[j]

                    # Bounce confirmed if close > MA20 (at touch)
                    if bounce_candle['close'] > ma20_at_touch:
                        distance_pct = abs(bounce_candle['close'] - ma20_at_touch) / ma20_at_touch * 100
                        
                        # Calculate signal metrics
                        volume_ratio = touch_candle['volume'] / avg_volume
                        candles_gap = j - i  # Gap between touch and bounce
                        
                        # Capture signal details
                        signal_details = {
                            'touch_time': touch_candle['timestamp'],
                            'touch_low': touch_candle['low'],
                            'touch_volume': touch_candle['volume'],
                            'bounce_time': bounce_candle['timestamp'],
                            'bounce_close': bounce_candle['close'],
                            'bounce_volume': bounce_candle['volume'],
                            'avg_volume': avg_volume,
                            'volume_ratio': volume_ratio,
                            'candles_gap': candles_gap,
                            'ma20_at_touch': ma20_at_touch
                        }
                        
                        return True, f"✅ BOUNCE! Price: ₹{bounce_candle['close']:.2f}, MA20: ₹{ma20_at_touch:.2f}, Distance: {distance_pct:.2f}%, Vol: {volume_ratio:.2f}x", distance_pct, signal_details

        # No bounce detected
        latest = candles[-1]
        latest_ma20 = calculate_ma(candles, MA_PERIOD)
        distance_pct = abs(latest['close'] - latest_ma20) / latest_ma20 * 100
        return False, f"No signal (Distance: {distance_pct:.2f}%)", distance_pct, None
        
    except Exception as e:
        logger.error(f"Signal check error: {e}")
        return False, f"Error: {e}", None, None


def place_order(symbol, instrument_key, current_price, strategy, quantity, signal_details=None):
    """Place BUY order via Upstox API"""
    try:
        # Calculate targets
        target_price = current_price * (1 + TARGET_PCT)
        stop_loss_price = current_price * (1 - STOP_LOSS_PCT)
        
        logger.info(f"Placing order: {symbol} @ ₹{current_price:.2f} x {quantity} shares")
        logger.info(f"Target: ₹{target_price:.2f} (+{TARGET_PCT*100}%), SL: ₹{stop_loss_price:.2f} (-{STOP_LOSS_PCT*100}%)")
        
        if MONITOR_ONLY:
            log_with_color("📊 MONITOR-ONLY: Order simulated", "WARNING")
            order_id = f"SIM_{int(time.time())}"
        else:
            # Place actual order
            url = f"{HFT_URL}/order/place"
            order_data = {
                "quantity": quantity,
                "product": "I",  # Intraday
                "validity": "DAY",
                "price": 0,
                "tag": "MA_BOUNCE_v1.0",
                "instrument_token": instrument_key,
                "order_type": "MARKET",
                "transaction_type": "BUY",
                "disclosed_quantity": 0,
                "trigger_price": 0,
                "is_amo": False
            }
            
            response = requests.post(url, headers=get_headers(), json=order_data)
            
            if response.status_code == 200:
                result = response.json()
                if result['status'] == 'success':
                    order_id = result['data']['order_ids'][0]
                    log_with_color(f"✅ Order placed: {order_id}", "SUCCESS")
                else:
                    logger.error(f"Order failed: {result}")
                    return None
            else:
                logger.error(f"API error: {response.status_code}")
                return None
        
        # Add to dashboard
        add_position_to_dashboard(symbol, instrument_key, current_price, target_price, stop_loss_price, order_id, strategy, quantity)
        
        # Log to CSV with signal details
        log_trade_to_csv(symbol, "BUY", current_price, quantity, order_id, strategy, target_price, stop_loss_price, signal_details=signal_details)
        
        return order_id
        
    except Exception as e:
        logger.error(f"Order placement error: {e}")
        return None

def add_position_to_dashboard(symbol, instrument_key, entry_price, target_price, stop_loss, order_id, strategy, quantity):
    """Add position to tracking dashboard"""
    dashboard_metrics["positions"][symbol] = {
        "instrument_key": instrument_key,
        "entry_price": entry_price,
        "target_price": target_price,
        "stop_loss": stop_loss,
        "quantity": quantity,
        "current_price": entry_price,
        "pnl": 0.0,
        "pnl_pct": 0.0,
        "order_id": order_id,
        "strategy": strategy,
        "entry_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    dashboard_metrics["traded_symbols_today"].add(symbol)
    dashboard_metrics["trades_today"] += 1
    
    logger.info(f"Added {symbol} to dashboard")

def update_position_prices():
    """Update current prices for all open positions"""
    for symbol, pos in dashboard_metrics["positions"].items():
        current_price = get_live_price(pos["instrument_key"])
        
        if current_price:
            pos["current_price"] = current_price
            pos["pnl"] = (current_price - pos["entry_price"]) * pos["quantity"]
            pos["pnl_pct"] = ((current_price - pos["entry_price"]) / pos["entry_price"]) * 100
            
            # Check for target/SL hit
            if current_price >= pos["target_price"]:
                log_with_color(f"🎯 TARGET HIT: {symbol} @ ₹{current_price:.2f}", "SUCCESS")
                exit_position(symbol, current_price, "TARGET")
            elif current_price <= pos["stop_loss"]:
                log_with_color(f"🛑 STOP LOSS HIT: {symbol} @ ₹{current_price:.2f}", "ERROR")
                exit_position(symbol, current_price, "SL")

def exit_position(symbol, exit_price, reason):
    """Exit position and place SELL order"""
    try:
        pos = dashboard_metrics["positions"][symbol]
        
        logger.info(f"Exiting {symbol} @ ₹{exit_price:.2f} - Reason: {reason}")
        
        if not MONITOR_ONLY:
            url = f"{HFT_URL}/order/place"
            order_data = {
                "quantity": pos["quantity"],
                "product": "I",
                "validity": "DAY",
                "price": 0,
                "tag": f"EXIT_{reason}",
                "instrument_token": pos["instrument_key"],
                "order_type": "MARKET",
                "transaction_type": "SELL",
                "disclosed_quantity": 0,
                "trigger_price": 0,
                "is_amo": False
            }
            
            response = requests.post(url, headers=get_headers(), json=order_data)
            
            if response.status_code == 200:
                result = response.json()
                if result['status'] == 'success':
                    log_with_color(f"✅ Exit order placed: {result['data']['order_ids'][0]}", "SUCCESS")
        
        # Log exit to CSV
        pnl = (exit_price - pos["entry_price"]) * pos["quantity"]
        log_trade_to_csv(symbol, "SELL", exit_price, pos["quantity"], f"EXIT_{reason}", pos["strategy"], 0, 0, pnl, reason)
        
        # Remove from dashboard
        del dashboard_metrics["positions"][symbol]
        
    except Exception as e:
        logger.error(f"Exit error: {e}")

def log_trade_to_csv(symbol, side, price, quantity, order_id, strategy, target=0, sl=0, realized_pnl=0, exit_reason="", signal_details=None):
    """Log trade to daily and master CSV"""
    trade_data = {
        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Symbol': symbol,
        'Side': side,
        'Price': f"{price:.2f}",
        'Quantity': quantity,
        'Order_Value': f"{price * quantity:.2f}",
        'Strategy': strategy,
        'Target': f"{target:.2f}" if target > 0 else "",
        'Stop_Loss': f"{sl:.2f}" if sl > 0 else "",
        'Order_ID': order_id,
        'Realized_PnL': f"{realized_pnl:.2f}" if realized_pnl != 0 else "",
        'Exit_Reason': exit_reason,
        # Signal details (only for BUY orders)
        'Touch_Time': signal_details.get('touch_time', '') if signal_details else '',
        'Touch_Low': f"{signal_details.get('touch_low', 0):.2f}" if signal_details else '',
        'Touch_Vol': f"{signal_details.get('touch_volume', 0):,}" if signal_details else '',
        'Bounce_Time': signal_details.get('bounce_time', '') if signal_details else '',
        'Bounce_Close': f"{signal_details.get('bounce_close', 0):.2f}" if signal_details else '',
        'Bounce_Vol': f"{signal_details.get('bounce_volume', 0):,}" if signal_details else '',
        'Avg_Vol': f"{signal_details.get('avg_volume', 0):,.0f}" if signal_details else '',
        'Vol_Ratio': f"{signal_details.get('volume_ratio', 0):.2f}" if signal_details else '',
        'Candles_Gap': signal_details.get('candles_gap', '') if signal_details else '',
        'MA20': f"{signal_details.get('ma20_at_touch', 0):.2f}" if signal_details else ''
    }
    
    fieldnames = ['Timestamp', 'Symbol', 'Side', 'Price', 'Quantity', 'Order_Value', 
                  'Strategy', 'Target', 'Stop_Loss', 'Order_ID', 'Realized_PnL', 'Exit_Reason',
                  'Touch_Time', 'Touch_Low', 'Touch_Vol', 'Bounce_Time', 'Bounce_Close', 
                  'Bounce_Vol', 'Avg_Vol', 'Vol_Ratio', 'Candles_Gap', 'MA20']
    
    # Write to daily CSV
    for csv_file in [TRADES_LOG_FILE, TRADES_MASTER_FILE]:
        file_exists = os.path.isfile(csv_file)
        
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(trade_data)

def update_dashboard_rich():
    """Display live dashboard using Rich - smooth updates without flicker"""

    # Create table with enhanced title
    title = (f"MA BOUNCE BOT v1.0 PRODUCTION - LIVE DASHBOARD\n"
             f"Strategy: {dashboard_metrics['current_strategy']} | "
             f"Signals: {dashboard_metrics['signals_today']} | "
             f"Trades: {dashboard_metrics['trades_today']}/9")

    table = Table(title=title, show_header=True, title_style="bold cyan")

    table.add_column("Symbol", style="cyan", width=12)
    table.add_column("Entry", justify="right", width=10)
    table.add_column("Current", justify="right", width=10)
    table.add_column("Target", justify="right", width=10)
    table.add_column("SL", justify="right", width=10)
    table.add_column("P&L", justify="right", width=12)
    table.add_column("%", justify="right", width=10)

    if dashboard_metrics["positions"]:
        for symbol, pos in dashboard_metrics["positions"].items():
            color = "green" if pos['pnl'] > 0 else "red" if pos['pnl'] < 0 else "yellow"

            table.add_row(
                symbol,
                f"₹{pos['entry_price']:.2f}",
                f"₹{pos['current_price']:.2f}",
                f"₹{pos['target_price']:.2f}",
                f"₹{pos['stop_loss']:.2f}",
                f"[{color}]₹{pos['pnl']:+.2f}[/{color}]",
                f"[{color}]{pos['pnl_pct']:+.2f}%[/{color}]"
            )

        total_pnl = sum(p['pnl'] for p in dashboard_metrics['positions'].values())
        pnl_color = "green" if total_pnl > 0 else "red" if total_pnl < 0 else "yellow"
        table.add_row("", "", "", "", "TOTAL:", f"[bold {pnl_color}]₹{total_pnl:+.2f}[/bold {pnl_color}]", "", style="bold")
    else:
        table.add_row("[yellow]No open positions[/yellow]", "", "", "", "", "", "")

    return table

def get_active_position_count():
    """Get count of active positions from Upstox API"""
    try:
        url = f"{BASE_URL}/portfolio/short-term-positions"
        response = requests.get(url, headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success' and 'data' in data:
                return len(data['data'])
    except Exception:
        pass
    
    return len(dashboard_metrics["positions"])


def sync_positions_with_upstox():
    """Sync bot's position tracking with Upstox positions"""
    try:
        url = f"{BASE_URL}/portfolio/short-term-positions"
        response = requests.get(url, headers=get_headers())

        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success' and 'data' in data:
                upstox_positions = data['data']
                # DEBUG: Print the actual response structure
                if upstox_positions:
                    logger.info(f"DEBUG: Position fields = {upstox_positions[0].keys()}")

                for pos in upstox_positions:
                    symbol = pos['tradingsymbol']

                    # Map symbol if needed (e.g., TMPV → TATAMOTORS)
                    symbol = SYMBOL_MAPPING.get(symbol, symbol)

                    # Check if we're tracking this stock
                    if symbol in WATCHLIST and symbol not in dashboard_metrics["positions"]:
                        logger.info(f"Found untracked position: {symbol}")

                        # Try different field names for average price
                        avg_price = pos.get('average_price') or pos.get('buy_price') or pos.get('pnl', {}).get(
                            'average_price', 0)

                        logger.info(f"DEBUG {symbol}: avg_price={avg_price}, pos keys={list(pos.keys())}")

                        if avg_price == 0:
                            logger.warning(f"Skipping {symbol} - no average price")
                            continue

                        # Add to dashboard
                        dashboard_metrics["positions"][symbol] = {
                            "instrument_key": WATCHLIST[symbol],
                            "entry_price": avg_price,
                            "target_price": avg_price * (1 + TARGET_PCT),
                            "stop_loss": avg_price * (1 - STOP_LOSS_PCT),
                            "quantity": pos.get('quantity', 0),
                            "current_price": pos.get('last_price', avg_price),
                            "pnl": pos.get('unrealised', 0),
                            "pnl_pct": ((pos.get('last_price',
                                                 avg_price) - avg_price) / avg_price * 100) if avg_price > 0 else 0,
                            "order_id": "SYNCED",
                            "strategy": "MORNING_BOUNCE",
                            "entry_time": "SYNCED"
                        }

                        dashboard_metrics["traded_symbols_today"].add(symbol)
    except Exception as e:
        logger.error(f"Position sync error: {e}")

# ============================================
# MAIN BOT LOOP
# ============================================
def run_bot():
    """Main bot execution loop"""
    
    # Holiday check
    if not is_trading_day():
        log_with_color("📅 Market closed today (Weekend/Holiday)", "WARNING")
        logger.info("Market closed - Bot exiting")
        return
    
    log_with_color("🚀 MA Bounce Bot v1.0 PRODUCTION started!", "SUCCESS")
    log_with_color(f"📊 Monitoring {len(WATCHLIST)} stocks", "INFO")
    log_with_color(f"⚙️  Config: No Filter + 1.5% Target + 0.5% SL", "INFO")
    log_with_color(f"💰 Dynamic position sizing (you'll be prompted per signal)", "INFO")
    
    # Load today's trade metrics from CSV
    load_today_metrics_from_csv()

    # After loading CSV trades
    print("\n📡 Fetching live positions from Upstox...")
    try:
        positions_response = upstox.get_positions()
        open_positions = positions_response.get('data', [])

        # Rebuild dashboard from live positions
        for pos in open_positions:
            symbol = pos['tradingsymbol']
            qty = pos['quantity']
            buy_price = pos['average_price']

            if qty > 0:  # Long position
                dashboard_metrics["positions"][symbol] = {
                    "qty": qty,
                    "buy_price": buy_price,
                    "target": buy_price * 1.015,
                    "stop_loss": buy_price * 0.99
                }
                print(f"✅ Loaded position: {symbol} @ ₹{buy_price}")

    except Exception as e:
        print(f"⚠️ Could not fetch positions: {e}")

    # Sync existing positions
    sync_positions_with_upstox()
    
    while True:
        # Check for EOD exit
        current_time = datetime.now().strftime("%H:%M")
        if current_time >= EOD_EXIT_TIME:
            log_with_color("\n⏰ 3:00 PM - EOD EXIT TIME", "WARNING")
            
            if dashboard_metrics["positions"]:
                log_with_color("📤 Squaring off all positions...", "INFO")
                
                for symbol in list(dashboard_metrics["positions"].keys()):
                    current_price = get_live_price(dashboard_metrics["positions"][symbol]["instrument_key"])
                    if current_price:
                        exit_position(symbol, current_price, "EOD")
                
                log_with_color("✅ All positions squared off", "SUCCESS")
            else:
                log_with_color("📝 No open positions to close", "INFO")
            
            log_with_color("\n🛑 Bot stopping after EOD exit", "INFO")
            break
        
        try:
            strategy = get_current_strategy()
            dashboard_metrics["current_strategy"] = strategy
            
            if strategy == "MARKET_CLOSED":
                print("⏰ Market closed. Bot stopping.")
                break
            
            elif strategy == "NO_TRADE":
                print("⏸️  After 2:30 PM - Monitor only mode...")
                
                if dashboard_metrics["positions"]:
                    update_position_prices()
                    console = Console()
                    console.print(update_dashboard_rich())

                time.sleep(60)
                continue
            
            current_time_str = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{current_time_str}] Strategy: {strategy}")
            print("-" * 60)
            
            dashboard_metrics["last_scan"] = datetime.now()
            
            # Update existing positions
            if dashboard_metrics["positions"]:
                update_position_prices()
                console = Console()
                console.print(update_dashboard_rich())

                # Check max trades limit
                if dashboard_metrics["trades_today"] >= MAX_TRADES_PER_DAY:
                    print(f"\n{CYAN}{'=' * 70}{RESET}")
                    print("🏁 MAX TRADES REACHED FOR TODAY!")
                    print(f"📊 TRADES: {dashboard_metrics['trades_today']}/{MAX_TRADES_PER_DAY}")
                    print(f"⏸️  NO MORE NEW TRADES - Monitoring exits only...")
                    print(f"{CYAN}{'=' * 70}{RESET}\n")
                    
                    time.sleep(60)
                    continue
                
                # Check max positions
                if len(dashboard_metrics["positions"]) >= MAX_POSITIONS:
                    print(f"\n⚠️  MAX POSITIONS ({len(dashboard_metrics['positions'])}/{MAX_POSITIONS})")
                    print("   Waiting for exits before new trades...")
                    time.sleep(60)
                    continue

            # Get current time
            now = datetime.now()
            current_time = now.strftime("%H:%M")

            # Block new signals after 2:30 PM
            if current_time >= "14:30":
                print("⏸️  NO MORE SIGNALS - Too late in day")
                # Continue loop to monitor exits only
                time.sleep(30)
                continue

            # Scan for new signals
            for symbol, instrument in WATCHLIST.items():
                print(f"\nScanning {symbol}...")
                
                has_signal, message, ma20_distance, signal_details = check_signal(instrument, strategy)
                print(f"  {message}")
                
                if has_signal:
                    # Check if already have position
                    if symbol in dashboard_metrics["positions"]:
                        print(f"⏭️  SKIP - Already have {symbol} position")
                        continue
                    
                    # Check if already traded today
                    if symbol in dashboard_metrics["traded_symbols_today"]:
                        print(f"⏭️  SKIP - {symbol} already traded today")
                        continue
                    
                    # Increment signals counter
                    dashboard_metrics["signals_today"] += 1
                    
                    # Log signal details
                    if signal_details:
                        logger.info("=" * 80)
                        logger.info("SIGNAL DETAILS:")
                        logger.info(f"  Touch Time: {signal_details['touch_time']}")
                        logger.info(f"  Touch Low: ₹{signal_details['touch_low']:.2f}")
                        logger.info(f"  Touch Volume: {signal_details['touch_volume']:,}")
                        logger.info(f"  Bounce Time: {signal_details['bounce_time']}")
                        logger.info(f"  Bounce Close: ₹{signal_details['bounce_close']:.2f}")
                        logger.info(f"  Bounce Volume: {signal_details['bounce_volume']:,}")
                        logger.info(f"  Avg Volume (20): {signal_details['avg_volume']:,.0f}")
                        logger.info(f"  Volume Ratio: {signal_details['volume_ratio']:.2f}x")
                        logger.info(f"  Candles Gap: {signal_details['candles_gap']}")
                        logger.info(f"  MA20 at Touch: ₹{signal_details['ma20_at_touch']:.2f}")
                        logger.info("=" * 80)
                    
                    # Play alert beeps
                    play_signal_alert()
                    
                    print("\n" + "=" * 70)
                    print(f"🔔 SIGNAL DETECTED FOR {symbol}!")
                    print("=" * 70)
                    
                    # Get live price
                    live_price = get_live_price(instrument)
                    if not live_price:
                        print("❌ Could not fetch live price. Skipping...")
                        continue
                    
                    print(f"💹 Current Price: ₹{live_price:.2f}")
                    print("=" * 70)
                    
                    if MONITOR_ONLY:
                        print("📊 MONITOR-ONLY MODE: Logging signal without placing order")
                        print("=" * 70 + "\n")
                        
                        # Use default 5 shares in monitor mode
                        order_result = place_order(symbol, instrument, live_price, strategy, 5, signal_details)
                        if order_result:
                            print(f"✅ Signal logged successfully")
                    else:
                        # INTERACTIVE PROMPTS
                        try:
                            # Step 1: Ask for quantity
                            print(f"\n📊 How many shares to buy? (Press Enter to skip): ", end='')
                            qty_input = input().strip()
                            
                            if qty_input.lower() in ['skip', '']:
                                print("⏭️  Signal skipped by user\n")
                                continue
                            
                            try:
                                quantity = int(qty_input)
                                if quantity <= 0:
                                    print("❌ Invalid quantity. Skipping...")
                                    continue
                            except ValueError:
                                print("❌ Invalid input. Skipping...")
                                continue
                            
                            # Step 2: Calculate and show capital requirement
                            total_capital = live_price * quantity
                            target_price = live_price * (1 + TARGET_PCT)
                            stop_loss_price = live_price * (1 - STOP_LOSS_PCT)
                            
                            target_value = target_price * quantity
                            stop_loss_value = stop_loss_price * quantity
                            
                            potential_profit = target_value - total_capital
                            potential_loss = total_capital - stop_loss_value
                            
                            print(f"\n{'='*70}")
                            print(f"💰 CAPITAL REQUIREMENT:")
                            print(f"{'='*70}")
                            print(f"   Total Capital: ₹{total_capital:,.2f}")
                            print(f"   Target (1.5%): ₹{target_value:,.2f} (Profit: +₹{potential_profit:.2f})")
                            print(f"   Stop Loss (0.5%): ₹{stop_loss_value:,.2f} (Loss: -₹{potential_loss:.2f})")
                            print(f"{'='*70}")
                            
                            # Step 3: Confirmation
                            print(f"\n⚠️  Proceed with order? (yes/no): ", end='')
                            confirm = input().strip().lower()
                            
                            if confirm not in ['yes', 'y']:
                                print("⏭️  Order cancelled by user\n")
                                continue
                            
                            print("✅ Order confirmed, proceeding...\n")
                            
                            # Capital cap check
                            if total_capital > MAX_CAPITAL_PER_ORDER:
                                log_with_color(
                                    f"⏭️  SKIP {symbol} - Order value ₹{total_capital:.2f} exceeds cap (₹{MAX_CAPITAL_PER_ORDER})",
                                    "WARNING")
                                logger.warning(f"Skipped {symbol} - exceeds capital cap")
                                continue
                            
                            # Place order with signal details
                            order_result = place_order(symbol, instrument, live_price, strategy, quantity, signal_details)
                            if order_result:
                                print(f"📝 Added {symbol} to active positions")
                        
                        except KeyboardInterrupt:
                            print("\n⏭️  Signal skipped (Ctrl+C)\n")
                            continue
                        except Exception as e:
                            print(f"\n❌ Error processing signal: {e}\n")
                            continue
                    
                    console = Console()
                    console.print(update_dashboard_rich())

            # Wait until next 5-minute mark
            now = datetime.now()
            current_minute = now.minute

            next_interval = ((current_minute // 5) + 1) * 5
            if next_interval >= 60:
                next_interval = 0
                next_scan_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            else:
                next_scan_time = now.replace(minute=next_interval, second=0, microsecond=0)

            sleep_seconds = (next_scan_time - now).total_seconds()

            logger.info(f"⏳ Next scan at {next_scan_time.strftime('%H:%M:%S')} (in {int(sleep_seconds)}s)")

            console = Console()

            # Countdown with Rich Live display (smooth, no flicker)
            with Live(console=console, refresh_per_second=1, screen=False) as live:
                while sleep_seconds > 0:
                    mins, secs = divmod(int(sleep_seconds), 60)
                    timer = f"{mins:02d}:{secs:02d}"

                    # Update positions every 5 seconds
                    if int(sleep_seconds) % 5 == 0 and dashboard_metrics["positions"]:
                        update_position_prices()

                    # Create display
                    if dashboard_metrics["positions"]:
                        table = update_dashboard_rich()
                        total_pnl = sum(p['pnl'] for p in dashboard_metrics['positions'].values())

                        # Combine table with footer
                        from rich.console import Group
                        footer = Text(f"\n💰 Total P&L: ₹{total_pnl:+.2f} | ⏱️  Next scan: {timer}", style="bold cyan")
                        display_group = Group(table, footer)
                        live.update(display_group)
                    else:
                        live.update(Text(f"⏱️  Next scan: {timer}", style="cyan"))

                    time.sleep(1)
                    sleep_seconds -= 1

        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped by user.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Main loop error: {e}")
            time.sleep(60)
    
    print("\n" + "=" * 60)
    print("Bot execution completed.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    run_bot()
