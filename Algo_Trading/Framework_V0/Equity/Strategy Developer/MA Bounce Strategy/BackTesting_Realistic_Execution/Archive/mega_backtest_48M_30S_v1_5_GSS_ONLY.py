# v1.5 GSS ONLY - No baseline rerun
# Compares against existing v1.4 results

"""
Mega Backtest Script v1.5 - GSS FILTER ONLY
╔═══════════════════════════════════════════════════════════════╗
║   MEGA BACKTEST - 48 Months × 30 F&O Stocks (CONSOLE ONLY)   ║
║   Jan 2022 → Dec 2025 | GSS Regime Filter Test               ║
║   GSS Threshold: 45 (31.8% precision on Nifty)               ║
╚═══════════════════════════════════════════════════════════════╝
"""

import os
import sqlite3
import upstox_client
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

# Import GSS functions
from gss_core_option_A_validation import calculate_gss, map_score_to_regime, calculate_adx, calculate_rsi

os.system("powercfg /change standby-timeout-ac 0")

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTdhMTExM2Q2NTkxMDUyZGMwM2Y4OWMiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2OTYwNzQ0MywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY5NjM3NjAwfQ.x2fmxmrIhLgoY4-Iv6hpm0VmkwoMaTmzsb0F_c2v07g"

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

VOLUME_MULTIPLIER = 1.2

ATR_CONFIGS = {
    'Sideways': {'sl_mult': 1.0, 'tp_mult': 1.5},
    'Regular-1': {'sl_mult': 1.5, 'tp_mult': 2.0},
    'Regular-2': {'sl_mult': 2.0, 'tp_mult': 3.0},
    'Extreme': {'sl_mult': 2.5, 'tp_mult': 4.0}
}

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

GSS_PARAMS = {
    'use_long_term_anchor': True, 'use_ma_slope': True, 'use_adx_strength': True,
    'use_adx_acceleration': True, 'use_rsi_equilibrium': True, 'use_rsi_rising': True,
    'use_rsi_ignition': False, 'use_rsi_exhaustion': True, 'use_price_proximity': True,
    'use_volume_confirmation': False, 'ma_period': 38, 'ema_period': 220,
    'adx_period': 14, 'rsi_period': 14, 'atr_multiplier': 1.00, 'ma_slope_threshold': 0.070,
    'adx_strength_threshold': 23, 'rsi_exhaustion_threshold': 70, 'price_proximity_max': 4.0,
    'vol_standard': 1.0, 'vol_momentum': 1.0, 'require_fresh_momentum': False, 
    'bear_threshold': 20, 'bull_threshold': 45
}

configuration = upstox_client.Configuration()
configuration.access_token = ACCESS_TOKEN

