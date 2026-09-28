"""
54d_xor_flags_top4.py — the true XOR-shaped test (as opposed to the AND-rule quadrant
tests in 54d_xor_top4.ipynb): for each of the 6 top-4-feature pairs, build one
xor_flag = (feature_x > median) != (feature_y > median) -- true when exactly one of
the two is high (merges the high-low + low-high quadrants into one group, high-high +
low-low into the other) -- then test each pair's xor_flag r against its own circular-
shift ceiling and a max-of-6 correction across the 6 XOR-flags.

Result: 0 of 6 pairs clear their own ceiling except dispersion x volume_surge (own 95th
only, not 99th, and fails max-of-6 regardless). Consistent with every other angle on
these 4 features -- no XOR-shaped interaction found either.
"""
import pandas as pd
import numpy as np
from itertools import combinations

trades = pd.read_csv('54c_trade_log_with_features.csv', parse_dates=['signal_dt'])
trades['date'] = trades['signal_dt'].dt.date
TOP4 = ['dispersion', 'gap_pct', 'india_vix_level', 'volume_surge']
daily = trades.groupby('date').agg(
    daily_zpnl=('zpnl', 'sum'),
    **{f: (f, 'first') for f in TOP4}
).reset_index().dropna(subset=TOP4 + ['daily_zpnl']).reset_index(drop=True)

medians = {f: daily[f].median() for f in TOP4}
y = daily['daily_zpnl'].values.astype(float)
n = len(y)
PAIRS = list(combinations(TOP4, 2))

def circular_null(flag, y):
    null_r = np.empty(n - 1)
    for shift in range(1, n):
        null_r[shift - 1] = np.corrcoef(flag, np.roll(y, shift))[0, 1]
    return null_r

xor_flags = {}
results = []
for fx, fy in PAIRS:
    xflag = ((daily[fx] > medians[fx]) != (daily[fy] > medians[fy])).astype(int).values
    xor_flags[(fx, fy)] = xflag
    r = np.corrcoef(xflag, y)[0, 1]
    null_own = circular_null(xflag, y)
    c95, c99 = np.percentile(np.abs(null_own), [95, 99])
    results.append(dict(pair=f'{fx} XOR {fy}', r=round(r, 4), n_xor_true=int(xflag.sum()),
                         clears_own_95=abs(r) > c95, clears_own_99=abs(r) > c99))

df = pd.DataFrame(results)

max6_null = np.empty(n - 1)
mat = np.array([xor_flags[p] for p in PAIRS])
for shift in range(1, n):
    y_shift = np.roll(y, shift)
    rs = np.abs([np.corrcoef(mat[i], y_shift)[0, 1] for i in range(len(PAIRS))])
    max6_null[shift - 1] = rs.max()
c95_6, c99_6 = np.percentile(max6_null, [95, 99])
df['clears_max6_95'] = df['r'].abs() > c95_6
df['clears_max6_99'] = df['r'].abs() > c99_6

print(f'max-of-6 (XOR flags): ceil95={c95_6:.4f} ceil99={c99_6:.4f}\n')
print(df.to_string(index=False))
