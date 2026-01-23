"""
╔═══════════════════════════════════════════════════════════════╗
║   MEGA BACKTEST - 48 Months × 30 F&O Stocks (CONSOLE ONLY)   ║
║   Jan 2022 → Dec 2025 | Speed Optimized | No Excel           ║
╚═══════════════════════════════════════════════════════════════╝
"""

import upstox_client
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTY1MTMzZGI1OTZjOTRjMTNlYTNhMzYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2ODIzMTc0MSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY4MjU1MjAwfQ.d5NYoR4EK-D5B39BO5NwZm4SY8iud0rv0mQEUoWvPCc"

STOCKS = {
    'TATASTEEL': 'NSE_EQ|INE081A01020',
    'HINDALCO': 'NSE_EQ|INE038A01020',
    'JSWSTEEL': 'NSE_EQ|INE019A01038',
    'NATIONALUM': 'NSE_EQ|INE139A01034',
    'SBIN': 'NSE_EQ|INE062A01020',
    'HDFCBANK': 'NSE_EQ|INE040A01034',
    'ICICIBANK': 'NSE_EQ|INE090A01021',
    'AXISBANK': 'NSE_EQ|INE238A01034',
    'PNB': 'NSE_EQ|INE160A01022',
    'INDUSINDBK': 'NSE_EQ|INE095A01012',
    'INFY': 'NSE_EQ|INE009A01021',
    'WIPRO': 'NSE_EQ|INE075A01022',
    'TECHM': 'NSE_EQ|INE669C01036',
    'TATAMOTORS': 'NSE_EQ|INE155A01022',
    'ASHOKLEY': 'NSE_EQ|INE208A01029',
    'SUNPHARMA': 'NSE_EQ|INE044A01036',
    'DIVISLAB': 'NSE_EQ|INE361B01024',
    'CIPLA': 'NSE_EQ|INE059A01026',
    'RELIANCE': 'NSE_EQ|INE002A01018',
    'ONGC': 'NSE_EQ|INE213A01029',
    'COALINDIA': 'NSE_EQ|INE522F01014',
    'ITC': 'NSE_EQ|INE154A01025',
    'DABUR': 'NSE_EQ|INE016A01026',
    'BHARTIARTL': 'NSE_EQ|INE397D01024',
    'IDEA': 'NSE_EQ|INE669E01016',
    'NTPC': 'NSE_EQ|INE733E01010',
    'POWERGRID': 'NSE_EQ|INE752E01010',
    'ADANIPORTS': 'NSE_EQ|INE742F01042',
    'VEDL': 'NSE_EQ|INE205A01025',
    'BANDHANBNK': 'NSE_EQ|INE545U01014'
}

TARGETS = [0.005, 0.01, 0.015]
STOP_LOSS = 0.005
VOLUME_MULTIPLIER = 1.2

FILTERS = {
    'No Filter': [],
    'MA50': ['ma50'],
    'MA100': ['ma100'],
    'MA200': ['ma200'],
    'MA50+100': ['ma50', 'ma100'],
    'MA50+200': ['ma50', 'ma200'],
    'MA100+200': ['ma100', 'ma200'],
    'MA50+100+200': ['ma50', 'ma100', 'ma200']
}

configuration = upstox_client.Configuration()
configuration.access_token = ACCESS_TOKEN

# ═══════════════════════════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════════════════════════

def fetch_upstox_data(instrument_key, from_date, to_date):
    try:
        api_instance = upstox_client.HistoryV3Api(upstox_client.ApiClient(configuration))
        api_response = api_instance.get_historical_candle_data1(
            instrument_key=instrument_key,
            unit="minutes",
            interval="5",
            to_date=to_date.strftime('%Y-%m-%d'),
            from_date=from_date.strftime('%Y-%m-%d')
        )
        
        if not hasattr(api_response, 'data') or not api_response.data:
            return None
        
        candles = api_response.data.candles
        if len(candles) == 0:
            return None
        
        candle_data = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        candle_data['datetime'] = pd.to_datetime(candle_data['datetime'])
        candle_data = candle_data.sort_values('datetime').reset_index(drop=True)
        candle_data['ma20'] = candle_data['close'].rolling(20).mean()
        candle_data['avg_volume'] = candle_data['volume'].rolling(20).mean()
        return candle_data
    except:
        return None

def fetch_daily_daily_daily_mas_data_data(instrument_key, end_date):
    try:
        api_instance = upstox_client.HistoryV3Api(upstox_client.ApiClient(configuration))
        start_date = end_date - timedelta(days=400)
        
        api_response = api_instance.get_historical_candle_data1(
            instrument_key=instrument_key,
            unit="days",
            interval="1",
            to_date=end_date.strftime('%Y-%m-%d'),
            from_date=start_date.strftime('%Y-%m-%d')
        )
        
        if not hasattr(api_response, 'data') or not api_response.data:
            return None
        
        candles = api_response.data.candles
        candle_data = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        candle_data['datetime'] = pd.to_datetime(candle_data['datetime'])
        candle_data = candle_data.sort_values('datetime').reset_index(drop=True)
        candle_data['ma50'] = candle_data['close'].rolling(50).mean()
        candle_data['ma100'] = candle_data['close'].rolling(100).mean()
        candle_data['ma200'] = candle_data['close'].rolling(200).mean()
        candle_data['date'] = candle_data['datetime'].dt.date
        return candle_data[['date', 'ma50', 'ma100', 'ma200']]
    except:
        return None


