"""
55a comparison chart — Section 7 (one feature) stacked above Section 8A (two features),
same data, same chronological 70/30 split, same TRAIN-only OLS fits as 55a_build.py.
Shared y-axis (daily_zpnl) so the two clouds are directly comparable. Each panel marks
its decision boundary (top: dispersion = -b0/b1, bottom: yhat = 0).

Standalone visual; does not modify 55a_single_feature_ols.ipynb or 55a_two_feature_static.png.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use('dark_background')

trades = pd.read_csv('54c_trade_log_with_features.csv', parse_dates=['signal_dt'])
trades['date'] = trades['signal_dt'].dt.date


def split(df):
    i = int(len(df) * 0.70)
    return df.iloc[:i], df.iloc[i:]


def oos_r2(y_te, yhat_te, y_tr):
    return 1 - np.sum((y_te - yhat_te) ** 2) / np.sum((y_te - y_tr.mean()) ** 2)


# ── One feature (Section 7) ───────────────────────────────────────────────────
d1 = (trades.groupby('date')
      .agg(daily_zpnl=('zpnl', 'sum'), dispersion=('dispersion', 'first'))
      .reset_index().dropna().sort_values('date').reset_index(drop=True))
tr1, te1 = split(d1)
x_tr, y_tr = tr1['dispersion'].values, tr1['daily_zpnl'].values
x_te, y_te = te1['dispersion'].values, te1['daily_zpnl'].values
b1 = np.sum((x_tr - x_tr.mean()) * (y_tr - y_tr.mean())) / np.sum((x_tr - x_tr.mean()) ** 2)
b0 = y_tr.mean() - b1 * x_tr.mean()
yhat_tr1, yhat_te1 = b0 + b1 * x_tr, b0 + b1 * x_te
r2_in1 = 1 - np.sum((y_tr - yhat_tr1) ** 2) / np.sum((y_tr - y_tr.mean()) ** 2)
r2_oos1 = oos_r2(y_te, yhat_te1, y_tr)
pct1 = (yhat_te1 > 0).mean()
crossing = -b0 / b1

# ── Two features (Section 8A) ─────────────────────────────────────────────────
d2 = (trades.groupby('date')
      .agg(daily_zpnl=('zpnl', 'sum'), dispersion=('dispersion', 'first'), gap_pct=('gap_pct', 'first'))
      .reset_index().dropna().sort_values('date').reset_index(drop=True))
tr2, te2 = split(d2)
A_tr = np.column_stack([np.ones(len(tr2)), tr2[['dispersion', 'gap_pct']].values])
A_te = np.column_stack([np.ones(len(te2)), te2[['dispersion', 'gap_pct']].values])
y_tr2, y_te2 = tr2['daily_zpnl'].values, te2['daily_zpnl'].values
coefs, *_ = np.linalg.lstsq(A_tr, y_tr2, rcond=None)
yhat_tr2, yhat_te2 = A_tr @ coefs, A_te @ coefs
r2_in2 = 1 - np.sum((y_tr2 - yhat_tr2) ** 2) / np.sum((y_tr2 - y_tr2.mean()) ** 2)
r2_oos2 = oos_r2(y_te2, yhat_te2, y_tr2)
pct2 = (yhat_te2 > 0).mean()

# ── Figure: stacked, shared y-axis ────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), sharey=True)
BLUE, ORANGE, GREEN, GREY = '#4a90d9', '#e67e22', '#2ecc71', '#888'

ax1.scatter(x_tr, y_tr, s=10, alpha=0.4, color=BLUE, label=f'TRAIN (n={len(tr1)})')
ax1.scatter(x_te, y_te, s=10, alpha=0.4, color=ORANGE, label=f'TEST (n={len(te1)})')
xl = np.linspace(d1['dispersion'].min(), d1['dispersion'].max(), 100)
ax1.plot(xl, b0 + b1 * xl, color=GREEN, linewidth=2, label=f'TRAIN-fit: y={b0:.3f}+{b1:.4f}x')
ax1.axhline(0, color=GREY, linewidth=0.8)
ax1.axvline(crossing, color='yellow', linewidth=1.2, linestyle='--',
            label=f'decision boundary: dispersion={crossing:.2f}')
ax1.set_xlabel('dispersion'); ax1.set_ylabel('daily_zpnl')
ax1.set_title(f'1 feature: dispersion\nin-sample R²={r2_in1:.4f}, OOS R²={r2_oos1:.4f}, '
              f'{pct1:.1%} of TEST days traded')
ax1.legend(loc='upper right')

ax2.scatter(yhat_tr2, y_tr2, s=10, alpha=0.4, color=BLUE, label=f'TRAIN (n={len(tr2)})')
ax2.scatter(yhat_te2, y_te2, s=10, alpha=0.4, color=ORANGE, label=f'TEST (n={len(te2)})')
yl = np.linspace(min(yhat_tr2.min(), yhat_te2.min()), max(yhat_tr2.max(), yhat_te2.max()), 100)
ax2.plot(yl, yl, color=GREEN, linewidth=2, label='y = yhat (perfect-fit diagonal)')
ax2.axhline(0, color=GREY, linewidth=0.8)
ax2.axvline(0, color='yellow', linewidth=1.2, linestyle='--', label='decision boundary: yhat=0')
ax2.set_xlabel('yhat = b0 + b1*dispersion + b2*gap_pct'); ax2.set_ylabel('daily_zpnl')
ax2.set_title(f'2 features: dispersion + gap_pct\nin-sample R²={r2_in2:.4f}, OOS R²={r2_oos2:.4f}, '
              f'{pct2:.1%} of TEST days traded')
ax2.legend(loc='upper right')

fig.suptitle('55a — one feature vs two features (shared daily_zpnl scale)', fontsize=13)
plt.tight_layout()
plt.savefig('55a_one_vs_two_feature_comparison.png', dpi=130)
print(f'1-feat: b0={b0:.4f} b1={b1:.4f} crossing={crossing:.3f} R2in={r2_in1:.4f} R2oos={r2_oos1:.4f} traded={pct1:.1%}')
print(f'2-feat: b={np.round(coefs, 4)} R2in={r2_in2:.4f} R2oos={r2_oos2:.4f} traded={pct2:.1%}')
print('Saved: 55a_one_vs_two_feature_comparison.png')
