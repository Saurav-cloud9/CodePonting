"""
Step 52 — interactive weekly time-lapse of the POWERGRID eta0=2.0 market_return vs
strategy_return scatter (the X-shaped diagonal-lines chart), colored by long/short signal.
Built at Saurav's request while walking through Part 2 of 52_alpha_beta_concept_and_powergrid.ipynb.

Replicates the exact eta0=2.0 Model C run from 50c_model_c_powergrid.ipynb / Part 2 of the
alpha/beta notebook (same DS3 source, same SGDRegressor config, same random_state=69) — no
new modeling decisions, purely a different (interactive, animated) view of the same result.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go

# --- Replicate Model C eta0=2.0 on POWERGRID (same as 50c/Part 2) ---
DS3_PATH = '../../../../data/historical/intraday_5min_DS3/POWERGRID.parquet'
pg_5min = pd.read_parquet(DS3_PATH)
pg_5min['date'] = pg_5min['datetime'].dt.date

pg_daily = pg_5min.groupby('date')['close'].last().to_frame()
pg_daily.index = pd.to_datetime(pg_daily.index)
pg_daily = pg_daily.sort_index()
pg_daily['close_log_return'] = np.log(pg_daily['close'] / pg_daily['close'].shift())
pg_daily['close_log_return_lag_1'] = pg_daily['close_log_return'].shift()

pg_clean = pg_daily.dropna()
X_stream = pg_clean[['close_log_return_lag_1']].to_numpy()
y_stream = pg_clean['close_log_return'].to_numpy()
dates = pg_clean.index

model = SGDRegressor(loss="epsilon_insensitive", epsilon=0.0002, penalty=None,
                      learning_rate="pa1", eta0=2.0, random_state=69)
scaler = StandardScaler()
rows = []
for t in range(len(X_stream)):
    X_t = X_stream[t].reshape(1, -1)
    y_t = np.array([y_stream[t]])
    scaler.partial_fit(X_t)
    X_t_scaled = scaler.transform(X_t)
    pred_y = 0.0 if t == 0 else model.predict(X_t_scaled)[0]
    model.partial_fit(X_t_scaled, y_t)
    signal = np.sign(pred_y)
    rows.append({'date': dates[t], 'signal': signal, 'market_return': y_t[0],
                 'strategy_return': signal * y_t[0]})

df = pd.DataFrame(rows)
n = len(df)

# --- Weekly frames (~5 trading days/frame per Saurav's choice) ---
FRAME_SIZE = 5
frame_ends = list(range(FRAME_SIZE, n + 1, FRAME_SIZE))
if frame_ends[-1] != n:
    frame_ends.append(n)

# palette.md categorical slots 1 (blue) & 2 (orange) — dark-surface steps, first two
# of the three slots validated for all-pairs (scatter) CVD/normal-vision separation.
COLOR_LONG = '#3987e5'
COLOR_SHORT = '#d95926'
SURFACE = '#1a1a19'
GRID = '#2c2c2a'
TEXT_PRIMARY = '#ffffff'
TEXT_SECONDARY = '#c3c2b7'
TEXT_MUTED = '#898781'

def split(sub):
    longs = sub[sub['signal'] > 0]
    shorts = sub[sub['signal'] < 0]
    return longs, shorts

x_pad = (df['market_return'].max() - df['market_return'].min()) * 0.05
y_pad = (df['strategy_return'].max() - df['strategy_return'].min()) * 0.05
x_range = [df['market_return'].min() - x_pad, df['market_return'].max() + x_pad]
y_range = [df['strategy_return'].min() - y_pad, df['strategy_return'].max() + y_pad]

marker_style = dict(size=5, opacity=0.65, line=dict(width=0))

# Initial frame (first FRAME_SIZE rows)
init_longs, init_shorts = split(df.iloc[:frame_ends[0]])

fig = go.Figure(
    data=[
        go.Scatter(x=init_longs['market_return'], y=init_longs['strategy_return'],
                   mode='markers', name='long (signal=+1)',
                   marker=dict(color=COLOR_LONG, **marker_style)),
        go.Scatter(x=init_shorts['market_return'], y=init_shorts['strategy_return'],
                   mode='markers', name='short (signal=-1)',
                   marker=dict(color=COLOR_SHORT, **marker_style)),
    ]
)

frames = []
for end in frame_ends:
    sub = df.iloc[:end]
    longs, shorts = split(sub)
    frames.append(go.Frame(
        data=[
            go.Scatter(x=longs['market_return'], y=longs['strategy_return'],
                       mode='markers', marker=dict(color=COLOR_LONG, **marker_style)),
            go.Scatter(x=shorts['market_return'], y=shorts['strategy_return'],
                       mode='markers', marker=dict(color=COLOR_SHORT, **marker_style)),
        ],
        name=str(end),
        layout=go.Layout(
            annotations=[dict(
                text=f"day {end}/{n} — {sub['date'].iloc[-1].date()}",
                xref='paper', yref='paper', x=0.02, y=0.98, showarrow=False,
                font=dict(color=TEXT_SECONDARY, size=13), align='left',
            )]
        ),
    ))
fig.frames = frames

fig.update_layout(
    template=None,
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(color=TEXT_PRIMARY, family='system-ui, -apple-system, "Segoe UI", sans-serif'),
    title=dict(text='POWERGRID eta0=2.0 — market_return vs strategy_return (weekly time-lapse)',
               font=dict(size=18, color=TEXT_PRIMARY)),
    xaxis=dict(title='market_return', range=x_range, gridcolor=GRID, zerolinecolor=TEXT_MUTED,
               zerolinewidth=1, color=TEXT_SECONDARY),
    yaxis=dict(title='strategy_return', range=y_range, gridcolor=GRID, zerolinecolor=TEXT_MUTED,
               zerolinewidth=1, color=TEXT_SECONDARY),
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color=TEXT_SECONDARY)),
    annotations=[dict(
        text=f"day {frame_ends[0]}/{n} — {df['date'].iloc[frame_ends[0]-1].date()}",
        xref='paper', yref='paper', x=0.02, y=0.98, showarrow=False,
        font=dict(color=TEXT_SECONDARY, size=13), align='left',
    )],
    updatemenus=[dict(
        type='buttons', direction='left', showactive=False,
        x=0.02, y=-0.12, xanchor='left', yanchor='top',
        pad=dict(t=0, r=10),
        bgcolor=GRID, bordercolor=TEXT_MUTED, font=dict(color=TEXT_PRIMARY),
        buttons=[
            dict(label='▶ Play', method='animate',
                 args=[None, dict(frame=dict(duration=80, redraw=True), fromcurrent=True,
                                   transition=dict(duration=0))]),
            dict(label='⏸ Pause', method='animate',
                 args=[[None], dict(frame=dict(duration=0, redraw=False), mode='immediate')]),
        ],
    )],
    sliders=[dict(
        active=0, x=0.02, y=-0.02, len=0.96,
        currentvalue=dict(prefix='Through day: ', font=dict(color=TEXT_SECONDARY, size=12)),
        bgcolor=GRID, bordercolor=TEXT_MUTED, font=dict(color=TEXT_PRIMARY, size=10),
        steps=[dict(
            method='animate', label=f"{df['date'].iloc[end-1].date()}",
            args=[[str(end)], dict(mode='immediate',
                                    frame=dict(duration=0, redraw=True),
                                    transition=dict(duration=0))],
        ) for end in frame_ends],
    )],
    margin=dict(t=70, b=90, l=60, r=30),
)

out_path = '52_powergrid_scatter_timelapse.html'
fig.write_html(out_path, include_plotlyjs=True, full_html=True)
print(f'Wrote {out_path} — {len(frame_ends)} frames, n={n} points')