def check_ma_filter(row, required_daily_daily_mas_data_data):
    """Check if price is above required daily_daily_mas_data_data"""
    if not required_daily_daily_mas_data_data:  # No filter
        return True

    for ma in required_daily_daily_mas_data_data:
        if pd.isna(row[ma]) or row['close'] < row[ma]:
            return False
    return True

def detect_bounce(candle_data, filter_daily_daily_mas_data_data):
    """Detect MA20 bounce signals - TRUE BOUNCE LOGIC v1.0"""
    signals = []

    for i in range(20, len(candle_data) - 3):  # -3 to allow checking next 3 candles
        row = candle_data.iloc[i]

        # Skip if MA20 not available
        if pd.isna(row['ma20']):
            continue

        # Check MA filter first
        if not check_ma_filter(row, filter_daily_daily_mas_data_data):
            continue

        # Volume confirmation (1.2x average)
        if pd.notna(row['avg_volume']) and row['volume'] < row['avg_volume'] * VOLUME_MULTIPLIER:
            continue

        # STEP 1: TOUCH CHECK - Price must touch or go below MA20
        if row['low'] <= row['ma20']:
            
            # STEP 2: BOUNCE CHECK - Check current + next 3 candles (15-min window)
            ma20_at_touch = row['ma20']  # Lock MA20 at touch candle
            
            for j in range(i, min(i + 4, len(candle_data))):  # Check i, i+1, i+2, i+3
                bounce_candle = candle_data.iloc[j]
                
                # Bounce confirmed if close > MA20 (at touch)
                if bounce_candle['close'] > ma20_at_touch:
                    signals.append({
                        'datetime': bounce_candle['datetime'],
                        'entry_price': bounce_candle['close'],
                        'ma20': ma20_at_touch,
                        'volume': row['volume'],  # Touch candle volume
                        'avg_volume': row['avg_volume']
                    })
                    break  # Stop checking once bounce confirmed

    return signals


def simulate_trades(candle_data, signals, target_pct):
    """Simulate trades with target and stop loss"""
    trades = []

    for signal in signals:
        entry_price = signal['entry_price']
        entry_time = signal['datetime']
        entry_idx = candle_data[candle_data['datetime'] == entry_time].index[0]

        target_price = entry_price * (1 + target_pct)
        stop_price = entry_price * (1 - STOP_LOSS)

        # Scan next candles for exit
        exit_price = None
        exit_time = None
        exit_reason = None

        for j in range(entry_idx + 1, min(entry_idx + 80, len(candle_data))):  # Max 80 candles (6.5 hours)
            candle = candle_data.iloc[j]

            # Check stop loss first
            if candle['low'] <= stop_price:
                exit_price = stop_price
                exit_time = candle['datetime']
                exit_reason = 'SL'
                break

            # Check target
            if candle['high'] >= target_price:
                exit_price = target_price
                exit_time = candle['datetime']
                exit_reason = 'Target'
                break

        # If no exit, close at end of day (last candle)
        if exit_price is None:
            last_candle = candle_data.iloc[min(entry_idx + 79, len(candle_data) - 1)]
            exit_price = last_candle['close']
            exit_time = last_candle['datetime']
            exit_reason = 'EOD'

        # Calculate P&L
        pnl = exit_price - entry_price
        pnl_pct = (pnl / entry_price) * 100

        trades.append({
            'entry_time': entry_time,
            'entry_price': entry_price,
            'exit_time': exit_time,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'reason': exit_reason
        })

    return trades

# ═══════════════════════════════════════════════════════════════
# BACKTEST ENGINE
# ═══════════════════════════════════════════════════════════════

