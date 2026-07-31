import os
import upstox_client
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

os.system("powercfg /change standby-timeout-ac 0")

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION (unchanged)
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
# OPTIMIZED: Nifty Regime Calculation (Vectorized)
# ═══════════════════════════════════════════════════════════════

def fetch_nifty_daily_data():
    """Fetch Nifty daily data for regime calculation"""
    try:
        api_instance = upstox_client.HistoryV3Api(upstox_client.ApiClient(configuration))
        api_response = api_instance.get_historical_candle_data1(
            instrument_key=NIFTY_INSTRUMENT,
            unit='days',
            interval='1',
            from_date='2021-12-01',
            to_date='2025-12-31'
        )

        if not hasattr(api_response, 'data') or not api_response.data:
            return None

        candles = api_response.data.candles
        df = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
        df['date'] = df['datetime'].dt.date

        # OPTIMIZED: Vectorized ATR calculation
        df['prev_close'] = df['close'].shift(1)
        df['tr'] = np.maximum.reduce([
            df['high'] - df['low'],
            np.abs(df['high'] - df['prev_close']),
            np.abs(df['low'] - df['prev_close'])
        ])
        df['atr'] = df['tr'].rolling(window=14).mean()

        return df[['date', 'close', 'atr']].dropna()

    except Exception as e:
        print(f"Error fetching Nifty data: {e}")
        return None


def calculate_nifty_regimes(nifty_df, lookahead=5, atr_multiplier=1.5):
    """OPTIMIZED: Vectorized regime calculation
    """
    n = len(nifty_df)

    # Vectorized calculation for all valid indices
    close_now = nifty_df['close'].values[:-lookahead]
    close_future = nifty_df['close'].values[lookahead:]
    atr_vals = nifty_df['atr'].values[:-lookahead]
    dates = nifty_df['date'].values[:-lookahead]

    # Calculate movements and thresholds (vectorized)
    movements = (close_future - close_now) / close_now
    thresholds = (atr_multiplier * atr_vals) / close_now

    # Classify regimes (vectorized)
    regimes_array = np.where(movements > thresholds, 'BULL',
                   np.where(movements < -thresholds, 'BEAR', 'SIDEWAYS'))

    # Create dictionary
    regimes = dict(zip(dates, regimes_array))

    return regimes


# ═══════════════════════════════════════════════════════════════
# OPTIMIZED: Data Fetching with Caching
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

        # OPTIMIZED: Use more efficient dtypes
        df['datetime'] = pd.to_datetime(df['datetime'])
        df['open'] = df['open'].astype('float32')
        df['high'] = df['high'].astype('float32')
        df['low'] = df['low'].astype('float32')
        df['close'] = df['close'].astype('float32')
        df['volume'] = df['volume'].astype('int32')

        df = df.sort_values('datetime').reset_index(drop=True)

        # OPTIMIZED: Vectorized MA calculation
        df['ma20'] = df['close'].rolling(20).mean().astype('float32')
        df['avg_volume'] = df['volume'].rolling(20).mean().astype('float32')

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

        # OPTIMIZED: Vectorized MA calculations
        df['ma50'] = df['close'].rolling(50).mean().astype('float32')
        df['ma100'] = df['close'].rolling(100).mean().astype('float32')
        df['ma200'] = df['close'].rolling(200).mean().astype('float32')
        df['date'] = df['datetime'].dt.date

        return df[['date', 'ma50', 'ma100', 'ma200']]
    except:
        return None


# ═══════════════════════════════════════════════════════════════
# ULTRA-OPTIMIZED: Bounce Detection (Fully Vectorized)
# ═══════════════════════════════════════════════════════════════

