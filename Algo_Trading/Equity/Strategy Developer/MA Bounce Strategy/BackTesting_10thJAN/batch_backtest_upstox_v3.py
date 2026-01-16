"""
╔═══════════════════════════════════════════════════════════════╗
║   BATCH BACKTEST - MA BOUNCE v0.9 (UPSTOX V3 API)            ║
║   30 Stocks × Random Months (Jan 2022 - Dec 2025)            ║
╚═══════════════════════════════════════════════════════════════╝

PURPOSE:
--------
Test MA Bounce strategy on 30 F&O stocks across random months from 4-year window.
Uses Upstox V3 API for reliable 5-minute historical data.

WORKFLOW:
---------
1. Ask user: How many random months to test?
2. Create timestamped results folder
3. For each iteration:
   - Pick random month from Jan 2022 - Dec 2025
   - Fetch 5-min data for all 30 stocks + NIFTY
   - Run MA Bounce v0.9 on each stock
   - Export results to Excel in the folder
4. Display summary of all iterations

OUTPUT:
-------
Backtest_Run_YYYYMMDD_HHMMSS/
  ├─ JAN_2022_results.xlsx
  ├─ MAR_2023_results.xlsx
  ├─ ...
  └─ Summary_AllIterations.xlsx (combined results)

USAGE:
------
python batch_backtest_upstox_v3.py
"""

import upstox_client
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import warnings
warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Your Upstox access token (update daily)
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTYxZGQ0ZDg0NTY1ODAzNGQ1N2ZiOTYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2ODAyMTMyNSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY4MDgyNDAwfQ.76dHYGD8FxoYMsd5MmAllBSo0tmWl4jBJZV5tTz_YCI"

# 30 F&O stocks with Upstox instrument keys
STOCKS = {
    # Metals
    'TATASTEEL': 'NSE_EQ|INE081A01020',
    'HINDALCO': 'NSE_EQ|INE038A01020',
    'JSWSTEEL': 'NSE_EQ|INE019A01038',
    'NATIONALUM': 'NSE_EQ|INE139A01034',
    
    # Banking
    'SBIN': 'NSE_EQ|INE062A01020',
    'HDFCBANK': 'NSE_EQ|INE040A01034',
    'ICICIBANK': 'NSE_EQ|INE090A01021',
    'AXISBANK': 'NSE_EQ|INE238A01034',
    'PNB': 'NSE_EQ|INE160A01022',
    'INDUSINDBK': 'NSE_EQ|INE095A01012',
    
    # IT
    'INFY': 'NSE_EQ|INE009A01021',
    'WIPRO': 'NSE_EQ|INE075A01022',
    'TECHM': 'NSE_EQ|INE669C01036',
    
    # Auto
    'TATAMOTORS': 'NSE_EQ|INE155A01022',
    'ASHOKLEY': 'NSE_EQ|INE208A01029',
    
    # Pharma
    'SUNPHARMA': 'NSE_EQ|INE044A01036',
    'DIVISLAB': 'NSE_EQ|INE361B01024',  # ✅ Replaced DRREDDY (invalid key) with DIVISLAB
    'CIPLA': 'NSE_EQ|INE059A01026',
    
    # Energy
    'RELIANCE': 'NSE_EQ|INE002A01018',
    'ONGC': 'NSE_EQ|INE213A01029',
    'COALINDIA': 'NSE_EQ|INE522F01014',
    
    # FMCG
    'ITC': 'NSE_EQ|INE154A01025',
    'DABUR': 'NSE_EQ|INE016A01026',
    
    # Telecom
    'BHARTIARTL': 'NSE_EQ|INE397D01024',
    'IDEA': 'NSE_EQ|INE669E01016',
    
    # Power
    'NTPC': 'NSE_EQ|INE733E01010',
    'POWERGRID': 'NSE_EQ|INE752E01010',
    
    # Others
    'ADANIPORTS': 'NSE_EQ|INE742F01042',
    'VEDL': 'NSE_EQ|INE205A01025',
    'BANDHANBNK': 'NSE_EQ|INE545U01014'
}

# NIFTY 50 for market context
NIFTY_KEY = 'NSE_INDEX|Nifty 50'

