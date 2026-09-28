"""
54c_10feature_screen.py — full 10-candidate r comparison + max-of-10 multiple-testing
null (iid shuffle), built 2026-09-16 to check whether the notebook's original max-of-2
combined null (dispersion + nifty_trend_10d only) under-corrected for how many of the
10 built candidates actually deserved a "look."

Finding: gap_pct (r=-0.0625) is marginally the single strongest of the 10 — bigger than
dispersion (r=0.0573) — on the common-sample intersection (n=2454, all 10 features non-null).
Neither r was known/screened before this script. Under the max-of-10 iid null (ceil95=
0.0555, ceil99=0.0676), both gap_pct and dispersion individually clear 95th, neither
clears 99th — same qualitative read as the max-of-2 version, so the under-correction
concern didn't end up flipping the verdict. NOT yet combined with the circular-shift
fix (autocorrelation-aware) — that combination (circular-shift AND max-of-10 together)
is stricter than either alone and hasn't been run. gap_pct itself is a brand-new,
unscreened candidate (no individual null-calibration, no theory check) — treat any
promise here as provisional.
"""
import pandas as pd
import numpy as np
from scipy import stats

np.random.seed(42)

trades = pd.read_csv('54c_trade_log.csv', parse_dates=['signal_dt'])
trades['date'] = trades['signal_dt'].dt.date
daily_zpnl = trades.groupby('date')['zpnl'].sum().rename('daily_zpnl')

feat = pd.read_csv('54c_daily_regime_features.csv')
feat['date'] = pd.to_datetime(feat['date']).dt.date
feature_cols = ['gap_pct', 'nifty_trend_5d', 'nifty_trend_10d', 'realized_vol_nifty_10d',
                 'dist_from_ma50_nifty', 'basket_trend_5d', 'basket_trend_10d', 'dispersion',
                 'breadth', 'realized_vol_basket_10d']

merged = feat.merge(daily_zpnl, on='date').dropna(subset=feature_cols + ['daily_zpnl'])
print(f'n days (all 10 features + target non-null): {len(merged)}\n')

X = merged[feature_cols].values
y = merged['daily_zpnl'].values

def pearson_cols(X, y):
    Xc = X - X.mean(axis=0)
    yc = y - y.mean()
    num = (Xc * yc[:, None]).sum(axis=0)
    den = np.sqrt((Xc**2).sum(axis=0) * (yc**2).sum())
    return num / den

real_r = pearson_cols(X, y)
real_max_abs_r = np.abs(real_r).max()
print('Real r per feature (sorted by |r|):')
for f, r in sorted(zip(feature_cols, real_r), key=lambda t: -abs(t[1])):
    print(f'  {f:>25}: {r:+.4f}')
print(f'\nReal best-of-10 |r| = {real_max_abs_r:.4f} (feature: {feature_cols[np.argmax(np.abs(real_r))]})')

N = 5000
max_null = np.empty(N)
y_shuf = y.copy()
for i in range(N):
    np.random.shuffle(y_shuf)
    max_null[i] = np.abs(pearson_cols(X, y_shuf)).max()

ceil95, ceil99 = np.percentile(max_null, [95, 99])
emp_p = (max_null >= real_max_abs_r).mean()
print(f'\niid max-of-10 null (5000 draws): ceil95={ceil95:.4f}, ceil99={ceil99:.4f}, empirical_p={emp_p:.4f}')

disp_r = real_r[feature_cols.index('dispersion')]
print(f'\ndispersion r={disp_r:.4f}: clears95={abs(disp_r)>ceil95}, clears99={abs(disp_r)>ceil99}')
gap_r = real_r[feature_cols.index('gap_pct')]
print(f'gap_pct    r={gap_r:.4f}: clears95={abs(gap_r)>ceil95}, clears99={abs(gap_r)>ceil99}  <- NEW, unscreened before this script')

print('\nNOT YET DONE: circular-shift version of this max-of-10 null (autocorrelation-aware,'
      '\nlikely stricter still). See 54_...baseline.md for next-session resume point.')
