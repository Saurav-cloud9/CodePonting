"""
╔═══════════════════════════════════════════════════════════════╗
║   BATCH BACKTEST - MA BOUNCE v0.9 (30 STOCKS, RANDOM MONTH)  ║
╚═══════════════════════════════════════════════════════════════╝

PURPOSE:
--------
Test MA Bounce strategy on 30 stocks for ONE random month (Jan 2023 - Dec 2025)
Find consistent winners across different market conditions

WORKFLOW:
---------
1. Pick random month from 36-month pool (Jan 2023 - Dec 2025)
2. Download NIFTY data for market context (regime, VIX, % change)
3. Download 5-min OHLC + daily MAs for all 30 stocks (that month)
4. Run MA Bounce v0.9 on each stock
5. Export results to Excel (4 sheets):
   - Sheet 1: Summary (all stocks, best filter/target)
   - Sheet 2: Winners (>55% WR or >₹20 profit)
   - Sheet 3: Losers (<45% WR or negative profit)
   - Sheet 4: Pattern Analysis (grouped by price vs MAs)

OUTPUT:
-------
backtest_MMM_YYYY.xlsx (e.g., backtest_JUN_2023.xlsx)

USAGE:
------
python batch_backtest_30stocks.py

Run 10 times = 10 random months = 300 stock-month backtests!
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import random
import warnings
warnings.filterwarnings('ignore')

# ═════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════

# 30 stocks to test
STOCKS = [
    'TATASTEEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS', 'NATIONALUM.NS',  # Metals
    'SBIN.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'PNB.NS', 'INDUSINDBK.NS',  # Banking
    'INFY.NS', 'WIPRO.NS', 'TECHM.NS',  # IT
    'TATAMOTORS.NS', 'ASHOKLEY.NS',  # Auto
    'SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS',  # Pharma
    'RELIANCE.NS', 'ONGC.NS', 'COALINDIA.NS',  # Energy
    'ITC.NS', 'DABUR.NS',  # FMCG
    'BHARTIARTL.NS', 'IDEA.NS',  # Telecom
    'NTPC.NS', 'POWERGRID.NS',  # Power
    'ADANIPORTS.NS', 'VEDL.NS', 'BANDHANBNK.NS'  # Others
]

# Strategy parameters (from v0.9)
TARGETS = [0.005, 0.01, 0.015]  # 0.5%, 1%, 1.5%
STOP_LOSS = 0.005  # 0.5%
VOLUME_MULTIPLIER = 1.2

# Filter names
FILTER_NAMES = [
    'No Filter', 'MA50', 'MA100', 'MA200',
    'MA50+100', 'MA50+200', 'MA100+200', 'MA50+100+200'
]

# Date range for random month selection
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)

# ═════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═════════════════════════════════════════════════════════════

def pick_random_month():
    """Pick a random month between Jan 2023 - Dec 2025"""
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
    
    return first_day, last_day, f"{first_day.strftime('%b').upper()}_{year}"

def download_nifty_context(start_date, end_date):
    """Download NIFTY 50 data for market context"""
    print("\n" + "="*90)
    print("DOWNLOADING NIFTY 50 CONTEXT")
    print("="*90)
    
    try:
        # Download NIFTY data
        nifty = yf.download('^NSEI', start=start_date, end=end_date + timedelta(days=1), 
                           progress=False, interval='1d')
        
        if nifty.empty:
            return None
        
        # Calculate metrics
        start_price = nifty['Close'].iloc[0]
        end_price = nifty['Close'].iloc[-1]
        pct_change = ((end_price - start_price) / start_price) * 100
        
        # Calculate MA50 and MA200 for regime detection
        nifty['MA50'] = nifty['Close'].rolling(50).mean()
        nifty['MA200'] = nifty['Close'].rolling(200).mean()
        
        # Determine market regime
        last_close = nifty['Close'].iloc[-1]
        last_ma50 = nifty['MA50'].iloc[-1]
        last_ma200 = nifty['MA200'].iloc[-1]
        
        if pd.notna(last_ma50) and pd.notna(last_ma200):
            if last_close > last_ma50 and last_close > last_ma200:
                regime = "UPTREND (Above MA50 & MA200)"
            elif last_close < last_ma50 and last_close < last_ma200:
                regime = "DOWNTREND (Below MA50 & MA200)"
            else:
                regime = "SIDEWAYS (Between MAs)"
        else:
            regime = "INSUFFICIENT DATA"
        
        # Approximate VIX (use ATR as proxy since VIX not available)
        nifty['ATR'] = nifty['High'] - nifty['Low']
        avg_volatility = nifty['ATR'].mean()
        
        context = {
            'start_price': start_price,
            'end_price': end_price,
            'pct_change': pct_change,
            'regime': regime,
            'avg_volatility': avg_volatility,
            'high': nifty['High'].max(),
            'low': nifty['Low'].min()
        }
        
        print(f"✓ NIFTY 50: {start_price:.2f} → {end_price:.2f} ({pct_change:+.2f}%)")
        print(f"✓ Market Regime: {regime}")
        print(f"✓ High: {context['high']:.2f}, Low: {context['low']:.2f}")
        
        return context
        
    except Exception as e:
        print(f"✗ Error downloading NIFTY: {e}")
        return None

def download_stock_data(ticker, start_date, end_date):
    """Download 5-min intraday + daily MAs for a stock"""
    try:
        # Download 5-min intraday data
        df_5min = yf.download(ticker, start=start_date, end=end_date + timedelta(days=1),
                             interval='5m', progress=False)
        
        if df_5min.empty:
            return None
        
        # Download daily data for MAs (need more history)
        daily_start = start_date - timedelta(days=365)  # 1 year history for MA200
        df_daily = yf.download(ticker, start=daily_start, end=end_date + timedelta(days=1),
                              interval='1d', progress=False)
        
        if df_daily.empty:
            return None
        
        # Calculate daily MAs
        df_daily['MA50'] = df_daily['Close'].rolling(50).mean()
        df_daily['MA100'] = df_daily['Close'].rolling(100).mean()
        df_daily['MA200'] = df_daily['Close'].rolling(200).mean()
        
        # Prepare 5-min dataframe
        df_5min = df_5min.reset_index()
        df_5min.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        df_5min['date'] = df_5min['datetime'].dt.date
        
        # Calculate MA20 on 5-min chart
        df_5min['ma20'] = df_5min['close'].rolling(20).mean()
        
        # Merge daily MAs
        daily_mas = df_daily[['MA50', 'MA100', 'MA200']].copy()
        daily_mas['date'] = daily_mas.index.date
        
        df_5min = df_5min.merge(daily_mas, on='date', how='left')
        df_5min = df_5min.rename(columns={'MA50': 'ma50', 'MA100': 'ma100', 'MA200': 'ma200'})
        
        # Calculate avg volume
        df_5min['avg_volume'] = df_5min['volume'].rolling(20).mean()
        
        # Skip first day for clean MA20
        first_date = df_5min['date'].min()
        df_5min = df_5min[df_5min['date'] > first_date].reset_index(drop=True)
        
        return df_5min
        
    except Exception as e:
        print(f"✗ Error downloading {ticker}: {e}")
        return None

def check_filter(close, ma50, ma100, ma200):
    """Check which filters pass for given price and MAs"""
    filters = {
        'No Filter': True,
        'MA50': close > ma50 if pd.notna(ma50) else False,
        'MA100': close > ma100 if pd.notna(ma100) else False,
        'MA200': close > ma200 if pd.notna(ma200) else False,
        'MA50+100': (close > ma50 and close > ma100) if (pd.notna(ma50) and pd.notna(ma100)) else False,
        'MA50+200': (close > ma50 and close > ma200) if (pd.notna(ma50) and pd.notna(ma200)) else False,
        'MA100+200': (close > ma100 and close > ma200) if (pd.notna(ma100) and pd.notna(ma200)) else False,
        'MA50+100+200': (close > ma50 and close > ma100 and close > ma200) if (pd.notna(ma50) and pd.notna(ma100) and pd.notna(ma200)) else False
    }
    return filters

def run_ma_bounce(df, stock_name):
    """Run MA Bounce v0.9 backtest on a stock (reuses v0.9 logic)"""
    
    # Initialize results structure
    results = {filter_name: {target: {'trades': 0, 'wins': 0, 'losses': 0, 'net': 0.0} 
               for target in TARGETS} for filter_name in FILTER_NAMES}
    
    filter_stats = {filter_name: {'uptrend': 0, 'volume_confirmed': 0, 'bounces': 0} 
                   for filter_name in FILTER_NAMES}
    
    # Main backtest loop
    for i in range(len(df)):
        close = df.iloc[i]['close']
        low = df.iloc[i]['low']
        ma20 = df.iloc[i]['ma20']
        ma50 = df.iloc[i]['ma50']
        ma100 = df.iloc[i]['ma100']
        ma200 = df.iloc[i]['ma200']
        volume = df.iloc[i]['volume']
        avg_volume = df.iloc[i]['avg_volume']
        
        # Skip if MA20 not available
        if pd.isna(ma20):
            continue
        
        # STEP 2: Check which filters pass (BEFORE looking for dip)
        filters_passed = check_filter(close, ma50, ma100, ma200)
        
        # Count uptrend for each filter
        for filter_name, passed in filters_passed.items():
            if passed:
                filter_stats[filter_name]['uptrend'] += 1
        
        # If no filters passed, skip this candle
        if not any(filters_passed.values()):
            continue
        
        # STEP 3: Check for MA20 touch
        if low > ma20:
            continue  # No touch
        
        # Volume confirmation
        if pd.isna(avg_volume) or volume <= avg_volume * VOLUME_MULTIPLIER:
            continue  # Weak volume
        
        # Count volume_confirmed for filters that passed uptrend
        for filter_name, passed in filters_passed.items():
            if passed:
                filter_stats[filter_name]['volume_confirmed'] += 1
        
        # STEP 4: Bounce detection (for each filter independently)
        for filter_name, passed in filters_passed.items():
            if not passed:
                continue
            
            bounce_confirmed = False
            entry_price = None
            entry_index = None
            
            # Check current candle first
            if close > ma20:
                bounce_confirmed = True
                entry_price = close
                entry_index = i
            else:
                # Check next 3 candles
                for j in range(i+1, min(i+4, len(df))):
                    close_j = df.iloc[j]['close']
                    breakdown = ma20 * 0.99
                    
                    if close_j > ma20:
                        bounce_confirmed = True
                        entry_price = close_j
                        entry_index = j
                        break
                    
                    if close_j < breakdown:
                        break  # Breakdown
            
            if not bounce_confirmed:
                continue
            
            # Count confirmed bounce
            filter_stats[filter_name]['bounces'] += 1
            
            # STEP 5: Outcome tracking
            for target_pct in TARGETS:
                results[filter_name][target_pct]['trades'] += 1
                
                target_price = entry_price * (1 + target_pct)
                sl_price = entry_price * (1 - STOP_LOSS)
                
                # Track next 75 candles
                outcome = None
                for k in range(entry_index + 1, min(entry_index + 76, len(df))):
                    if df.iloc[k]['high'] >= target_price:
                        outcome = 'WIN'
                        break
                    if df.iloc[k]['low'] <= sl_price:
                        outcome = 'LOSS'
                        break
                
                # Calculate P&L
                if outcome == 'WIN':
                    results[filter_name][target_pct]['wins'] += 1
                    profit = target_price - entry_price
                    results[filter_name][target_pct]['net'] += profit
                else:
                    results[filter_name][target_pct]['losses'] += 1
                    loss = entry_price - sl_price
                    results[filter_name][target_pct]['net'] -= loss
    
    # Find best scenario for this stock
    best_filter = None
    best_target = 0
    best_net = -999999
    best_wr = 0
    best_trades = 0
    
    for filter_name in FILTER_NAMES:
        for target_pct in TARGETS:
            stats = results[filter_name][target_pct]
            if stats['net'] > best_net:
                best_net = stats['net']
                best_filter = filter_name
                best_target = target_pct
                best_trades = stats['trades']
                best_wr = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
    
    # Classify stock by price vs MAs
    avg_close = df['close'].mean()
    avg_ma50 = df['ma50'].mean()
    avg_ma100 = df['ma100'].mean()
    avg_ma200 = df['ma200'].mean()
    
    if pd.notna(avg_ma50) and pd.notna(avg_ma100) and pd.notna(avg_ma200):
        if avg_close > avg_ma50 and avg_close > avg_ma100 and avg_close > avg_ma200:
            price_vs_mas = "Above All MAs"
        elif avg_close < avg_ma50 and avg_close < avg_ma100 and avg_close < avg_ma200:
            price_vs_mas = "Below All MAs"
        else:
            price_vs_mas = "Between MAs"
    else:
        price_vs_mas = "Unknown"
    
    return {
        'stock': stock_name,
        'best_filter': best_filter,
        'best_target': best_target * 100,  # Convert to percentage
        'net_profit': best_net,
        'win_rate': best_wr,
        'trades': best_trades,
        'price_vs_mas': price_vs_mas,
        'avg_price': avg_close,
        'results': results,
        'filter_stats': filter_stats
    }

# ═════════════════════════════════════════════════════════════
# EXCEL EXPORT
# ═════════════════════════════════════════════════════════════

def export_to_excel(all_results, nifty_context, month_name):
    """Export results to Excel with 4 sheets"""
    
    filename = f"backtest_{month_name}.xlsx"
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        
        # ============================================================
        # SHEET 1: SUMMARY
        # ============================================================
        
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
        
        # Add market context at top
        context_rows = []
        if nifty_context:
            context_rows.append(['MARKET CONTEXT', '', '', '', '', '', '', ''])
            context_rows.append(['NIFTY 50 Start', round(nifty_context['start_price'], 2), '', '', '', '', '', ''])
            context_rows.append(['NIFTY 50 End', round(nifty_context['end_price'], 2), '', '', '', '', '', ''])
            context_rows.append(['% Change', f"{nifty_context['pct_change']:+.2f}%", '', '', '', '', '', ''])
            context_rows.append(['Market Regime', nifty_context['regime'], '', '', '', '', '', ''])
            context_rows.append(['High', round(nifty_context['high'], 2), '', '', '', '', '', ''])
            context_rows.append(['Low', round(nifty_context['low'], 2), '', '', '', '', '', ''])
            context_rows.append(['', '', '', '', '', '', '', ''])
            context_rows.append(['STOCK RESULTS', '', '', '', '', '', '', ''])
        
        df_context = pd.DataFrame(context_rows, columns=df_summary.columns)
        df_final = pd.concat([df_context, df_summary], ignore_index=True)
        
        df_final.to_excel(writer, sheet_name='Summary', index=False)
        
        # ============================================================
        # SHEET 2: WINNERS
        # ============================================================
        
        winners = [r for r in all_results if r['win_rate'] > 55 or r['net_profit'] > 20]
        winners_data = []
        for result in winners:
            winners_data.append({
                'Stock': result['stock'],
                'Best Filter': result['best_filter'],
                'Best Target': f"{result['best_target']:.1f}%",
                'Net Profit (₹)': round(result['net_profit'], 2),
                'Win Rate (%)': round(result['win_rate'], 1),
                'Trades': result['trades'],
                'Price vs MAs': result['price_vs_mas']
            })
        
        df_winners = pd.DataFrame(winners_data)
        if not df_winners.empty:
            df_winners = df_winners.sort_values('Net Profit (₹)', ascending=False)
        
        df_winners.to_excel(writer, sheet_name='Winners', index=False)
        
        # ============================================================
        # SHEET 3: LOSERS
        # ============================================================
        
        losers = [r for r in all_results if r['win_rate'] < 45 or r['net_profit'] < 0]
        losers_data = []
        for result in losers:
            losers_data.append({
                'Stock': result['stock'],
                'Best Filter': result['best_filter'],
                'Best Target': f"{result['best_target']:.1f}%",
                'Net Profit (₹)': round(result['net_profit'], 2),
                'Win Rate (%)': round(result['win_rate'], 1),
                'Trades': result['trades'],
                'Price vs MAs': result['price_vs_mas']
            })
        
        df_losers = pd.DataFrame(losers_data)
        if not df_losers.empty:
            df_losers = df_losers.sort_values('Net Profit (₹)', ascending=True)
        
        df_losers.to_excel(writer, sheet_name='Losers', index=False)
        
        # ============================================================
        # SHEET 4: PATTERN ANALYSIS
        # ============================================================
        
        # Group by price vs MAs
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
    
    print(f"\n✓ Results exported to: {filename}")
    return filename

# ═════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════

def main():
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║   BATCH BACKTEST - MA BOUNCE v0.9 (30 STOCKS, RANDOM MONTH)  ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    # Step 1: Pick random month
    start_date, end_date, month_name = pick_random_month()
    print(f"\n🎲 RANDOMLY SELECTED MONTH: {month_name}")
    print(f"   Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Step 2: Download NIFTY context
    nifty_context = download_nifty_context(start_date, end_date)
    
    # Step 3: Process all 30 stocks
    print("\n" + "="*90)
    print(f"PROCESSING 30 STOCKS FOR {month_name}")
    print("="*90)
    
    all_results = []
    success_count = 0
    
    for idx, ticker in enumerate(STOCKS, 1):
        stock_name = ticker.replace('.NS', '')
        print(f"\n[{idx}/30] Processing {stock_name}...", end=' ')
        
        # Download data
        df = download_stock_data(ticker, start_date, end_date)
        
        if df is None or len(df) < 100:
            print(f"✗ SKIP (insufficient data)")
            continue
        
        # Run backtest
        result = run_ma_bounce(df, stock_name)
        all_results.append(result)
        success_count += 1
        
        print(f"✓ DONE | Best: {result['best_filter']} @ {result['best_target']:.1f}% → ₹{result['net_profit']:.2f} ({result['win_rate']:.1f}% WR)")
    
    # Step 4: Export to Excel
    print("\n" + "="*90)
    print(f"BACKTEST COMPLETE - {success_count}/{len(STOCKS)} stocks processed")
    print("="*90)
    
    if all_results:
        filename = export_to_excel(all_results, nifty_context, month_name)
        
        # Quick summary
        print("\n" + "="*90)
        print("QUICK SUMMARY")
        print("="*90)
        
        winners = [r for r in all_results if r['win_rate'] > 55 or r['net_profit'] > 20]
        print(f"🏆 Winners (>55% WR or >₹20 profit): {len(winners)}")
        
        if winners:
            top_3 = sorted(winners, key=lambda x: x['net_profit'], reverse=True)[:3]
            for i, stock in enumerate(top_3, 1):
                print(f"   {i}. {stock['stock']}: ₹{stock['net_profit']:.2f} @ {stock['win_rate']:.1f}% WR ({stock['best_filter']})")
        
        losers = [r for r in all_results if r['win_rate'] < 45 or r['net_profit'] < 0]
        print(f"\n❌ Losers (<45% WR or negative): {len(losers)}")
        
        print("\n" + "="*90)
        print("✓ RUN COMPLETE! Check Excel file for detailed analysis.")
        print("="*90)
    else:
        print("\n✗ No results to export. All stocks failed data download.")

if __name__ == '__main__':
    main()
