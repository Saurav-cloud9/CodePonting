"""
Step 50 — interactive 3D version of the "fitted line swept across time" plot.
Same data/math as notebook 50's Part 1 toy walkthrough, just rendered with Plotly so it's
genuinely rotatable/zoomable in a browser, not a static matplotlib PNG.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

# --- same toy data + Model C run as notebook 50 ---
toy_x = np.array([0.010, -0.005, 0.020, -0.010, 0.003, -0.008, 0.015, -0.002])
toy_y = np.array([0.008, -0.004, 0.015, -0.012, 0.0028, -0.009, 0.011, -0.001])

EPSILON = 0.0002
model_toy = SGDRegressor(
    loss="epsilon_insensitive", epsilon=EPSILON, penalty=None,
    learning_rate="pa1", eta0=0.01, random_state=69,
)
scaler_toy = StandardScaler()

trace_rows = []
for t in range(len(toy_x)):
    X_t = toy_x[t].reshape(1, -1)
    y_t = np.array([toy_y[t]])
    scaler_toy.partial_fit(X_t)
    X_t_scaled = scaler_toy.transform(X_t)
    model_toy.partial_fit(X_t_scaled, y_t)
    w_after, b_after = model_toy.coef_[0], model_toy.intercept_[0]
    trace_rows.append({'tick': t, 'x_scaled': X_t_scaled[0][0], 'true_y': y_t[0],
                        'w_after': w_after, 'b_after': b_after})

trace_df = pd.DataFrame(trace_rows)

# --- build the ruled surface: y = w(t)*x + b(t) ---
x_line = np.linspace(trace_df['x_scaled'].min() - 0.3, trace_df['x_scaled'].max() + 0.3, 40)
ticks = trace_df['tick'].to_numpy()
X_grid, T_grid = np.meshgrid(x_line, ticks)
Y_grid = np.zeros_like(X_grid)
for i, row in trace_df.iterrows():
    Y_grid[i, :] = row['w_after'] * x_line + row['b_after']

fig = go.Figure()

fig.add_trace(go.Surface(
    x=X_grid, y=T_grid, z=Y_grid,
    colorscale='Plasma', opacity=0.75, showscale=True,
    colorbar=dict(title='fitted y'),
    name='y = w(t)·x + b(t)',
))

fig.add_trace(go.Scatter3d(
    x=trace_df['x_scaled'], y=trace_df['tick'], z=trace_df['true_y'],
    mode='markers+text',
    marker=dict(size=6, color='white', line=dict(color='black', width=1)),
    text=[f"tick {t}" for t in trace_df['tick']],
    textposition='top center',
    name='(x_scaled, tick, true_y)',
))

fig.update_layout(
    title='Toy walkthrough: fitted line swept across time — y = w(t)·x + b(t)',
    scene=dict(
        xaxis_title='x_scaled',
        yaxis_title='tick',
        zaxis_title='y',
        bgcolor='black',
    ),
    paper_bgcolor='black',
    font=dict(color='white'),
    template='plotly_dark',
    width=1000, height=800,
)

out_path = 'scripts/trials/regime_model/memlabs/50_toy_line_evolution_3d_interactive.html'
fig.write_html(out_path)
print('saved', out_path)
