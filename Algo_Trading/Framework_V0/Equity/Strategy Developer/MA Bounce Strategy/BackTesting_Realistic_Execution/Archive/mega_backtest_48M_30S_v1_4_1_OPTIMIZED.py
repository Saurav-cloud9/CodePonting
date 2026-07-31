# TODO_done (2026-01-20): [URGENT] Fix best_trades filtering - EOD exits being excluded
# TODO_done (2026-01-21): Implemented ATR-based dynamic SL/Target with 4 configs
# TODO_done (2026-01-29): [v1.4.1] Added NIFTY_Regime labeling for playbook analysis
# TODO_done (2026-01-29): Applied Copilot optimizations - NumPy arrays, vectorized checks
# TODO: [v1.4.2] Add remaining 11 columns for pattern analysis
# TODO: [ANALYSIS] Analyze regime-segmented results to build playbooks

"""
Mega Backtest Script v1.4.1 OPTIMIZED
╔════════════════════════════════════════════════════════════════╗
║   MEGA BACKTEST - 48 Months × 30 F&O Stocks                   ║
║   Jan 2022 → Dec 2025 | Copilot Optimized | Regime Labeled    ║
║   NEW: Nifty regime tagging for playbook creation             ║
╚════════════════════════════════════════════════════════════════╝
"""

import os
import upstox_client
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

os.system("powercfg /change standby-timeout-ac 0")

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTdhMTExM2Q2NTkxMDUyZGMwM2Y4OWMiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2OTYwNzQ0MywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY5NjM3NjAwfQ.x2fmxmrIhLgoY4-Iv6hpm0VmkwoMaTmzsb0F_c2v07g"

NIFTY_INSTRUMENT = 'NSE_INDEX|Nifty 50'

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

configuration = upstox_client.Configuration()
configuration.access_token = ACCESS_TOKEN

# ═══════════════════════════════════════════════════════════════
# NIFTY REGIME CALCULATION (NEW v1.4.1)
# ═══════════════════════════════════════════════════════════════

def fetch_nifty_daily_data():
    """Fetch Nifty daily data for regime calculation"""
    try:
        api_instance = upstox_client.HistoryV3Api(upstox_client.ApiClient(configuration))
        api_response = api_instance.get_historical_candle_data1(
            instrument_key=NIFTY_INSTRUMENT,
            unit='days',
            interval='1',
            from_date='2021-12-01',  # Extra buffer for ATR calculation
            to_date='2025-12-31'
        )
        
        if not hasattr(api_response, 'data') or not api_response.data:
            return None
            
        candles = api_response.data.candles
        df = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
        df['date'] = df['datetime'].dt.date
        
        # Calculate ATR for regime threshold
        df['prev_close'] = df['close'].shift(1)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['prev_close'])
        df['tr3'] = abs(df['low'] - df['prev_close'])
        df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        df['atr'] = df['true_range'].rolling(window=14).mean()
        
        return df[['date', 'close', 'atr']].dropna()
        
    except Exception as e:
        print(f"Error fetching Nifty data: {e}")
        return None


def calculate_nifty_regimes(nifty_df, lookahead=5, atr_multiplier=1.5):
    """
    Calculate actual regime for each day using lookahead
    Returns: dict {date: 'BULL'/'BEAR'/'SIDEWAYS'}
    """
    regimes = {}
    n = len(nifty_df)
    
    for i in range(n - lookahead):
        current_close = nifty_df.iloc[i]['close']
        future_close = nifty_df.iloc[i + lookahead]['close']
        atr = nifty_df.iloc[i]['atr']
        current_date = nifty_df.iloc[i]['date']
        
        # Calculate movement and threshold
        movement = (future_close - current_close) / current_close
        threshold = (atr_multiplier * atr) / current_close
        
        # Classify regime
        if movement > threshold:
            regimes[current_date] = 'BULL'
        elif movement < -threshold:
            regimes[current_date] = 'BEAR'
        else:
            regimes[current_date] = 'SIDEWAYS'
    
    return regimes


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
        
        if not hasattr(api_response, 'data') or not api_response.data:
            return None
            
        candles = api_response.data.candles
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
        start_date = (end_date - timedelta(days=400)).strftime('%Y-%m-%d')
        api_response = api_instance.get_historical_candle_data1(
            instrument_key=instrument_key,
            unit='days',
            interval='1',
            from_date=start_date,
            to_date=end_date.strftime('%Y-%m-%d')
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


# ═══════════════════════════════════════════════════════════════
# BOUNCE DETECTION (COPILOT OPTIMIZED)
# ═══════════════════════════════════════════════════════════════

def detect_bounce_optimized(df, filter_mas):
    """
    OPTIMIZED: Use NumPy arrays for 50-100x speedup
    Copilot optimization applied - extract arrays once, use fast indexing
    """
    signals = []
    n = len(df)
    if n < 24:
        return signals
    
    # Extract arrays ONCE (avoid repeated df.iloc[i] calls)
    ma20 = df['ma20'].to_numpy()
    avg_vol = df['avg_volume'].to_numpy()
    vol = df['volume'].to_numpy()
    low = df['low'].to_numpy()
    close_arr = df['close'].to_numpy()
    open_arr = df['open'].to_numpy()
    datetime_arr = df['datetime'].to_numpy()
    
    # Pre-compute MA filter mask (vectorized)
    if filter_mas:
        filter_mask = np.ones(n, dtype=bool)
        for ma_col in filter_mas:
            if ma_col in df.columns:
                ma_vals = df[ma_col].to_numpy()
                filter_mask &= (close_arr > ma_vals) & ~np.isnan(ma_vals)
    else:
        filter_mask = np.ones(n, dtype=bool)
    
    # Fast loop with array indexing
    for i in range(20, n - 3):
        m20 = ma20[i]
        if np.isnan(m20):
            continue
        
        # Volume check (cheap array lookup)
        if not np.isnan(avg_vol[i]) and vol[i] < avg_vol[i] * VOLUME_MULTIPLIER:
            continue
        
        # Touch check
        if low[i] <= m20:
            ma20_at_touch = m20
            
            # Bounce window check (next 3 candles)
            for j in range(i, min(i + 4, n)):
                if close_arr[j] > ma20_at_touch:
                    next_idx = j + 1
                    if next_idx >= n:
                        break
                    
                    # MA filter check (instant array lookup)
                    if not filter_mask[j]:
                        break
                    
                    signals.append({
                        'datetime': datetime_arr[next_idx],
                        'entry_price': open_arr[next_idx],
                        'ma20': ma20_at_touch,
                        'volume': vol[i],
                        'avg_volume': avg_vol[i]
                    })
                    break
    
    return signals


def simulate_trades(df, signals, atr_config, nifty_regimes):
    """Simulate trades with ATR-based SL/Target + regime tagging"""
    trades = []

    for signal in signals:
        entry_price = signal['entry_price']
        entry_time = signal['datetime']
        entry_idx = df[df['datetime'] == entry_time].index[0]
        entry_date = entry_time.date()
        
        # Get regime for this trade date
        regime = nifty_regimes.get(entry_date, 'UNKNOWN')
        
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
            'entry_time': entry_time,
            'entry_price': entry_price,
            'exit_time': exit_time,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'reason': exit_reason,
            'nifty_regime': regime  # NEW: Regime tagging
        })

    return trades


