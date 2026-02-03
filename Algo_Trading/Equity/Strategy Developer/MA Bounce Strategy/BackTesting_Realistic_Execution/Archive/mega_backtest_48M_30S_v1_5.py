# TODO_done: [v1.5] GSS Regime Filter Integration - Add GSS as entry filter to proven MA Bounce system
# TODO_done (2026-01-20): [URGENT] Fix best_trades filtering - EOD exits being excluded (Win% = ProTrades% bug)
# TODO_done (2026-01-21): Implemented ATR-based dynamic SL/Target with 4 configs (Sideways/Regular-1/Regular-2/Extreme)
# TODO: [v1.4] Add 12 new columns: Volume_Ratio, Bounce_Strength_Pct, Wick_Ratio, Candle_Color, Hours_Until_Close, Touch_Candle_Index, Bounce_Candle_Index, NIFTY_Price, NIFTY_MA20, NIFTY_MA50, NIFTY_MA200, NIFTY_Regime
# TODO: [BACKLOG] Review std deviation calculations for threshold discovery
# TODO: [ANALYSIS] Analyze correlations to discover data-driven thresholds (winners vs losers median/std)

"""
Mega Backtest Script v1.5 - GSS INTEGRATION
╔═══════════════════════════════════════════════════════════════╗
║   MEGA BACKTEST - 48 Months × 30 F&O Stocks (CONSOLE ONLY)   ║
║   Jan 2022 → Dec 2025 | Speed Optimized | No Excel           ║
║   NEW: GSS Regime Filter (Threshold 45, 31.8% Precision)     ║
╚═══════════════════════════════════════════════════════════════╝
"""

import os
import upstox_client
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

# Import GSS functions
from gss_core_option_A_validation import calculate_gss, map_score_to_regime, calculate_adx, calculate_rsi

# Prevent PC from sleeping during overnight backtest
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

TARGETS = [0.005, 0.01, 0.015]
STOP_LOSS = 0.005
VOLUME_MULTIPLIER = 1.2

