"""
Step 1 (foundation) — MemLabs memory-encoding experiment on MA rejection SHORT.
Builds TATAMOTORS' 2023 trade log using the exact same signal logic as the
live/offline Kite bot (ma_rejection_v1_core.py), then attaches a memory-encoded
feature to each trade: the rolling-40-mean of ATR% at the trade's touch bar
(the bar immediately before entry, where the touch condition actually fired).

No lookahead: the rolling window only ever looks at bars up to and including
the touch bar itself, never anything after.
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
YEAR = 2023
WARMUP_DAYS = 30  # extra calendar days of prior data so MA20/ATR14 are ready by Jan 1


def zerodha_short(entry, exit_px):
    """Same formula as baseline_reserve_lock/ma_30_rejection.py's zerodha_short()
    - per-trade Zerodha intraday SHORT charges (brokerage/STT/txn/SEBI/stamp/GST)."""
    brok = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt = entry * 0.00025
    txn = (entry + exit_px) * 0.0000307
    sebi = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def calc_metrics(trades_df):
    if len(trades_df) == 0:
        return 0, 0.0, 0.0, 0.0
    tdf = trades_df.copy()
    tdf['zpnl'] = tdf.apply(lambda r: r['pnl'] - zerodha_short(r['entry'], r['exit_price']), axis=1)
    gp = tdf[tdf['pnl'] > 0]['pnl'].sum()
    gl = -tdf[tdf['pnl'] <= 0]['pnl'].sum()
    zw = tdf[tdf['zpnl'] > 0]['zpnl'].sum()
    zl = -tdf[tdf['zpnl'] <= 0]['zpnl'].sum()
    pf = round(gp / gl, 3) if gl > 0 else 0.0
    zpf = round(zw / zl, 3) if zl > 0 else 0.0
    daily = tdf.set_index(pd.to_datetime(tdf['exit_dt']).dt.date)['zpnl'].groupby(level=0).sum()
    daily = daily[daily != 0]
    zshd = round((daily.mean() / daily.std()) * np.sqrt(252), 3) if len(daily) > 1 else 0.0
    return len(tdf), pf, zpf, zshd


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
    """ATR14 as a % of close, computed via pandas directly on the full bar
    series (independent of the core module's deque - just for feature
    engineering, not signal logic)."""
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

    warmup_start = pd.Timestamp(YEAR, 1, 1) - pd.Timedelta(days=WARMUP_DAYS)
    year_end = pd.Timestamp(YEAR + 1, 1, 1)
    bars_slice = bars[(bars['datetime'] >= warmup_start) & (bars['datetime'] < year_end)].reset_index(drop=True)
    print(f'Loaded {len(bars):,} total {SYMBOL} bars; using {len(bars_slice):,} bars '
          f'from {warmup_start.date()} (warm-up) through {YEAR}-12-31.')

    # --- Run the exact same signal logic used live/offline ---
    state = StockState()
    trades = []
    for bar in bars_slice.to_dict('records'):
        process_bar(SYMBOL, bar, state, trades)
    trades_df = pd.DataFrame(trades)

    # Keep only trades whose entry actually falls within the target year
    # (warm-up period exists purely to seed indicators, not to be traded)
    trades_df['entry_dt'] = pd.to_datetime(trades_df['entry_dt'])
    trades_df = trades_df[trades_df['entry_dt'].dt.year == YEAR].reset_index(drop=True)
    print(f'{len(trades_df)} trades in {YEAR}.')

    # --- Feature engineering: ATR% and its rolling-40-mean, no lookahead ---
    bars_slice['atr_pct'] = compute_atr_pct(bars_slice)
    bars_slice['atr_pct_rollmean40'] = bars_slice['atr_pct'].rolling(40).mean()

    # For each trade, the touch bar is the row immediately before entry_dt
    # (found positionally, not by a fixed time delta, to be safe against gaps)
    dt_to_idx = {dt: i for i, dt in enumerate(bars_slice['datetime'])}
    touch_features = []
    for entry_dt in trades_df['entry_dt']:
        idx = dt_to_idx.get(entry_dt)
        if idx is None or idx == 0:
            touch_features.append({'touch_dt': pd.NaT, 'atr_pct_at_touch': None, 'hidden_atr_pct_rollmean40': None})
            continue
        touch_row = bars_slice.iloc[idx - 1]
        touch_features.append({
            'touch_dt': touch_row['datetime'],
            'atr_pct_at_touch': touch_row['atr_pct'],
            'hidden_atr_pct_rollmean40': touch_row['atr_pct_rollmean40'],
        })

    trades_df = pd.concat([trades_df, pd.DataFrame(touch_features)], axis=1)

    out_path = OUT_DIR / f'{SYMBOL}_{YEAR}_trade_log_with_memory_feature.csv'
    trades_df.to_csv(out_path, index=False)
    print(f'Saved {len(trades_df)} trades with memory-encoded feature to {out_path}')

    n, pf, zpf, zshd = calc_metrics(trades_df)
    win_rate = (trades_df['pnl'] > 0).mean() * 100
    print(f'N={n}  PF={pf}  ZPF={zpf}  ZSh(D)={zshd}  Win rate={win_rate:.1f}%')
    print(f'Rows missing the hidden feature (indicator not warmed up yet): '
          f'{trades_df["hidden_atr_pct_rollmean40"].isna().sum()}')


if __name__ == '__main__':
    main()