# ═══════════════════════════════════════════════════════════════
# BACKTEST ENGINE
# ═══════════════════════════════════════════════════════════════

def backtest_stock(df, daily_mas, stock_name, nifty_regimes):
    if df is None or len(df) == 0:
        return None

    if daily_mas is not None:
        df['date'] = df['datetime'].dt.date
        df = df.merge(daily_mas, on='date', how='left')
    else:
        df['ma50'] = df['ma100'] = df['ma200'] = np.nan

    # Calculate ATR
    df['prev_close'] = df['close'].shift(1)
    df['high_low'] = df['high'] - df['low']
    df['high_prev_close'] = abs(df['high'] - df['prev_close'])
    df['low_prev_close'] = abs(df['low'] - df['prev_close'])
    df['true_range'] = df[['high_low', 'high_prev_close', 'low_prev_close']].max(axis=1)
    df['atr_14'] = df['true_range'].rolling(window=14).mean()
    
    results = {}

    for filter_name, filter_mas in FILTERS.items():
        for atr_name, atr_config in ATR_CONFIGS.items():
            signals = detect_bounce_optimized(df, filter_mas)

            if len(signals) == 0:
                results[(filter_name, atr_name)] = {
                    'trades': 0,
                    'win_rate': 0,
                    'net_profit': 0
                }
                continue

            trades = simulate_trades(df, signals, atr_config, nifty_regimes)
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
    print(" MEGA BACKTEST v1.4.1 OPTIMIZED - WITH NIFTY REGIME LABELING")
    print("="*70)
    print(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Stocks: {len(STOCKS)} | Period: Jan 2022 - Dec 2025")
    print(f"NEW: Nifty regime tagging for playbook analysis")
    print("="*70)
    
    # Fetch and calculate Nifty regimes
    print("\nFetching Nifty data for regime calculation...")
    nifty_df = fetch_nifty_daily_data()
    if nifty_df is None:
        print("ERROR: Failed to fetch Nifty data. Exiting.")
        return
    
    print("Calculating daily regimes...")
    nifty_regimes = calculate_nifty_regimes(nifty_df, lookahead=5, atr_multiplier=1.5)
    
    regime_counts = Counter(nifty_regimes.values())
    print(f"Regime distribution: BULL={regime_counts['BULL']}, BEAR={regime_counts['BEAR']}, SIDEWAYS={regime_counts['SIDEWAYS']}")
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
        results = backtest_stock(df, daily_mas, stock_name, nifty_regimes)

        if results:
            for (filter_name, atr_name), metrics in results.items():
                all_results[(filter_name, atr_name)][stock_name] = metrics

        print(f"  ✓ Done")

    # Save results
    print("\n" + "="*70)
    print(" RESULTS SUMMARY")
    print("="*70)
    
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
    summary_df.to_csv('backtest_v1_4_1_results.csv', index=False)
    print("\n✓ Results saved to: backtest_v1_4_1_results.csv")
    
    print("\n" + "="*70)
    print(" TOP 10 CONFIGURATIONS")
    print("="*70)
    top10 = summary_df.sort_values('Net_Profit', ascending=False).head(10)
    print(top10.to_string(index=False))

    end_time = datetime.now()
    duration = end_time - start_time
    print("\n" + "="*70)
    print(f" BACKTEST COMPLETE | Duration: {duration}")
    print("="*70)
    print("\nNEXT STEP: Analyze results by regime to build playbooks!")
    print("  - Group trades by stock × regime")
    print("  - Identify top performers per regime")
    print("  - Create PBS-BULL, PBS-BEAR, PBS-SIDEWAYS")


if __name__ == "__main__":
    main()
