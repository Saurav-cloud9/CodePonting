"""
Step 17 - same as step 16 (correlation check, no model), but every feature is
now smoothed the same way: compute the raw indicator per-bar, then take a
40-bar rolling mean of THAT series before sampling at the touch bar - matching
the existing atr_pct_rollmean40 convention consistently across all 6 candidates
(step 16 mixed rolling-mean ATR% with raw un-smoothed snapshots for the rest).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KITE_BOT_SCRIPTS = Path(r'C:\Users\Saurav\CodePonting\Algo_Trading\kite_oracle_papertrading\scripts')
sys.path.insert(0, str(KITE_BOT_SCRIPTS))
from ma_rejection_v1_core import StockState, process_bar  # noqa: E402

DS3_DIR = Path(r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3')
OUT_DIR = Path(__file__).resolve().parent

SYMBOL = 'TATAMOTORS'
START_YEAR = 2015
END_YEAR = 2025
SMOOTH_WINDOW = 40


def load_bars():
    f = DS3_DIR / f'{SYMBOL}.parquet'
    df = pd.read_parquet(f, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].apply(lambda x: x.replace(tzinfo=None))
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df.sort_values('datetime', inplace=True, kind='mergesort')
    df.reset_index(drop=True, inplace=True)
    return df


def compute_atr_pct(bars, period=14):
    high, low, close = bars['high'], bars['low'], bars['close']
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return (atr / close) * 100


def compute_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_macd_pct(close, fast=12, slow=26):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    return (ema_fast - ema_slow) / close * 100


def wma(series, n):
    weights = np.arange(1, n + 1)
    return series.rolling(n).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def compute_hma(close, n=100):
    half = wma(close, n // 2)
    full = wma(close, n)
    raw_hma = 2 * half - full
    return wma(raw_hma, int(np.sqrt(n)))


def compute_vwap(bars):
    typical = (bars['high'] + bars['low'] + bars['close']) / 3
    tp_vol = typical * bars['volume']
    cum_tp_vol = tp_vol.groupby(bars['date']).cumsum()
    cum_vol = bars['volume'].groupby(bars['date']).cumsum()
    return cum_tp_vol / cum_vol


def main():
    bars = load_bars()
    print(f'Loaded {len(bars):,} total {SYMBOL} bars ({bars["datetime"].min()} to {bars["datetime"].max()}).')

    state = StockState()
    trades = []
    for bar in bars.to_dict('records'):
        process_bar(SYMBOL, bar, state, trades)
    trades_df = pd.DataFrame(trades)
    trades_df['entry_dt'] = pd.to_datetime(trades_df['entry_dt'])
    trades_df = trades_df[
        (trades_df['entry_dt'].dt.year >= START_YEAR) & (trades_df['entry_dt'].dt.year <= END_YEAR)
    ].reset_index(drop=True)
    print(f'{len(trades_df)} trades from {START_YEAR}-{END_YEAR}.')

    # --- Raw indicators, computed per-bar, no lookahead ---
    bars['atr_pct'] = compute_atr_pct(bars)
    bars['rsi14'] = compute_rsi(bars['close'])
    bars['macd_pct'] = compute_macd_pct(bars['close'])
    ema100 = bars['close'].ewm(span=100, adjust=False).mean()
    bars['ema100_rel_pos'] = (bars['close'] - ema100) / ema100 * 100
    hma100 = compute_hma(bars['close'], 100)
    bars['hma100_rel_pos'] = (bars['close'] - hma100) / hma100 * 100
    vwap = compute_vwap(bars)
    bars['vwap_rel_pos'] = (bars['close'] - vwap) / vwap * 100

    raw_cols = ['atr_pct', 'rsi14', 'macd_pct', 'ema100_rel_pos', 'hma100_rel_pos', 'vwap_rel_pos']
    smoothed_cols = []
    for col in raw_cols:
        smoothed_name = f'{col}_rollmean{SMOOTH_WINDOW}'
        bars[smoothed_name] = bars[col].rolling(SMOOTH_WINDOW).mean()
        smoothed_cols.append(smoothed_name)

    dt_to_idx = {dt: i for i, dt in enumerate(bars['datetime'])}
    touch_features = []
    for entry_dt in trades_df['entry_dt']:
        idx = dt_to_idx.get(entry_dt)
        if idx is None or idx == 0:
            touch_features.append({c: None for c in smoothed_cols})
            continue
        touch_row = bars.iloc[idx - 1]
        touch_features.append({c: touch_row[c] for c in smoothed_cols})

    trades_df = pd.concat([trades_df, pd.DataFrame(touch_features)], axis=1)
    trades_df = trades_df.dropna(subset=smoothed_cols).reset_index(drop=True)
    print(f'{len(trades_df)} trades with all 6 smoothed features available.\n')

    trades_df['win'] = (trades_df['pnl'] > 0).astype(int)

    out_path = OUT_DIR / f'{SYMBOL}_{START_YEAR}-{END_YEAR}_smoothed_features_correlation_check.csv'
    trades_df.to_csv(out_path, index=False)
    print(f'Saved full feature trade log to {out_path}\n')

    print(f'{"Feature (40-bar smoothed)":>30} {"r vs PnL":>10} {"r vs win/loss":>14}')
    for col in smoothed_cols:
        r_pnl = trades_df[col].corr(trades_df['pnl'])
        r_win = trades_df[col].corr(trades_df['win'])
        print(f'{col:>30} {r_pnl:>10.4f} {r_win:>14.4f}')


if __name__ == '__main__':
    main()
