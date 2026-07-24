"""
Step 3 — direct comparison: does memory encoding (rolling-40-mean of ATR%)
add value over just using the raw, instantaneous ATR% at touch? Buckets the
same 316 trades by BOTH features independently and compares the spread.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

IN_DIR = Path(__file__).resolve().parent
TRADE_LOG = IN_DIR / (sys.argv[1] if len(sys.argv) > 1 else 'TATAMOTORS_2023_trade_log_with_memory_feature.csv')


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
        return 0, 0.0, 0.0, 0.0, 0.0
    tdf = tdf.copy()
    tdf['zpnl'] = tdf.apply(lambda r: r['pnl'] - zerodha_short(r['entry'], r['exit_price']), axis=1)
    gp = tdf[tdf['pnl'] > 0]['pnl'].sum()
    gl = -tdf[tdf['pnl'] <= 0]['pnl'].sum()
    zw = tdf[tdf['zpnl'] > 0]['zpnl'].sum()
    zl = -tdf[tdf['zpnl'] <= 0]['zpnl'].sum()
    pf = round(gp / gl, 3) if gl > 0 else 0.0
    zpf = round(zw / zl, 3) if zl > 0 else 0.0
    win_rate = round((tdf['pnl'] > 0).mean() * 100, 1)
    daily = tdf.set_index(pd.to_datetime(tdf['exit_dt']).dt.date)['zpnl'].groupby(level=0).sum()
    daily = daily[daily != 0]
    zshd = round((daily.mean() / daily.std()) * np.sqrt(252), 3) if len(daily) > 1 else 0.0
    return len(tdf), pf, zpf, zshd, win_rate


def bucket_report(trades, feature, title):
    print(f'--- {title} ({feature}) ---')
    trades = trades.copy()
    trades['bucket'] = pd.qcut(trades[feature], q=3, labels=['Low', 'Mid', 'High'])
    print(f'{"Bucket":<6} {"N":>5} {"Feature range":>20} {"PF":>7} {"ZPF":>7} {"ZSh(D)":>8} {"Win rate":>9}')
    zpf_spread = []
    for label in ['Low', 'Mid', 'High']:
        sub = trades[trades['bucket'] == label]
        n, pf, zpf, zshd, wr = calc_metrics(sub)
        zpf_spread.append(zpf)
        lo, hi = sub[feature].min(), sub[feature].max()
        print(f'{label:<6} {n:>5} {f"{lo:.3f}-{hi:.3f}":>20} {pf:>7} {zpf:>7} {zshd:>8} {wr:>8}%')
    spread = max(zpf_spread) - min(zpf_spread)
    print(f'ZPF spread (High-Low bucket range): {spread:.3f}\n')
    return spread


def main():
    trades = pd.read_csv(TRADE_LOG)
    trades.columns = trades.columns.str.strip()
    for col in trades.columns:
        if trades[col].dtype == object:
            trades[col] = trades[col].str.strip()
    trades['entry_dt'] = pd.to_datetime(trades['entry_dt'])
    trades['exit_dt'] = pd.to_datetime(trades['exit_dt'])

    spread_raw = bucket_report(trades, 'atr_pct_at_touch', 'RAW (no memory encoding)')
    spread_mem = bucket_report(trades, 'hidden_atr_pct_rollmean40', 'MEMORY-ENCODED (rolling-40-mean)')

    print(f'Raw ATR% ZPF spread:            {spread_raw:.3f}')
    print(f'Memory-encoded ATR% ZPF spread: {spread_mem:.3f}')
    if spread_mem > spread_raw:
        print('=> Memory encoding produces a STRONGER regime split than raw ATR% alone.')
    else:
        print('=> Raw ATR% alone produces an equal or stronger split - memory encoding adds no extra value here.')


if __name__ == '__main__':
    main()
