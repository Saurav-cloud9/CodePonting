import pandas as pd, numpy as np, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR   = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
MAX_TB_GAP = 3; SL_MULT = 2.5; TGT_MULT = 4.5; CUT_EXIT = 15 * 60
P05_MIN, P05_MAX = 0.0, 1.6; P06_MAX = 55; P08_MIN = 0.5
STOCK = 'ASHOKLEY'

def _pf(arr):
    gp=arr[arr>0].sum(); gl=abs(arr[arr<0].sum())
    return float(gp/gl) if gl>0 else 9999.0

def show(label, pnls, wins):
    arr=np.asarray(pnls); n=len(arr)
    if n==0: print(f"  {label:<30}  N=0"); return
    wr=wins/n*100
    pf=_pf(arr)
    aw=arr[arr>0].mean() if (arr>0).any() else 0
    al=arr[arr<0].mean() if (arr<0).any() else 0
    be=(-al)/(aw-al)*100 if (aw>0 and al<0) else 0
    mk='+' if pf>=1.0 else ' '
    print(f"  {mk}{label:<29} N={n:>5,}  WR={wr:>5.1f}%  BE={be:>5.1f}%  PF={pf:>7.3f}")

df = pd.read_csv(os.path.join(DATA_DIR, f'{STOCK}_5min.csv'))
df.columns = df.columns.str.strip()
df['datetime'] = pd.to_datetime(df['datetime'])
df['date']     = df['datetime'].dt.date
df = df[df['datetime'].dt.year.between(2022,2025)].copy().reset_index(drop=True)
pc  = df['close'].shift(1)
tr  = np.maximum(df['high']-df['low'], np.maximum((df['high']-pc).abs(),(df['low']-pc).abs()))
atr = tr.rolling(14, min_periods=14).mean().values
vm  = df['volume'].rolling(20, min_periods=20).mean().values
vr  = df['volume'].values / vm
ma  = df['close'].rolling(20, min_periods=20).mean().values
dates = np.array([d.toordinal() for d in df['date']])
mins  = (df['datetime'].dt.hour*60 + df['datetime'].dt.minute).values
op=df['open'].values; hi=df['high'].values; lo=df['low'].values; cl=df['close'].values
N=len(df)

# run with configurable filters
def run(open_f=False, p05_f=False, p06_f=False, p08_f=False, p11_f=False):
    pnls=[]; wins=0; i=20
    while i < N-2:
        m=ma[i]; a=atr[i]
        if np.isnan(m) or np.isnan(a) or lo[i]>m: i+=1; continue
        if open_f and op[i]<=m: i+=1; continue
        d0=dates[i]; lim=min(i+MAX_TB_GAP+1,N-1); bb=-1
        for j in range(i,lim):
            if dates[j]!=d0: break
            if cl[j]>ma[j]: bb=j; break
        if bb<0: i+=1; continue
        eb=bb+1
        if eb>=N or dates[eb]!=d0 or mins[eb]>=CUT_EXIT: i+=1; continue
        if p05_f:
            cr=hi[i]-lo[i]; p05=(m-lo[i])/a if a>0 else np.nan
            if np.isnan(p05) or not(P05_MIN<=p05<=P05_MAX): i+=1; continue
        if p06_f:
            cr=hi[i]-lo[i]; p06=abs(cl[i]-op[i])/cr*100 if cr>0 else 100.0
            if p06>P06_MAX: i+=1; continue
        if p08_f:
            p08=vr[bb]
            if np.isnan(p08) or p08<P08_MIN: i+=1; continue
        if p11_f:
            if op[eb]<=cl[bb]: i+=1; continue
        entry=op[eb]; sl=entry-SL_MULT*a; tgt=entry+TGT_MULT*a; pnl=cl[eb]-entry; oc='EOD-'
        for j in range(eb,N):
            if dates[j]!=d0: pnl=cl[j-1]-entry; oc='EOD+' if pnl>0 else 'EOD-'; break
            if mins[j]>=CUT_EXIT: pnl=op[j]-entry; oc='EOD+' if pnl>0 else 'EOD-'; break
            if lo[j]<=sl and hi[j]>=tgt:
                if abs(op[j]-sl)<=abs(op[j]-tgt): oc='L'; pnl=-SL_MULT*a
                else: oc='W'; pnl=TGT_MULT*a
                break
            if lo[j]<=sl: oc='L'; pnl=-SL_MULT*a; break
            if hi[j]>=tgt: oc='W'; pnl=TGT_MULT*a; break
        pnls.append(round(pnl,4)); wins+=(1 if oc in('W','EOD+') else 0); i=eb+1
    return pnls, wins

print(f'\nASHOKLEY — SMA20 | 2022-2025 | isolating what changed\n')
print('='*65)
p,w = run();                           show('raw (no filters)',            p,w)
p,w = run(open_f=True);               show('+open>MA',                    p,w)
p,w = run(p11_f=True);                show('+p11 only',                   p,w)
p,w = run(p08_f=True);                show('+p08 only',                   p,w)
p,w = run(p05_f=True);                show('+p05 only',                   p,w)
p,w = run(p06_f=True);                show('+p06 only',                   p,w)
p,w = run(p05_f=True,p06_f=True,
          p08_f=True,p11_f=True);     show('all gates (no open>MA)',       p,w)
p,w = run(open_f=True,p05_f=True,
          p06_f=True,p08_f=True,
          p11_f=True);                show('all gates + open>MA',          p,w)
print('='*65)
