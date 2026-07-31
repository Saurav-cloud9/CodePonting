"""
Fair comparison: v0 LONG bare vs v2 SHORT bare
Each swept for best SL×TP, then yearwise PF + Sharpe at best config.
"""
import sys, io, glob
import pandas as pd, numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_DIR  = 'Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'
EOD_HOUR = 15; ATR_LEN = 14; MA_LEN = 20

SL_VALS  = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
TP_VALS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]

def load(f):
    df = pd.read_csv(f, low_memory=False)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime']).apply(
        lambda x: x.replace(tzinfo=None) if x.tzinfo else x)
    for col in ['open','high','low','close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.sort_values('datetime').reset_index(drop=True)
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df['ma20'] = df['close'].rolling(MA_LEN).mean()
    prev_c = df['close'].shift(1)
    tr = pd.concat([df['high']-df['low'],
                    (df['high']-prev_c).abs(),
                    (df['low'] -prev_c).abs()], axis=1).max(axis=1)
    df['atr'] = tr.ewm(alpha=1/ATR_LEN, adjust=False).mean()
    return df.dropna(subset=['ma20','atr']).reset_index(drop=True)

def get_long_signals(df):
    high=df['high'].values; low=df['low'].values
    close=df['close'].values; open_=df['open'].values
    ma=df['ma20'].values; atr=df['atr'].values
    hour=df['hour'].values; date=df['date'].values; n=len(df)
    sigs=[]; MAX_TB_GAP=3
    for i in range(n):
        if hour[i]>=EOD_HOUR: continue
        if low[i]<=ma[i]:
            touch_date=date[i]; touch_atr=atr[i]
            bounce=None
            for j in range(i, min(i+MAX_TB_GAP+1, n)):
                if date[j]!=touch_date or hour[j]>=EOD_HOUR: break
                if close[j]>ma[j]: bounce=j; break
            if bounce is None: continue
            ei=bounce+1
            if ei>=n or date[ei]!=touch_date: continue
            sigs.append({'ei':ei,'atr':touch_atr,'date':date[ei],'year':pd.Timestamp(date[ei]).year,'entry_px':open_[ei]})
    return sigs

def get_short_signals(df):
    high=df['high'].values; low=df['low'].values
    close=df['close'].values; open_=df['open'].values
    ma=df['ma20'].values; atr=df['atr'].values
    hour=df['hour'].values; date=df['date'].values; n=len(df)
    sigs=[]
    i=0
    while i<n:
        if hour[i]>=EOD_HOUR: i+=1; continue
        if high[i]>=ma[i]:
            touch_date=date[i]; touch_atr=atr[i]
            rej=None
            for j in range(i, min(i+4,n)):
                if date[j]!=touch_date or hour[j]>=EOD_HOUR: break
                if close[j]<ma[j]: rej=j; break
            if rej is not None:
                ei=rej+1
                if ei<n and date[ei]==touch_date:
                    sigs.append({'ei':ei,'atr':touch_atr,'date':date[ei],'year':pd.Timestamp(date[ei]).year,'entry_px':open_[ei]})
            i=rej+1 if rej else i+1
        else:
            i+=1
    return sigs

def sim_long(df, sigs, sl_m, tp_m):
    high=df['high'].values; low=df['low'].values
    open_=df['open'].values; hour=df['hour'].values; date=df['date'].values; n=len(df)
    trades=[]; next_allowed=0
    for s in sigs:
        if s['ei']<next_allowed: continue
        entry=s['entry_px']; atr=s['atr']
        sl=entry-sl_m*atr; tp=entry+tp_m*atr; ed=s['date']
        for k in range(s['ei'],n):
            if hour[k]>=EOD_HOUR or date[k]!=ed: pnl=open_[k]-entry; break
            if high[k]>=tp: pnl=tp-entry; break
            if low[k]<=sl:   pnl=sl-entry;  break
        next_allowed=k+1
        trades.append({'pnl':pnl,'date':pd.Timestamp(s['date']),'year':s['year']})
    return trades

def sim_short(df, sigs, sl_m, tp_m):
    high=df['high'].values; low=df['low'].values
    open_=df['open'].values; hour=df['hour'].values; date=df['date'].values; n=len(df)
    trades=[]; next_allowed=0
    for s in sigs:
        if s['ei']<next_allowed: continue
        entry=s['entry_px']; atr=s['atr']
        sl=entry+sl_m*atr; tp=entry-tp_m*atr; ed=s['date']
        for k in range(s['ei'],n):
            if hour[k]>=EOD_HOUR or date[k]!=ed: pnl=entry-open_[k]; break
            if low[k]<=tp:  pnl=entry-tp; break
            if high[k]>=sl:  pnl=entry-sl;  break
        next_allowed=k+1
        trades.append({'pnl':pnl,'date':pd.Timestamp(s['date']),'year':s['year']})
    return trades

def pf(trades):
    w=sum(t['pnl'] for t in trades if t['pnl']>0)
    l=sum(-t['pnl'] for t in trades if t['pnl']<0)
    return w/l if l>0 else 0

def sharpe(trades):
    if len(trades)<2: return 0
    tdf=pd.DataFrame(trades); tdf['date']=pd.to_datetime(tdf['date'])
    m=tdf.resample('ME',on='date')['pnl'].sum()
    return (m.mean()/m.std())*np.sqrt(12) if m.std()>0 else 0

# ── Load all data + signals ───────────────────────────────────────────────────
files=sorted(glob.glob(f'{CSV_DIR}/*.csv'))
print(f'Loading {len(files)} stocks...')
long_data =[]; short_data=[]
for f in files:
    df=load(f)
    long_data.append((df, get_long_signals(df)))
    short_data.append((df, get_short_signals(df)))

# ── Sweep LONG ────────────────────────────────────────────────────────────────
print('Sweeping LONG...')
best_long_pf=0; best_long_sl=0; best_long_tp=0
for sl_m in SL_VALS:
    for tp_m in TP_VALS:
        t=[]; [t.extend(sim_long(df,s,sl_m,tp_m)) for df,s in long_data]
        p=pf(t)
        if p>best_long_pf: best_long_pf=p; best_long_sl=sl_m; best_long_tp=tp_m

# ── Sweep SHORT ───────────────────────────────────────────────────────────────
print('Sweeping SHORT...')
best_short_pf=0; best_short_sl=0; best_short_tp=0
for sl_m in SL_VALS:
    for tp_m in TP_VALS:
        t=[]; [t.extend(sim_short(df,s,sl_m,tp_m)) for df,s in short_data]
        p=pf(t)
        if p>best_short_pf: best_short_pf=p; best_short_sl=sl_m; best_short_tp=tp_m

print(f'\nBest LONG:  SL={best_long_sl}x  TP={best_long_tp}x  PF={best_long_pf:.4f}')
print(f'Best SHORT: SL={best_short_sl}x  TP={best_short_tp}x  PF={best_short_pf:.4f}')

# ── Run at best configs ───────────────────────────────────────────────────────
long_best=[]; [long_best.extend(sim_long(df,s,best_long_sl,best_long_tp)) for df,s in long_data]
short_best=[]; [short_best.extend(sim_short(df,s,best_short_sl,best_short_tp)) for df,s in short_data]

# ── Print ─────────────────────────────────────────────────────────────────────
print(f'\n{"="*60}')
print(f'v0 LONG  best: SL={best_long_sl}x TP={best_long_tp}x  |  N={len(long_best)}  PF={pf(long_best):.4f}  Sharpe={sharpe(long_best):.3f}')
print(f'v2 SHORT best: SL={best_short_sl}x TP={best_short_tp}x  |  N={len(short_best)}  PF={pf(short_best):.4f}  Sharpe={sharpe(short_best):.3f}')
print(f'{"="*60}')

print(f'\n  {"Year":<6} {"v0 PF":>8} {"v0 Sharpe":>10} {"v2 PF":>8} {"v2 Sharpe":>10}')
print(f'  {"-"*48}')
for yr in [2022,2023,2024,2025]:
    lt=[t for t in long_best  if t['year']==yr]
    st=[t for t in short_best if t['year']==yr]
    print(f'  {yr}  {pf(lt):>8.4f}  {sharpe(lt):>10.3f}  {pf(st):>8.4f}  {sharpe(st):>10.3f}')