# ═══════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def ensure_numeric(df):
    """Convert common columns to proper dtypes to avoid pandas' slow dtype inference."""
    df = df.copy()
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    numeric_cols = [
        'open','high','low','close','volume','oi',
        'ma20','avg_volume','ma50','ma100','ma200',
        'prev_close','high_low','high_prev_close','low_prev_close',
        'true_range','atr_14','MA','EMA','MA_5d_ago',
        'ADX','Plus_DI','Minus_DI','ADX_prev','ADX_slope',
        'RSI','RSI_prev','Volume_MA','Price_Proximity'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('float64')
    return df


def save_results_to_db(all_results, all_trades, filename='mega_backtest_v1_5_GSS.db'):
    """Save backtest results to SQLite database for later analysis.

    Creates two tables:
    - summary: Aggregated results by filter/ATR config/stock
    - trades: Individual trade details for deep analysis
    """
    print(f"\n{'='*70}")
    print(" SAVING TO DATABASE")
    print(f"{'='*70}")

    conn = sqlite3.connect(filename)

    # Table 1: Summary Results
    summary_data = []
    for (filter_name, atr_name), stock_data in all_results.items():
        for stock, metrics in stock_data.items():
            summary_data.append({
                'stock': stock,
                'filter': filter_name,
                'atr_config': atr_name,
                'trades': metrics['trades'],
                'win_rate': metrics['win_rate'],
                'net_profit': metrics['net_profit']
            })

    if summary_data:
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_sql('summary', conn, if_exists='replace', index=False)
        print(f"  ✓ Summary table: {len(df_summary)} records")

    # Table 2: Individual Trades
    if all_trades:
        df_trades = pd.DataFrame(all_trades)
        df_trades.to_sql('trades', conn, if_exists='replace', index=False)
        print(f"  ✓ Trades table: {len(df_trades)} records")

    conn.close()
    print(f"  ✓ Database saved: {filename}")
    print(f"{'='*70}")



# ═══════════════════════════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════════════════════════

def fetch_upstox_data(instrument_key, from_date, to_date):
    try:
        api_instance = upstox_client.HistoryV3Api(upstox_client.ApiClient(configuration))
        api_response = api_instance.get_historical_candle_data1(
            instrument_key=instrument_key,
            unit='minutes',
            interval='5',
            from_date=from_date,
            to_date=to_date
        )

        if not hasattr(api_response, 'data') or not api_response.data or not api_response.data.candles:
            return None

        candles = api_response.data.candles
        df = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
        df['ma20'] = df['close'].rolling(20).mean()
        df['avg_volume'] = df['volume'].rolling(20).mean()
        return df

    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


def fetch_daily_mas(instrument_key, end_date):
    try:
        api_instance = upstox_client.HistoryV3Api(upstox_client.ApiClient(configuration))
        start_date = (end_date - timedelta(days=400)).strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        api_response = api_instance.get_historical_candle_data1(
            instrument_key=instrument_key,
            unit='days',
            interval='1',
            from_date=start_date,
            to_date=end_date_str
        )

        if not hasattr(api_response, 'data') or not api_response.data or not api_response.data.candles:
            return None

        candles = api_response.data.candles
        df = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['datetime'] = pd.to_datetime(df['datetime']).dt.date
        df = df.sort_values('datetime').reset_index(drop=True)
        df['ma50'] = df['close'].rolling(50).mean()
        df['ma100'] = df['close'].rolling(100).mean()
        df['ma200'] = df['close'].rolling(200).mean()
        return df[['datetime', 'ma50', 'ma100', 'ma200']].rename(columns={'datetime': 'date'})

    except Exception as e:
        print(f"Error fetching daily MAs: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# GSS INDICATOR PREPARATION
# ═══════════════════════════════════════════════════════════════

def prepare_gss_indicators(df):
    df = df.copy()
    df = df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
    
    df['MA'] = df['Close'].rolling(GSS_PARAMS['ma_period']).mean()
    df['EMA'] = df['Close'].ewm(span=GSS_PARAMS['ema_period']).mean()
    df['MA_5d_ago'] = df['MA'].shift(5)
    df['ADX'], df['Plus_DI'], df['Minus_DI'] = calculate_adx(df, GSS_PARAMS['adx_period'])
    df['ADX_prev'] = df['ADX'].shift(1)
    df['ADX_slope'] = df['ADX'].diff().rolling(3).mean()
    df['RSI'] = calculate_rsi(df['Close'], GSS_PARAMS['rsi_period'])
    df['RSI_prev'] = df['RSI'].shift(1)
    df['Volume_MA'] = df['Volume'].rolling(20).mean()
    df['Price_Proximity'] = (df['Close'] - df['MA']).abs() / df['MA'] * 100
    
    df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
    return df


def check_gss_regime(row, prev_row):
    required_cols = ['MA', 'EMA', 'MA_5d_ago', 'ADX', 'ADX_prev', 'ADX_slope', 
                     'RSI', 'RSI_prev', 'Price_Proximity', 'Volume_MA', 'Plus_DI', 'Minus_DI']
    for col in required_cols:
        if pd.isna(row[col]):
            return False
    
    score = calculate_gss(
        row['close'], row['MA'], row['EMA'], row['MA_5d_ago'],
        row['ADX'], row['ADX_prev'], row['ADX_slope'],
        row['RSI'], row['RSI_prev'], row['Price_Proximity'],
        GSS_PARAMS
    )
    
    regime = map_score_to_regime(
        score, row['volume'], row['Volume_MA'], row['RSI'],
        row['Plus_DI'], row['Minus_DI'], 
        prev_row['Plus_DI'], prev_row['Minus_DI'],
        row['ADX_slope'], GSS_PARAMS
    )
    
    return regime == "BULL"


def check_ma_filter(row, filter_mas):
    if not filter_mas:
        return True
    for ma in filter_mas:
        if pd.isna(row[ma]) or row['close'] <= row[ma]:
            return False
    return True


# ═══════════════════════════════════════════════════════════════
# BOUNCE DETECTION WITH GSS FILTER
# ═══════════════════════════════════════════════════════════════

def detect_bounce_gss(df, filter_mas, gss_bull_flags):
    """OPTIMIZED: Use pre-computed GSS regime flags with instant array lookups."""
    signals = []
    n = len(df)
    if n < 24:
        return signals


    # ✅ PRE-COMPUTE MA FILTER FLAGS (vectorized)
    if filter_mas:
        filter_mask = np.ones(n, dtype=bool)
        close = df['close'].to_numpy()
        for ma_col in filter_mas:
            if ma_col in df.columns:
                ma_vals = df[ma_col].to_numpy()
                filter_mask &= (close > ma_vals) & ~np.isnan(ma_vals)
    else:
        filter_mask = np.ones(n, dtype=bool)

    # ✅ EXTRACT ARRAYS FOR CHEAP CHECKS
    ma20 = df['ma20'].to_numpy() if 'ma20' in df.columns else np.full(n, np.nan)
    avg_vol = df['avg_volume'].to_numpy() if 'avg_volume' in df.columns else np.full(n, np.nan)
    vol = df['volume'].to_numpy() if 'volume' in df.columns else np.full(n, np.nan)
    low = df['low'].to_numpy() if 'low' in df.columns else np.full(n, np.nan)
    close = df['close'].to_numpy() if 'close' in df.columns else np.full(n, np.nan)
    open_arr = df['open'].to_numpy() if 'open' in df.columns else np.full(n, np.nan)
    datetime_arr = df['datetime'].to_numpy() if 'datetime' in df.columns else np.array([None]*n)

    # ✅ NOW SCAN FOR BOUNCES USING PRE-COMPUTED FLAGS (instant lookups!)
    for i in range(20, n - 3):
        m20 = ma20[i]
        if np.isnan(m20):
            continue

        # Cheap volume check
        av = avg_vol[i]
        if not np.isnan(av) and vol[i] < av * VOLUME_MULTIPLIER:
            continue

        # Cheap touch check
        if low[i] <= m20:
            ma20_at_touch = m20

            # Scan up to next 3 candles to find a bounce
            for j in range(i, min(i + 4, n)):
                if close[j] > ma20_at_touch:
                    next_idx = j + 1
                    if next_idx >= n:
                        break

                    # ✅ INSTANT LOOKUPS - no expensive function calls!
                    if not filter_mask[j]:  # MA filter check
                        break

                    if not gss_bull_flags[j]:  # GSS regime check
                        break

                    signals.append({
                        'datetime': datetime_arr[next_idx],
                        'entry_price': open_arr[next_idx],
                        'ma20': ma20_at_touch,
                        'volume': vol[i],
                        'avg_volume': av
                    })
                    break

    return signals


def simulate_trades(df, signals, atr_config, stock_name='', filter_name='', atr_name=''):
    trades = []

    for signal in signals:
        entry_price = signal['entry_price']
        entry_time = signal['datetime']
        entry_idx = df[df['datetime'] == entry_time].index[0]
        entry_atr = df.loc[entry_idx, 'atr_14']

        if pd.isna(entry_atr):
            continue

        stop_price = entry_price - (entry_atr * atr_config['sl_mult'])
        target_price = entry_price + (entry_atr * atr_config['tp_mult'])
        exit_price = None
        exit_time = None
        exit_reason = None

        for k in range(entry_idx + 1, min(entry_idx + 80, len(df))):
            candle = df.iloc[k]

            if candle['close'] >= candle['open']:
                if candle['low'] <= stop_price:
                    exit_price = stop_price
                    exit_time = candle['datetime']
                    exit_reason = 'SL'
                    break
                if candle['high'] >= target_price:
                    exit_price = target_price
                    exit_time = candle['datetime']
                    exit_reason = 'Target'
                    break
            else:
                if candle['high'] >= target_price:
                    exit_price = target_price
                    exit_time = candle['datetime']
                    exit_reason = 'Target'
                    break
                if candle['low'] <= stop_price:
                    exit_price = stop_price
                    exit_time = candle['datetime']
                    exit_reason = 'SL'
                    break

        if exit_price is None:
            last_candle = df.iloc[min(entry_idx + 79, len(df) - 1)]
            exit_price = last_candle['close']
            exit_time = last_candle['datetime']
            exit_reason = 'EOD'

        pnl = exit_price - entry_price
        pnl_pct = (pnl / entry_price) * 100

        trades.append({
            'stock': stock_name,
            'filter': filter_name,
            'atr_config': atr_name,
            'entry_time': entry_time,
            'entry_price': entry_price,
            'exit_time': exit_time,
            'exit_price': exit_price,
            'stop_price': stop_price,
            'target_price': target_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'reason': exit_reason
        })

    return trades


def backtest_stock_gss(df, daily_mas, stock_name):
    if df is None or len(df) == 0:
        return None, []

    if daily_mas is not None:
        df['date'] = df['datetime'].dt.date
        df = df.merge(daily_mas, on='date', how='left')
    else:
        df['ma50'] = df['ma100'] = df['ma200'] = np.nan

    # Ensure numeric dtypes early to avoid repeated dtype inference during loops
    df = ensure_numeric(df)

    df['prev_close'] = df['close'].shift(1)
    df['high_low'] = df['high'] - df['low']
    df['high_prev_close'] = abs(df['high'] - df['prev_close'])
    df['low_prev_close'] = abs(df['low'] - df['prev_close'])
    df['true_range'] = df[['high_low', 'high_prev_close', 'low_prev_close']].max(axis=1)
    df['atr_14'] = df['true_range'].rolling(window=14).mean()
    
    df = prepare_gss_indicators(df)

    # ✅ PRE-COMPUTE GSS REGIME FLAGS ONCE FOR ENTIRE STOCK (not per filter!)
    print("  → Pre-computing GSS regime flags...", end='', flush=True)
    n = len(df)
    gss_bull_flags = np.zeros(n, dtype=bool)

    required_cols = ['MA', 'EMA', 'MA_5d_ago', 'ADX', 'ADX_prev', 'ADX_slope',
                     'RSI', 'RSI_prev', 'Price_Proximity', 'Volume_MA', 'Plus_DI', 'Minus_DI']

    # Check GSS for all rows once
    for i in range(1, n):  # Start at 1 for prev_row
        row = df.iloc[i]
        prev_row = df.iloc[i-1]

        # Quick skip if any required column is NaN
        if any(pd.isna(row[col]) for col in required_cols):
            continue

        gss_bull_flags[i] = check_gss_regime(row, prev_row)

    print(f" Done ({gss_bull_flags.sum()} BULL candles)")

    results = {}
    all_trades = []

    for filter_name, filter_mas in FILTERS.items():
        for atr_name, atr_config in ATR_CONFIGS.items():
            # Pass pre-computed GSS flags to avoid re-computing
            signals = detect_bounce_gss(df, filter_mas, gss_bull_flags)

            if len(signals) == 0:
                results[(filter_name, atr_name)] = {
                    'trades': 0,
                    'win_rate': 0,
                    'net_profit': 0
                }
                continue

            trades = simulate_trades(df, signals, atr_config, stock_name, filter_name, atr_name)
            all_trades.extend(trades)

            wins = sum(1 for t in trades if t['pnl'] > 0)
            total_trades = len(trades)
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            net_profit = sum(t['pnl'] for t in trades)

            results[(filter_name, atr_name)] = {
                'trades': total_trades,
                'win_rate': win_rate,
                'net_profit': net_profit
            }

    return results, all_trades


# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════

def main():
    start_time = datetime.now()
    print("="*70)
    print(" MEGA BACKTEST v1.5 - GSS FILTER ONLY")
    print("="*70)
    print(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Stocks: {len(STOCKS)} | Period: Jan 2022 - Dec 2025")
    print(f"GSS Threshold: 45 (31.8% Nifty precision)")
    print("="*70)

    months = []
    current = datetime(2022, 1, 1)
    end = datetime(2025, 12, 31)

    while current <= end:
        first_day = current
        if current.month == 12:
            last_day = datetime(current.year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(current.year, current.month + 1, 1) - timedelta(days=1)
        
        months.append((first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')))
        
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)

    all_results = defaultdict(lambda: defaultdict(list))
    all_trades = []  # Collect all trades for database
    stock_count = 0

    for stock_name, instrument_key in STOCKS.items():
        stock_count += 1
        print(f"\n[{stock_count}/{len(STOCKS)}] {stock_name}...")

        combined_df = []
        for month_start, month_end in months:
            df_month = fetch_upstox_data(instrument_key, month_start, month_end)
            if df_month is not None and len(df_month) > 0:
                combined_df.append(df_month)

        if not combined_df:
            print(f"  ⚠ No data")
            continue

        df = pd.concat(combined_df, ignore_index=True)
        daily_mas = fetch_daily_mas(instrument_key, datetime(2025, 12, 31))
        results, stock_trades = backtest_stock_gss(df, daily_mas, stock_name)

        if results:
            for (filter_name, atr_name), metrics in results.items():
                all_results[(filter_name, atr_name)][stock_name] = metrics
            all_trades.extend(stock_trades)  # Collect trades from this stock

        # Mini summary for this stock
        if stock_trades:
            total_stock_trades = len(stock_trades)
            wins = sum(1 for t in stock_trades if t['pnl'] > 0)
            losses = sum(1 for t in stock_trades if t['pnl'] < 0)
            win_rate = (wins / total_stock_trades * 100) if total_stock_trades > 0 else 0
            net_pnl = sum(t['pnl'] for t in stock_trades)
            avg_pnl_pct = np.mean([t['pnl_pct'] for t in stock_trades])

            # Calculate BULL precision (all trades assumed BULL regime)
            bull_precision = (wins / total_stock_trades * 100) if total_stock_trades > 0 else 0
            bear_count = losses  # Losing trades could be considered false BULL signals

            print(f"  ✓ Done | Trades: {total_stock_trades:4d} | Win Rate: {win_rate:5.1f}% | Net P&L: {net_pnl:8.2f} | Avg: {avg_pnl_pct:+5.2f}%")
            print(f"         BULL Precision: {bull_precision:5.1f}% ({wins}/{total_stock_trades} wins) | False Signals: {losses}")
        else:
            print(f"  ✓ Done | No trades generated")

    print("\n" + "="*70)
    print(" RESULTS - GSS FILTER")
    print("="*70)
    
    # Calculate overall BULL/BEAR precision metrics
    if all_trades:
        total_all_trades = len(all_trades)
        total_wins = sum(1 for t in all_trades if t['pnl'] > 0)
        total_losses = sum(1 for t in all_trades if t['pnl'] < 0)
        total_breakeven = sum(1 for t in all_trades if t['pnl'] == 0)

        overall_bull_precision = (total_wins / total_all_trades * 100) if total_all_trades > 0 else 0

        print(f"\n OVERALL GSS BULL REGIME ACCURACY:")
        print(f"   Total Trades (BULL signals): {total_all_trades}")
        print(f"   Winning Trades: {total_wins} ({total_wins/total_all_trades*100:.1f}%)")
        print(f"   Losing Trades: {total_losses} ({total_losses/total_all_trades*100:.1f}%)")
        print(f"   Breakeven: {total_breakeven}")
        print(f"   → BULL Precision: {overall_bull_precision:.1f}%")
        print(f"   → False BULL Signals: {total_losses} ({total_losses/total_all_trades*100:.1f}%)")

    summary_data = []
    for (filter_name, atr_name), stock_data in all_results.items():
        total_trades = sum(m['trades'] for m in stock_data.values())
        total_profit = sum(m['net_profit'] for m in stock_data.values())
        avg_win_rate = np.mean([m['win_rate'] for m in stock_data.values() if m['trades'] > 0])
        
        summary_data.append({
            'Filter': filter_name,
            'ATR_Config': atr_name,
            'Total_Trades': total_trades,
            'Avg_Win_Rate': avg_win_rate,
            'Net_Profit': total_profit
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv('backtest_v1_5_GSS_ONLY.csv', index=False)
    print("\n✓ Saved: backtest_v1_5_GSS_ONLY.csv")
    
    # Save to database
    save_results_to_db(all_results, all_trades)

    print("\n" + "="*70)
    print(" TOP 10 CONFIGURATIONS")
    print("="*70)
    top10 = summary_df.sort_values('Net_Profit', ascending=False).head(10)
    print(top10.to_string(index=False))

    end_time = datetime.now()
    duration = end_time - start_time
    print("\n" + "="*70)
    print(f" COMPLETE | Duration: {duration}")
    print(f" Total Trades Logged: {len(all_trades)}")
    print("="*70)


if __name__ == "__main__":
    main()
