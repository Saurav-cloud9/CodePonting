import json

def md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)}

def code(src):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": src.splitlines(keepends=True)}

cells = []

cells.append(md("""# Step 54d (extension) — Top-4 pairwise XOR/interaction check

Top 4 candidates by |r| (dispersion, gap_pct, india_vix_level, volume_surge) — all 4
already individually RULED OUT under the max-of-12 circular-shift test (see
`54c_screen.ipynb` §6, `54d_screen_round2.ipynb` §7). Run anyway, at Saurav's explicit
request, purely to see the actual visual evidence firsthand — not because the
prerequisite for escalation (individual promise) was met; it wasn't.

6 pairs = C(4,2). Each pair's combined AND-rule (median-split both, require both
high) tested against its own circular-shift null AND a max-of-6 ceiling (correcting
for testing 6 pair-candidates, not just 1) — per the discipline established for the
individual-feature screen, applied one level up."""))

cells.append(code("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('dark_background')

np.random.seed(42)
TOP4 = ['dispersion', 'gap_pct', 'india_vix_level', 'volume_surge']

trades = pd.read_csv('54c_trade_log_with_features.csv', parse_dates=['signal_dt'])
trades['date'] = trades['signal_dt'].dt.date
daily = trades.groupby('date').agg(
    daily_zpnl=('zpnl', 'sum'),
    **{f: (f, 'first') for f in TOP4}
).reset_index()
daily['profitable_day'] = (daily['daily_zpnl'] > 0).astype(int)
daily = daily.dropna(subset=TOP4 + ['daily_zpnl']).reset_index(drop=True)
print(f'{len(daily):,} days retained (all top-4 features + target non-null)')

from itertools import combinations
PAIRS = list(combinations(TOP4, 2))
print(f'{len(PAIRS)} pairs: {PAIRS}')
"""))

cells.append(md("## All 6 quadrant scatters (colour = daily_zpnl), one grid"))
cells.append(code("""fig, axes = plt.subplots(2, 3, figsize=(18, 11))
vmax = daily['daily_zpnl'].abs().max()
medians = {f: daily[f].median() for f in TOP4}

for ax, (fx, fy) in zip(axes.flat, PAIRS):
    sc = ax.scatter(daily[fx], daily[fy], c=daily['daily_zpnl'], cmap='RdYlGn',
                     vmin=-vmax, vmax=vmax, s=16, alpha=0.7)
    ax.axvline(medians[fx], color='#888', linestyle=':', linewidth=1)
    ax.axhline(medians[fy], color='#888', linestyle=':', linewidth=1)
    ax.set_xlabel(fx); ax.set_ylabel(fy)
    ax.set_title(f'{fx}  x  {fy}')
plt.colorbar(sc, ax=axes, label='daily_zpnl', shrink=0.6)
plt.suptitle('Top-4 pairwise quadrant scatters (colour=daily_zpnl, dashed=median split)', y=1.00)
plt.savefig('54d_xor_top4_scatters.png', dpi=110, bbox_inches='tight')
plt.show()
"""))

cells.append(md("## Quadrant tables + combined-rule test, all 6 pairs"))
cells.append(code("""def zpf(z):
    pos = z[z > 0].sum(); neg = z[z < 0].sum()
    return pos / abs(neg) if neg != 0 else np.nan

def circular_null(flag, y):
    n = len(y)
    null_r = np.empty(n - 1)
    for shift in range(1, n):
        null_r[shift - 1] = np.corrcoef(flag, np.roll(y, shift))[0, 1]
    return null_r

y_zpnl = daily['daily_zpnl'].values.astype(float)
combined_flags = {}
pair_results = []
for fx, fy in PAIRS:
    flag = ((daily[fx] > medians[fx]) & (daily[fy] > medians[fy])).astype(int).values
    combined_flags[(fx, fy)] = flag
    r = np.corrcoef(flag, y_zpnl)[0, 1]
    null_own = circular_null(flag, y_zpnl)
    ceil95_own, ceil99_own = np.percentile(np.abs(null_own), [95, 99])
    pair_results.append(dict(pair=f'{fx} x {fy}', r=round(r, 4),
                              clears_own_95=abs(r) > ceil95_own, clears_own_99=abs(r) > ceil99_own,
                              n_high_high=int(flag.sum())))

pair_df = pd.DataFrame(pair_results)
print(pair_df.to_string(index=False))
"""))

cells.append(code("""# max-of-6 correction: for each circular-shift rotation, compute all 6 combined-rule
# r's against that one shifted target, take the max |r| -- the honest ceiling for
# "did ANY of the 6 pairs get lucky."
n = len(y_zpnl)
max6_null = np.empty(n - 1)
flags_matrix = np.array([combined_flags[p] for p in PAIRS])  # (6, n)
for shift in range(1, n):
    y_shift = np.roll(y_zpnl, shift)
    rs = [abs(np.corrcoef(flags_matrix[i], y_shift)[0, 1]) for i in range(len(PAIRS))]
    max6_null[shift - 1] = max(rs)

ceil95_6, ceil99_6 = np.percentile(max6_null, [95, 99])
print(f'max-of-6 ceiling: ceil95={ceil95_6:.4f}  ceil99={ceil99_6:.4f}')
pair_df['clears_max6_95'] = pair_df['r'].abs() > ceil95_6
pair_df['clears_max6_99'] = pair_df['r'].abs() > ceil99_6
print()
print(pair_df.to_string(index=False))
"""))

cells.append(md("## Quadrant net_zpnl tables (all 6 pairs)"))
cells.append(code("""for fx, fy in PAIRS:
    daily['_qx'] = np.where(daily[fx] > medians[fx], 'high', 'low')
    daily['_qy'] = np.where(daily[fy] > medians[fy], 'high', 'low')
    q = daily.groupby(['_qx', '_qy']).agg(n_days=('daily_zpnl', 'size'),
                                            mean_zpnl=('daily_zpnl', 'mean'),
                                            net_zpnl=('daily_zpnl', 'sum')).reset_index()
    print(f'--- {fx} (rows) x {fy} (cols) ---')
    print(q.to_string(index=False))
    print()
daily.drop(columns=['_qx', '_qy'], inplace=True, errors='ignore')
"""))

cells.append(md("## Verdict"))
cells.append(code("""passed = pair_df[pair_df.clears_max6_95]
print(f'Clears max-of-6 95th: {len(passed)} of {len(pair_df)} pairs')
if len(passed):
    print(passed.to_string(index=False))
else:
    print('None of the 6 combined AND-rules clear the max-of-6 ceiling -- consistent with all')
    print('4 underlying features already having failed the max-of-12 individual test. No pair')
    print('rescues the group. Confirms the a priori expectation: interaction effects rarely')
    print('manufacture signal out of features that carry none individually.')
"""))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"}
    },
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open('54d_xor_top4.ipynb', 'w'), indent=1)
print('54d_xor_top4.ipynb built,', len(cells), 'cells')
