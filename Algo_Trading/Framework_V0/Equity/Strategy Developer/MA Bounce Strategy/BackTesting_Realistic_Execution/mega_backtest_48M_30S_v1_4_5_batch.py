# mega_backtest_48M_30S_v1_4_5_batch.py

"""
Mega Backtest Script v1.4.5 — 30-Stock Batch Runner (PARQUET EDITION)
╔═══════════════════════════════════════════════════════════════╗
║   ORIGINAL v1.4.5 LOGIC — ALL ORIGINAL BUGS PRESERVED        ║
║   API replaced with local .parquet reads                      ║
║   KNOWN ISSUES (intentionally kept):                          ║
║     1. Rolling indicators reset per-month slice               ║
║        (NaN warm-up gap at month boundaries)                  ║
║     2. detect_bounce starts from index 20 (skips warm-up)    ║
║     3. No deduplication of signals                            ║
║     4. EOD: 80-candle max hold, exit at last candle close     ║
║     5. No 14:30 entry cutoff                                  ║
║     6. No cross-month signal guard                            ║
║   Output: v145_30stocks_results.csv                           ║
╚═══════════════════════════════════════════════════════════════╝
"""

import os
import traceback
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))

INTRADAY_DIR      = Path(r'c:\Users\Saurav\CodePonting\Algo_Trading\Framework_V1\data\historical\intraday_5min')
VOLUME_MULTIPLIER = 1.2

ATR_CONFIGS = {
    'Extreme-1': {'sl_mult': 2.5, 'tp_mult': 4.0},
    'Extreme-2': {'sl_mult': 2.5, 'tp_mult': 4.5},
    'Extreme-3': {'sl_mult': 3.0, 'tp_mult': 4.5},
    'Extreme-4': {'sl_mult': 3.0, 'tp_mult': 5.0},
}

# No Filter only — for direct comparison with Framework_V1
FILTERS = {'No Filter': []}


# ═══════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════

def load_full_parquet(parquet_path):
    """Load full intraday dataset. NO rolling indicators here — they are computed
    per-month slice in get_month_slice() to replicate original v1.4.5 behaviour."""
    df = pd.read_parquet(parquet_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)
    # No market-hours filter in original v1.4.5 (API returned clean data)
    # We keep hours filter to remove bad rows but this is neutral
    _t = df['datetime'].dt.time
    df = df[_t.between(pd.Timestamp('09:15').time(), pd.Timestamp('15:30').time())]
    df = df.reset_index(drop=True)
    return df


def compute_daily_mas(df_intraday):
    """Compute daily MAs from intraday data (replaces fetch_daily_mas API call)."""
    df_intraday = df_intraday.copy()
    df_intraday['date'] = df_intraday['datetime'].dt.date
    daily = df_intraday.groupby('date').agg(
        open=('open', 'first'), high=('high', 'max'),
        low=('low', 'min'),    close=('close', 'last'),
        volume=('volume', 'sum')
    ).reset_index()
    daily['ma50']  = daily['close'].rolling(50).mean()
    daily['ma100'] = daily['close'].rolling(100).mean()
    daily['ma200'] = daily['close'].rolling(200).mean()
    return daily[['date', 'ma50', 'ma100', 'ma200']]


def get_month_slice(df_full, from_date, to_date):
    """Slice for the month AND compute ma20/avg_volume on the slice
    — replicating the original v1.4.5 per-month rolling (the warm-up bug)."""
    mask = (
        (df_full['datetime'].dt.date >= from_date.date()) &
        (df_full['datetime'].dt.date <= to_date.date())
    )
    df = df_full[mask].copy().reset_index(drop=True)

    # BUG (original): rolling on slice only → NaN for first 19 candles
    df['ma20']       = df['close'].rolling(20).mean()
    df['avg_volume'] = df['volume'].rolling(20).mean()
    return df


# ═══════════════════════════════════════════════════════════════
# CORE LOGIC  (original v1.4.5 — bugs intact)
# ═══════════════════════════════════════════════════════════════

