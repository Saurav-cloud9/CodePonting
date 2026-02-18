# mega_backtest_48M_30S_v1_4_5_tatasteel.py

"""
Mega Backtest Script v1.4.5 - TATASTEEL ONLY (PARQUET + WARM-UP FIX)
╔═══════════════════════════════════════════════════════════════╗
║   MEGA BACKTEST - 48 Months × TATASTEEL Only                 ║
║   FEATURES:                                                   ║
║     1. NO Anti-Chasing Filter (Standard Bounce)               ║
║     2. Reads from local TATASTEEL.parquet (no API calls)      ║
║     3. FIXED: Rolling indicators computed on full continuous   ║
║        dataset - no NaN warm-up gap at month boundaries       ║
║     4. Full Data Collection (CSV + SQLite)                    ║
╚═══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import sqlite3
import warnings

# At top of script, extract version from filename
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]  # Gets current script name without extension
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

warnings.filterwarnings('ignore')

# Prevent PC from sleeping during backtest
os.system("powercfg /change standby-timeout-ac 0")

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

PARQUET_FILE = os.path.join(SCRIPT_DIR, 'TATASTEEL.parquet')

TARGETS = [0.005, 0.01, 0.015]
STOP_LOSS = 0.005
VOLUME_MULTIPLIER = 1.2

ATR_CONFIGS = {
    'Extreme-1': {'sl_mult': 2.5, 'tgt_mult': 4.0},
    'Extreme-2': {'sl_mult': 2.5, 'tgt_mult': 4.5},
    'Extreme-3': {'sl_mult': 3.0, 'tgt_mult': 4.5},
    'Extreme-4': {'sl_mult': 3.0, 'tgt_mult': 5.0}
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

ALL_TRADES_DATA = []
MONTHLY_SUMMARY_DATA = []


# ═══════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════

def load_intraday_data():
    """Load full TATASTEEL 5-min intraday data from parquet and compute rolling indicators."""
    df = pd.read_parquet(PARQUET_FILE)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)

    # Compute rolling indicators on the FULL continuous dataset (no NaN warm-up gap at month boundaries)
    df['ma20'] = df['close'].rolling(20).mean()
    df['avg_volume'] = df['volume'].rolling(20).mean()

    # ATR computed on full continuous dataset (same warm-up fix as MA20)
    df['prev_close'] = df['close'].shift(1)
    df['high_low'] = df['high'] - df['low']
    df['high_prev_close'] = abs(df['high'] - df['prev_close'])
    df['low_prev_close'] = abs(df['low'] - df['prev_close'])
    df['true_range'] = df[['high_low', 'high_prev_close', 'low_prev_close']].max(axis=1)
    df['atr_14'] = df['true_range'].rolling(14).mean()

    return df


def compute_daily_mas(df_intraday):
    """Compute daily MAs from the intraday data itself (no API needed)."""
    # Resample to daily OHLCV
    df_intraday['date'] = df_intraday['datetime'].dt.date
    daily = df_intraday.groupby('date').agg(
        open=('open', 'first'),
        high=('high', 'max'),
        low=('low', 'min'),
        close=('close', 'last'),
        volume=('volume', 'sum')
    ).reset_index()

    daily['ma50'] = daily['close'].rolling(50).mean()
    daily['ma100'] = daily['close'].rolling(100).mean()
    daily['ma200'] = daily['close'].rolling(200).mean()

    return daily[['date', 'ma50', 'ma100', 'ma200']]


def get_month_slice(df_full, from_date, to_date):
    """Slice the full dataframe for a specific month. Indicators are already computed."""
    mask = (df_full['datetime'].dt.date >= from_date.date()) & (df_full['datetime'].dt.date <= to_date.date())
    month_df = df_full[mask].copy().reset_index(drop=True)
    return month_df


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

    # FIX: Start from index 0 - indicators are warm because they were computed on the full dataset
    for i in range(0, n - 3):
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

    # Deduplicate by entry time (keep first occurrence)
    seen_times = set()
    unique_signals = []
    for sig in signals:
        if sig['datetime'] not in seen_times:
            unique_signals.append(sig)
            seen_times.add(sig['datetime'])
    return unique_signals


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
        target_price = entry_price + (entry_atr * atr_config['tgt_mult'])
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
        if 'date' not in df.columns:
            df['date'] = df['datetime'].dt.date
        df = df.merge(daily_mas, on='date', how='left')
    else:
        df['ma50'] = df['ma100'] = df['ma200'] = np.nan
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


# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 78)
    print(" " * 10 + "48-MONTH BACKTEST - TATASTEEL ONLY (PARQUET + WARM-UP FIX)")
    print(" " * 10 + f"{SCRIPT_NAME.upper()}")
    print("=" * 78 + "\n")

    # Load full dataset once - rolling indicators computed on continuous data
    print("Loading TATASTEEL.parquet...")
    df_full = load_intraday_data()
    print(f"Loaded {len(df_full)} candles ({df_full['datetime'].min()} to {df_full['datetime'].max()})")

    # Compute daily MAs from the intraday data
    print("Computing daily MAs (MA50/100/200)...")
    daily_mas = compute_daily_mas(df_full)
    print(f"Daily MA data: {len(daily_mas)} trading days\n")

    months = []
    current = datetime(2022, 1, 1)
    while current <= datetime(2025, 12, 31):
        first_day = current
        last_day = (datetime(current.year + 1, 1, 1) if current.month == 12 else datetime(current.year,
                                                                                          current.month + 1,
                                                                                          1)) - timedelta(days=1)
        months.append((first_day, last_day, f"{current.strftime('%b').upper()}_{current.year}"))
        current = datetime(current.year + (1 if current.month == 12 else 0), (current.month % 12) + 1, 1)

    print(f"Total Months: {len(months)} | Stocks: TATASTEEL only")
    print(f"Data Source: {PARQUET_FILE}\n")

    start_time = datetime.now()

    for i, (f, t, month_name) in enumerate(months, 1):
        # Slice the pre-computed full dataframe for this month
        month_df = get_month_slice(df_full, f, t)
        result = backtest_stock(month_df, daily_mas, 'TATASTEEL', month_name)

        if result is not None:
            ALL_TRADES_DATA.extend(result['all_trades'])
            print(f"[{i:2}/48] {month_name:<12} | Filter: {result['best_filter']:<15} | ATR: {result['best_atr_config']:<10} | "
                  f"Trades: {result['trades']:<3} | Win%: {result['win_pct']:<5.0f} | "
                  f"Net: {result['net_profit']:>8.2f} | Eff: {result['capital_efficiency']:.1f}%")
            MONTHLY_SUMMARY_DATA.append(
                {'month': month_name, 'rank': 1, 'stock': 'TATASTEEL', 'win_pct': result['win_pct'],
                 'efficiency': result['capital_efficiency'], 'net_pnl': result['net_profit'],
                 'filter': result['best_filter'], 'atr_config': result['best_atr_config']})
        else:
            print(f"[{i:2}/48] {month_name:<12} | NO DATA / NO TRADES")

    elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 78)
    print("TATASTEEL - 48 MONTH SUMMARY")
    print("=" * 78)

    trades_df = pd.DataFrame(ALL_TRADES_DATA)
    monthly_df = pd.DataFrame(MONTHLY_SUMMARY_DATA)

    if len(trades_df) > 0:
        total_trades = len(trades_df)
        total_wins = len(trades_df[trades_df['pnl'] > 0])
        total_pnl = trades_df['pnl'].sum()
        print(f"\nTotal Trades:  {total_trades}")
        print(f"Total Wins:    {total_wins} ({total_wins/total_trades*100:.1f}%)")
        print(f"Total Losses:  {total_trades - total_wins} ({(total_trades-total_wins)/total_trades*100:.1f}%)")
        print(f"Total PnL:     {total_pnl:.2f}")
        print(f"Avg PnL/Trade: {total_pnl/total_trades:.2f}")

        # Filter breakdown
        print(f"\nFilter Breakdown:")
        for filt in trades_df['filter'].unique():
            f_trades = trades_df[trades_df['filter'] == filt]
            f_wins = len(f_trades[f_trades['pnl'] > 0])
            print(f"  {filt:<20} | Trades: {len(f_trades):<4} | Win%: {f_wins/len(f_trades)*100:5.1f} | PnL: {f_trades['pnl'].sum():>8.2f}")

    if len(trades_df) > 0: trades_df.to_csv(os.path.join(SCRIPT_DIR, f'{SCRIPT_NAME}_trades.csv'), index=False)
    if len(monthly_df) > 0: monthly_df.to_csv(os.path.join(SCRIPT_DIR, f'{SCRIPT_NAME}_monthly.csv'), index=False)

    conn = sqlite3.connect(os.path.join(SCRIPT_DIR, f'{SCRIPT_NAME}.db'))
    if len(trades_df) > 0: trades_df.to_sql('trades', conn, if_exists='replace', index=False)
    if len(monthly_df) > 0: monthly_df.to_sql('monthly_summary', conn, if_exists='replace', index=False)
    conn.close()

    print(f"\nData saved to {SCRIPT_NAME}_trades.csv and {SCRIPT_NAME}.db")
    print(f"Execution time: {elapsed:.1f} seconds")
    print("Done.")


if __name__ == "__main__":
    main()
