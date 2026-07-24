"""
Step 2 — MemLabs memory-encoding experiment on MA rejection SHORT.
Buckets the trade log (from 01_build_trade_log.py) into tertiles by the
memory-encoded feature (rolling-40-mean of ATR% at touch) and compares
win rate / PF / ZPF per bucket - same spirit as the SL/TGT sweep tables,
just sweeping across the feature's value range instead of strategy params.
"""
from pathlib import Path

import numpy as np
import pandas as pd

IN_DIR = Path(__file__).resolve().parent
TRADE_LOG = IN_DIR / 'TATAMOTORS_2023_trade_log_with_memory_feature.csv'


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


def main():
    trades = pd.read_csv(TRADE_LOG)
    trades.columns = trades.columns.str.strip()
    for col in trades.columns:
        if trades[col].dtype == object:
            trades[col] = trades[col].str.strip()
    trades['entry_dt'] = pd.to_datetime(trades['entry_dt'])
    trades['exit_dt'] = pd.to_datetime(trades['exit_dt'])

    feature = 'hidden_atr_pct_rollmean40'
    trades['bucket'] = pd.qcut(trades[feature], q=3, labels=['Low vol', 'Mid vol', 'High vol'])

    print(f'Overall (all {len(trades)} trades):')
    n, pf, zpf, zshd, wr = calc_metrics(trades)
    print(f'  N={n}  PF={pf}  ZPF={zpf}  ZSh(D)={zshd}  Win rate={wr}%\n')

    print(f'{"Bucket":<10} {"N":>5} {"Feature range":>22} {"PF":>7} {"ZPF":>7} {"ZSh(D)":>8} {"Win rate":>9}')
    for label in ['Low vol', 'Mid vol', 'High vol']:
        sub = trades[trades['bucket'] == label]
        n, pf, zpf, zshd, wr = calc_metrics(sub)
        lo, hi = sub[feature].min(), sub[feature].max()
        print(f'{label:<10} {n:>5} {f"{lo:.3f}-{hi:.3f}":>22} {pf:>7} {zpf:>7} {zshd:>8} {wr:>8}%')

    out_path = IN_DIR / 'TATAMOTORS_2023_bucketed_by_memory_feature.csv'
    trades.to_csv(out_path, index=False)
    print(f'\nSaved bucketed trade log to {out_path}')


if __name__ == '__main__':
    main()