def detect_bounce(df, filter_mas):
    """Original v1.4.5: starts from index 20, no dedup, no 14:30 cutoff."""
    signals = []
    n            = len(df)
    ma20         = df['ma20'].to_numpy()
    avg_vol      = df['avg_volume'].to_numpy()
    vol          = df['volume'].to_numpy()
    low          = df['low'].to_numpy()
    close_arr    = df['close'].to_numpy()
    open_arr     = df['open'].to_numpy()
    datetime_arr = df['datetime'].to_numpy()

    if filter_mas:
        filter_mask = np.ones(n, dtype=bool)
        for ma_col in filter_mas:
            if ma_col in df.columns:
                ma_vals = df[ma_col].to_numpy()
                filter_mask &= (close_arr > ma_vals) & ~np.isnan(ma_vals)
    else:
        filter_mask = np.ones(n, dtype=bool)

    # BUG (original): starts from 20 to skip NaN warm-up
    for i in range(20, n - 3):
        if np.isnan(ma20[i]) or not filter_mask[i]: continue
        if not np.isnan(avg_vol[i]) and vol[i] < avg_vol[i] * VOLUME_MULTIPLIER: continue

        if low[i] <= ma20[i]:
            ma20_at_touch = ma20[i]
            for j in range(i, min(i + 4, n)):
                if close_arr[j] > ma20_at_touch:
                    next_candle_idx = j + 1
                    if next_candle_idx >= n: break
                    # No 14:30 cutoff in original v1.4.5
                    signals.append({
                        'datetime':    datetime_arr[next_candle_idx],
                        'entry_price': open_arr[next_candle_idx],
                        'ma20':        ma20_at_touch,
                        'volume':      vol[i],
                        'avg_volume':  avg_vol[i],
                    })
                    break
    # No deduplication in original v1.4.5
    return signals


def simulate_trades(df, signals, atr_config, stock_name="", filter_name="", atr_name="", month_name=""):
    """Original v1.4.5: 80-candle max hold, EOD at last-candle close (not open of 15:00 bar)."""
    trades = []
    for signal in signals:
        entry_price = signal['entry_price']
        entry_time  = signal['datetime']
        try:
            entry_idx = df.index[df['datetime'] == entry_time][0]
        except:
            continue

        entry_atr = df.loc[entry_idx, 'atr_14']
        if pd.isna(entry_atr): continue

        stop_price   = entry_price - (entry_atr * atr_config['sl_mult'])
        target_price = entry_price + (entry_atr * atr_config['tp_mult'])
        exit_price, exit_time, exit_reason, exit_idx = None, None, None, None

        # BUG (original): 80-candle hard cap, no same-day EOD logic
        for j in range(entry_idx + 1, min(entry_idx + 80, len(df))):
            candle = df.iloc[j]
            is_bullish = candle['close'] > candle['open']
            if is_bullish:
                if candle['low']  <= stop_price:   exit_price, exit_time, exit_reason, exit_idx = stop_price,   candle['datetime'], 'SL',     j; break
                if candle['high'] >= target_price: exit_price, exit_time, exit_reason, exit_idx = target_price, candle['datetime'], 'Target', j; break
            else:
                if candle['high'] >= target_price: exit_price, exit_time, exit_reason, exit_idx = target_price, candle['datetime'], 'Target', j; break
                if candle['low']  <= stop_price:   exit_price, exit_time, exit_reason, exit_idx = stop_price,   candle['datetime'], 'SL',     j; break

        # BUG (original): if no exit in 80 candles, close at last candle's close price
        if exit_price is None:
            last_idx = min(entry_idx + 79, len(df) - 1)
            exit_price  = df.iloc[last_idx]['close']
            exit_time   = df.iloc[last_idx]['datetime']
            exit_reason = 'EOD'
            exit_idx    = last_idx

        trades.append({
            'stock': stock_name, 'month': month_name,
            'filter': filter_name, 'atr_config': atr_name,
            'entry_time': entry_time, 'entry_price': entry_price,
            'exit_time': exit_time,   'exit_price': exit_price,
            'pnl': exit_price - entry_price,
            'pnl_pct': ((exit_price - entry_price) / entry_price) * 100,
            'reason': exit_reason, 'candles_held': exit_idx - entry_idx,
        })
    return trades