def detect_bounce_ultra_optimized(df, filter_mas):
    """
    ULTRA-OPTIMIZED: Maximum vectorization + early exits
    """
    n = len(df)
    if n < 24:
        return []

    # Extract arrays ONCE
    ma20 = df['ma20'].to_numpy()
    avg_vol = df['avg_volume'].to_numpy()
    vol = df['volume'].to_numpy()
    low = df['low'].to_numpy()
    close_arr = df['close'].to_numpy()
    open_arr = df['open'].to_numpy()
    datetime_arr = df['datetime'].to_numpy()

    # OPTIMIZED: Vectorized pre-filtering
    valid_mask = ~np.isnan(ma20) & (vol >= avg_vol * VOLUME_MULTIPLIER)

    # Pre-compute MA filter mask (vectorized)
    if filter_mas:
        for ma_col in filter_mas:
            if ma_col in df.columns:
                ma_vals = df[ma_col].to_numpy()
                valid_mask &= (close_arr > ma_vals) & ~np.isnan(ma_vals)

    # Find touch points (vectorized)
    touch_mask = (low <= ma20) & valid_mask
    touch_indices = np.where(touch_mask)[0]

    # Filter to valid range [20, n-4)
    touch_indices = touch_indices[(touch_indices >= 20) & (touch_indices < n - 3)]

    signals = []
    used_touches = set()  # Prevent duplicate signals from same touch

    for i in touch_indices:
        if i in used_touches:
            continue
        ma20_at_touch = ma20[i]

        # Check bounce in next 3 candles
        for j in range(i, min(i + 4, n)):
            if close_arr[j] > ma20_at_touch:
                next_idx = j + 1
                if next_idx >= n:
                    break

                signals.append({
                    'datetime': datetime_arr[next_idx],
                    'entry_price': open_arr[next_idx],
                    'ma20': ma20_at_touch,
                    'volume': vol[i],
                    'avg_volume': avg_vol[i]
                })
                used_touches.add(i)
                break

    return signals


# ═══════════════════════════════════════════════════════════════
# OPTIMIZED: Trade Simulation (Vectorized Exit Detection)
# ═══════════════════════════════════════════════════════════════

def simulate_trades_optimized(df, signals, atr_config, nifty_regimes):
    """OPTIMIZED: Vectorized exit detection where possible"""
    if not signals:
        return []

    trades = []

    # Pre-extract arrays
    high_arr = df['high'].to_numpy()
    low_arr = df['low'].to_numpy()
    close_arr = df['close'].to_numpy()
    open_arr = df['open'].to_numpy()
    datetime_arr = df['datetime'].to_numpy()
    atr_arr = df['atr_14'].to_numpy()

    for signal in signals:
        entry_price = signal['entry_price']
        entry_time = signal['datetime']
        entry_idx = df[df['datetime'] == entry_time].index[0]
        entry_date = entry_time.date()

        # Get regime (instant dict lookup)
        regime = nifty_regimes.get(entry_date, 'UNKNOWN')

        entry_atr = atr_arr[entry_idx]
        if np.isnan(entry_atr):
            continue

        stop_price = entry_price - (entry_atr * atr_config['sl_mult'])
        target_price = entry_price + (entry_atr * atr_config['tp_mult'])

        # OPTIMIZED: Vectorized exit check for window
        end_idx = min(entry_idx + 80, len(df))
        window_high = high_arr[entry_idx + 1:end_idx]
        window_low = low_arr[entry_idx + 1:end_idx]
        window_close = close_arr[entry_idx + 1:end_idx]
        window_open = open_arr[entry_idx + 1:end_idx]

        # Check bullish/bearish candles
        bullish = window_close >= window_open

        # Find first SL/Target hit (vectorized)
        sl_hit_bull = bullish & (window_low <= stop_price)
        tp_hit_bull = bullish & (window_high >= target_price)
        tp_hit_bear = ~bullish & (window_high >= target_price)
        sl_hit_bear = ~bullish & (window_low <= stop_price)

        # Combine conditions
        exit_found = False

        # Check bullish candles (SL before target)
        sl_indices_bull = np.where(sl_hit_bull)[0]
        tp_indices_bull = np.where(tp_hit_bull)[0]

        if len(sl_indices_bull) > 0 or len(tp_indices_bull) > 0:
            first_sl_bull = sl_indices_bull[0] if len(sl_indices_bull) > 0 else 999999
            first_tp_bull = tp_indices_bull[0] if len(tp_indices_bull) > 0 else 999999

            if first_sl_bull < first_tp_bull:
                exit_idx = entry_idx + 1 + first_sl_bull
                exit_price = stop_price
                exit_reason = 'SL'
                exit_found = True
            elif first_tp_bull < first_sl_bull:
                exit_idx = entry_idx + 1 + first_tp_bull
                exit_price = target_price
                exit_reason = 'Target'
                exit_found = True
        # Check bearish candles (Target before SL)
        if not exit_found:
            tp_indices_bear = np.where(tp_hit_bear)[0]
            sl_indices_bear = np.where(sl_hit_bear)[0]

            if len(tp_indices_bear) > 0 or len(sl_indices_bear) > 0:
                first_tp_bear = tp_indices_bear[0] if len(tp_indices_bear) > 0 else 999999
                first_sl_bear = sl_indices_bear[0] if len(sl_indices_bear) > 0 else 999999

                if first_tp_bear < first_sl_bear:
                    exit_idx = entry_idx + 1 + first_tp_bear
                    exit_price = target_price
                    exit_reason = 'Target'
                    exit_found = True
                elif first_sl_bear < first_tp_bear:
                    exit_found = True
                elif first_sl_bear < first_tp_bear:
                    exit_idx = entry_idx + 1 + first_sl_bear
                    exit_price = stop_price
                    exit_reason = 'SL'
                    exit_found = True

        # EOD exit if no target/SL hit
        if not exit_found:
            exit_idx = end_idx - 1
            exit_price = close_arr[exit_idx]
            exit_reason = 'EOD'

        exit_time = datetime_arr[exit_idx]
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
            'nifty_regime': regime
        })

    return trades


