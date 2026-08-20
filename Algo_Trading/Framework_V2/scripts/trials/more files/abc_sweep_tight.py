"""
Trading ABC — tight SL x TP sweep (0.3–1.5 SL, 0.3–2.0 TP)
First upward triangle per ABC, long only, all 30 stocks 2022-2025
"""
import sys, io, glob, pandas as pd, numpy as np
import matplotlib.pyplot as plt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_DIR  = 'Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'
OUT_DIR  = 'Algo_Trading/Framework_V2/outputs/reports/screenshots'
ZZ_LEN   = 8
FIB_LO   = 0.382; FIB_HI = 0.618; ERR_RATE = 0.05
MAX_BARS = 6; ATR_LEN = 14; EOD_HOUR = 15
MA_SPANS = [50,100,150,200]; EMA_SPANS = [20,40]
FIB_LO_EFF = FIB_LO*(1-ERR_RATE); FIB_HI_EFF = FIB_HI*(1+ERR_RATE)

SL_VALS  = [0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5]
TP_VALS = [0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 1.7, 2.0]

def load(f):
    df = pd.read_csv(f, low_memory=False)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime']).apply(
        lambda x: x.replace(tzinfo=None) if x.tzinfo else x)
    for col in ['open','high','low','close','volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.sort_values('datetime').reset_index(drop=True)
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    for sp in MA_SPANS:  df[f'sma{sp}'] = df['close'].rolling(sp).mean()
    for sp in EMA_SPANS: df[f'ema{sp}'] = df['close'].ewm(span=sp, adjust=False).mean()
    prev_c = df['close'].shift(1)
    tr = pd.concat([df['high']-df['low'],
                    (df['high']-prev_c).abs(),
                    (df['low']-prev_c).abs()], axis=1).max(axis=1)
    df['atr'] = tr.ewm(alpha=1/ATR_LEN, adjust=False).mean()
    df['ph'] = df['high'] == df['high'].rolling(ZZ_LEN).max()
    df['pl'] = df['low']  == df['low'].rolling(ZZ_LEN).min()
    ma_cols = [f'sma{s}' for s in MA_SPANS] + [f'ema{s}' for s in EMA_SPANS]
    return df.dropna(subset=ma_cols+['atr']).reset_index(drop=True)

def get_signals(df):
    ma_cols = [f'sma{s}' for s in MA_SPANS] + [f'ema{s}' for s in EMA_SPANS]
    ma_vals = df[ma_cols].values
    high=df['high'].values; low=df['low'].values
    close=df['close'].values; open_=df['open'].values
    ph=df['ph'].values; pl=df['pl'].values; n=len(df)
    trend=0; up_streak=0; down_streak=0
    zigzag=[]; last_abc_id=None; abc_bar_count=0
    lowest_since_c=np.inf; last_zz_point=None; signals=[]
    for i in range(n):
        body_hi=max(open_[i],close[i]); body_lo=min(open_[i],close[i])
        upper=(ma_vals[i]>=body_hi).sum(); lower=(ma_vals[i]<=body_lo).sum()
        up_streak  = up_streak+1   if lower>0 and upper==0 else 0
        down_streak= down_streak+1 if upper>0 and lower==0 else 0
        if up_streak>=2: trend=1
        elif down_streak>=2: trend=-1
        changed=False
        ctype='H' if ph[i] else ('L' if pl[i] else None)
        if ctype is not None:
            price=high[i] if ctype=='H' else low[i]
            if not zigzag: zigzag.append([i,price,ctype]); changed=True
            else:
                _,lv,lt=zigzag[-1]
                if ctype==lt:
                    if (ctype=='H' and price>lv) or (ctype=='L' and price<lv):
                        zigzag[-1]=[i,price,ctype]; changed=True
                else: zigzag.append([i,price,ctype]); changed=True
            if len(zigzag)>10: zigzag=zigzag[-10:]
        new_abc=False
        if changed and ctype=='L' and trend==1 and len(zigzag)>=5:
            ap=zigzag[-1][1]; bp=zigzag[-3][1]; cp=zigzag[-5][1]
            if low[i]<ma_vals[i].max() and (cp-bp)!=0:
                rate=(ap-bp)/(cp-bp)
                if FIB_LO_EFF<=rate<=FIB_HI_EFF:
                    last_zz_point=ap; abc_bar_count=0
                    lowest_since_c=low[i]; last_abc_id=i; new_abc=True
        if not new_abc:
            abc_bar_count+=1
            if last_zz_point is not None: lowest_since_c=min(lowest_since_c,low[i])
        if (last_zz_point is not None and trend==1 and abc_bar_count<=MAX_BARS
                and lowest_since_c>=last_zz_point and last_abc_id is not None):
            lbounced=False
            if i>=1:
                low2=min(low[i],low[i-1])
                if close[i]>open_[i]:
                    for ma in ma_vals[i]:
                        if low2<=ma and close[i]>ma: lbounced=True; break
            if lbounced:
                ei=i+1
                if ei<n and df.iloc[ei]['hour']<EOD_HOUR:
                    signals.append({'entry_i':ei,'atr':df.iloc[i]['atr'],
                                    'date':df.iloc[ei]['date'],
                                    'year':df.iloc[ei]['datetime'].year,
                                    'entry_px':df.iloc[ei]['open']})
                last_abc_id=None
    return signals

def simulate(df, signals, sl_m, tp_m):
    trades=[]; high=df['high'].values; low=df['low'].values
    open_=df['open'].values; n=len(df)
    for sig in signals:
        entry=sig['entry_px']; atr=sig['atr']
        sl=entry-sl_m*atr; tp=entry+tp_m*atr
        entry_date=sig['date']
        for k in range(sig['entry_i'],n):
            kb=df.iloc[k]
            if kb['hour']>=EOD_HOUR or kb['date']!=entry_date: pnl=open_[k]-entry; break
            if high[k]>=tp: pnl=tp-entry; break
            if low[k]<=sl:   pnl=sl-entry;  break
        trades.append({'pnl':pnl,'year':sig['year'],'date':pd.Timestamp(sig['date'])})
    return trades

def pf(trades):
    if not trades: return 0
    w=sum(t['pnl'] for t in trades if t['pnl']>0)
    l=sum(-t['pnl'] for t in trades if t['pnl']<0)
    return w/l if l>0 else 0

files = sorted(glob.glob(f'{CSV_DIR}/*.csv'))
print(f'Loading {len(files)} stocks...')
all_data = [(load(f), []) for f in files]
all_data = [(df, get_signals(df)) for df, _ in all_data]
total = sum(len(s) for _,s in all_data)
print(f'Total signals: {total}')

print('Running tight SL x TP sweep...')
grid = np.zeros((len(SL_VALS), len(TP_VALS)))
for si, sl_m in enumerate(SL_VALS):
    for ti, tp_m in enumerate(TP_VALS):
        all_t = []
        for df,sigs in all_data: all_t.extend(simulate(df,sigs,sl_m,tp_m))
        grid[si,ti] = pf(all_t)

# Best combo
best_idx = np.unravel_index(np.argmax(grid), grid.shape)
best_sl=SL_VALS[best_idx[0]]; best_tp=TP_VALS[best_idx[1]]
print(f'\nBest combo: SL={best_sl}x  TP={best_tp}x  PF={grid[best_idx]:.3f}')

# Heatmap — SL ascending from bottom
grid_flipped = np.flipud(grid)
sl_labels = SL_VALS[::-1]

plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(11, 7))
fig.patch.set_facecolor('#0d1117'); ax.set_facecolor('#0d1117')