# ATR-based SL/Target configurations
ATR_CONFIGS = {
    'Sideways': {'sl_mult': 1.0, 'tgt_mult': 1.5},
    'Regular-1': {'sl_mult': 1.5, 'tgt_mult': 2.0},
    'Regular-2': {'sl_mult': 2.0, 'tgt_mult': 3.0},
    'Extreme': {'sl_mult': 2.5, 'tgt_mult': 4.0}
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

# GSS Parameters (From threshold sweep - best = 45)
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

        # Calculate MA20 and Volume MA for bounce detection
        df['ma20'] = df['close'].rolling(20).mean()
        df['avg_volume'] = df['volume'].rolling(20).mean()

        return df

    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


def fetch_daily_mas(instrument_key, end_date):
    """Fetch daily MA50/100/200 for filtering"""
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
    """Calculate all GSS indicators on 5-min dataframe"""
    df = df.copy()
    
    # Rename columns to match GSS expectations (Title Case)
    df = df.rename(columns={
        'open': 'Open', 'high': 'High', 'low': 'Low',
        'close': 'Close', 'volume': 'Volume'
    })
    
    # Calculate GSS indicators
    df['MA'] = df['Close'].rolling(GSS_PARAMS['ma_period']).mean()
    df['EMA'] = df['Close'].ewm(span=GSS_PARAMS['ema_period']).mean()
    df['MA_5d_ago'] = df['MA'].shift(5)  # 5 candles back (25 min)
    
    df['ADX'], df['Plus_DI'], df['Minus_DI'] = calculate_adx(df, GSS_PARAMS['adx_period'])
    df['ADX_prev'] = df['ADX'].shift(1)
    df['ADX_slope'] = df['ADX'].diff().rolling(3).mean()
    
    df['RSI'] = calculate_rsi(df['Close'], GSS_PARAMS['rsi_period'])
    df['RSI_prev'] = df['RSI'].shift(1)
    
    df['Volume_MA'] = df['Volume'].rolling(20).mean()
    df['Price_Proximity'] = (df['Close'] - df['MA']).abs() / df['MA'] * 100
    
    # Rename back to lowercase for compatibility with existing logic
    df = df.rename(columns={
        'Open': 'open', 'High': 'high', 'Low': 'low',
        'Close': 'close', 'Volume': 'volume'
    })
    
    return df


def check_gss_regime(row, prev_row):
    """Check if GSS regime is BULL at this candle"""
    # Skip if required indicators are NaN
    required_cols = ['MA', 'EMA', 'MA_5d_ago', 'ADX', 'ADX_prev', 'ADX_slope', 
                     'RSI', 'RSI_prev', 'Price_Proximity', 'Volume_MA', 'Plus_DI', 'Minus_DI']
    for col in required_cols:
        if pd.isna(row[col]):
            return False
    
    # Calculate GSS score
    score = calculate_gss(
        row['close'], row['MA'], row['EMA'], row['MA_5d_ago'],
        row['ADX'], row['ADX_prev'], row['ADX_slope'],
        row['RSI'], row['RSI_prev'], row['Price_Proximity'],
        GSS_PARAMS
    )
    
    # Map to regime
    regime = map_score_to_regime(
        score, row['volume'], row['Volume_MA'], row['RSI'],
        row['Plus_DI'], row['Minus_DI'], 
        prev_row['Plus_DI'], prev_row['Minus_DI'],
        row['ADX_slope'], GSS_PARAMS
    )
    
    return regime == "BULL"


# ═══════════════════════════════════════════════════════════════
# MA FILTER CHECK
# ═══════════════════════════════════════════════════════════════

def check_ma_filter(row, filter_mas):
    """Check if price is above all required MAs"""
    if not filter_mas:
        return True
    for ma in filter_mas:
        if pd.isna(row[ma]) or row['close'] <= row[ma]:
            return False
    return True


# ═══════════════════════════════════════════════════════════════
# BOUNCE DETECTION WITH GSS FILTER
# ═══════════════════════════════════════════════════════════════

def detect_bounce(df, filter_mas, use_gss=False):
    """
    Detect MA20 bounces with optional GSS regime filter
    v1.5 ADDITION: GSS regime check added as final entry filter
    """
    signals = []

    for i in range(20, len(df) - 3):  # -3 to allow checking next 3 candles
        row = df.iloc[i]

        # Skip if MA20 not available
        if pd.isna(row['ma20']):
            continue

        # Check MA filter first
        if not check_ma_filter(row, filter_mas):
            continue

        # Volume confirmation (1.2x average)
        if pd.notna(row['avg_volume']) and row['volume'] < row['avg_volume'] * VOLUME_MULTIPLIER:
            continue

        # STEP 1: TOUCH CHECK - Price must touch or go below MA20
        if row['low'] <= row['ma20']:
            
            # STEP 2: BOUNCE CHECK - Check current + next 3 candles (15-min window)
            ma20_at_touch = row['ma20']  # Lock MA20 at touch candle
            
            for j in range(i, min(i + 4, len(df))):  # Check i, i+1, i+2, i+3
                bounce_candle = df.iloc[j]
                
                # Bounce confirmed if close > MA20 (at touch)
                if bounce_candle['close'] > ma20_at_touch:
                    # Entry happens AFTER bounce detection, so we enter at next candle's open price
                    next_candle_idx = j + 1
                    if next_candle_idx >= len(df):
                        break  # Skip if no next candle available
                    
                    next_candle = df.iloc[next_candle_idx]
                    
                    # NEW v1.5: GSS REGIME CHECK
                    if use_gss:
                        # Check GSS regime at bounce candle (before entry)
                        if not check_gss_regime(bounce_candle, df.iloc[j-1] if j > 0 else bounce_candle):
                            break  # GSS not BULL, skip this bounce
                    
                    signals.append({
                        'datetime': next_candle['datetime'],  # Entry time is next candle
                        'entry_price': next_candle['open'],    # Entry at next candle OPEN
                        'ma20': ma20_at_touch,
                        'volume': row['volume'],  # Touch candle volume
                        'avg_volume': row['avg_volume']
                    })
                    break  # Stop checking once bounce confirmed

    return signals


def simulate_trades(df, signals, atr_config):
    """Simulate trades with target and stop loss"""
    trades = []

    for signal in signals:
        entry_price = signal['entry_price']
        entry_time = signal['datetime']
        entry_idx = df[df['datetime'] == entry_time].index[0]

        # Get ATR at entry candle
        entry_atr = df.loc[entry_idx, 'atr_14']

        # Skip if ATR not available (first 14 candles)
        if pd.isna(entry_atr):
            continue

        # Calculate ATR-based SL/Target
        stop_price = entry_price - (entry_atr * atr_config['sl_mult'])
        target_price = entry_price + (entry_atr * atr_config['tgt_mult'])

        # Check subsequent candles
        exit_price = None
        exit_time = None
        exit_reason = None

        for k in range(entry_idx + 1, min(entry_idx + 80, len(df))):
            candle = df.iloc[k]

            # Bullish candle: likely dropped first, then rallied
            if candle['close'] >= candle['open']:
                # Check stop loss first
                if candle['low'] <= stop_price:
                    exit_price = stop_price
                    exit_time = candle['datetime']
                    exit_reason = 'SL'
                    break

                # Check target second
                if candle['high'] >= target_price:
                    exit_price = target_price
                    exit_time = candle['datetime']
                    exit_reason = 'Target'
                    break
            else:
                # Bearish candle: likely rallied first, then dropped
                # Check target first
                if candle['high'] >= target_price:
                    exit_price = target_price
                    exit_time = candle['datetime']
                    exit_reason = 'Target'
                    break

                # Check stop loss second
                if candle['low'] <= stop_price:
                    exit_price = stop_price
                    exit_time = candle['datetime']
                    exit_reason = 'SL'
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

def backtest_stock(df, daily_mas, stock_name, use_gss=False):
    """Run MA Bounce with GSS filter option"""
    if df is None or len(df) == 0:
        return None

    if daily_mas is not None:
        df['date'] = df['datetime'].dt.date
        df = df.merge(daily_mas, on='date', how='left')
    else:
        df['ma50'] = df['ma100'] = df['ma200'] = np.nan

    # Calculate ATR for dynamic SL/Target
    df['prev_close'] = df['close'].shift(1)
    df['high_low'] = df['high'] - df['low']
    df['high_prev_close'] = abs(df['high'] - df['prev_close'])
    df['low_prev_close'] = abs(df['low'] - df['prev_close'])
    df['true_range'] = df[['high_low', 'high_prev_close', 'low_prev_close']].max(axis=1)
    df['atr_14'] = df['true_range'].rolling(window=14).mean()
    
    # NEW v1.5: Prepare GSS indicators if using GSS filter
    if use_gss:
        df = prepare_gss_indicators(df)
    
    results = {}

    for filter_name, filter_mas in FILTERS.items():
        for atr_name, atr_config in ATR_CONFIGS.items():
            # Detect bounces with optional GSS filter
            signals = detect_bounce(df, filter_mas, use_gss=use_gss)

            if len(signals) == 0:
                results[(filter_name, atr_name)] = {
                    'trades': 0,
                    'win_rate': 0,
                    'net_profit': 0
                }
                continue

            # Simulate trades
            trades = simulate_trades(df, signals, atr_config)

            # Calculate metrics
            wins = sum(1 for t in trades if t['pnl'] > 0)
            total_trades = len(trades)
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            net_profit = sum(t['pnl'] for t in trades)

            results[(filter_name, atr_name)] = {
                'trades': total_trades,
                'win_rate': win_rate,
                'net_profit': net_profit
            }

    return results


# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════

def main():
    start_time = datetime.now()
    print("="*70)
    print(" MEGA BACKTEST v1.5 - WITH GSS REGIME FILTER")
    print("="*70)
    print(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Stocks: {len(STOCKS)} | Period: Jan 2022 - Dec 2025 (48 months)")
    print(f"GSS Threshold: 45 (31.8% precision on Nifty)")
    print("="*70)

    # Generate month tuples
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
    stock_count = 0

    for stock_name, instrument_key in STOCKS.items():
        stock_count += 1
        print(f"\n[{stock_count}/{len(STOCKS)}] Processing {stock_name}...")

        combined_df = []
        
        # Fetch month by month
        for month_start, month_end in months:
            df_month = fetch_upstox_data(instrument_key, month_start, month_end)
            if df_month is not None and len(df_month) > 0:
                combined_df.append(df_month)

        if not combined_df:
            print(f"  ⚠ No data for {stock_name}")
            continue

        df = pd.concat(combined_df, ignore_index=True)
        
        # Fetch daily MAs
        daily_mas = fetch_daily_mas(instrument_key, datetime(2025, 12, 31))

        # Run both versions: without GSS (baseline) and with GSS (v1.5)
        print(f"  Running baseline (no GSS)...")
        results_baseline = backtest_stock(df, daily_mas, stock_name, use_gss=False)
        
        print(f"  Running v1.5 (with GSS)...")
        results_gss = backtest_stock(df, daily_mas, stock_name, use_gss=True)

        if results_baseline:
            for (filter_name, atr_name), metrics in results_baseline.items():
                all_results[(filter_name, atr_name, 'Baseline')][stock_name] = metrics
        
        if results_gss:
            for (filter_name, atr_name), metrics in results_gss.items():
                all_results[(filter_name, atr_name, 'GSS')][stock_name] = metrics

        print(f"  ✓ {stock_name} completed")

    # ═══════════════════════════════════════════════════════════════
    # RESULTS SUMMARY
    # ═══════════════════════════════════════════════════════════════
    
    print("\n" + "="*70)
    print(" RESULTS SUMMARY - BASELINE vs GSS")
    print("="*70)
    
    summary_data = []
    
    for (filter_name, atr_name, version), stock_data in all_results.items():
        total_trades = sum(m['trades'] for m in stock_data.values())
        total_profit = sum(m['net_profit'] for m in stock_data.values())
        avg_win_rate = np.mean([m['win_rate'] for m in stock_data.values() if m['trades'] > 0])
        
        summary_data.append({
            'Filter': filter_name,
            'ATR_Config': atr_name,
            'Version': version,
            'Total_Trades': total_trades,
            'Avg_Win_Rate': avg_win_rate,
            'Net_Profit': total_profit
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Save to CSV
    summary_df.to_csv('backtest_v1_5_gss_comparison.csv', index=False)
    print("\n✓ Results saved to: backtest_v1_5_gss_comparison.csv")
    
    # Display top performers
    print("\n" + "="*70)
    print(" TOP 10 CONFIGURATIONS (GSS Version)")
    print("="*70)
    gss_only = summary_df[summary_df['Version'] == 'GSS'].sort_values('Net_Profit', ascending=False).head(10)
    print(gss_only.to_string(index=False))
    
    print("\n" + "="*70)
    print(" TOP 10 CONFIGURATIONS (Baseline - No GSS)")
    print("="*70)
    baseline_only = summary_df[summary_df['Version'] == 'Baseline'].sort_values('Net_Profit', ascending=False).head(10)
    print(baseline_only.to_string(index=False))

    end_time = datetime.now()
    duration = end_time - start_time
    print("\n" + "="*70)
    print(f" BACKTEST COMPLETE")
    print(f" Duration: {duration}")
    print(f" End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)


if __name__ == "__main__":
    main()
