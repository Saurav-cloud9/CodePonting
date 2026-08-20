import pandas as pd, numpy as np, os, glob, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
DS3_DIR  = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V1\data\historical\intraday_5min_DS3'
BASE_SL=2.5; BASE_TP=4.5; MAX_TB_GAP=3; EOD_HOUR=15; WARMUP=40

def compute_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    return 100 - (100 / (1 + gain / loss))

def compute_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def run_backtest(csv_path):
    fv2 = pd.read_csv(csv_path, low_memory=False)
    fv2.columns = fv2.columns.str.strip()
    fv2['datetime'] = pd.to_datetime(fv2['datetime']).dt.tz_localize(None)
    for col in ['open','high','low','close','ma20','atr14']:
        fv2[col] = pd.to_numeric(fv2[col], errors='coerce')

    # prepend DS3 warm-up bars for RSI/MACD
    symbol = os.path.basename(csv_path).replace('_5min.csv','')
    ds3_path = os.path.join(DS3_DIR, f'{symbol}.parquet')
    if os.path.exists(ds3_path):
        ds3 = pd.read_parquet(ds3_path)
        if ds3.index.name == 'datetime' or 'datetime' not in ds3.columns:
            ds3 = ds3.reset_index()
        ds3['datetime'] = pd.to_datetime(ds3['datetime']).dt.tz_localize(None)
        warmup = ds3[ds3['datetime'] < fv2['datetime'].iloc[0]].tail(WARMUP)[['datetime','open','high','low','close']]
        combined = pd.concat([warmup, fv2[['datetime','open','high','low','close']]], ignore_index=True)
    else:
        combined = fv2[['datetime','open','high','low','close']].copy()
        warmup = pd.DataFrame()

    # compute indicators on combined data
    rsi_all = compute_rsi(combined['close'])
    _, _, macd_hist_all = compute_macd(combined['close'])

    # assign back to fv2 only (drop warmup rows)
    n_warm = len(warmup)
    fv2['rsi']       = rsi_all.iloc[n_warm:].values
    fv2['macd_hist'] = macd_hist_all.iloc[n_warm:].values

    df = fv2.copy()
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour

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
            rsi_val  = bounce_bar['rsi']
            macd_val = bounce_bar['macd_hist']
            entry_idx = j + 1
            if entry_idx >= len(df): i += 1; continue
            entry_bar = df.iloc[entry_idx]
            if entry_bar['date'] != touch_date: i += 1; continue
            entry = entry_bar['open']

            mfe = 0.0; mae = 0.0; outcome = None; pnl_atr = 0.0; k = entry_idx
            while k < len(df):
                kb = df.iloc[k]
                mfe = max(mfe, (kb['high'] - entry) / atr)
                mae = max(mae, (entry - kb['low'])  / atr)
                if kb['hour'] >= EOD_HOUR:
                    pnl_atr = (kb['open'] - entry) / atr
                    outcome = 'EOD+' if pnl_atr > 0 else 'EOD-'; k += 1; break
                if kb['high'] >= entry + BASE_TP * atr:
                    pnl_atr = BASE_TP; outcome = 'W'; k += 1; break
                if kb['low']  <= entry - BASE_SL  * atr:
                    pnl_atr = -BASE_SL; outcome = 'L'; k += 1; break
                k += 1
            trades.append({'rsi': rsi_val, 'macd_hist': macd_val,
                           'mfe': mfe, 'mae': mae, 'outcome': outcome, 'pnl': pnl_atr})
            i = k
        else:
            i += 1
    return trades

print('Running 30-stock backtest...')
csv_files = sorted(glob.glob(os.path.join(DATA_DIR, '*_5min.csv')))
all_trades = []
for csv_path in csv_files:
    all_trades.extend(run_backtest(csv_path))
print(f'Trades collected: {len(all_trades)}')

df = pd.DataFrame(all_trades).dropna(subset=['rsi','macd_hist'])

# ── outcome colors & labels ───────────────────────────────────
omap = {
    'W':    ('#00e676', 'Target Hit — Winner'),
    'EOD+': ('#ffe600', 'EOD Exit — Profit'),
    'EOD-': ('#ff7c00', 'EOD Exit — Loss'),
    'L':    ('#ff1744', 'Stop Loss Hit — Loser'),
}

# ════════════════════════════════════════════════════════════
# CHART 1 — RSI at Bounce Bar vs Median MFE (bar chart by bucket)
# ════════════════════════════════════════════════════════════
rsi_bins   = [0,20,30,40,50,60,70,80,100]
rsi_labels = ['<20','20-30','30-40','40-50','50-60','60-70','70-80','>80']
df['rsi_bucket'] = pd.cut(df['rsi'], bins=rsi_bins, labels=rsi_labels)

plt.style.use('dark_background')
fig, axes = plt.subplots(2, 2, figsize=(20, 14))
fig.suptitle('RSI & MACD at Bounce Bar vs Trade Quality (MFE / Profit Factor)\n'
             '30 Stocks | 2022–2025 | Baseline SL=2.5x ATR, TP=4.5x ATR',
             fontsize=14, y=1.01)

# Panel 1: RSI bucket vs median MFE by outcome
ax = axes[0][0]
for outcome, (color, label) in omap.items():
    sub = df[df['outcome'] == outcome]
    medians = sub.groupby('rsi_bucket', observed=True)['mfe'].median()
    ax.plot(medians.index, medians.values, color=color, linewidth=2.5,
            marker='o', markersize=7, label=label)
