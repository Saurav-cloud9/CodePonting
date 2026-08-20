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

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTYzNjM1NzczOGU1NDNmMDIwYmNjMjQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2ODEyMTE3NSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY4MTY4ODAwfQ.g5X2qmcKTDqvOCOxhJ1ndpl3KXPPPXcUvgbLu_AlB3U"

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
        
        df = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
        df['ma20'] = df['close'].rolling(20).mean()
        df['avg_volume'] = df['volume'].rolling(20).mean()
        return df
    except:
        return None

def fetch_daily_mas(instrument_key, end_date):
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
        df = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
        df['ma50'] = df['close'].rolling(50).mean()
        df['ma100'] = df['close'].rolling(100).mean()
        df['ma200'] = df['close'].rolling(200).mean()
        df['date'] = df['datetime'].dt.date
        return df[['date', 'ma50', 'ma100', 'ma200']]
    except:
        return None


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

# ═══════════════════════════════════════════════════════════════
# BACKTEST ENGINE
# ═══════════════════════════════════════════════════════════════

def backtest_stock(df, daily_mas, stock_name):
    """Run MA Bounce v0.9 with all filter/target combinations"""
    if daily_mas is not None:
        df['date'] = df['datetime'].dt.date
        df = df.merge(daily_mas, on='date', how='left')
    else:
        df['ma50'] = df['ma100'] = df['ma200'] = np.nan
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

    # Calculate profit efficiency (Total profit as % of average stock price)
    avg_price = df['close'].mean()  # Average of ALL candles in the month
    profit_efficiency = (best_result['net_profit'] / avg_price * 100) if avg_price > 0 else 0

    return {
        'stock': stock_name,
        'best_filter': best_filter,
        'best_target': best_target * 100,  # Convert to percentage
        'trades': best_result['trades'],
        'win_rate': best_result['win_rate'],
        'net_profit': best_result['net_profit'],
        'profit_efficiency': profit_efficiency,  # NEW: ROI %
        'price_vs_mas': price_vs_mas,
        'avg_price': avg_price
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
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + " "*22 + "48-MONTH MEGA BACKTEST (30 STOCKS)" + " "*22 + "║")
    print("╚" + "═"*78 + "╝\n")
    
    # Generate months
    months = []
    current = datetime(2022, 1, 1)
    while current <= datetime(2025, 12, 31):
        first_day = current
        if current.month == 12:
            last_day = datetime(current.year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(current.year, current.month + 1, 1) - timedelta(days=1)
        months.append((first_day, last_day, f"{current.strftime('%b').upper()}_{current.year}"))
        current = datetime(current.year + (1 if current.month == 12 else 0), (current.month % 12) + 1, 1)
    
    print(f"Months: {len(months)} | Stocks: {len(STOCKS)} | Total: {len(months)*len(STOCKS)}\n")
    
    all_top10 = []
    start_time = datetime.now()
    
    for month_idx, (from_date, to_date, month_name) in enumerate(months, 1):
        print(f"[{month_idx:2}/48] {month_name:<12}", end=" ", flush=True)
        
        month_results = []
        for stock, key in STOCKS.items():
            df = fetch_upstox_data(key, from_date, to_date)
            mas = fetch_daily_mas(key, to_date)
            result = backtest_stock(df, mas, stock)
            if result:
                month_results.append(result)
        
        month_results.sort(key=lambda x: x['profit_efficiency'], reverse=True)  # ✅ Fixed: was 'efficiency'

        print("\n  🏆 TOP 10:")
        print(f"  {'Rank':<6} {'Stock':<15} {'Eff%':<8} {'Filter':<18} {'Target':<8}")
        print("  " + "-" * 65)
        for rank, r in enumerate(month_results[:10], 1):
            print(f"  {rank:<6} {r['stock']:<15} {r['profit_efficiency']:<8.1f} {r['best_filter']:<18} {r['best_target']:.1f}%")  # ✅ Fixed: field names

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
