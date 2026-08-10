"""
Add atr14_wilder column to all DS3 parquets, and re-fix atr14 (simple) using
strict TR alongside it.

DS3 currently has: datetime, open, high, low, close, volume, oi, ma20, atr14 (simple)
This adds atr14_wilder (Wilder RMA smoothing, period=14) computed fresh on the
current DS3 data (post DIVISLAB/INFY fixes, full 2015-2026 range).

Also recomputes atr14 fresh via strict rolling-mean on the same TR array.
2 boundary rows (DIVISLAB file start, INFY post-gap resume) had atr14 valid
1 bar too early — traced to a NaN-tolerant max used at those specific
no-prev-close bars in an earlier one-off recompute, producing a technically
valid but not-a-true-TR number there. Strict TR (bar-0/post-gap = NaN)
matches the other 28 stocks and the documented convention below, so this
recompute is a no-op for them and only corrects those 2 boundary spots.

Formula matches scripts/trials/ATR_exploration/atr_formula_exploration.py's
validated wilder_atr() — TR bar-0 = NaN, seed = simple mean of first 14 valid TR,
then RMA: ATR_t = (ATR_{t-1}*(N-1) + TR_t) / N.

Writes back to the same DS3 parquet files (local, source of truth). VM sync is
a separate manual step (confirm diff first, per CLAUDE.md sync rule).
"""
import glob
import os

import numpy as np
import pandas as pd

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3'
PERIOD = 14


def true_range(high, low, close):
    n = len(close)
    tr = np.full(n, np.nan)
    if n < 2:
        return tr
    pc = close[:-1]
    h, l = high[1:], low[1:]
    tr[1:] = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    return tr


def simple_atr(tr, period):
    """Strict rolling mean — pandas requires all `period` window rows
    non-null when min_periods=period, so this naturally NaNs any window
    touching a gap, same requirement as wilder_atr's reseed condition."""
    return pd.Series(tr).rolling(period, min_periods=period).mean().to_numpy()


def wilder_atr(tr, period):
    """
    Wilder RMA, re-seeding after any NaN gap (e.g. corrupted-data windows
    NaN'd out mid-series). A plain recursive carry-forward would go NaN at
    the first gap and stay NaN for the rest of the file — rolling mean
    self-heals after a gap, Wilder's doesn't unless re-seeded explicitly.
    """
    n = len(tr)
    atr = np.full(n, np.nan)
    i = 0
    while i < n:
        if np.isnan(atr[i - 1]) if i > 0 else True:
            # not currently primed — look for the next run of `period`
            # consecutive valid TR values starting at or after i to reseed
            if np.isnan(tr[i]):
                i += 1
                continue
            run_start = i
            j = i
            while j < n and not np.isnan(tr[j]) and (j - run_start) < period:
                j += 1
            if (j - run_start) < period:
                # not enough consecutive valid bars here to seed; advance
                # past this broken run and keep scanning
                i = j + 1
                continue
            seed_end = j - 1
            atr[seed_end] = float(np.mean(tr[run_start:j]))
            i = seed_end + 1
            continue
        if np.isnan(tr[i]):
            atr[i] = np.nan
        else:
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        i += 1
    return atr


def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet')))
    print(f'Adding atr14_wilder to {len(files)} DS3 parquets...')
    for path in files:
        symbol = os.path.basename(path).replace('.parquet', '')
        df = pd.read_parquet(path)
        high = df['high'].values.astype(float)
        low = df['low'].values.astype(float)
        close = df['close'].values.astype(float)
        tr = true_range(high, low, close)

        old_atr14 = df['atr14'].to_numpy(dtype=float)
        new_atr14 = simple_atr(tr, PERIOD)
        both_valid = ~np.isnan(old_atr14) & ~np.isnan(new_atr14)
        n_changed = int(np.sum(~np.isclose(old_atr14[both_valid], new_atr14[both_valid])))
        n_newly_nan = int(np.sum(~np.isnan(old_atr14) & np.isnan(new_atr14)))
        n_newly_valid = int(np.sum(np.isnan(old_atr14) & ~np.isnan(new_atr14)))
        df['atr14'] = new_atr14
        df['atr14_wilder'] = wilder_atr(tr, PERIOD)
        df.to_parquet(path, index=False)

        n_nan_simple = df['atr14'].isna().sum()
        n_nan_wilder = df['atr14_wilder'].isna().sum()
        flag = 'OK' if n_nan_simple == n_nan_wilder else 'MISMATCH IN NaN COUNT'
        diff_note = ''
        if n_changed or n_newly_nan or n_newly_valid:
            diff_note = (f'  [atr14 fix: {n_newly_nan} newly-NaN, '
                         f'{n_newly_valid} newly-valid, {n_changed} value-changed]')
        print(f'  {symbol:15s}  rows={len(df):,}  atr14 NaN={n_nan_simple:,}  '
              f'atr14_wilder NaN={n_nan_wilder:,}  {flag}{diff_note}')
    print('Done.')


if __name__ == '__main__':
    main()
