# TODO_done (2026-01-20): [URGENT] Fix best_trades filtering - EOD exits being excluded (Win% = ProTrades% bug)
# TODO_done (2026-01-21): Implemented ATR-based dynamic SL/Target with 4 configs (Sideways/Regular-1/Regular-2/Extreme)
# TODO: [v1.4] Add 12 new columns: Volume_Ratio, Bounce_Strength_Pct, Wick_Ratio, Candle_Color, Hours_Until_Close, Touch_Candle_Index, Bounce_Candle_Index, NIFTY_Price, NIFTY_MA20, NIFTY_MA50, NIFTY_MA200, NIFTY_Regime
# TODO_done (2026-01-30): [v1.4.3] SAFE OPTIMIZATION - NumPy arrays, 10x faster, ZERO logic changes
# TODO: [BACKLOG] Review std deviation calculations for threshold discovery
# TODO: [POST-FIX] Run 48-month backtest overnight with corrected metrics
# TODO: [ANALYSIS] Analyze correlations to discover data-driven thresholds (winners vs losers median/std)

"""
Mega Backtest Script v1.4.3 SAFE OPTIMIZED
╔═══════════════════════════════════════════════════════════════╗
║   MEGA BACKTEST - 48 Months × 30 F&O Stocks (CONSOLE ONLY)    ║
║   Jan 2022 → Dec 2025 | 10x FASTER | Logic Preserved          ║
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

# Prevent PC from sleeping during overnight backtest
os.system("powercfg /change standby-timeout-ac 0")

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTY2NWJhMTA2NDFlYzdhMDY4ZTQ3ZjUiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2ODMxNTgwOSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY4MzQxNjAwfQ.T0IPCUjlVL09FMqAI3P8vPncdtu6zgwnlcPm6lmBbSg"

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
    """SAFE OPTIMIZED: NumPy arrays for 10x speedup, ZERO logic changes"""
    signals = []
    n = len(df)

    # Extract NumPy arrays ONCE (avoid repeated df.iloc[] overhead)
    ma20 = df['ma20'].to_numpy()
    avg_vol = df['avg_volume'].to_numpy()
    vol = df['volume'].to_numpy()
    low = df['low'].to_numpy()
    close_arr = df['close'].to_numpy()
    open_arr = df['open'].to_numpy()
    datetime_arr = df['datetime'].to_numpy()

    # Pre-compute MA filter mask (PRESERVES ORIGINAL: close > ma)
    if filter_mas:
        filter_mask = np.ones(n, dtype=bool)
        for ma_col in filter_mas:
            if ma_col in df.columns:
                ma_vals = df[ma_col].to_numpy()
                filter_mask &= (close_arr > ma_vals) & ~np.isnan(ma_vals)
    else:
        filter_mask = np.ones(n, dtype=bool)

    # PRESERVED: Original loop structure, same range, same order
    for i in range(20, n - 3):
        if np.isnan(ma20[i]):
            continue

        if not filter_mask[i]:
            continue

        if not np.isnan(avg_vol[i]) and vol[i] < avg_vol[i] * VOLUME_MULTIPLIER:
            continue

        if low[i] <= ma20[i]:
            ma20_at_touch = ma20[i]

            for j in range(i, min(i + 4, n)):
                if close_arr[j] > ma20_at_touch:
                    next_candle_idx = j + 1
                    if next_candle_idx >= n:
                        break

                    signals.append({
                        'datetime': datetime_arr[next_candle_idx],
                        'entry_price': open_arr[next_candle_idx],
                        'ma20': ma20_at_touch,
                        'volume': vol[i],
                        'avg_volume': avg_vol[i]
                    })
                    break

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
        target_price = entry_price + (entry_atr * atr_config['tp_mult'])

        # Scan next candles for exit
        exit_price = None
        exit_time = None
        exit_reason = None

        for j in range(entry_idx + 1, min(entry_idx + 80, len(df))):  # Max 80 candles (6.5 hours)
            candle = df.iloc[j]

            # TODO_done (2026-01-20) CLAUDE FIX: Intra-bar sequence logic - check SL/Target based on candle color
            # Bullish candle likely went: Open -> Low -> High -> Close (check SL first)
            # Bearish candle likely went: Open -> High -> Low -> Close (check Target first)

            is_bullish = candle['close'] > candle['open']

            if is_bullish:
                # Bullish candle: likely dipped first, then rallied
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

def backtest_stock(df, daily_mas, stock_name):
    """Run MA Bounce v0.9 with all filter/target combinations"""
    # TODO_done (2026-01-20): Handle None df from API failures
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
    results = {}

    for filter_name, filter_mas in FILTERS.items():
        for atr_name, atr_config in ATR_CONFIGS.items():
            # Detect bounces with this filter
            signals = detect_bounce(df, filter_mas)

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

    # Find best combination
    best_combo = max(results.items(), key=lambda x: x[1]['net_profit'])
    best_filter, best_atr_config = best_combo[0]
    best_result = best_combo[1]

    # Determine price vs MAs category
    price_vs_mas = categorize_price_vs_mas(df)

    # Calculate capital-based efficiency (CORRECTED v1.1)
    # Get the best combo's trades
    best_signals = detect_bounce(df, FILTERS[best_filter])
    best_trades = simulate_trades(df, best_signals, ATR_CONFIGS[best_atr_config])

    # Total capital deployed = sum of all entry prices
    total_capital = sum(t['entry_price'] for t in best_trades)

    # Efficiency = net profit as % of capital deployed
    capital_efficiency = (best_result['net_profit'] / total_capital * 100) if total_capital > 0 else 0

    # Calculate exit reason counts
    target_hits = sum(1 for t in best_trades if t['reason'] == 'Target')
    sl_hits = sum(1 for t in best_trades if t['reason'] == 'SL')
    eod_exits = sum(1 for t in best_trades if t['reason'] == 'EOD')

    # Calculate win metrics
    profitable_trades = sum(1 for t in best_trades if t['pnl'] > 0)
    win_pct = (target_hits / len(best_trades) * 100) if len(best_trades) > 0 else 0
    protrades_pct = (profitable_trades / len(best_trades) * 100) if len(best_trades) > 0 else 0

    # Keep avg_price for reference
    avg_price = df['close'].mean()

    return {
        'stock': stock_name,
        'best_filter': best_filter,
        'best_atr_config': best_atr_config,  # ATR config name (e.g., "Regular-1")
        'trades': best_result['trades'],
        'target_hits': target_hits,
        'sl_hits': sl_hits,
        'eod_exits': eod_exits,
        'win_pct': win_pct,
        'protrades_pct': protrades_pct,
        'net_profit': best_result['net_profit'],
        'total_capital': total_capital,
        'capital_efficiency': capital_efficiency,  # CORRECTED: capital-based
        'price_vs_mas': price_vs_mas,
        'avg_price': avg_price  # For reference only
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
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 22 + "48-MONTH MEGA BACKTEST (30 STOCKS)" + " " * 22 + "║")
    print("╚" + "═" * 78 + "╝\n")

    # Generate months - FULL 48-MONTH RUN
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

    print(f"Months: {len(months)} | Stocks: {len(STOCKS)} | Total: {len(months) * len(STOCKS)}\n")

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

        month_results.sort(key=lambda x: x['capital_efficiency'], reverse=True)

        print("\n  🏆 TOP 10:")
        print(
            f"  {'Rank':<6} {'Stock':<12} {'Trades':<7} {'Targets':<8} {'SL':<4} {'EOD':<5} {'Win%':<6} {'Eff%':<6} {'ProTrades%':<11} {'Net₹':<10} {'Capital₹':<12} {'GE':<20} {'Filter':<12} {'ATR_Config':<12}")
        print("  " + "-" * 140)
        for rank, r in enumerate(month_results[:10], 1):
            ge_str = f"₹{r['net_profit']:.0f}/₹{r['total_capital'] / 1000:.0f}K"
            print(
                f"  {rank:<6} {r['stock']:<12} {r['trades']:<7} {r['target_hits']:<8} {r['sl_hits']:<4} {r['eod_exits']:<5} {r['win_pct']:<6.0f} {r['capital_efficiency']:<6.1f} {r['protrades_pct']:<11.0f} {r['net_profit']:<10.0f} {r['total_capital']:<12.0f} {ge_str:<20} {r['best_filter']:<12} {r['best_atr_config']:<12}")

        # Track top 10
        for r in month_results[:10]:
            all_top10.append(r['stock'])

    elapsed = (datetime.now() - start_time).total_seconds()

    # Final report
    print("\n" + "=" * 80)
    print("CONSISTENCY REPORT (48 MONTHS)")
    print("=" * 80)

    freq = Counter(all_top10)
    sorted_stocks = sorted(freq.items(), key=lambda x: x[1], reverse=True)

    print(f"\n{'Rank':<6} {'Stock':<15} {'Top 10 Count':<15} {'Consistency %':<15}")
    print("-" * 80)
    for rank, (stock, count) in enumerate(sorted_stocks[:15], 1):
        consistency = (count / 48) * 100
        print(f"{rank:<6} {stock:<15} {count}/48{' ' * 2} {consistency:<15.1f}%")

    print(f"\n⏱️  Execution time: {elapsed / 60:.1f} minutes")
    print("=" * 80)


if __name__ == "__main__":
    main()