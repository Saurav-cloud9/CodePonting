"""
MA BOUNCE BOT v1.0 PRODUCTION 🚀
============================================================
v1.0 (Jan 12, 2026) - LIVE DEPLOYMENT:
     ✅ 9 Champion Stocks (48-month backtest validated)
     ✅ Unified Config: No Filter + 1.5% Target + 0.5% SL
     ✅ TIER 1: VEDL, TATAMOTORS, BHARTIARTL, SUNPHARMA, HINDALCO
     ✅ TIER 2: ONGC, TATASTEEL, CIPLA, PNB
     ✅ Single strategy: MORNING_BOUNCE (9:30 AM - 2:30 PM)
     ✅ Week 1 Testing: 5 shares per stock (₹2,500-10k risk)
     ✅ Append-mode logging (survives restarts)

BACKTEST RESULTS (48 MONTHS):
- VEDL: 50.0% consistency, +142% momentum
- TATAMOTORS: 43.8% consistency, +219% momentum
- BHARTIARTL: 41.7% consistency, +294% momentum
- SUNPHARMA: 41.7% consistency, +294% momentum
- HINDALCO: 37.5% consistency, +100% momentum
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
import json
import time
from datetime import datetime, timedelta
import os
import csv
import logging

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

# ============================================
# CONFIGURATION - v1.0 PRODUCTION
# ============================================

# Upstox API Credentials
API_KEY = "18185106-6257-4a85-a84a-2ea314f91927"
API_SECRET = "15m0va42ni"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTYzNjM1NzczOGU1NDNmMDIwYmNjMjQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2ODEyMTE3NSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY4MTY4ODAwfQ.g5X2qmcKTDqvOCOxhJ1ndpl3KXPPPXcUvgbLu_AlB3U"

# ============================================
# v1.0: 9 CHAMPION STOCKS (48-MONTH VALIDATED)
# ============================================
WATCHLIST = {
    # TIER 1: PRODUCTION READY (Super Rising Stars)
    "VEDL": "NSE_EQ|INE205A01025",           # #1: 50.0%, +142% momentum
    "TATAMOTORS": "NSE_EQ|INE155A01022",    # #2: 43.8%, +219% momentum
    "BHARTIARTL": "NSE_EQ|INE397D01024",    # #4: 41.7%, +294% momentum
    "SUNPHARMA": "NSE_EQ|INE044A01036",     # #6: 41.7%, +294% momentum
    "HINDALCO": "NSE_EQ|INE038A01020",      # #12: 37.5%, +100% momentum
    
    # TIER 2: NEXT IN LINE (All-Weather + Improving)
    "ONGC": "NSE_EQ|INE213A01029",          # #3: 41.7%, Stable
    "TATASTEEL": "NSE_EQ|INE081A01020",     # #8: 39.6%, +11% momentum
    "CIPLA": "NSE_EQ|INE059A01026",         # #9: 39.6%, +39% momentum
    "PNB": "NSE_EQ|INE160A01022",           # #10: 39.6%, +11% momentum
}

# ============================================
# v1.0: UNIFIED CONFIG (NO FILTER + 1.5% + 0.5%)
# ============================================
QUANTITY = 5  # Week 1 testing: 5 shares per stock
TARGET_PCT = 0.015  # 1.5% target (backtest winner: 85% of Top 10)
STOP_LOSS_PCT = 0.005  # 0.5% stop loss (1:3 risk/reward)
BOUNCE_THRESHOLD_PCT = 0.5  # Within 0.5% of MA20
MA_PERIOD = 20  # MA20 only (no MA50/100/200 filters)

# Risk Management
MAX_CAPITAL_PER_ORDER = 10000  # ₹10k max per order
MAX_POSITIONS = 9  # Max 9 positions (one per stock)
MAX_TRADES_PER_DAY = 9  # One trade per stock per day
EOD_EXIT_TIME = "15:00"  # 3:00 PM square-off

# API Base
BASE_URL = "https://api.upstox.com/v2"

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
logger.info(f"MA BOUNCE BOT v1.0 PRODUCTION STARTED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("=" * 80)
logger.info("TIER 1 STOCKS: VEDL, TATAMOTORS, BHARTIARTL, SUNPHARMA, HINDALCO")
logger.info("TIER 2 STOCKS: ONGC, TATASTEEL, CIPLA, PNB")
logger.info("CONFIG: No Filter + 1.5% Target + 0.5% SL")
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
            if data['status'] == 'success':
                ltp = data['data'][instrument_key]['last_price']
                return ltp
    except Exception as e:
        logger.error(f"Error fetching LTP: {e}")
    return None

def get_historical_candles(instrument_key, from_date, to_date):
    """Fetch 5-minute historical candles from Upstox"""
    try:
        url = f"{BASE_URL}/historical-candle/{instrument_key}/5minute/{to_date}/{from_date}"
        response = requests.get(url, headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success' and 'data' in data and 'candles' in data['data']:
                candles = data['data']['candles']
                
                if len(candles) > 0:
                    df_data = []
                    for candle in candles:
                        df_data.append({
                            'timestamp': candle[0],
                            'open': float(candle[1]),
                            'high': float(candle[2]),
                            'low': float(candle[3]),
                            'close': float(candle[4]),
                            'volume': int(candle[5])
                        })
                    
                    # Sort by timestamp
                    df_data.sort(key=lambda x: x['timestamp'])
                    return df_data
        
        return None
    except Exception as e:
        logger.error(f"Error fetching candles: {e}")
        return None

def calculate_ma(candles, period=20):
    """Calculate moving average"""
    if len(candles) < period:
        return None
    
    closes = [c['close'] for c in candles[-period:]]
    return sum(closes) / len(closes)

def check_signal(instrument_key, strategy):
    """Check for MA20 bounce signal - v1.0 NO FILTER"""
    try:
        # Get today's date
        today = datetime.now()
        from_date = (today - timedelta(days=10)).strftime('%Y-%m-%d')
        to_date = today.strftime('%Y-%m-%d')
        
        candles = get_historical_candles(instrument_key, from_date, to_date)
        
        if not candles or len(candles) < MA_PERIOD:
            return False, "Insufficient data", None
        
        # Calculate MA20
        ma20 = calculate_ma(candles, MA_PERIOD)
        if ma20 is None:
            return False, "MA20 unavailable", None
        
        # Get latest candle
        latest = candles[-1]
        current_price = latest['close']
        
        # Calculate distance from MA20
        distance_pct = abs(current_price - ma20) / ma20 * 100
        
        # Bounce detection: Within 0.5% of MA20 AND price >= MA20
        if distance_pct <= BOUNCE_THRESHOLD_PCT and current_price >= ma20:
            return True, f"✅ BOUNCE! Price: ₹{current_price:.2f}, MA20: ₹{ma20:.2f}, Distance: {distance_pct:.2f}%", distance_pct
        
        return False, f"No signal (Distance: {distance_pct:.2f}%)", distance_pct
        
    except Exception as e:
        logger.error(f"Signal check error: {e}")
        return False, f"Error: {e}", None

def place_order(symbol, instrument_key, current_price, strategy):
    """Place BUY order via Upstox API"""
    try:
        # Calculate targets
        target_price = current_price * (1 + TARGET_PCT)
        stop_loss_price = current_price * (1 - STOP_LOSS_PCT)
        
        logger.info(f"Placing order: {symbol} @ ₹{current_price:.2f}")
        logger.info(f"Target: ₹{target_price:.2f} (+{TARGET_PCT*100}%), SL: ₹{stop_loss_price:.2f} (-{STOP_LOSS_PCT*100}%)")
        
        if MONITOR_ONLY:
            log_with_color("📊 MONITOR-ONLY: Order simulated", "WARNING")
            order_id = f"SIM_{int(time.time())}"
        else:
            # Place actual order
            url = f"{BASE_URL}/order/place"
            order_data = {
                "quantity": QUANTITY,
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
                    order_id = result['data']['order_id']
                    log_with_color(f"✅ Order placed: {order_id}", "SUCCESS")
                else:
                    logger.error(f"Order failed: {result}")
                    return None
            else:
                logger.error(f"API error: {response.status_code}")
                return None
        
        # Add to dashboard
        add_position_to_dashboard(symbol, instrument_key, current_price, target_price, stop_loss_price, order_id, strategy)
        
        # Log to CSV
        log_trade_to_csv(symbol, "BUY", current_price, QUANTITY, order_id, strategy, target_price, stop_loss_price)
        
        return order_id
        
    except Exception as e:
        logger.error(f"Order placement error: {e}")
        return None

def add_position_to_dashboard(symbol, instrument_key, entry_price, target_price, stop_loss, order_id, strategy):
    """Add position to tracking dashboard"""
    dashboard_metrics["positions"][symbol] = {
        "instrument_key": instrument_key,
        "entry_price": entry_price,
        "target_price": target_price,
        "stop_loss": stop_loss,
        "quantity": QUANTITY,
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
            url = f"{BASE_URL}/order/place"
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
                    log_with_color(f"✅ Exit order placed: {result['data']['order_id']}", "SUCCESS")
        
        # Log exit to CSV
        pnl = (exit_price - pos["entry_price"]) * pos["quantity"]
        log_trade_to_csv(symbol, "SELL", exit_price, pos["quantity"], f"EXIT_{reason}", pos["strategy"], 0, 0, pnl, reason)
        
        # Remove from dashboard
        del dashboard_metrics["positions"][symbol]
        
    except Exception as e:
        logger.error(f"Exit error: {e}")

def log_trade_to_csv(symbol, side, price, quantity, order_id, strategy, target=0, sl=0, realized_pnl=0, exit_reason=""):
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
        'Exit_Reason': exit_reason
    }
    
    fieldnames = ['Timestamp', 'Symbol', 'Side', 'Price', 'Quantity', 'Order_Value', 
                  'Strategy', 'Target', 'Stop_Loss', 'Order_ID', 'Realized_PnL', 'Exit_Reason']
    
    # Write to daily CSV
    for csv_file in [TRADES_LOG_FILE, TRADES_MASTER_FILE]:
        file_exists = os.path.isfile(csv_file)
        
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(trade_data)

def update_dashboard():
    """Display live dashboard"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("\n" + "="*80)
    print(f"{CYAN}MA BOUNCE BOT v1.0 PRODUCTION - LIVE DASHBOARD{RESET}")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Strategy: {dashboard_metrics['current_strategy']}")
    print(f"Signals: {dashboard_metrics['signals_today']} | Trades: {dashboard_metrics['trades_today']}/9")
    print("="*80)
    
    if dashboard_metrics["positions"]:
        print(f"\n{CYAN}{'Symbol':<12} {'Entry':<8} {'Current':<8} {'Target':<8} {'SL':<8} {'P&L':<10} {'%':<8}{RESET}")
        print("-"*80)
        
        for symbol, pos in dashboard_metrics["positions"].items():
            color = GREEN if pos['pnl'] > 0 else RED if pos['pnl'] < 0 else YELLOW
            print(f"{color}{symbol:<12} ₹{pos['entry_price']:<7.2f} ₹{pos['current_price']:<7.2f} "
                  f"₹{pos['target_price']:<7.2f} ₹{pos['stop_loss']:<7.2f} "
                  f"₹{pos['pnl']:<9.2f} {pos['pnl_pct']:<7.2f}%{RESET}")
        
        total_pnl = sum(p['pnl'] for p in dashboard_metrics['positions'].values())
        print("-"*80)
        print(f"{CYAN}TOTAL P&L: ₹{total_pnl:+.2f}{RESET}")
    else:
        print(f"\n{YELLOW}No open positions{RESET}")
    
    print("="*80 + "\n")

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
                
                for pos in upstox_positions:
                    symbol = pos['tradingsymbol']
                    
                    # Check if we're tracking this stock
                    if symbol in WATCHLIST and symbol not in dashboard_metrics["positions"]:
                        logger.info(f"Found untracked position: {symbol}")
                        
                        # Add to dashboard (as best effort - won't have all original data)
                        dashboard_metrics["positions"][symbol] = {
                            "instrument_key": WATCHLIST[symbol],
                            "entry_price": pos['average_price'],
                            "target_price": pos['average_price'] * (1 + TARGET_PCT),
                            "stop_loss": pos['average_price'] * (1 - STOP_LOSS_PCT),
                            "quantity": pos['quantity'],
                            "current_price": pos['last_price'],
                            "pnl": pos['unrealised'],
                            "pnl_pct": (pos['last_price'] - pos['average_price']) / pos['average_price'] * 100,
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
    log_with_color(f"💰 Position size: {QUANTITY} shares per stock", "INFO")
    
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
                    update_dashboard()
                
                time.sleep(60)
                continue
            
            current_time_str = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{current_time_str}] Strategy: {strategy}")
            print("-" * 60)
            
            dashboard_metrics["last_scan"] = datetime.now()
            
            # Update existing positions
            if dashboard_metrics["positions"]:
                update_position_prices()
                update_dashboard()
                
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
            
            # Scan for new signals
            for symbol, instrument in WATCHLIST.items():
                print(f"\nScanning {symbol}...")
                
                has_signal, message, ma20_distance = check_signal(instrument, strategy)
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
                    
                    # Play alert beeps
                    play_signal_alert()
                    
                    print("\n" + "=" * 60)
                    print(f"🔔 SIGNAL DETECTED FOR {symbol}!")
                    print("=" * 60)
                    
                    if MONITOR_ONLY:
                        print("📊 MONITOR-ONLY MODE: Logging signal without placing order")
                        print("=" * 60 + "\n")
                        
                        live_price = get_live_price(instrument)
                        if live_price:
                            order_result = place_order(symbol, instrument, live_price, strategy)
                            if order_result:
                                print(f"✅ Signal logged successfully")
                    else:
                        # Live trading - get confirmation
                        print("⚠️  SIGNAL DETECTED - Review and confirm:")
                        print(f"    Symbol: {symbol}")
                        print(f"    Strategy: {strategy}")
                        print(f"    Press ENTER to place order (or type 'skip' to ignore)")
                        print("=" * 60 + "\n")
                        
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
                            # Capital cap check
                            order_value = live_price * QUANTITY
                            if order_value > MAX_CAPITAL_PER_ORDER:
                                log_with_color(
                                    f"⏭️  SKIP {symbol} - Order value ₹{order_value:.2f} exceeds cap (₹{MAX_CAPITAL_PER_ORDER})",
                                    "WARNING")
                                logger.warning(f"Skipped {symbol} - exceeds capital cap")
                                continue
                            
                            order_result = place_order(symbol, instrument, live_price, strategy)
                            if order_result:
                                print(f"📝 Added {symbol} to active positions")
                    
                    update_dashboard()
            
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
            
            print(f"\n⏳ Next scan at {next_scan_time.strftime('%H:%M:%S')}")
            logger.info(f"Next scan at {next_scan_time.strftime('%H:%M:%S')} (in {int(sleep_seconds)}s)")
            
            # Countdown timer
            while sleep_seconds > 0:
                mins, secs = divmod(int(sleep_seconds), 60)
                timer = f"{mins:02d}:{secs:02d}"
                
                update_dashboard()
                print(f"\r⏱️  Next scan: {timer}   ", end='', flush=True)
                
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
