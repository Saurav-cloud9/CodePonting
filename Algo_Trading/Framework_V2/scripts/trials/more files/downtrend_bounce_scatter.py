import pandas as pd, numpy as np, os, glob, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
DS3_DIR  = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V1\data\historical\intraday_5min_DS3'
BASE_SL=2.5; BASE_TP=4.5; MAX_TB_GAP=3; EOD_HOUR=15; WARMUP=200

def compute_indicators(close):
    ema200 = close.ewm(span=200, adjust=False).mean()
    ema12  = close.ewm(span=12,  adjust=False).mean()
    ema26  = close.ewm(span=26,  adjust=False).mean()
    macd   = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return ema200, macd, signal

def run(csv_path):
    fv2 = pd.read_csv(csv_path, low_memory=False)
    fv2.columns = fv2.columns.str.strip()
    fv2['datetime'] = pd.to_datetime(fv2['datetime']).dt.tz_localize(None)
    for col in ['open','high','low','close','ma20','atr14']:
        fv2[col] = pd.to_numeric(fv2[col], errors='coerce')

    symbol = os.path.basename(csv_path).replace('_5min.csv','')
    ds3_path = os.path.join(DS3_DIR, f'{symbol}.parquet')
    if os.path.exists(ds3_path):
        ds3 = pd.read_parquet(ds3_path)
        if 'datetime' not in ds3.columns: ds3 = ds3.reset_index()
        ds3['datetime'] = pd.to_datetime(ds3['datetime']).dt.tz_localize(None)
        warmup = ds3[ds3['datetime'] < fv2['datetime'].iloc[0]].tail(WARMUP)[['datetime','close']]
        combined = pd.concat([warmup[['datetime','close']], fv2[['datetime','close']]], ignore_index=True)
    else:
        combined = fv2[['datetime','close']].copy(); warmup = pd.DataFrame()

    ema200_all, macd_all, signal_all = compute_indicators(combined['close'])
    n_warm = len(warmup)
    fv2['ema200']  = ema200_all.iloc[n_warm:].values
    fv2['macd']    = macd_all.iloc[n_warm:].values
    fv2['macd_sig']= signal_all.iloc[n_warm:].values

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
                if b['date'] != touch_date or b['hour'] >= EOD_HOUR: break
                if b['close'] > b['ma20']: bounce_bar = b; break
            if bounce_bar is None: i += 1; continue

            # DOWNTREND regime at bounce bar
            regime = 'NONE'
            if not (pd.isna(bounce_bar['ema200']) or pd.isna(bounce_bar['macd']) or pd.isna(bounce_bar['macd_sig'])):
                above = bounce_bar['close'] > bounce_bar['ema200']
                bull_macd = bounce_bar['macd'] > bounce_bar['macd_sig']
                if not above and not bull_macd:
                    regime = 'DOWNTREND'
                elif above and bull_macd:
                    regime = 'UPTREND'
                else:
                    regime = 'MIXED'

            entry_idx = j + 1
            if entry_idx >= len(df): i += 1; continue
            entry_bar = df.iloc[entry_idx]
            if entry_bar['date'] != touch_date: i += 1; continue
            entry = entry_bar['open']
            pnl_atr = 0.0; outcome = None; k = entry_idx
            while k < len(df):
                kb = df.iloc[k]
                if kb['hour'] >= EOD_HOUR:
                    pnl_atr = (kb['open'] - entry) / atr
                    outcome = 'EOD+' if pnl_atr > 0 else 'EOD-'; k += 1; break
                if kb['high'] >= entry + BASE_TP * atr:
                    pnl_atr = BASE_TP; outcome = 'W'; k += 1; break
                if kb['low'] <= entry - BASE_SL * atr:
                    pnl_atr = -BASE_SL; outcome = 'L'; k += 1; break
                k += 1
            trades.append({'date': pd.Timestamp(touch_date), 'symbol': symbol,
                           'regime': regime, 'outcome': outcome, 'pnl': pnl_atr})
            i = k
        else:
            i += 1
    return trades

print('Running backtest...')
all_trades = []
for f in sorted(glob.glob(os.path.join(DATA_DIR, '*_5min.csv'))):
    all_trades.extend(run(f))
df = pd.DataFrame(all_trades).dropna(subset=['outcome'])

dt = df[df['regime'] == 'DOWNTREND'].copy()
dt['year'] = dt['date'].dt.year
print(f'DOWNTREND trades: {len(dt):,}')

# ── Colors & outcome order ────────────────────────────────
omap = {'W': '#00e676', 'EOD+': '#ffe600', 'EOD-': '#ff7c00', 'L': '#ff1744'}

plt.style.use('dark_background')
fig = plt.figure(figsize=(22, 16))
fig.suptitle('DOWNTREND/Bounce Segment — Trade Distribution (N=3,002)\n'
             'Regime: close < EMA200 AND MACD < Signal at Bounce Bar | 30 stocks 2022-2025',
             fontsize=13, y=1.01)

# ── Panel 1: Scatter — date vs PnL (all 3002 dots) ───────
ax1 = fig.add_subplot(3, 2, (1, 2))
for outcome, color in omap.items():
    sub = dt[dt['outcome'] == outcome]
    ax1.scatter(sub['date'], sub['pnl'], c=color, s=12, alpha=0.5, label=outcome, zorder=3)