# Strategy parameters (MA Bounce v0.9)
TARGETS = [0.005, 0.01, 0.015]  # 0.5%, 1%, 1.5%
STOP_LOSS = 0.005  # 0.5%
VOLUME_MULTIPLIER = 1.2

# Filter configurations
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

# Date range for random month selection
START_DATE = datetime(2022, 1, 1)  # Jan 2022
END_DATE = datetime(2025, 12, 31)  # Dec 2025

# Configure Upstox API
configuration = upstox_client.Configuration()
configuration.access_token = ACCESS_TOKEN

# ═══════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def create_results_folder():
    """Create timestamped folder for this batch test run"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"Backtest_Run_{timestamp}"
    os.makedirs(folder_name, exist_ok=True)
    print(f"\n📁 Results folder created: {folder_name}")
    return folder_name

def pick_random_month():
    """Pick a random month between Jan 2022 - Dec 2025"""
    months_list = []
    current = START_DATE
    
    while current <= END_DATE:
        months_list.append((current.year, current.month))
        # Move to next month
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
    
    year, month = random.choice(months_list)
    
    # Get first and last day of selected month
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    month_name = f"{first_day.strftime('%b').upper()}_{year}"
    
    return first_day, last_day, month_name

def fetch_upstox_data(instrument_key, from_date, to_date, name="Stock"):
    """Fetch 5-minute historical data from Upstox V3 API"""
    try:
        api_instance = upstox_client.HistoryV3Api(upstox_client.ApiClient(configuration))
        
        # Convert dates to string format
        from_str = from_date.strftime('%Y-%m-%d')
        to_str = to_date.strftime('%Y-%m-%d')
        
        # Fetch 5-minute data
        api_response = api_instance.get_historical_candle_data1(
            instrument_key=instrument_key,
            unit="minutes",
            interval="5",
            to_date=to_str,
            from_date=from_str
        )
        
        if not hasattr(api_response, 'data') or not api_response.data or not hasattr(api_response.data, 'candles'):
            return None
        
        candles = api_response.data.candles
        
        if len(candles) == 0:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
        
        # Calculate MA20 on 5-min chart
        df['ma20'] = df['close'].rolling(20).mean()
        
        # Calculate average volume for volume confirmation
        df['avg_volume'] = df['volume'].rolling(20).mean()
        
        return df
        
    except Exception as e:
        print(f"      ✗ Error fetching {name}: {str(e)[:100]}")
        return None

def fetch_daily_mas(instrument_key, end_date, name="Stock"):
    """Fetch daily data for MA50, MA100, MA200 calculation"""
    try:
        api_instance = upstox_client.HistoryV3Api(upstox_client.ApiClient(configuration))
        
        # Need 1 year of history for MA200
        start_date = end_date - timedelta(days=400)  # Extra buffer
        from_str = start_date.strftime('%Y-%m-%d')
        to_str = end_date.strftime('%Y-%m-%d')
        
        # Fetch daily data
        api_response = api_instance.get_historical_candle_data1(
            instrument_key=instrument_key,
            unit="days",
            interval="1",
            to_date=to_str,
            from_date=from_str
        )
        
        if not hasattr(api_response, 'data') or not api_response.data:
            return None
        
        candles = api_response.data.candles
        df_daily = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df_daily['datetime'] = pd.to_datetime(df_daily['datetime'])
        df_daily = df_daily.sort_values('datetime').reset_index(drop=True)
        
        # Calculate MAs
        df_daily['ma50'] = df_daily['close'].rolling(50).mean()
        df_daily['ma100'] = df_daily['close'].rolling(100).mean()
        df_daily['ma200'] = df_daily['close'].rolling(200).mean()
        
        # Keep only date and MAs
        df_daily['date'] = df_daily['datetime'].dt.date
        
        return df_daily[['date', 'ma50', 'ma100', 'ma200']]
        
    except Exception as e:
        print(f"      ✗ Error fetching daily MAs for {name}: {str(e)[:100]}")
        return None

def merge_daily_mas(df_5min, df_daily_mas):
    """Merge daily MAs into 5-minute dataframe"""
    if df_daily_mas is None or df_5min is None:
        return df_5min
    
    df_5min['date'] = df_5min['datetime'].dt.date
    df_merged = df_5min.merge(df_daily_mas, on='date', how='left', suffixes=('', '_daily'))
    
    # Rename daily MAs
    if 'ma50_daily' in df_merged.columns:
        df_merged = df_merged.rename(columns={'ma50_daily': 'ma50', 'ma100_daily': 'ma100', 'ma200_daily': 'ma200'})
    
    return df_merged

# ═══════════════════════════════════════════════════════════════
# MA BOUNCE v0.9 LOGIC
# ═══════════════════════════════════════════════════════════════

def check_ma_filter(row, required_mas):
    """Check if price is above required MAs"""
    if not required_mas:  # No filter
        return True
    
    for ma in required_mas:
        if pd.isna(row[ma]) or row['close'] < row[ma]:
            return False
    return True

def detect_bounce(df, filter_mas):
    """Detect MA20 bounce signals with filters"""
    signals = []
    
    for i in range(20, len(df)):
        row = df.iloc[i]
        
        # Skip if MA20 not available
        if pd.isna(row['ma20']):
            continue
        
        # Check MA filter first
        if not check_ma_filter(row, filter_mas):
            continue
        
        # Volume confirmation
        if pd.notna(row['avg_volume']) and row['volume'] < row['avg_volume'] * VOLUME_MULTIPLIER:
            continue
        
        # Bounce detection: Close within 0.5% of MA20
        distance = abs(row['close'] - row['ma20']) / row['ma20']
        
        if distance <= 0.005:  # Within 0.5%
            # Confirm bounce: current candle closes above MA20
            if row['close'] >= row['ma20']:
                signals.append({
                    'datetime': row['datetime'],
                    'entry_price': row['close'],
                    'ma20': row['ma20'],
                    'volume': row['volume'],
                    'avg_volume': row['avg_volume']
                })
    
    return signals

def simulate_trades(df, signals, target_pct):
    """Simulate trades with target and stop loss"""
    trades = []
    
    for signal in signals:
        entry_price = signal['entry_price']
        entry_time = signal['datetime']
        entry_idx = df[df['datetime'] == entry_time].index[0]
        
        target_price = entry_price * (1 + target_pct)
        stop_price = entry_price * (1 - STOP_LOSS)
        
        # Scan next candles for exit
        exit_price = None
        exit_time = None
        exit_reason = None
        
        for j in range(entry_idx + 1, min(entry_idx + 80, len(df))):  # Max 80 candles (6.5 hours)
            candle = df.iloc[j]
            
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
            last_candle = df.iloc[min(entry_idx + 79, len(df) - 1)]
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

def run_ma_bounce(df, stock_name):
    """Run MA Bounce v0.9 with all filter/target combinations"""
    
    results = {}
    
    for filter_name, filter_mas in FILTERS.items():
        for target in TARGETS:
            # Detect bounces with this filter
            signals = detect_bounce(df, filter_mas)
            
            if len(signals) == 0:
                results[(filter_name, target)] = {
                    'trades': 0,
                    'win_rate': 0,
                    'net_profit': 0
                }
                continue
            
            # Simulate trades
            trades = simulate_trades(df, signals, target)
            
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
    
    # Determine price vs MAs category
    price_vs_mas = categorize_price_vs_mas(df)
    
    return {
        'stock': stock_name,
        'best_filter': best_filter,
        'best_target': best_target * 100,  # Convert to percentage
        'trades': best_result['trades'],
        'win_rate': best_result['win_rate'],
        'net_profit': best_result['net_profit'],
        'price_vs_mas': price_vs_mas,
        'avg_price': df['close'].mean()
    }

def categorize_price_vs_mas(df):
    """Categorize stock based on price position vs MAs"""
    # Use last valid row with all MAs
    valid_rows = df.dropna(subset=['ma50', 'ma100', 'ma200'])
    
    if len(valid_rows) == 0:
        return "INSUFFICIENT DATA"
    
    last_row = valid_rows.iloc[-1]
    price = last_row['close']
    
    if price > last_row['ma50'] and price > last_row['ma100'] and price > last_row['ma200']:
        return "STRONG UPTREND (Above all MAs)"
    elif price < last_row['ma50'] and price < last_row['ma100'] and price < last_row['ma200']:
        return "STRONG DOWNTREND (Below all MAs)"
    elif price > last_row['ma50']:
        return "UPTREND (Above MA50)"
    elif price > last_row['ma200']:
        return "SIDEWAYS (Between MAs)"
    else:
        return "DOWNTREND (Below MA200)"

# ═══════════════════════════════════════════════════════════════
# NIFTY CONTEXT
# ═══════════════════════════════════════════════════════════════

def fetch_nifty_context(from_date, to_date):
    """Fetch NIFTY 50 daily data for market context"""
    print("\n" + "="*90)
    print("FETCHING NIFTY 50 CONTEXT")
    print("="*90)
    
    try:
        # Fetch daily NIFTY data
        df_nifty = fetch_upstox_data(NIFTY_KEY, from_date - timedelta(days=300), to_date, "NIFTY")
        
        if df_nifty is None or len(df_nifty) == 0:
            return None
        
        # Get daily candles (sample 1 per day)
        df_nifty['date'] = df_nifty['datetime'].dt.date
        df_daily = df_nifty.groupby('date').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }).reset_index()
        
        # Calculate MAs
        df_daily['ma50'] = df_daily['close'].rolling(50).mean()
        df_daily['ma200'] = df_daily['close'].rolling(200).mean()
        
        # Get month data
        month_data = df_daily[(df_daily['date'] >= from_date.date()) & (df_daily['date'] <= to_date.date())]
        
        if len(month_data) == 0:
            return None
        
        start_price = month_data['close'].iloc[0]
        end_price = month_data['close'].iloc[-1]
        pct_change = ((end_price - start_price) / start_price) * 100
        
        # Determine regime
        last_row = df_daily.iloc[-1]
        if pd.notna(last_row['ma50']) and pd.notna(last_row['ma200']):
            if last_row['close'] > last_row['ma50'] and last_row['close'] > last_row['ma200']:
                regime = "UPTREND (Above MA50 & MA200)"
            elif last_row['close'] < last_row['ma50'] and last_row['close'] < last_row['ma200']:
                regime = "DOWNTREND (Below MA50 & MA200)"
            else:
                regime = "SIDEWAYS (Between MAs)"
        else:
            regime = "INSUFFICIENT DATA"
        
        context = {
            'start_price': start_price,
            'end_price': end_price,
            'pct_change': pct_change,
            'regime': regime,
            'high': month_data['high'].max(),
            'low': month_data['low'].min()
        }
        
        print(f"✓ NIFTY 50: {start_price:.2f} → {end_price:.2f} ({pct_change:+.2f}%)")
        print(f"✓ Market Regime: {regime}")
        
        return context
        
    except Exception as e:
        print(f"✗ Error fetching NIFTY: {str(e)[:100]}")
        return None

# ═══════════════════════════════════════════════════════════════
# EXCEL EXPORT
# ═══════════════════════════════════════════════════════════════

def export_to_excel(all_results, nifty_context, month_name, folder):
    """Export results to Excel with 4 sheets"""
    
    filename = os.path.join(folder, f"{month_name}_results.xlsx")
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        
        # Sheet 1: SUMMARY
        summary_data = []
        for result in all_results:
            summary_data.append({
                'Stock': result['stock'],
                'Best Filter': result['best_filter'],
                'Best Target': f"{result['best_target']:.1f}%",
                'Net Profit (₹)': round(result['net_profit'], 2),
                'Win Rate (%)': round(result['win_rate'], 1),
                'Trades': result['trades'],
                'Price vs MAs': result['price_vs_mas'],
                'Avg Price (₹)': round(result['avg_price'], 2)
            })
        
        df_summary = pd.DataFrame(summary_data)
        df_summary = df_summary.sort_values('Net Profit (₹)', ascending=False).reset_index(drop=True)
        
        # Add market context
        context_rows = []
        if nifty_context:
            context_rows.append(['MARKET CONTEXT', '', '', '', '', '', '', ''])
            context_rows.append(['NIFTY 50 Start', round(nifty_context['start_price'], 2), '', '', '', '', '', ''])
            context_rows.append(['NIFTY 50 End', round(nifty_context['end_price'], 2), '', '', '', '', '', ''])
            context_rows.append(['% Change', f"{nifty_context['pct_change']:+.2f}%", '', '', '', '', '', ''])
            context_rows.append(['Market Regime', nifty_context['regime'], '', '', '', '', '', ''])
            context_rows.append(['', '', '', '', '', '', '', ''])
            context_rows.append(['STOCK RESULTS', '', '', '', '', '', '', ''])
        
        df_context = pd.DataFrame(context_rows, columns=df_summary.columns)
        df_final = pd.concat([df_context, df_summary], ignore_index=True)
        df_final.to_excel(writer, sheet_name='Summary', index=False)
        
        # Sheet 2: WINNERS (>55% WR)
        winners = [r for r in all_results if r['win_rate'] > 55]
        df_winners = pd.DataFrame([{
            'Stock': r['stock'],
            'Best Filter': r['best_filter'],
            'Best Target': f"{r['best_target']:.1f}%",
            'Net Profit (₹)': round(r['net_profit'], 2),
            'Win Rate (%)': round(r['win_rate'], 1),
            'Trades': r['trades'],
            'Price vs MAs': r['price_vs_mas']
        } for r in winners])
        
        if not df_winners.empty:
            df_winners = df_winners.sort_values('Net Profit (₹)', ascending=False)
        
        df_winners.to_excel(writer, sheet_name='Winners', index=False)
        
        # Sheet 3: LOSERS (<55% WR)
        losers = [r for r in all_results if r['win_rate'] <= 55]
        df_losers = pd.DataFrame([{
            'Stock': r['stock'],
            'Best Filter': r['best_filter'],
            'Best Target': f"{r['best_target']:.1f}%",
            'Net Profit (₹)': round(r['net_profit'], 2),
            'Win Rate (%)': round(r['win_rate'], 1),
            'Trades': r['trades'],
            'Price vs MAs': r['price_vs_mas']
        } for r in losers])
        
        if not df_losers.empty:
            df_losers = df_losers.sort_values('Net Profit (₹)', ascending=True)
        
        df_losers.to_excel(writer, sheet_name='Losers', index=False)
        
        # Sheet 4: PATTERN ANALYSIS
        pattern_data = {}
        for result in all_results:
            category = result['price_vs_mas']
            if category not in pattern_data:
                pattern_data[category] = []
            pattern_data[category].append(result)
        
        pattern_rows = []
        for category, stocks in pattern_data.items():
            pattern_rows.append(['', '', '', '', '', ''])
            pattern_rows.append([f"CATEGORY: {category}", '', '', '', '', ''])
            pattern_rows.append(['Stock', 'Best Filter', 'Net Profit (₹)', 'Win Rate (%)', 'Trades', 'Avg Price (₹)'])
            
            for stock in sorted(stocks, key=lambda x: x['net_profit'], reverse=True):
                pattern_rows.append([
                    stock['stock'],
                    stock['best_filter'],
                    round(stock['net_profit'], 2),
                    round(stock['win_rate'], 1),
                    stock['trades'],
                    round(stock['avg_price'], 2)
                ])
        
        df_patterns = pd.DataFrame(pattern_rows)
        df_patterns.to_excel(writer, sheet_name='Pattern Analysis', index=False, header=False)
    
    print(f"   ✓ Results exported: {month_name}_results.xlsx")
    return filename

# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║   BATCH BACKTEST - MA BOUNCE v0.9 (UPSTOX V3 API)            ║")
    print("║   30 Stocks × Random Months (Jan 2022 - Dec 2025)            ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    # Ask user for number of iterations
    while True:
        try:
            num_iterations = int(input("\nHow many random months to test? (1-48): "))
            if 1 <= num_iterations <= 48:
                break
            else:
                print("Please enter a number between 1 and 48.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    # Create results folder
    results_folder = create_results_folder()
    
    # Store all iteration results for summary
    all_iteration_results = []
    
    # Run iterations
    for iteration in range(1, num_iterations + 1):
        print("\n" + "="*90)
        print(f"ITERATION {iteration}/{num_iterations}")
        print("="*90)
        
        # Pick random month
        start_date, end_date, month_name = pick_random_month()
        print(f"\n🎲 RANDOMLY SELECTED: {month_name}")
        print(f"   Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Fetch NIFTY context
        nifty_context = fetch_nifty_context(start_date, end_date)
        
        # Process all 30 stocks
        print("\n" + "="*90)
        print(f"PROCESSING 30 STOCKS FOR {month_name}")
        print("="*90)
        
        all_results = []
        success_count = 0
        
        for idx, (stock_name, instrument_key) in enumerate(STOCKS.items(), 1):
            print(f"\n[{idx}/30] {stock_name}...", end=' ')
            
            # Fetch 5-min data
            df_5min = fetch_upstox_data(instrument_key, start_date, end_date, stock_name)
            
            if df_5min is None or len(df_5min) < 100:
                print("✗ SKIP (insufficient data)")
                continue
            
            # Fetch daily MAs
            df_daily_mas = fetch_daily_mas(instrument_key, end_date, stock_name)
            
            # Merge MAs into 5-min data
            df = merge_daily_mas(df_5min, df_daily_mas)
            
            # Run MA Bounce backtest
            result = run_ma_bounce(df, stock_name)
            all_results.append(result)
            success_count += 1
            
            print(f"✓ {result['best_filter']} @ {result['best_target']:.1f}% → ₹{result['net_profit']:.2f} ({result['win_rate']:.1f}% WR, {result['trades']} trades)")
        
        # Export to Excel
        print("\n" + "="*90)
        print(f"ITERATION {iteration} COMPLETE - {success_count}/30 stocks processed")
        print("="*90)
        
        if all_results:
            export_to_excel(all_results, nifty_context, month_name, results_folder)
            
            # Store for summary
            all_iteration_results.append({
                'iteration': iteration,
                'month': month_name,
                'results': all_results,
                'nifty': nifty_context
            })
            
            # Quick summary
            winners = [r for r in all_results if r['win_rate'] > 55]
            print(f"\n   🏆 Winners (>55% WR): {len(winners)}")
            
            if winners:
                top_3 = sorted(winners, key=lambda x: x['net_profit'], reverse=True)[:3]
                for i, stock in enumerate(top_3, 1):
                    print(f"      {i}. {stock['stock']}: ₹{stock['net_profit']:.2f} @ {stock['win_rate']:.1f}% WR")
        else:
            print("\n   ✗ No results - all stocks failed")
    
    # Final summary
    print("\n" + "="*90)
    print("ALL ITERATIONS COMPLETE!")
    print("="*90)
    print(f"\n📁 All results saved in: {results_folder}")
    print(f"📊 Total iterations: {num_iterations}")
    print(f"📈 Total stock-months tested: {sum(len(ir['results']) for ir in all_iteration_results)}")
    
    # Aggregate stats
    all_stocks_data = []
    for ir in all_iteration_results:
        all_stocks_data.extend(ir['results'])
    
    if all_stocks_data:
        # Top performers across all iterations
        stock_performance = {}
        for result in all_stocks_data:
            stock = result['stock']
            if stock not in stock_performance:
                stock_performance[stock] = {'wins': 0, 'total': 0, 'total_profit': 0}
            
            stock_performance[stock]['total'] += 1
            if result['win_rate'] > 55:
                stock_performance[stock]['wins'] += 1
            stock_performance[stock]['total_profit'] += result['net_profit']
        
        # Calculate consistency score
        for stock, data in stock_performance.items():
            data['consistency'] = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            data['avg_profit'] = data['total_profit'] / data['total']
        
        # Top 10 by consistency
        top_consistent = sorted(stock_performance.items(), key=lambda x: x[1]['consistency'], reverse=True)[:10]
        
        print("\n" + "="*90)
        print("TOP 10 CONSISTENT PERFORMERS (by % of winning months)")
        print("="*90)
        for i, (stock, data) in enumerate(top_consistent, 1):
            print(f"{i:2d}. {stock:15s} → {data['consistency']:5.1f}% consistency ({data['wins']}/{data['total']} months won) | Avg: ₹{data['avg_profit']:8.2f}")
        
        print("\n" + "="*90)
        print("✅ BACKTEST COMPLETE! Review Excel files for detailed analysis.")
        print("="*90)

if __name__ == '__main__':
    main()
