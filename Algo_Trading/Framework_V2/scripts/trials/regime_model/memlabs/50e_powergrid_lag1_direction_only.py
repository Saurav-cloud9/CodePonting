"""
Step 50e -- single-feature separability check for Model C's actual input feature
(close_log_return_lag_1), analogous to Model B's #32-series direction-only check, but for
POWERGRID/Model C, which uses only ONE feature (not two like Model B, so no quadrant structure
applies -- see 52_mathmode_xor_interaction_quadrant_example.py discussion, parked as TODO F10).

Question: does lag_1 alone carry any visual/numeric separating power for next-day direction
(actual up-day = buy, actual down-day = sell), independent of Model C's online-learning fit?

Note: this is NOT the same variable as "market_return" in 52_alpha_beta_concept_and_powergrid.ipynb
(which is true_y, i.e. the actual same-day return, used for the "beat buy-and-hold" CAPM test).
This script checks the model's actual INPUT feature (lag_1) against the actual OUTCOME instead.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use('dark_background')

DS3_PATH = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3/POWERGRID.parquet'
pg_5min = pd.read_parquet(DS3_PATH)
pg_5min['date'] = pg_5min['datetime'].dt.date

pg_daily = pg_5min.groupby('date')['close'].last().to_frame()
pg_daily.index = pd.to_datetime(pg_daily.index)
pg_daily = pg_daily.sort_index()
pg_daily['close_log_return'] = np.log(pg_daily['close'] / pg_daily['close'].shift())
pg_daily['close_log_return_lag_1'] = pg_daily['close_log_return'].shift()
pg_clean = pg_daily.dropna()

lag_1 = pg_clean['close_log_return_lag_1'].to_numpy()
actual = pg_clean['close_log_return'].to_numpy()
actual_sign = np.sign(actual)

n = len(lag_1)
buy = actual_sign > 0
sell = actual_sign < 0

corr_return = np.corrcoef(lag_1, actual)[0, 1]
corr_sign = np.corrcoef(lag_1, actual_sign)[0, 1]

# --- Simple OLS fit: actual ~ a + b*lag_1 (same recipe as the derivation's alpha/beta) ---
x_bar = lag_1.mean()
y_bar = actual.mean()
b_fit = np.mean((lag_1 - x_bar) * (actual - y_bar)) / np.mean((lag_1 - x_bar) ** 2)
a_fit = y_bar - b_fit * x_bar
print(f"fitted line: actual = {a_fit:.6f} + {b_fit:.4f} * lag_1")

print(f"n = {n}  actual buy-days: {buy.sum()} ({buy.sum()/n*100:.1f}%)  actual sell-days: {sell.sum()} ({sell.sum()/n*100:.1f}%)")
print(f"corr(lag_1, actual return) = {corr_return:.4f}")
print(f"corr(lag_1, actual sign)   = {corr_sign:.4f}")

COLOR_BUY = '#2ecc71'
COLOR_SELL = '#e74c3c'

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

# --- Left: lag_1 vs actual return (continuous) ---
axes[0].scatter(lag_1[buy], actual[buy], s=6, alpha=0.4, color=COLOR_BUY, label=f'actual buy (n={buy.sum()})')
axes[0].scatter(lag_1[sell], actual[sell], s=6, alpha=0.4, color=COLOR_SELL, label=f'actual sell (n={sell.sum()})')
axes[0].axhline(0, color='white', lw=0.8, ls='--', alpha=0.6)
axes[0].axvline(0, color='white', lw=0.8, ls='--', alpha=0.6)
x_line = np.linspace(lag_1.min(), lag_1.max(), 200)
axes[0].plot(x_line, a_fit + b_fit * x_line, color='#5b9bd5', lw=2, label=f'fitted line: y={a_fit:.5f}+{b_fit:.3f}x')
axes[0].set_xlabel('lag_1'); axes[0].set_ylabel('actual return')
axes[0].set_title(f'lag_1 vs actual return\ncorr={corr_return:.3f}')
axes[0].legend(fontsize=8)

# --- Right: lag_1 as a 1D strip, colored by actual direction (the true single-feature analog) ---
rng = np.random.default_rng(0)
jitter = rng.uniform(-1, 1, n)  # vertical jitter only for visual separation, not real data
axes[1].scatter(lag_1[buy], jitter[buy], s=6, alpha=0.4, color=COLOR_BUY, label='actual buy')
axes[1].scatter(lag_1[sell], jitter[sell], s=6, alpha=0.4, color=COLOR_SELL, label='actual sell')
axes[1].axvline(0, color='white', lw=0.8, ls='--', alpha=0.6)
x_boundary = -a_fit / b_fit
axes[1].axvline(x_boundary, color='#5b9bd5', lw=2, label=f'model boundary (y_hat=0) at lag_1={x_boundary:.5f}')
axes[1].set_xlabel('lag_1'); axes[1].set_yticks([])
axes[1].set_title(f'lag_1 (1D strip, jittered for visibility)\ncorr(lag_1, sign)={corr_sign:.3f}')
axes[1].legend(fontsize=8)

fig.suptitle('POWERGRID Model C -- does lag_1 alone separate actual buy vs sell days?', fontsize=12)
plt.tight_layout()
out_path = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/50e_powergrid_lag1_direction_only.png'
plt.savefig(out_path, dpi=130)
print(f'Saved {out_path}')
