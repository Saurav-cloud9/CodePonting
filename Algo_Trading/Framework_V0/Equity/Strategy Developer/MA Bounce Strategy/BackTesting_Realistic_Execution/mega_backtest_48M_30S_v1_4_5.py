# mega_backtest_48M_30S_v1_4_5.py

"""
Mega Backtest Script v1.4.5 (FULL COMPLETE VERSION - SLOW & STEADY)
╔═══════════════════════════════════════════════════════════════╗
║   MEGA BACKTEST - 48 Months × 30 F&O Stocks                  ║
║   FEATURES:                                                   ║
║     1. Multiprocessing (4 Workers) - Fast & API Safe          ║
║     2. NO Anti-Chasing Filter (Standard Bounce)               ║
║     3. Batch Processing (Month-by-Month) - Low Memory Usage   ║
║     4. Full Data Collection (CSV + SQLite)                    ║
╚═══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import upstox_client
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import sqlite3
import warnings
from concurrent.futures import ProcessPoolExecutor

# At top of script, extract version from filename
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]  # Gets current script name without extension

warnings.filterwarnings('ignore')

# Prevent PC from sleeping during backtest
os.system("powercfg /change standby-timeout-ac 0")

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# REPLACE THIS WITH YOUR VALID TOKEN
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTdmNTk1NzE0YzgwNzE4ZmViM2FkODQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2OTk1MzYyMywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY5OTgzMjAwfQ.kkO39D0Wl4K7vfqZGd4iM3oiZMfD50eP25jYDJ7LPy4"

# OPTIMIZATION SETTINGS
MAX_WORKERS = 4  # 4 Workers = ~65 req/min (Safe for 2000 req/30min limit)

STOCKS = {
    'TATASTEEL': 'NSE_EQ|INE081A01020', 'HINDALCO': 'NSE_EQ|INE038A01020',
    'JSWSTEEL': 'NSE_EQ|INE019A01038', 'NATIONALUM': 'NSE_EQ|INE139A01034',
    'SBIN': 'NSE_EQ|INE062A01020', 'HDFCBANK': 'NSE_EQ|INE040A01034',
    'ICICIBANK': 'NSE_EQ|INE090A01021', 'AXISBANK': 'NSE_EQ|INE238A01034',
    'PNB': 'NSE_EQ|INE160A01022', 'INDUSINDBK': 'NSE_EQ|INE095A01012',
    'INFY': 'NSE_EQ|INE009A01021', 'WIPRO': 'NSE_EQ|INE075A01022',
    'TECHM': 'NSE_EQ|INE669C01036', 'TATAMOTORS': 'NSE_EQ|INE155A01022',
    'ASHOKLEY': 'NSE_EQ|INE208A01029', 'SUNPHARMA': 'NSE_EQ|INE044A01036',
    'DIVISLAB': 'NSE_EQ|INE361B01024', 'CIPLA': 'NSE_EQ|INE059A01026',
    'RELIANCE': 'NSE_EQ|INE002A01018', 'ONGC': 'NSE_EQ|INE213A01029',
    'COALINDIA': 'NSE_EQ|INE522F01014', 'ITC': 'NSE_EQ|INE154A01025',
    'DABUR': 'NSE_EQ|INE016A01026', 'BHARTIARTL': 'NSE_EQ|INE397D01024',
    'IDEA': 'NSE_EQ|INE669E01016', 'NTPC': 'NSE_EQ|INE733E01010',
    'POWERGRID': 'NSE_EQ|INE752E01010', 'ADANIPORTS': 'NSE_EQ|INE742F01042',
    'VEDL': 'NSE_EQ|INE205A01025', 'BANDHANBNK': 'NSE_EQ|INE545U01014'
}

TARGETS = [0.005, 0.01, 0.015]
STOP_LOSS = 0.005
VOLUME_MULTIPLIER = 1.2

ATR_CONFIGS = {
    'Extreme-1': {'sl_mult': 2.5, 'tp_mult': 4.0},
    'Extreme-2': {'sl_mult': 2.5, 'tp_mult': 4.5},
    'Extreme-3': {'sl_mult': 3.0, 'tp_mult': 4.5},
    'Extreme-4': {'sl_mult': 3.0, 'tp_mult': 5.0}
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

ALL_TRADES_DATA = []
MONTHLY_SUMMARY_DATA = []


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
        if not hasattr(api_response, 'data') or not api_response.data: return None
        candles = api_response.data.candles
        if len(candles) == 0: return None
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
        if not hasattr(api_response, 'data') or not api_response.data: return None
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
# CORE LOGIC
# ═══════════════════════════════════════════════════════════════

def detect_bounce(df, filter_mas):
    """Detects bounces without anti-chasing filter."""
    signals = []
    n = len(df)
    ma20 = df['ma20'].to_numpy()
    avg_vol = df['avg_volume'].to_numpy()
    vol = df['volume'].to_numpy()
    low = df['low'].to_numpy()
    close_arr = df['close'].to_numpy()
    open_arr = df['open'].to_numpy()
    datetime_arr = df['datetime'].to_numpy()

    if filter_mas:
        filter_mask = np.ones(n, dtype=bool)
        for ma_col in filter_mas:
            if ma_col in df.columns:
                ma_vals = df[ma_col].to_numpy()
                filter_mask &= (close_arr > ma_vals) & ~np.isnan(ma_vals)
    else:
        filter_mask = np.ones(n, dtype=bool)

    for i in range(20, n - 3):
        if np.isnan(ma20[i]) or not filter_mask[i]: continue
        if not np.isnan(avg_vol[i]) and vol[i] < avg_vol[i] * VOLUME_MULTIPLIER: continue

        if low[i] <= ma20[i]:
            ma20_at_touch = ma20[i]
            for j in range(i, min(i + 4, n)):
                if close_arr[j] > ma20_at_touch:
                    next_candle_idx = j + 1
                    if next_candle_idx >= n: break

                    signals.append({
                        'datetime': datetime_arr[next_candle_idx],
                        'entry_price': open_arr[next_candle_idx],
                        'ma20': ma20_at_touch,
                        'volume': vol[i],
                        'avg_volume': avg_vol[i]
                    })
                    break
    return signals


def simulate_trades(df, signals, atr_config, stock_name="", filter_name="", atr_name="", month_name=""):
    trades = []
    for signal in signals:
        entry_price = signal['entry_price']
        entry_time = signal['datetime']
        try:
            entry_idx = df.index[df['datetime'] == entry_time][0]
        except:
            continue
        entry_atr = df.loc[entry_idx, 'atr_14']
        if pd.isna(entry_atr): continue
        stop_price = entry_price - (entry_atr * atr_config['sl_mult'])
        target_price = entry_price + (entry_atr * atr_config['tp_mult'])
        exit_price, exit_time, exit_reason, exit_idx = None, None, None, None
        for j in range(entry_idx + 1, min(entry_idx + 80, len(df))):
            candle = df.iloc[j]
            is_bullish = candle['close'] > candle['open']
            if is_bullish:
                if candle['low'] <= stop_price: exit_price, exit_time, exit_reason, exit_idx = stop_price, candle[
                    'datetime'], 'SL', j; break
                if candle['high'] >= target_price: exit_price, exit_time, exit_reason, exit_idx = target_price, candle[
                    'datetime'], 'Target', j; break
            else:
                if candle['high'] >= target_price: exit_price, exit_time, exit_reason, exit_idx = target_price, candle[
                    'datetime'], 'Target', j; break
                if candle['low'] <= stop_price: exit_price, exit_time, exit_reason, exit_idx = stop_price, candle[
                    'datetime'], 'SL', j; break
        if exit_price is None:
            last_idx = min(entry_idx + 79, len(df) - 1)
            exit_price, exit_time, exit_reason, exit_idx = df.iloc[last_idx]['close'], df.iloc[last_idx][
                'datetime'], 'EOD', last_idx
        trades.append({'stock': stock_name, 'month': month_name, 'filter': filter_name, 'atr_config': atr_name,
                       'entry_time': entry_time, 'entry_price': entry_price, 'exit_time': exit_time,
                       'exit_price': exit_price, 'pnl': exit_price - entry_price,
                       'pnl_pct': ((exit_price - entry_price) / entry_price) * 100, 'reason': exit_reason,
                       'candles_held': exit_idx - entry_idx})
    return trades


def categorize_price_vs_mas(df):
    valid_rows = df.dropna(subset=['ma50', 'ma100', 'ma200'])
    if len(valid_rows) == 0: return "INSUFFICIENT DATA"
    last_row = valid_rows.iloc[-1]
    p = last_row['close']
    if p > last_row['ma50'] and p > last_row['ma100'] and p > last_row['ma200']: return "STRONG UPTREND (Above all)"
    if p < last_row['ma50'] and p < last_row['ma100'] and p < last_row['ma200']: return "STRONG DOWNTREND (Below all)"
    if p > last_row['ma50']: return "UPTREND (Above MA50)"
    if p > last_row['ma200']: return "SIDEWAYS (Between MAs)"
    return "DOWNTREND (Below MA200)"


def backtest_stock(df, daily_mas, stock_name, month_name=""):
    if df is None or len(df) == 0: return None
    if daily_mas is not None:
        df['date'] = df['datetime'].dt.date
        df = df.merge(daily_mas, on='date', how='left')
    else:
        df['ma50'] = df['ma100'] = df['ma200'] = np.nan
    df['prev_close'] = df['close'].shift(1)
    df['high_low'] = df['high'] - df['low']
    df['high_prev_close'] = abs(df['high'] - df['prev_close'])
    df['low_prev_close'] = abs(df['low'] - df['prev_close'])
    df['true_range'] = df[['high_low', 'high_prev_close', 'low_prev_close']].max(axis=1)
    df['atr_14'] = df['true_range'].rolling(window=14).mean()
    results, all_trades_log = {}, []
    for filter_name, filter_mas in FILTERS.items():
        for atr_name, atr_config in ATR_CONFIGS.items():
            signals = detect_bounce(df, filter_mas)
            if len(signals) == 0: results[(filter_name, atr_name)] = {'trades': 0, 'win_rate': 0,
                                                                      'net_profit': 0}; continue
            trades = simulate_trades(df, signals, atr_config, stock_name, filter_name, atr_name, month_name)
            all_trades_log.extend(trades)
            wins = sum(1 for t in trades if t['pnl'] > 0)
            results[(filter_name, atr_name)] = {'trades': len(trades),
                                                'win_rate': (wins / len(trades) * 100) if len(trades) > 0 else 0,
                                                'net_profit': sum(t['pnl'] for t in trades)}
    best_combo = max(results.items(), key=lambda x: x[1]['net_profit'])
    best_filter, best_atr_config = best_combo[0]
    best_result = best_combo[1]
    best_signals = detect_bounce(df, FILTERS[best_filter])
    best_trades = simulate_trades(df, best_signals, ATR_CONFIGS[best_atr_config], stock_name, best_filter,
                                  best_atr_config, month_name)
    total_capital = sum(t['entry_price'] for t in best_trades)
    return {'stock': stock_name, 'best_filter': best_filter, 'best_atr_config': best_atr_config,
            'trades': best_result['trades'], 'target_hits': sum(1 for t in best_trades if t['reason'] == 'Target'),
            'sl_hits': sum(1 for t in best_trades if t['reason'] == 'SL'),
            'eod_exits': sum(1 for t in best_trades if t['reason'] == 'EOD'),
            'win_pct': (sum(1 for t in best_trades if t['reason'] == 'Target') / len(best_trades) * 100) if len(
                best_trades) > 0 else 0,
            'protrades_pct': (sum(1 for t in best_trades if t['pnl'] > 0) / len(best_trades) * 100) if len(
                best_trades) > 0 else 0, 'net_profit': best_result['net_profit'], 'total_capital': total_capital,
            'capital_efficiency': (best_result['net_profit'] / total_capital * 100) if total_capital > 0 else 0,
            'price_vs_mas': categorize_price_vs_mas(df), 'all_trades': all_trades_log}


def backtest_worker(args):
    stock, key, from_date, to_date, month_name = args
    df = fetch_upstox_data(key, from_date, to_date)
    mas = fetch_daily_mas(key, to_date)
    result = backtest_stock(df, mas, stock, month_name)
    return result, month_name


# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 22 + "48-MONTH MEGA BACKTEST (BATCH MODE)" + " " * 21 + "║")
    print("║" + " " * 22 + f"{SCRIPT_NAME.upper()}" + " " * (56 - len(SCRIPT_NAME)) + "║")
    print("╚" + "═" * 78 + "╝\n")

    months = []
    current = datetime(2022, 1, 1)
    while current <= datetime(2025, 12, 31):
        first_day = current
        last_day = (datetime(current.year + 1, 1, 1) if current.month == 12 else datetime(current.year,
                                                                                          current.month + 1,
                                                                                          1)) - timedelta(days=1)
        months.append((first_day, last_day, f"{current.strftime('%b').upper()}_{current.year}"))
        current = datetime(current.year + (1 if current.month == 12 else 0), (current.month % 12) + 1, 1)

    print(f"Total Months: {len(months)} | Stocks per Month: {len(STOCKS)}")
    print(f"Workers: {MAX_WORKERS} | Anti-Chasing Filter: DISABLED\n")

    start_time = datetime.now()
    all_top10_stocks = []

    for i, (f, t, month_name) in enumerate(months, 1):
        print(f"[{i:2}/48] {month_name:<12} Processing...", end="\r")
        current_month_tasks = [(stock, key, f, t, month_name) for stock, key in STOCKS.items()]
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = list(executor.map(backtest_worker, current_month_tasks))

        month_results = [r[0] for r in results if r[0] is not None]
        for r in month_results: ALL_TRADES_DATA.extend(r['all_trades'])
        month_results.sort(key=lambda x: x['capital_efficiency'], reverse=True)

        print(f"[{i:2}/48] {month_name:<12} 🏆 TOP 10:")
        print(
            f"  {'Rank':<6} {'Stock':<12} {'Win%':<6} {'Eff%':<6} {'Net₹':<10} {'GE':<20} {'Filter':<12} {'ATR_Config':<12}")
        print("  " + "-" * 100)

        for rank, r in enumerate(month_results[:10], 1):
            ge_str = f"₹{r['net_profit']:.0f}/₹{r['total_capital'] / 1000:.0f}K"
            print(
                f"  {rank:<6} {r['stock']:<12} {r['win_pct']:<6.0f} {r['capital_efficiency']:<6.1f} {r['net_profit']:<10.0f} {ge_str:<20} {r['best_filter']:<12} {r['best_atr_config']:<12}")
            MONTHLY_SUMMARY_DATA.append(
                {'month': month_name, 'rank': rank, 'stock': r['stock'], 'win_pct': r['win_pct'],
                 'efficiency': r['capital_efficiency'], 'net_pnl': r['net_profit'], 'filter': r['best_filter'],
                 'atr_config': r['best_atr_config']})
            all_top10_stocks.append(r['stock'])
        print("")

    elapsed = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 80 + "\nCONSISTENCY REPORT (48 MONTHS)\n" + "=" * 80)
    freq = Counter(all_top10_stocks)
    print(f"\n{'Rank':<6} {'Stock':<15} {'Top 10 Count':<15} {'Consistency %':<15}\n" + "-" * 80)
    for rank, (stock, count) in enumerate(freq.most_common(15), 1):
        print(f"{rank:<6} {stock:<15} {count}/48{' ' * 10} {(count / 48) * 100:.1f}%")
    print(f"\n⏱️  Execution time: {elapsed / 60:.1f} minutes")

    print("\n" + "=" * 70 + "\n SAVING DATA TO CSV & DATABASE\n" + "=" * 70)
    trades_df, monthly_df = pd.DataFrame(ALL_TRADES_DATA), pd.DataFrame(MONTHLY_SUMMARY_DATA)
    if len(trades_df) > 0: trades_df.to_csv(f'{SCRIPT_NAME}_trades.csv', index=False)
    if len(monthly_df) > 0: monthly_df.to_csv(f'{SCRIPT_NAME}_monthly.csv', index=False)

    all_top10_for_consistency = [r['stock'] for r in MONTHLY_SUMMARY_DATA if r['rank'] <= 10]
    stock_freq = Counter(all_top10_for_consistency)
    stock_consistency = [{'stock': s, 'top10_appearances': c, 'consistency_pct': (c / 48) * 100} for s, c in
                         stock_freq.most_common()]
    consistency_df = pd.DataFrame(stock_consistency)
    if len(consistency_df) > 0: consistency_df.to_csv(f'{SCRIPT_NAME}_consistency.csv', index=False)

    conn = sqlite3.connect(f'{SCRIPT_NAME}.db')
    if len(trades_df) > 0: trades_df.to_sql('trades', conn, if_exists='replace', index=False)
    if len(monthly_df) > 0: monthly_df.to_sql('monthly_summary', conn, if_exists='replace', index=False)
    if len(consistency_df) > 0: consistency_df.to_sql('stock_consistency', conn, if_exists='replace', index=False)
    conn.close()
    print("✓ Database Saved (3 tables: trades, monthly_summary, stock_consistency).\nDone.")


if __name__ == "__main__":
    main()