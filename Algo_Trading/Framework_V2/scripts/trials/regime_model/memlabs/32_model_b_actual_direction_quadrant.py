"""
Step 32 -- static PNG version of the 2D top-down panel from 32_model_b_actual_direction_only.py
(real Model B data, NOT dummy), redrawn with explicit quadrant lines/labels so it can be directly
compared side-by-side against the dummy XOR interaction toy example
(52_mathmode_xor_interaction_quadrant_example.png).

Same data/model/features as 32_model_b_actual_direction_only.py -- lag_1 vs ma_lag_1, colored by
actual outcome direction, plus the model's fitted y_hat=0 boundary line.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

plt.style.use('dark_background')

NIFTY_PATH = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/daily/NIFTY50.parquet'

daily = pd.read_parquet(NIFTY_PATH)
daily['datetime'] = pd.to_datetime(daily['datetime'])
if daily['datetime'].dt.tz is not None:
    daily['datetime'] = daily['datetime'].apply(lambda x: x.replace(tzinfo=None))
daily.set_index('datetime', inplace=True)
daily.rename(columns={'close': 'c'}, inplace=True)
daily = daily[['c']]
daily['close_log_return'] = np.log(daily['c'] / daily['c'].shift())
daily['close_log_return_lag_1'] = daily['close_log_return'].shift()
daily['close_log_return_ma_lag_1'] = daily['close_log_return_lag_1'].rolling(40).mean()

features = ['close_log_return_lag_1', 'close_log_return_ma_lag_1']
df = daily.dropna(subset=features + ['close_log_return'])
df_train, df_test = train_test_split(df, test_size=0.25, shuffle=False)
model = LinearRegression()
model.fit(df_train[features], df_train['close_log_return'])

combined = df.copy()
combined['actual'] = combined['close_log_return']
combined['actual_sign'] = np.sign(combined['actual'])

buy = combined[combined['actual_sign'] > 0]
sell = combined[combined['actual_sign'] < 0]

corr_x1 = df[features[0]].corr(np.sign(df['close_log_return']))
corr_x2 = df[features[1]].corr(np.sign(df['close_log_return']))
print(f"corr(lag_1, actual sign) = {corr_x1:.4f}   corr(ma_lag_1, actual sign) = {corr_x2:.4f}")

COLOR_BUY = '#2ecc71'
COLOR_SELL = '#e74c3c'

fig, ax = plt.subplots(figsize=(9, 8))

ax.scatter(buy[features[0]], buy[features[1]], color=COLOR_BUY, s=14, alpha=0.6,
           label=f'actual buy (n={len(buy)}, {len(buy)/len(combined)*100:.1f}%)')
ax.scatter(sell[features[0]], sell[features[1]], color=COLOR_SELL, s=14, alpha=0.6,
           label=f'actual sell (n={len(sell)}, {len(sell)/len(combined)*100:.1f}%)')

ax.axhline(0, color='white', linewidth=1, linestyle='--', alpha=0.6)
ax.axvline(0, color='white', linewidth=1, linestyle='--', alpha=0.6)

# Model's fitted decision boundary: intercept + coef1*x1 + coef2*x2 = 0
x1_lo, x1_hi = combined[features[0]].min(), combined[features[0]].max()
x2_lo, x2_hi = combined[features[1]].min(), combined[features[1]].max()
boundary_x1 = np.linspace(x1_lo, x1_hi, 200)
boundary_x2 = -(model.intercept_ + model.coef_[0] * boundary_x1) / model.coef_[1]
mask = (boundary_x2 >= x2_lo) & (boundary_x2 <= x2_hi)
ax.plot(boundary_x1[mask], boundary_x2[mask], color='white', linewidth=2.2,
        label='model boundary (y_hat=0)')

# Quadrant labels
ax.text(x1_hi * 0.7, x2_hi * 0.9, 'Q1', color='#cccccc', fontsize=11, ha='center', weight='bold')
ax.text(x1_lo * 0.7, x2_hi * 0.9, 'Q2', color='#cccccc', fontsize=11, ha='center', weight='bold')
ax.text(x1_lo * 0.7, x2_lo * 0.9, 'Q3', color='#cccccc', fontsize=11, ha='center', weight='bold')
ax.text(x1_hi * 0.7, x2_lo * 0.9, 'Q4', color='#cccccc', fontsize=11, ha='center', weight='bold')

x_pad = (x1_hi - x1_lo) * 0.15
y_pad = (x2_hi - x2_lo) * 0.15
ax.set_xlim(x1_lo - x_pad, x1_hi + x_pad)
ax.set_ylim(x2_lo - y_pad, x2_hi + y_pad)

ax.set_xlabel('lag_1')
ax.set_ylabel('ma_lag_1')
ax.set_title(f"Model B (real data) -- actual buy vs sell, lag_1 vs ma_lag_1 only\n"
             f"corr(lag_1, sign)={corr_x1:.3f}, corr(ma_lag_1, sign)={corr_x2:.3f} -- no visible quadrant pattern",
             fontsize=11)
ax.legend(loc='upper right', fontsize=9)

plt.tight_layout()
out_path = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/32_model_b_actual_direction_quadrant.png'
plt.savefig(out_path, dpi=130)
print(f'Saved {out_path}')
