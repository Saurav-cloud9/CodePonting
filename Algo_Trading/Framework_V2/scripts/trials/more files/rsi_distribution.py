import pandas as pd, numpy as np, os, glob, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
SL_MULT=2.5; TP_MULT=4.5; MAX_TB_GAP=3; EOD_HOUR=15

def compute_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def run_backtest(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    for col in ['open','high','low','close','ma20','atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df['rsi'] = compute_rsi(df['close'])

    trades = []; i = 0
    while i < len(df):
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']): i += 1; continue
        if row['low'] <= row['ma20']:
            if row['hour'] >= EOD_HOUR: i += 1; continue
            touch_date = row['date']; atr = row['atr14']; bounce_bar = None
            for j in range(i, i + MAX_TB_GAP + 1):
                b = df.iloc[j]
                if b['date'] != touch_date: break
                if b['hour'] >= EOD_HOUR: break
                if b['close'] > b['ma20']: bounce_bar = b; break
            if bounce_bar is None: i += 1; continue
            entry_idx = j + 1
            if entry_idx >= len(df): i += 1; continue
            entry_bar = df.iloc[entry_idx]
            if entry_bar['date'] != touch_date: i += 1; continue
            entry = entry_bar['open']; sl = entry - SL_MULT*atr; tp = entry + TP_MULT*atr
            rsi_at_entry = bounce_bar['rsi']
            for k in range(entry_idx, len(df)):
                k_bar = df.iloc[k]
                if k_bar['hour'] >= EOD_HOUR:
                    pnl = k_bar['open'] - entry; outcome = 'EOD+' if pnl > 0 else 'EOD-'; break
                if k_bar['high'] >= tp: pnl = tp - entry; outcome = 'W'; break
                if k_bar['low'] <= sl: pnl = sl - entry; outcome = 'L'; break
            trades.append({'pnl': pnl, 'outcome': outcome, 'rsi': rsi_at_entry})
            i = k + 1
        else:
            i += 1
    return trades

csv_files = sorted(glob.glob(os.path.join(DATA_DIR, '*_5min.csv')))
all_trades = []
for csv_path in csv_files:
    all_trades.extend(run_backtest(csv_path))

df = pd.DataFrame(all_trades).dropna(subset=['rsi'])

bins   = [0, 30, 40, 50, 60, 70, 80, 100]
labels = ['<30', '30-40', '40-50', '50-60', '60-70', '70-80', '>80']
df['rsi_bucket'] = pd.cut(df['rsi'], bins=bins, labels=labels)

BE_PURE = SL_MULT / (SL_MULT + TP_MULT) * 100  # 35.7% fixed

rows = []
for bucket in labels:
    sub = df[df['rsi_bucket'] == bucket]
    n = len(sub)
    if n == 0: continue
    prof_wr = (sub['pnl'] > 0).sum() / n * 100
    pure_wr = (sub['outcome'] == 'W').sum() / n * 100
    avg_win = sub[sub['pnl'] > 0]['pnl'].mean() if (sub['pnl'] > 0).any() else 0
    avg_loss = abs(sub[sub['pnl'] < 0]['pnl'].mean()) if (sub['pnl'] < 0).any() else 0
    be_prof = avg_loss / (avg_win + avg_loss) * 100 if (avg_win + avg_loss) > 0 else 0
    gp = sub[sub['pnl'] > 0]['pnl'].sum()
    gl = abs(sub[sub['pnl'] < 0]['pnl'].sum())
    pf = gp / gl if gl > 0 else 999
    rows.append({'RSI': bucket, 'N': n,
                 'Prof_WR%': round(prof_wr,1), 'BE_prof%': round(be_prof,1),
                 'Pure_WR%': round(pure_wr,1), 'BE_pure%': round(BE_PURE,1),
                 'PF': round(pf,3)})

summary = pd.DataFrame(rows)
print(summary.to_string(index=False))

# ── Chart ────────────────────────────────────────────────────
plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Baseline Trade Distribution by RSI at Entry — 30 Stocks', fontsize=13)

colors = ['#00ff88' if pf >= 1.0 else '#ff4444' for pf in summary['PF']]

ax1.bar(summary['RSI'], summary['N'], color='#00aaff', alpha=0.8)
ax1.set_title('Trade Count by RSI')
ax1.set_xlabel('RSI at Entry'); ax1.set_ylabel('N')
for i, v in enumerate(summary['N']): ax1.text(i, v+20, str(v), ha='center', fontsize=8)

ax2.bar(summary['RSI'], summary['PF'], color=colors, alpha=0.8)
ax2.axhline(1.0, color='white', linewidth=0.8, linestyle='--', label='Breakeven PF=1.0')
ax2.set_title('Profit Factor by RSI')
ax2.set_xlabel('RSI at Entry'); ax2.set_ylabel('PF')
for i, v in enumerate(summary['PF']): ax2.text(i, v+0.005, str(v), ha='center', fontsize=8)
ax2.legend()

plt.tight_layout()
out = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\reports\rsi_distribution.png'
plt.savefig(out, dpi=150); plt.close()
print(f'\nChart saved: {out}')