# ═══════════════════════════════════════════════════════════════
# OPTIMIZED: Backtest Engine (Reduced Redundancy)
# ═══════════════════════════════════════════════════════════════

def backtest_stock_optimized(df, daily_mas, stock_name, nifty_regimes):
    """OPTIMIZED: Pre-compute once, reuse for all filter/ATR combos"""
    if df is None or len(df) == 0:
        return None, 0

    # Merge daily MAs once
    if daily_mas is not None:
        df['date'] = df['datetime'].dt.date
        df = df.merge(daily_mas, on='date', how='left')
    else:
        df['ma50'] = df['ma100'] = df['ma200'] = np.nan

    # Calculate ATR once (vectorized)
    df['prev_close'] = df['close'].shift(1)
    df['true_range'] = np.maximum.reduce([
        df['high'] - df['low'],
        np.abs(df['high'] - df['prev_close']),
        np.abs(df['low'] - df['prev_close'])
    ])
    df['atr_14'] = df['true_range'].rolling(window=14).mean().astype('float32')

    results = {}
    total_trades = 0

    for filter_name, filter_mas in FILTERS.items():
        # Detect signals once per filter
        signals = detect_bounce_ultra_optimized(df, filter_mas)

        for atr_name, atr_config in ATR_CONFIGS.items():
            if len(signals) == 0:
                results[(filter_name, atr_name)] = {
                    'trades': 0,
                    'win_rate': 0,
                    'net_profit': 0,
                    'avg_pnl_pct': 0
                }
                continue

            trades = simulate_trades_optimized(df, signals, atr_config, nifty_regimes)
            wins = sum(1 for t in trades if t['pnl'] > 0)
            num_trades = len(trades)
            total_trades += num_trades
            win_rate = (wins / num_trades * 100) if num_trades > 0 else 0
            net_profit = sum(t['pnl'] for t in trades)
            avg_pnl_pct = np.mean([t['pnl_pct'] for t in trades]) if num_trades > 0 else 0

            results[(filter_name, atr_name)] = {
                'trades': num_trades,
                'win_rate': win_rate,
                'net_profit': net_profit,
                'avg_pnl_pct': avg_pnl_pct
            }

    return results, total_trades


# ═══════════════════════════════════════════════════════════════
# NEW: Parallel Stock Processing
# ═══════════════════════════════════════════════════════════════