def backtest_stock_month(df, daily_mas, stock_name, month_name):
    """Original v1.4.5: ATR computed on the month slice (warm-up bug)."""
    if df is None or len(df) == 0: return []

    if daily_mas is not None:
        df['date'] = df['datetime'].dt.date
        df = df.merge(daily_mas, on='date', how='left')
    else:
        df['ma50'] = df['ma100'] = df['ma200'] = np.nan

    # BUG (original): ATR computed per-month slice (resets rolling window each month)
    df['prev_close']      = df['close'].shift(1)
    df['high_low']        = df['high'] - df['low']
    df['high_prev_close'] = abs(df['high'] - df['prev_close'])
    df['low_prev_close']  = abs(df['low']  - df['prev_close'])
    df['true_range']      = df[['high_low', 'high_prev_close', 'low_prev_close']].max(axis=1)
    df['atr_14']          = df['true_range'].rolling(window=14).mean()

    all_trades = []
    for filter_name, filter_mas in FILTERS.items():
        for atr_name, atr_config in ATR_CONFIGS.items():
            signals = detect_bounce(df, filter_mas)
            if not signals: continue
            trades  = simulate_trades(df, signals, atr_config, stock_name, filter_name, atr_name, month_name)
            all_trades.extend(trades)
    return all_trades


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("  48-MONTH BACKTEST — ALL STOCKS  [v1.4.5  ORIGINAL LOGIC]")
    print("=" * 70 + "\n")

    stock_files = sorted(f for f in INTRADAY_DIR.glob("*.parquet") if f.stem != "NIFTY50")
    print(f"Found {len(stock_files)} parquet files\n")

    # Build month list (Jan 2022 – Dec 2025)
    months = []
    current = datetime(2022, 1, 1)
    while current <= datetime(2025, 12, 31):
        first_day = current
        last_day  = (datetime(current.year + 1, 1, 1) if current.month == 12
                     else datetime(current.year, current.month + 1, 1)) - timedelta(days=1)
        months.append((first_day, last_day, f"{current.strftime('%b').upper()}_{current.year}"))
        current = datetime(current.year + (1 if current.month == 12 else 0),
                           (current.month % 12) + 1, 1)

    all_results  = []
    errors       = []
    master_trades = []   # accumulates all trades across every stock
    start_time   = datetime.now()

    for stock_path in stock_files:
        stock = stock_path.stem
        print(f"\n{'='*60}")
        print(f"  STOCK: {stock}")
        print(f"{'='*60}")

        try:
            df_full   = load_full_parquet(str(stock_path))
            daily_mas = compute_daily_mas(df_full)

            stock_trades = []
            for f, t, month_name in months:
                month_df = get_month_slice(df_full, f, t)
                trades   = backtest_stock_month(month_df, daily_mas, stock, month_name)
                stock_trades.extend(trades)

            if not stock_trades:
                print(f"  No trades generated.")
                continue

            trades_df = pd.DataFrame(stock_trades)
            master_trades.append(trades_df)

            # Extract No Filter trades per ATR config
            nf = trades_df[trades_df['filter'] == 'No Filter']
            for atr_name in ATR_CONFIGS:
                cfg = nf[nf['atr_config'] == atr_name]
                trade_count = len(cfg)
                if trade_count == 0:
                    all_results.append({
                        'stock': stock, 'config': atr_name,
                        'trade_count': 0, 'win%': 0.0,
                        'protrades%': 0.0, 'total_pnl': 0.0, 'pnl_per_share': 0.0,
                    })
                    print(f"  {atr_name}: 0 trades")
                    continue

                win_pct       = (cfg['reason'] == 'Target').sum() / trade_count * 100
                protrades_pct = (cfg['pnl'] > 0).sum()            / trade_count * 100
                total_pnl     = cfg['pnl'].sum()
                pnl_per_share = total_pnl / trade_count  # pnl is per-share (no qty)

                all_results.append({
                    'stock':         stock,
                    'config':        atr_name,
                    'trade_count':   trade_count,
                    'win%':          round(win_pct,       2),
                    'protrades%':    round(protrades_pct, 2),
                    'total_pnl':     round(total_pnl,     4),
                    'pnl_per_share': round(pnl_per_share, 6),
                })
                print(
                    f"  {atr_name}: {trade_count:4d} trades | "
                    f"Win={win_pct:.1f}% | ProTrades={protrades_pct:.1f}% | "
                    f"PnL={total_pnl:>10.2f} | PnL/share={pnl_per_share:.4f}"
                )

        except Exception as e:
            msg = f"{stock}: {e}"
            print(f"  [ERROR] {msg}")
            errors.append(msg)
            traceback.print_exc()

    # Save summary
    elapsed  = (datetime.now() - start_time).total_seconds()
    out_path = os.path.join(SCRIPT_DIR, 'v145_30stocks_results.csv')
    results_df = pd.DataFrame(all_results, columns=[
        'stock', 'config', 'trade_count', 'win%', 'protrades%', 'total_pnl', 'pnl_per_share'
    ])
    results_df.to_csv(out_path, index=False)

    if master_trades:
        all_trades_df = pd.concat(master_trades, ignore_index=True)
        trades_out = os.path.join(SCRIPT_DIR, 'v145_all_trades.csv')
        all_trades_df.to_csv(trades_out, index=False)
        print(f"  Saved -> {trades_out}  ({len(all_trades_df)} rows)")

    print(f"\n{'='*60}")
    print(f"Saved -> {out_path}  ({len(results_df)} rows)")
    print(f"Elapsed: {elapsed:.1f}s")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
    else:
        print("All stocks processed with no errors.")


if __name__ == "__main__":
    main()