ax1.axhline(0, color='white', lw=0.8, ls='--', alpha=0.4)
ax1.axhline(BASE_TP, color='#00e676', lw=0.6, ls=':', alpha=0.3)
ax1.axhline(-BASE_SL, color='#ff1744', lw=0.6, ls=':', alpha=0.3)
ax1.set_title('Every DOWNTREND trade as a dot — Date vs PnL (ATR)', fontsize=11)
ax1.set_ylabel('PnL (ATR multiples)'); ax1.legend(fontsize=9, markerscale=2); ax1.grid(alpha=0.1)

# ── Panel 2: Year-by-year PF bar ──────────────────────────
ax2 = fig.add_subplot(3, 2, 3)
def calc_pf(sub):
    gp = sub[sub['pnl'] > 0]['pnl'].sum()
    gl = abs(sub[sub['pnl'] < 0]['pnl'].sum())
    return gp / gl if gl > 0 else 999

years = sorted(dt['year'].unique())
pf_by_year = [(y, calc_pf(dt[dt['year']==y]), len(dt[dt['year']==y])) for y in years]
colors_yr = ['#00e676' if p >= 1.0 else '#ff1744' for _, p, _ in pf_by_year]
bars = ax2.bar([str(y) for y, _, _ in pf_by_year], [p for _, p, _ in pf_by_year], color=colors_yr, alpha=0.85)
ax2.axhline(1.0, color='white', lw=1.5, ls='--')
ax2.axhline(0.922, color='#888', lw=1, ls=':', label='Baseline PF=0.922')
for bar, (y, p, n) in zip(bars, pf_by_year):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.01, f'{p:.3f}\n(n={n})', ha='center', va='bottom', fontsize=9)
ax2.set_title('PF by Year — DOWNTREND segment', fontsize=11)
ax2.set_ylabel('Profit Factor'); ax2.legend(fontsize=9); ax2.grid(alpha=0.1)

# ── Panel 3: Year-by-year outcome stacked bar ─────────────
ax3 = fig.add_subplot(3, 2, 4)
outcomes = ['W', 'EOD+', 'EOD-', 'L']
bottom = np.zeros(len(years))
for outcome in outcomes:
    vals = [len(dt[(dt['year']==y) & (dt['outcome']==outcome)]) for y in years]
    ax3.bar([str(y) for y in years], vals, bottom=bottom, color=omap[outcome], label=outcome, alpha=0.85)
    bottom += np.array(vals)
ax3.set_title('Outcome Count by Year — DOWNTREND segment', fontsize=11)
ax3.set_ylabel('Trade Count'); ax3.legend(fontsize=9); ax3.grid(alpha=0.1)

# ── Panel 4: PnL distribution — DOWNTREND vs rest ─────────
ax4 = fig.add_subplot(3, 2, 5)
rest = df[df['regime'] != 'DOWNTREND']
ax4.hist(dt['pnl'].clip(-4, 6), bins=60, color='#00b0ff', alpha=0.6, density=True, label=f'DOWNTREND (n={len(dt):,})')
ax4.hist(rest['pnl'].clip(-4, 6), bins=60, color='#888', alpha=0.4, density=True, label=f'Rest (n={len(rest):,})')
ax4.axvline(0, color='white', lw=0.8, ls='--')
ax4.set_title('PnL Distribution — DOWNTREND vs Rest', fontsize=11)
ax4.set_xlabel('PnL (ATR)'); ax4.set_ylabel('Density'); ax4.legend(fontsize=9); ax4.grid(alpha=0.1)

# ── Panel 5: Monthly trade count ──────────────────────────
ax5 = fig.add_subplot(3, 2, 6)
dt['ym'] = dt['date'].dt.to_period('M')
monthly = dt.groupby(['ym','outcome']).size().unstack(fill_value=0)
months = [str(m) for m in monthly.index]
bottom = np.zeros(len(months))
for outcome in outcomes:
    if outcome in monthly.columns:
        vals = monthly[outcome].values
        ax5.bar(months, vals, bottom=bottom, color=omap[outcome], label=outcome, alpha=0.85, width=0.8)
        bottom += vals
ax5.set_title('Monthly Trade Count — DOWNTREND segment', fontsize=11)
ax5.set_ylabel('Trade Count')
ax5.set_xticks(range(0, len(months), 3))
ax5.set_xticklabels(months[::3], rotation=45, fontsize=7)
ax5.legend(fontsize=9); ax5.grid(alpha=0.1)

plt.tight_layout()
out = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\reports\downtrend_bounce_scatter.png'
plt.savefig(out, dpi=150, bbox_inches='tight'); plt.close()
print(f'Saved: {out}')

# ── Console summary ───────────────────────────────────────
print(f'\nYear-by-year breakdown:')
print(f'{"Year":<6} {"N":>5} {"PF":>6} {"WR%":>6}  W   EOD+  EOD-   L')
print('-'*55)
for y in years:
    sub = dt[dt['year']==y]
    pf = calc_pf(sub); wr = (sub['pnl']>0).sum()/len(sub)*100
    w = len(sub[sub['outcome']=='W']); ep = len(sub[sub['outcome']=='EOD+'])
    em = len(sub[sub['outcome']=='EOD-']); l = len(sub[sub['outcome']=='L'])
    print(f'{y:<6} {len(sub):>5} {pf:>6.3f} {wr:>5.1f}%  {w:>3}  {ep:>4}  {em:>4}  {l:>4}')