ax.set_title('RSI at Bounce Bar vs Median MFE by Exit Type', fontsize=12)
ax.set_xlabel('RSI at Bounce Bar', fontsize=10)
ax.set_ylabel('Median MFE (ATR multiples)', fontsize=10)
ax.legend(fontsize=9); ax.grid(alpha=0.15)

# Panel 2: RSI bucket vs Profit Factor
ax = axes[0][1]
def calc_pf(sub):
    gp = sub[sub['pnl'] > 0]['pnl'].sum()
    gl = abs(sub[sub['pnl'] < 0]['pnl'].sum())
    return gp / gl if gl > 0 else 999

pf_rows = []
for bucket in rsi_labels:
    sub = df[df['rsi_bucket'] == bucket]
    if len(sub) < 10: continue
    pf_rows.append({'bucket': bucket, 'pf': calc_pf(sub), 'n': len(sub)})
pf_df = pd.DataFrame(pf_rows)
colors = ['#00e676' if p >= 1.0 else '#ff1744' for p in pf_df['pf']]
bars = ax.bar(pf_df['bucket'], pf_df['pf'], color=colors, alpha=0.85)
ax.axhline(1.0, color='white', linewidth=1.5, linestyle='--', label='Break-even PF = 1.0')
for bar, row in zip(bars, pf_df.itertuples()):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{row.pf:.2f}\n(n={row.n:,})', ha='center', va='bottom', fontsize=8)
ax.set_title('RSI at Bounce Bar vs Profit Factor', fontsize=12)
ax.set_xlabel('RSI at Bounce Bar', fontsize=10)
ax.set_ylabel('Profit Factor', fontsize=10)
ax.legend(fontsize=9); ax.grid(alpha=0.15)

# Panel 3: MACD histogram sign vs median MFE
ax = axes[1][0]
df['macd_zone'] = pd.cut(df['macd_hist'],
    bins=[-np.inf, -0.5, -0.1, 0, 0.1, 0.5, np.inf],
    labels=['Strong\nBearish\n(<-0.5)', 'Bearish\n(-0.5 to -0.1)',
            'Weak\nBearish\n(-0.1 to 0)', 'Weak\nBullish\n(0 to 0.1)',
            'Bullish\n(0.1 to 0.5)', 'Strong\nBullish\n(>0.5)'])
for outcome, (color, label) in omap.items():
    sub = df[df['outcome'] == outcome]
    medians = sub.groupby('macd_zone', observed=True)['mfe'].median()
    ax.plot(medians.index, medians.values, color=color, linewidth=2.5,
            marker='o', markersize=7, label=label)
ax.set_title('MACD Histogram at Bounce Bar vs Median MFE by Exit Type', fontsize=12)
ax.set_xlabel('MACD Histogram Zone at Bounce Bar', fontsize=10)
ax.set_ylabel('Median MFE (ATR multiples)', fontsize=10)
ax.legend(fontsize=9); ax.grid(alpha=0.15)

# Panel 4: MACD zone vs Profit Factor
ax = axes[1][1]
pf_rows2 = []
macd_labels = ['Strong\nBearish\n(<-0.5)', 'Bearish\n(-0.5 to -0.1)',
               'Weak\nBearish\n(-0.1 to 0)', 'Weak\nBullish\n(0 to 0.1)',
               'Bullish\n(0.1 to 0.5)', 'Strong\nBullish\n(>0.5)']
for bucket in macd_labels:
    sub = df[df['macd_zone'] == bucket]
    if len(sub) < 10: continue
    pf_rows2.append({'bucket': bucket, 'pf': calc_pf(sub), 'n': len(sub)})
pf_df2 = pd.DataFrame(pf_rows2)
colors2 = ['#00e676' if p >= 1.0 else '#ff1744' for p in pf_df2['pf']]
bars2 = ax.bar(range(len(pf_df2)), pf_df2['pf'], color=colors2, alpha=0.85)
ax.axhline(1.0, color='white', linewidth=1.5, linestyle='--', label='Break-even PF = 1.0')
for bar, row in zip(bars2, pf_df2.itertuples()):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{row.pf:.2f}\n(n={row.n:,})', ha='center', va='bottom', fontsize=8)
ax.set_xticks(range(len(pf_df2)))
ax.set_xticklabels(pf_df2['bucket'], fontsize=8)
ax.set_title('MACD Histogram at Bounce Bar vs Profit Factor', fontsize=12)
ax.set_xlabel('MACD Histogram Zone at Bounce Bar', fontsize=10)
ax.set_ylabel('Profit Factor', fontsize=10)
ax.legend(fontsize=9); ax.grid(alpha=0.15)

plt.tight_layout()
out = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\reports\rsi_macd_mfe.png'
plt.savefig(out, dpi=180, bbox_inches='tight'); plt.close()
print(f'Saved: {out}')

# ── Sanity check vs baseline ──────────────────────────────────
n_total = len(df)
gp_total = df[df['pnl'] > 0]['pnl'].sum()
gl_total = abs(df[df['pnl'] < 0]['pnl'].sum())
pf_total = gp_total / gl_total if gl_total > 0 else 999
prof_wr  = (df['pnl'] > 0).sum() / n_total * 100
print(f'\n--- Sanity Check vs Baseline ---')
print(f'N       : {n_total:,}   (baseline: 49,039)')
print(f'PF      : {pf_total:.3f}   (baseline: 0.922)')
print(f'Prof_WR : {prof_wr:.1f}%   (baseline: 41.5%)')
print(f'Match   : {"YES" if abs(pf_total - 0.922) < 0.01 and n_total == 49039 else "NO — CHECK LOGIC"}')