im = ax.imshow(grid_flipped, cmap='RdYlGn', vmin=0.7, vmax=1.3, aspect='auto')
ax.set_xticks(range(len(TP_VALS))); ax.set_xticklabels(TP_VALS, color='#aaa')
ax.set_yticks(range(len(SL_VALS)));  ax.set_yticklabels(sl_labels, color='#aaa')
ax.set_xlabel('TP Multiplier', color='#aaa', fontsize=11)
ax.set_ylabel('SL Multiplier',  color='#aaa', fontsize=11)
ax.set_title(f'PF Heatmap -- Trading ABC Tight Range (SL 0.3-1.5 x TP 0.3-2.0)\n30 Stocks | 2022-2025 | N={total}',
             color='white', fontsize=13, pad=12)

for si in range(len(SL_VALS)):
    for ti in range(len(TP_VALS)):
        v = grid_flipped[si,ti]
        ax.text(ti, si, f'{v:.3f}', ha='center', va='center',
                fontsize=8, color='black' if 0.85<v<1.15 else 'white')

cbar = fig.colorbar(im, ax=ax, pad=0.02)
cbar.set_label('Profit Factor', color='#aaa')
cbar.ax.yaxis.set_tick_params(color='#aaa')
plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#aaa')

plt.tight_layout()
out = f'{OUT_DIR}/abc_sl_tp_heatmap_tight.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f'Saved: {out}')
