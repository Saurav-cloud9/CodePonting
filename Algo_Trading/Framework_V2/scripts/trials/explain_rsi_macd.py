import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

CSV = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min\TATAMOTORS_5min.csv'

df = pd.read_csv(CSV, low_memory=False)
df.columns = df.columns.str.strip()
df['datetime'] = pd.to_datetime(df['datetime'])
df['close'] = pd.to_numeric(df['close'], errors='coerce')
df['ma20'] = pd.to_numeric(df['ma20'], errors='coerce')

# pick a clean 3-day slice
df = df[df['datetime'].dt.date.astype(str).between('2023-03-01', '2023-03-03')].reset_index(drop=True)

# ── RSI ──────────────────────────────────────────────────────
delta = df['close'].diff()
gain = delta.clip(lower=0).rolling(14).mean()
loss = (-delta.clip(upper=0)).rolling(14).mean()
rs = gain / loss
df['rsi'] = 100 - (100 / (1 + rs))

# ── MACD ─────────────────────────────────────────────────────
ema12 = df['close'].ewm(span=12, adjust=False).mean()
ema26 = df['close'].ewm(span=26, adjust=False).mean()
df['macd'] = ema12 - ema26
df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
df['hist'] = df['macd'] - df['signal']

x = range(len(df))
# tick every 2 hours to avoid label overlap
xticks = [i for i, dt in enumerate(df['datetime']) if dt.minute == 15 and dt.hour in [9, 11, 13, 15]]
xlabels = [df['datetime'].iloc[i].strftime('%d %b\n%H:%M') for i in xticks]

# ════════════════════════════════════════════════════════════
# CHART 1 — RSI
# ════════════════════════════════════════════════════════════
plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 10), gridspec_kw={'height_ratios': [2, 1]}, sharex=True)
fig.suptitle('RSI Explained — TATAMOTORS 5min', fontsize=14, y=0.98)

# price + MA20
ax1.plot(x, df['close'], color='white', linewidth=1, label='Price')
ax1.plot(x, df['ma20'], color='#00aaff', linewidth=1, linestyle='--', label='MA20')
ax1.set_ylabel('Price')
ax1.legend(loc='upper left', fontsize=9)
ax1.set_title('Price', fontsize=10, pad=4)

# RSI panel
ax2.plot(x, df['rsi'], color='#ffdd00', linewidth=1.2, label='RSI (14)')
ax2.axhline(70, color='#ff4444', linewidth=0.8, linestyle='--')
ax2.axhline(30, color='#00ff88', linewidth=0.8, linestyle='--')
ax2.axhline(50, color='gray', linewidth=0.5, linestyle=':')
ax2.fill_between(x, 70, df['rsi'].clip(upper=100), where=df['rsi'] >= 70, alpha=0.15, color='#ff4444', label='Overbought zone')
ax2.fill_between(x, df['rsi'].clip(lower=0), 30, where=df['rsi'] <= 30, alpha=0.15, color='#00ff88', label='Oversold zone')
ax2.set_ylim(0, 100)
ax2.set_ylabel('RSI')
ax2.set_yticks([0, 30, 50, 70, 100])
ax2.set_yticklabels(['0', '30 (Oversold)', '50', '70 (Overbought)', '100'], fontsize=8)
ax2.legend(loc='upper left', fontsize=9)
ax2.set_title('RSI (14) — momentum oscillator', fontsize=10, pad=4)

ax2.set_xticks(xticks)
ax2.set_xticklabels(xlabels, fontsize=8)

# annotations
ob_idx = df['rsi'].idxmax()
os_idx = df['rsi'].idxmin()
if df['rsi'].iloc[ob_idx] >= 60:
    ax2.annotate('Overbought\n→ momentum fading', xy=(ob_idx, df['rsi'].iloc[ob_idx]),
                 xytext=(ob_idx+3, 85), color='#ff4444', fontsize=8,
                 arrowprops=dict(arrowstyle='->', color='#ff4444'))
if df['rsi'].iloc[os_idx] <= 40:
    ax2.annotate('Oversold\n→ bounce potential', xy=(os_idx, df['rsi'].iloc[os_idx]),
                 xytext=(os_idx+3, 15), color='#00ff88', fontsize=8,
                 arrowprops=dict(arrowstyle='->', color='#00ff88'))

plt.tight_layout()
out1 = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\reports\explain_rsi.png'
plt.savefig(out1, dpi=180, bbox_inches='tight')
plt.close()
print(f'RSI chart saved: {out1}')

# ════════════════════════════════════════════════════════════
# CHART 2 — MACD
# ════════════════════════════════════════════════════════════
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 10), gridspec_kw={'height_ratios': [2, 1]}, sharex=True)
fig.suptitle('MACD Explained — TATAMOTORS 5min', fontsize=14, y=0.98)

ax1.plot(x, df['close'], color='white', linewidth=1, label='Price')
ax1.plot(x, df['ma20'], color='#00aaff', linewidth=1, linestyle='--', label='MA20')
ax1.set_ylabel('Price')
ax1.legend(loc='upper left', fontsize=9)
ax1.set_title('Price', fontsize=10, pad=4)

# MACD panel
ax2.plot(x, df['macd'], color='#00aaff', linewidth=1.2, label='MACD line (EMA12 − EMA26)')
ax2.plot(x, df['signal'], color='#ffdd00', linewidth=1.2, label='Signal line (EMA9 of MACD)')
bars_pos = [h if h >= 0 else 0 for h in df['hist']]
bars_neg = [h if h < 0 else 0 for h in df['hist']]
ax2.bar(x, bars_pos, color='#00ff88', alpha=0.6, width=0.8, label='Histogram +ve (bullish momentum)')
ax2.bar(x, bars_neg, color='#ff4444', alpha=0.6, width=0.8, label='Histogram −ve (bearish momentum)')
ax2.axhline(0, color='gray', linewidth=0.5, linestyle=':')
ax2.set_ylabel('MACD')
ax2.legend(loc='upper left', fontsize=8)
ax2.set_title('MACD (12, 26, 9) — trend + momentum', fontsize=10, pad=4)

ax2.set_xticks(xticks)
ax2.set_xticklabels(xlabels, fontsize=8)

# annotate crossover
for i in range(1, len(df)):
    if df['macd'].iloc[i-1] < df['signal'].iloc[i-1] and df['macd'].iloc[i] >= df['signal'].iloc[i]:
        ax2.annotate('Bullish\ncrossover', xy=(i, df['macd'].iloc[i]),
                     xytext=(i+3, df['macd'].iloc[i] + abs(df['hist'].max())*0.5),
                     color='#00ff88', fontsize=8,
                     arrowprops=dict(arrowstyle='->', color='#00ff88'))
        break
for i in range(1, len(df)):
    if df['macd'].iloc[i-1] > df['signal'].iloc[i-1] and df['macd'].iloc[i] <= df['signal'].iloc[i]:
        ax2.annotate('Bearish\ncrossover', xy=(i, df['macd'].iloc[i]),
                     xytext=(i+3, df['macd'].iloc[i] - abs(df['hist'].max())*0.5),
                     color='#ff4444', fontsize=8,
                     arrowprops=dict(arrowstyle='->', color='#ff4444'))
        break

plt.tight_layout()
out2 = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\reports\explain_macd.png'
plt.savefig(out2, dpi=180, bbox_inches='tight')
plt.close()
print(f'MACD chart saved: {out2}')