def backtest_stock(candle_data, daily_daily_daily_mas_data_data, stock_name):
    """Run MA Bounce v0.9 with all filter/target combinations"""
    if daily_daily_daily_mas_data_data is not None:
        candle_data['date'] = candle_data['datetime'].dt.date
        candle_data = candle_data.merge(daily_daily_daily_mas_data_data, on='date', how='left')
    else:
        candle_data['ma50'] = candle_data['ma100'] = candle_data['ma200'] = np.nan
    results = {}

    for filter_name, filter_daily_daily_mas_data_data in FILTERS.items():
        for target in TARGETS:
            # Detect bounces with this filter
            signals = detect_bounce(candle_data, filter_daily_daily_mas_data_data)

            if len(signals) == 0:
                results[(filter_name, target)] = {
                    'trades': 0,
                    'win_rate': 0,
                    'net_profit': 0
                }
                continue

            # Simulate trades
            trades = simulate_trades(candle_data, signals, target)

            # Calculate metrics
            wins = sum(1 for t in trades if t['pnl'] > 0)
            total_trades = len(trades)
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            net_profit = sum(t['pnl'] for t in trades)

            results[(filter_name, target)] = {
                'trades': total_trades,
                'win_rate': win_rate,
                'net_profit': net_profit
            }

    # Find best combination
    best_combo = max(results.items(), key=lambda x: x[1]['net_profit'])
    best_filter, best_target = best_combo[0]
    best_result = best_combo[1]

    # Determine price vs daily_daily_mas_data_data category
    price_vs_daily_daily_mas_data_data = categorize_price_vs_daily_daily_mas_data_data(candle_data)

    # Calculate capital-based efficiency (CORRECTED v1.1)
    # Get the best combo's trades
    best_signals = detect_bounce(candle_data, FILTERS[best_filter])
    best_trades = simulate_trades(candle_data, best_signals, best_target / 100)
    
    # Total capital deployed = sum of all entry prices
    total_capital = sum(t['entry_price'] for t in best_trades)
    
    # Efficiency = net profit as % of capital deployed
    capital_efficiency = (best_result['net_profit'] / total_capital * 100) if total_capital > 0 else 0
    
    # Keep avg_price for reference
    avg_price = candle_data['close'].mean()

    return {
        'stock': stock_name,
        'best_filter': best_filter,
        'best_target': best_target * 100,  # Convert to percentage
        'trades': best_result['trades'],
        'win_rate': best_result['win_rate'],
        'net_profit': best_result['net_profit'],
        'capital_efficiency': capital_efficiency,  # CORRECTED: capital-based
        'price_vs_daily_daily_mas_data_data': price_vs_daily_daily_mas_data_data,
        'avg_price': avg_price  # For reference only
    }


def categorize_price_vs_daily_daily_mas_data_data(candle_data):
    """Categorize stock based on price position vs daily_daily_mas_data_data"""
    # Use last valid row with all daily_daily_mas_data_data
    valid_rows = candle_data.dropna(subset=['ma50', 'ma100', 'ma200'])

    if len(valid_rows) == 0:
        return "INSUFFICIENT DATA"

    last_row = valid_rows.iloc[-1]
    price = last_row['close']

    if price > last_row['ma50'] and price > last_row['ma100'] and price > last_row['ma200']:
        return "STRONG UPTREND (Above all daily_daily_mas_data_data)"
    elif price < last_row['ma50'] and price < last_row['ma100'] and price < last_row['ma200']:
        return "STRONG DOWNTREND (Below all daily_daily_mas_data_data)"
    elif price > last_row['ma50']:
        return "UPTREND (Above MA50)"
    elif price > last_row['ma200']:
        return "SIDEWAYS (Between daily_daily_mas_data_data)"
    else:
        return "DOWNTREND (Below MA200)"

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + " "*22 + "48-MONTH MEGA BACKTEST (30 STOCKS)" + " "*22 + "║")
    print("╚" + "═"*78 + "╝\n")
    
    # Generate months - TEST MODE: Just 1 month
    months = [(datetime(2022, 1, 1), datetime(2022, 1, 31), "JAN_2022")]
    
    print(f"Months: {len(months)} | Stocks: {len(STOCKS)} | Total: {len(months)*len(STOCKS)}\n")
    
    all_top10 = []
    start_time = datetime.now()
    
    for month_idx, (from_date, to_date, month_name) in enumerate(months, 1):
        print(f"[{month_idx:2}/48] {month_name:<12}", end=" ", flush=True)
        
        month_results = []
        for stock, key in STOCKS.items():
            candle_data = fetch_upstox_data(key, from_date, to_date)
            daily_daily_mas_data_data = fetch_daily_daily_daily_mas_data_data(key, to_date)
            result = backtest_stock(candle_data, daily_daily_mas_data_data, stock)
            if result:
                month_results.append(result)
        
        month_results.sort(key=lambda x: x['capital_efficiency'], reverse=True)

        print("\n  🏆 TOP 10:")
        print(f"  {'Rank':<6} {'Stock':<15} {'Eff%':<8} {'Filter':<18} {'Target':<8}")
        print("  " + "-" * 65)
        for rank, r in enumerate(month_results[:10], 1):
            print(f"  {rank:<6} {r['stock']:<15} {r['capital_efficiency']:<8.1f} {r['best_filter']:<18} {r['best_target']:.1f}%")

        # Track top 10
        for r in month_results[:10]:
            all_top10.append(r['stock'])
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Final report
    print("\n" + "="*80)
    print("CONSISTENCY REPORT (48 MONTHS)")
    print("="*80)
    
    freq = Counter(all_top10)
    sorted_stocks = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n{'Rank':<6} {'Stock':<15} {'Top 10 Count':<15} {'Consistency %':<15}")
    print("-"*80)
    for rank, (stock, count) in enumerate(sorted_stocks[:15], 1):
        consistency = (count / 48) * 100
        print(f"{rank:<6} {stock:<15} {count}/48{' '*10} {consistency:<15.1f}%")
    
    print(f"\n⏱️  Execution time: {elapsed/60:.1f} minutes")
    print("="*80)

if __name__ == "__main__":
    main()
