"""
v1.1 SL x TP grid sweep — find best combo before CBQ
v1.1 = v1 (wick-only) + Above VWAP + Below EMA100 | 30 stocks 2022-2025
"""
import sys, io, glob, pandas as pd, numpy as np
import matplotlib.pyplot as plt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_DIR  = 'Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'
OUT_DIR  = 'Algo_Trading/Framework_V2/outputs/reports/screenshots'
ATR_LEN  = 14; MA_LEN = 20; EMA_SPAN = 100; EOD_HOUR = 15

SL_VALS  = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
TP_VALS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]

def load(f):
    df = pd.read_csv(f, low_memory=False); df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime']).apply(
        lambda x: x.replace(tzinfo=None) if x.tzinfo else x)
    for col in ['open','high','low','close','volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.sort_values('datetime').reset_index(drop=True)
    df['date'] = df['datetime'].dt.date; df['hour'] = df['datetime'].dt.hour
    df['ma20'] = df['close'].rolling(MA_LEN).mean()
    df['ema100'] = df['close'].ewm(span=EMA_SPAN, adjust=False).mean()
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['cum_tpv'] = df.groupby('date').apply(
        lambda g: (g['tp'] * g['volume']).cumsum(), include_groups=False
    ).reset_index(level=0, drop=True)
    df['cum_vol'] = df.groupby('date')['volume'].cumsum()
    df['vwap'] = df['cum_tpv'] / df['cum_vol']
    prev_c = df['close'].shift(1)
    tr = pd.concat([df['high']-df['low'],
                    (df['high']-prev_c).abs(),
                    (df['low']-prev_c).abs()], axis=1).max(axis=1)
    df['atr'] = tr.ewm(alpha=1/ATR_LEN, adjust=False).mean()
    return df.dropna(subset=['ma20','ema100','vwap','atr']).reset_index(drop=True)

def get_signals(df):
    high=df['high'].values; low=df['low'].values
    close=df['close'].values; open_=df['open'].values
    ma=df['ma20'].values; ema=df['ema100'].values
    vwap=df['vwap'].values; atr=df['atr'].values
    hour=df['hour'].values; date=df['date'].values; n=len(df)
    signals=[]
    for i in range(n-1):
        if (low[i] <= ma[i] and open_[i] > ma[i] and close[i] > ma[i]
                and close[i] >= vwap[i] and close[i] < ema[i]
                and hour[i] < EOD_HOUR):
            ei = i + 1
            if date[ei] == date[i]:
                signals.append({'entry_i': ei, 'atr': atr[i],
                                 'date': date[ei],
                                 'year': df.iloc[ei]['datetime'].year,
                                 'entry_px': open_[ei]})
    return signals

def simulate(df, signals, sl_m, tp_m):
    trades=[]; high=df['high'].values; low=df['low'].values
    open_=df['open'].values; hour=df['hour'].values; date=df['date'].values; n=len(df)
    next_entry_allowed = 0  # position guard: skip signals until previous trade exits
    for sig in signals:
        if sig['entry_i'] < next_entry_allowed:
            continue
        entry=sig['entry_px']; atr=sig['atr']
        sl  = entry - sl_m  * atr
        tp = entry + tp_m * atr
        entry_date=sig['date']
        pnl = entry  # fallback
        for k in range(sig['entry_i'], n):
            if hour[k] >= EOD_HOUR or date[k] != entry_date:
                pnl = open_[k] - entry; break
            if high[k] >= tp: pnl = tp - entry; break
            if low[k]  <= sl:  pnl = sl  - entry; break
        next_entry_allowed = k + 1
        trades.append({'pnl': pnl, 'year': sig['year'], 'date': pd.Timestamp(sig['date'])})
    return trades

def pf(trades):
    if not trades: return 0
    w=sum(t['pnl'] for t in trades if t['pnl']>0)
    l=sum(-t['pnl'] for t in trades if t['pnl']<0)
    return w/l if l>0 else 0

def sharpe(trades):
    if len(trades)<2: return 0
    tdf=pd.DataFrame(trades); tdf['date']=pd.to_datetime(tdf['date'])
    m=tdf.resample('ME',on='date')['pnl'].sum()
    return (m.mean()/m.std())*np.sqrt(12) if m.std()>0 else 0

# ── Main ─────────────────────────────────────────────────────────────────────
files=sorted(glob.glob(f'{CSV_DIR}/*.csv'))
print(f'Loading {len(files)} stocks...')
all_data=[(load(f), None) for f in files]
all_data=[(df, get_signals(df)) for df,_ in all_data]
total=sum(len(s) for _,s in all_data)
print(f'Total v1.1 signals: {total}')

print('Running SL x TP grid sweep...')
grid=np.zeros((len(SL_VALS), len(TP_VALS)))
for si,sl_m in enumerate(SL_VALS):
    for ti,tp_m in enumerate(TP_VALS):
        all_t=[]
        for df,sigs in all_data: all_t.extend(simulate(df,sigs,sl_m,tp_m))
        grid[si,ti]=pf(all_t)

best_idx=np.unravel_index(np.argmax(grid),grid.shape)
best_sl=SL_VALS[best_idx[0]]; best_tp=TP_VALS[best_idx[1]]
all_best=[]
for df,sigs in all_data: all_best.extend(simulate(df,sigs,best_sl,best_tp))

print(f'\nBest combo: SL={best_sl}x  TP={best_tp}x')
print(f'Overall: N={len(all_best)}  PF={grid[best_idx]:.3f}  Sharpe={sharpe(all_best):.3f}')
print(f"\n{'Year':<6} {'N':>5}  {'PF':>6}  {'Sharpe':>7}  {'WR%':>6}")
for yr in [2022,2023,2024,2025]:
    g=[t for t in all_best if t['year']==yr]
    if not g: continue
    gp=sum(t['pnl'] for t in g if t['pnl']>0); gl=sum(-t['pnl'] for t in g if t['pnl']<0)
    wr=sum(1 for t in g if t['pnl']>0)/len(g)*100
    print(f"  {yr}  {len(g):>5}  {gp/gl if gl>0 else 0:>6.3f}  {sharpe(g):>7.3f}  {wr:>5.1f}%")

print(f'\nTop 5 combos:')
flat=[(grid[si,ti],SL_VALS[si],TP_VALS[ti])
      for si in range(len(SL_VALS)) for ti in range(len(TP_VALS))]
flat.sort(reverse=True)
for v,s,t in flat[:5]:
    print(f'  SL={s}x TP={t}x  PF={v:.3f}')

# Heatmap
grid_flipped=np.flipud(grid); sl_labels=SL_VALS[::-1]
plt.style.use('dark_background')
fig,ax=plt.subplots(figsize=(11,7))
fig.patch.set_facecolor('#0d1117'); ax.set_facecolor('#0d1117')
im=ax.imshow(grid_flipped,cmap='RdYlGn',vmin=0.7,vmax=1.3,aspect='auto')
ax.set_xticks(range(len(TP_VALS))); ax.set_xticklabels(TP_VALS,color='#aaa')
ax.set_yticks(range(len(SL_VALS)));  ax.set_yticklabels(sl_labels,color='#aaa')
ax.set_xlabel('TP Multiplier',color='#aaa',fontsize=11)
ax.set_ylabel('SL Multiplier',color='#aaa',fontsize=11)
ax.set_title(f'PF Heatmap — v1.1 (wick + VWAP + EMA100)\n30 Stocks | 2022-2025 | N={total}',
             color='white',fontsize=13,pad=12)
for si in range(len(SL_VALS)):
    for ti in range(len(TP_VALS)):
        v=grid_flipped[si,ti]
        ax.text(ti,si,f'{v:.3f}',ha='center',va='center',
                fontsize=8,color='black' if 0.85<v<1.15 else 'white')
cbar=fig.colorbar(im,ax=ax,pad=0.02)
cbar.set_label('Profit Factor',color='#aaa')
cbar.ax.yaxis.set_tick_params(color='#aaa')
plt.setp(cbar.ax.yaxis.get_ticklabels(),color='#aaa')
plt.tight_layout()
out=f'{OUT_DIR}/v1_1_sl_tp_heatmap.png'
plt.savefig(out,dpi=150,bbox_inches='tight',facecolor=fig.get_facecolor())
plt.close()
print(f'\nHeatmap saved: {out}')
