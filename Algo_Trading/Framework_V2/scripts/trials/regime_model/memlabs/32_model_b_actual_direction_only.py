"""
Step 32 — companion to 32_model_b_actual_vs_predicted_interactive.py, same data/model, but this
time coloring dots purely by the GENUINE actual outcome direction (actual return > 0 = actual buy
day, actual return < 0 = actual sell day) -- NOT by whether the model's prediction matched it.

Purpose: separate two questions that were getting mixed together in the correct/incorrect chart --
  1. "Did the model call it right?"        <- 32_model_b_actual_vs_predicted_interactive.py
  2. "Can lag_1 / ma_lag_1 alone separate actual buy-days from actual sell-days at all?" <- THIS file

Two panels:
  Left  -- 3D scatter (lag_1, ma_lag_1, actual return) with a FLAT z=0 reference plane. Points
           above the flat plane are actual buy-days, below are actual sell-days, by definition.
  Right -- 2D top-down projection: just lag_1 vs ma_lag_1, colored by actual direction. This is
           the "view that only has the two axes of the two features in contention" -- if the two
           colors look randomly interleaved here with no visible boundary, that's direct visual
           evidence the two features carry little/no separating power for direction.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

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

buy = combined[combined['actual_sign'] > 0]     # actual up-days -- long would've won
sell = combined[combined['actual_sign'] < 0]    # actual down-days -- short would've won

print(f"n = {len(combined)}  actual buy-days: {len(buy)} ({len(buy)/len(combined)*100:.1f}%)  "
      f"actual sell-days: {len(sell)} ({len(sell)/len(combined)*100:.1f}%)")
print(f"lag_1    mean | buy={buy[features[0]].mean():.6f}  sell={sell[features[0]].mean():.6f}")
print(f"ma_lag_1 mean | buy={buy[features[1]].mean():.6f}  sell={sell[features[1]].mean():.6f}")
print(f"lag_1    corr with actual_sign: {combined[features[0]].corr(combined['actual_sign']):.4f}")
print(f"ma_lag_1 corr with actual_sign: {combined[features[1]].corr(combined['actual_sign']):.4f}")

COLOR_BUY = '#2ecc71'
COLOR_SELL = '#e74c3c'

fig = make_subplots(
    rows=1, cols=2,
    specs=[[{'type': 'scene'}, {'type': 'xy'}]],
    subplot_titles=('3D: actual return vs. flat z=0 plane', 'Top-down: lag_1 vs ma_lag_1 only'),
    column_widths=[0.55, 0.45],
)

# --- Left: 3D scatter + flat z=0 plane ---
x1_range = np.linspace(combined[features[0]].min(), combined[features[0]].max(), 2)
x2_range = np.linspace(combined[features[1]].min(), combined[features[1]].max(), 2)
X1, X2 = np.meshgrid(x1_range, x2_range)
ZERO_PLANE = np.zeros_like(X1)

fig.add_trace(go.Surface(x=X1, y=X2, z=ZERO_PLANE, colorscale=[[0, '#888888'], [1, '#888888']],
                          opacity=0.25, showscale=False, name='z=0 plane'), row=1, col=1)
fig.add_trace(go.Scatter3d(x=buy[features[0]], y=buy[features[1]], z=buy['actual'],
                            mode='markers', marker=dict(size=2.5, color=COLOR_BUY),
                            name=f'Actual buy (n={len(buy)})', legendgroup='buy'), row=1, col=1)
fig.add_trace(go.Scatter3d(x=sell[features[0]], y=sell[features[1]], z=sell['actual'],
                            mode='markers', marker=dict(size=2.5, color=COLOR_SELL),
                            name=f'Actual sell (n={len(sell)})', legendgroup='sell'), row=1, col=1)

# --- Right: 2D top-down projection, features only ---
fig.add_trace(go.Scatter(x=buy[features[0]], y=buy[features[1]], mode='markers',
                          marker=dict(size=4, color=COLOR_BUY), name='Actual buy',
                          legendgroup='buy', showlegend=False), row=1, col=2)
fig.add_trace(go.Scatter(x=sell[features[0]], y=sell[features[1]], mode='markers',
                          marker=dict(size=4, color=COLOR_SELL), name='Actual sell',
                          legendgroup='sell', showlegend=False), row=1, col=2)

# --- Model's fitted decision boundary (y_hat=0): intercept + coef1*x1 + coef2*x2 = 0 ---
x2_lo, x2_hi = combined[features[1]].min(), combined[features[1]].max()
boundary_x1 = np.linspace(combined[features[0]].min(), combined[features[0]].max(), 200)
boundary_x2 = -(model.intercept_ + model.coef_[0] * boundary_x1) / model.coef_[1]
mask = (boundary_x2 >= x2_lo) & (boundary_x2 <= x2_hi)

fig.add_trace(go.Scatter(x=boundary_x1[mask], y=boundary_x2[mask], mode='lines',
                          line=dict(color='white', width=3, dash='solid'),
                          name='Model boundary (y_hat=0)'), row=1, col=2)

fig.update_scenes(xaxis_title='lag_1', yaxis_title='ma_lag_1', zaxis_title='actual close_log_return',
                   aspectmode='cube', row=1, col=1)
fig.update_xaxes(title_text='lag_1', row=1, col=2)
fig.update_yaxes(title_text='ma_lag_1', row=1, col=2)

fig.update_layout(
    template='plotly_dark',
    title="Actual buy vs. actual sell days -- do lag_1 / ma_lag_1 separate them at all?<br>"
          f"Green = actual up-day (buy) | Red = actual down-day (sell) -- {len(buy)/len(combined)*100:.1f}% / "
          f"{len(sell)/len(combined)*100:.1f}% split",
    legend=dict(x=0.01, y=0.99),
    width=1500, height=800,
)

out_path = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/32_model_b_actual_direction_only.html'
fig.write_html(out_path)
print(f'Saved {out_path}')