def process_single_stock(args):
    """Worker function for parallel processing"""
    stock_name, instrument_key, months, nifty_regimes, stock_idx, total_stocks = args

    try:
        print(f"\n[{stock_idx}/{total_stocks}] {stock_name}...")

        # Fetch all months
        combined_df = []
        for month_start, month_end in months:
            df_month = fetch_upstox_data(instrument_key, month_start, month_end)
            if df_month is not None and len(df_month) > 0:
                combined_df.append(df_month)

        if not combined_df:
            print(f"  ⚠ No data")
            return stock_name, None, 0

        df = pd.concat(combined_df, ignore_index=True)
        daily_mas = fetch_daily_mas(instrument_key, datetime(2025, 12, 31))
        results, total_trades = backtest_stock_optimized(df, daily_mas, stock_name, nifty_regimes)

        if results:
            # Calculate summary stats
            all_trades = sum(r['trades'] for r in results.values())
            all_wins = sum(r['trades'] * r['win_rate'] / 100 for r in results.values())
            overall_win_rate = (all_wins / all_trades * 100) if all_trades > 0 else 0
            net_pnl = sum(r['net_profit'] for r in results.values())
            avg_pnl = np.mean([r['avg_pnl_pct'] for r in results.values() if r['trades'] > 0])

            print(f"  ✓ Done | Trades: {all_trades:,} | Win Rate: {overall_win_rate:5.1f}% | Net P&L: {net_pnl:+10.2f} | Avg: {avg_pnl:+.2f}%")
        else:
            print(f"  ✓ Done | No trades")

        return stock_name, results, total_trades

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return stock_name, None, 0


# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION (Parallelized)
# ═══════════════════════════════════════════════════════════════

def main():
    start_time = datetime.now()
    print("="*70)
    print(" MEGA BACKTEST v1.4.1 ULTRA-OPTIMIZED")
    print("="*70)
    print(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Stocks: {len(STOCKS)} | Period: Jan 2022 - Dec 2025")
    print(f"NEW: Parallel processing + Full vectorization")
    print("="*70)

    # Fetch and calculate Nifty regimes
    print("\nFetching Nifty data for regime calculation...")
    nifty_df = fetch_nifty_daily_data()
    if nifty_df is None:
        print("ERROR: Failed to fetch Nifty data. Exiting.")
        return

    print("Calculating daily regimes (vectorized)...")
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

    # PARALLEL PROCESSING
    print("\n🚀 Processing stocks in parallel (4 workers)...")
    all_results = defaultdict(lambda: defaultdict(list))

    # Prepare work items
    work_items = [
        (stock_name, instrument_key, months, nifty_regimes, idx + 1, len(STOCKS))
        for idx, (stock_name, instrument_key) in enumerate(STOCKS.items())
    ]

    # Process with ThreadPoolExecutor (4 workers for API calls)
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_single_stock, item): item[0] for item in work_items}

        for future in as_completed(futures):
            stock_name, results, total_trades = future.result()

            if results:
                for (filter_name, atr_name), metrics in results.items():
                    all_results[(filter_name, atr_name)][stock_name] = metrics

    # Save results
    print("\n" + "="*70)
    print(" RESULTS SUMMARY")
    print("="*70)

    summary_data = []
    for (filter_name, atr_name), stock_data in all_results.items():
        total_trades = sum(m['trades'] for m in stock_data.values())
        total_profit = sum(m['net_profit'] for m in stock_data.values())
        avg_win_rate = np.mean([m['win_rate'] for m in stock_data.values() if m['trades'] > 0])
        avg_pnl_pct = np.mean([m['avg_pnl_pct'] for m in stock_data.values() if m['trades'] > 0])

        summary_data.append({
            'Filter': filter_name,
            'ATR_Config': atr_name,
            'Total_Trades': total_trades,
            'Avg_Win_Rate': avg_win_rate,
            'Net_Profit': total_profit,
            'Avg_PnL_Pct': avg_pnl_pct
        })

    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv('backtest_v1_4_1_OPTIMIZED_results.csv', index=False)
    print("\n✓ Results saved to: backtest_v1_4_1_OPTIMIZED_results.csv")

    print("\n" + "="*70)
    print(" TOP 10 CONFIGURATIONS BY NET PROFIT")
    print("="*70)
    top10 = summary_df.sort_values('Net_Profit', ascending=False).head(10)
    print(top10.to_string(index=False))

    end_time = datetime.now()
    duration = end_time - start_time
    print("\n" + "="*70)
    print(f" BACKTEST COMPLETE | Duration: {duration}")
    print("="*70)

    # Calculate speedup
    minutes = duration.total_seconds() / 60
    print(f"\n⚡ Performance: {minutes:.1f} minutes (Expected: 5-10 min with optimizations)")
    print("\nOptimizations Applied:")
    print("  ✅ Parallel processing (4 workers)")
    print("  ✅ Vectorized regime calculation")
    print("  ✅ Ultra-optimized bounce detection")
    print("  ✅ Vectorized trade simulation")
    print("  ✅ Memory-efficient data types")


if __name__ == "__main__":
    main()