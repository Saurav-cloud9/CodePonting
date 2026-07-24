"""
Step 5 — year-wise breakdown per bucket, for both the raw ATR% feature and
the memory-encoded (rolling-40-mean) feature. Buckets are fixed using the
FULL 2015-2025 tertile cutoffs (from 03's run), then sliced by year - shows
whether either pattern is stable across years or just an average of noise.
"""
from pathlib import Path

import numpy as np
import pandas as pd

IN_DIR = Path(__file__).resolve().parent
TRADE_LOG = IN_DIR / 'TATAMOTORS_2015-2025_trade_log_with_memory_feature.csv'


def zerodha_short(entry, exit_px):
    brok = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt = entry * 0.00025
    txn = (entry + exit_px) * 0.0000307
    sebi = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def calc_metrics(tdf):
    if len(tdf) == 0:
        return 0, 0.0, 0.0, 0.0
    tdf = tdf.copy()
    tdf['zpnl'] = tdf.apply(lambda r: r['pnl'] - zerodha_short(r['entry'], r['exit_price']), axis=1)
    gp = tdf[tdf['pnl'] > 0]['pnl'].sum()
    gl = -tdf[tdf['pnl'] <= 0]['pnl'].sum()
    zw = tdf[tdf['zpnl'] > 0]['zpnl'].sum()
    zl = -tdf[tdf['zpnl'] <= 0]['zpnl'].sum()
    pf = round(gp / gl, 3) if gl > 0 else 0.0
    zpf = round(zw / zl, 3) if zl > 0 else 0.0
    win_rate = round((tdf['pnl'] > 0).mean() * 100, 1)
    return len(tdf), pf, zpf, win_rate


def yearwise_report(trades, feature, title):
    print(f'\n=== {title} ({feature}) ===')
    trades = trades.copy()
    trades['bucket'], bin_edges = pd.qcut(trades[feature], q=3, labels=['Low', 'Mid', 'High'], retbins=True)
    print(f'Fixed cutoffs (full-sample tertiles): {bin_edges.round(3).tolist()}')
    trades['year'] = trades['entry_dt'].dt.year

    for label in ['Low', 'Mid', 'High']:
        print(f'\n-- {label} bucket --')
        print(f'{"Year":<6} {"N":>5} {"PF":>7} {"ZPF":>7} {"Win rate":>9}')
        sub_bucket = trades[trades['bucket'] == label]
        for yr in sorted(sub_bucket['year'].unique()):
            sub = sub_bucket[sub_bucket['year'] == yr]
            n, pf, zpf, wr = calc_metrics(sub)
            print(f'{yr:<6} {n:>5} {pf:>7} {zpf:>7} {wr:>8}%')


def main():
    trades = pd.read_csv(TRADE_LOG)
    trades.columns = trades.columns.str.strip()
    for col in trades.columns:
        if trades[col].dtype == object:
            trades[col] = trades[col].str.strip()
    trades['entry_dt'] = pd.to_datetime(trades['entry_dt'])
    trades['exit_dt'] = pd.to_datetime(trades['exit_dt'])

    yearwise_report(trades, 'atr_pct_at_touch', 'RAW (no memory encoding)')
    yearwise_report(trades, 'hidden_atr_pct_rollmean40', 'MEMORY-ENCODED (rolling-40-mean)')


if __name__ == '__main__':
    main()
