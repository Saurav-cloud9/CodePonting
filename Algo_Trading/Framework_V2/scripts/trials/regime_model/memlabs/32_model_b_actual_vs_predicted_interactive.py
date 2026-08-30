"""
Step 32 — corrected companion to 32_model_b_real_plane_interactive.html (that file is left
UNTOUCHED; this is a new, separate file). Same Model B fit (same features, same NIFTY50 data,
same LinearRegression, same train/test split), but this time the scatter points show the
GENUINE actual outcome value (close_log_return) at its own true z-coordinate — generally OFF
the y_hat plane, since real data almost never matches a model's prediction exactly — rather
than the model's own prediction re-plotted and mislabeled "Actual."

Points are colored by whether the model's predicted SIGN matched the actual SIGN (correct call)
or not (incorrect call) — since this model's real use is a Buy/Sell (sign of y_hat) signal.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
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
combined['y_hat'] = model.predict(combined[features])
combined['actual'] = combined['close_log_return']          # the GENUINE real outcome
combined['pred_sign'] = np.sign(combined['y_hat'])
combined['actual_sign'] = np.sign(combined['actual'])
combined['correct'] = combined['pred_sign'] == combined['actual_sign']

print(f"Model B: coef_={model.coef_}  intercept_={model.intercept_}")
print(f"n = {len(combined)}  correct calls: {combined['correct'].sum()} ({combined['correct'].mean()*100:.1f}%)")

# --- Build the y_hat plane over the same feature range ---
x1_range = np.linspace(combined[features[0]].min(), combined[features[0]].max(), 30)
x2_range = np.linspace(combined[features[1]].min(), combined[features[1]].max(), 30)
X1, X2 = np.meshgrid(x1_range, x2_range)
Y_HAT_PLANE = model.intercept_ + model.coef_[0]*X1 + model.coef_[1]*X2

fig = go.Figure()

fig.add_trace(go.Surface(x=X1, y=X2, z=Y_HAT_PLANE, colorscale=[[0, '#3987e5'], [1, '#3987e5']],
                          opacity=0.35, showscale=False, name='y_hat plane'))

correct = combined[combined['correct']]
incorrect = combined[~combined['correct']]

fig.add_trace(go.Scatter3d(x=correct[features[0]], y=correct[features[1]], z=correct['actual'],
                            mode='markers', marker=dict(size=3, color='#2ecc71'),
                            name=f'Correct call (n={len(correct)}, {len(correct)/len(combined)*100:.1f}%)'))
fig.add_trace(go.Scatter3d(x=incorrect[features[0]], y=incorrect[features[1]], z=incorrect['actual'],
                            mode='markers', marker=dict(size=3, color='#e74c3c'),
                            name=f'Incorrect call (n={len(incorrect)}, {len(incorrect)/len(combined)*100:.1f}%)'))

# --- Predicted points (y_hat) -- these sit exactly ON the plane, colored by PREDICTED direction ---
pred_long = combined[combined['pred_sign'] > 0]
pred_short = combined[combined['pred_sign'] < 0]

fig.add_trace(go.Scatter3d(x=pred_long[features[0]], y=pred_long[features[1]], z=pred_long['y_hat'],
                            mode='markers', marker=dict(size=2.5, color='#ff6ec7', symbol='diamond'),
                            name=f'Predicted LONG (n={len(pred_long)}) -- pink, on the plane'))
fig.add_trace(go.Scatter3d(x=pred_short[features[0]], y=pred_short[features[1]], z=pred_short['y_hat'],
                            mode='markers', marker=dict(size=2.5, color='#4a90d9', symbol='diamond'),
                            name=f'Predicted SHORT (n={len(pred_short)}) -- blue, on the plane'))

fig.update_layout(
    template='plotly_dark',
    title=f"Model B — GENUINE actual outcomes (off the plane) vs. predicted plane<br>"
          f"Green = predicted sign matched actual sign | Red = mismatch — {combined['correct'].mean()*100:.1f}% correct overall",
    scene=dict(xaxis_title='lag_1', yaxis_title='ma_lag_1', zaxis_title='actual close_log_return',
               aspectmode='cube'),
    legend=dict(x=0.01, y=0.99),
    width=1000, height=900,
)

fig.write_html('/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/32_model_b_actual_vs_predicted_interactive.html')
print('Saved 32_model_b_actual_vs_predicted_interactive.html')
