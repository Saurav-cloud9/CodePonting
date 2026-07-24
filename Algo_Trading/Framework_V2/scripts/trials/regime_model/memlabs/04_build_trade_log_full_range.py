"""
Step 4a — same pipeline as 01_build_trade_log.py, but full DS3 range
(2015-2025) instead of just 2023, to test whether the raw-ATR% vs
memory-encoded-ATR% pattern found on 2023 alone holds up across years.
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


def load_bars():
    f = DS3_DIR / f'{SYMBOL}.parquet'
    df = pd.read_parquet(f, columns=['datetime', 'open', 'high', 'low', 'close'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].apply(lambda x: x.replace(tzinfo=None))
    for col in ['open', 'high', 'low', 'close']:
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


def main():
    bars = load_bars()
    print(f'Loaded {len(bars):,} total {SYMBOL} bars ({bars["datetime"].min()} to {bars["datetime"].max()}).')

    # --- Run the exact same signal logic used live/offline, over the full history ---
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

    # --- Feature engineering: ATR% and its rolling-40-mean, no lookahead ---
    bars['atr_pct'] = compute_atr_pct(bars)
    bars['atr_pct_rollmean40'] = bars['atr_pct'].rolling(40).mean()

    dt_to_idx = {dt: i for i, dt in enumerate(bars['datetime'])}
    touch_features = []
    for entry_dt in trades_df['entry_dt']:
        idx = dt_to_idx.get(entry_dt)
        if idx is None or idx == 0:
            touch_features.append({'touch_dt': pd.NaT, 'atr_pct_at_touch': None, 'hidden_atr_pct_rollmean40': None})
            continue
        touch_row = bars.iloc[idx - 1]
        touch_features.append({
            'touch_dt': touch_row['datetime'],
            'atr_pct_at_touch': touch_row['atr_pct'],
            'hidden_atr_pct_rollmean40': touch_row['atr_pct_rollmean40'],
        })

    trades_df = pd.concat([trades_df, pd.DataFrame(touch_features)], axis=1)
    trades_df = trades_df.dropna(subset=['hidden_atr_pct_rollmean40']).reset_index(drop=True)

    out_path = OUT_DIR / f'{SYMBOL}_{START_YEAR}-{END_YEAR}_trade_log_with_memory_feature.csv'
    trades_df.to_csv(out_path, index=False)
    print(f'Saved {len(trades_df)} trades with memory-encoded feature to {out_path}')

    gp = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
    gl = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
    pf = gp / gl if gl > 0 else 0.0
    win_rate = (trades_df['pnl'] > 0).mean() * 100
    print(f'N={len(trades_df)}  PF={pf:.3f}  Win rate={win_rate:.1f}%')


if __name__ == '__main__':
    main()
