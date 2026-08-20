import pandas as pd, numpy as np, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR   = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
MAX_TB_GAP = 3; SL_MULT = 2.5; TP_MULT = 4.5; CUT_EXIT = 15 * 60

STOCKS = [
    'ADANIPORTS','ASHOKLEY','AXISBANK','BAJFINANCE','BANDHANBNK',
    'BHARTIARTL','CIPLA','COALINDIA','DABUR','DIVISLAB',
    'HDFCBANK','HINDALCO','ICICIBANK','INDUSINDBK','INFY',
    'ITC','JSWSTEEL','NATIONALUM','NTPC','ONGC',
    'PNB','POWERGRID','RELIANCE','SBIN','SUNPHARMA',
    'TATAMOTORS','TATASTEEL','TECHM','VEDL','WIPRO',
]

def _wma(s, n):
    w = np.arange(1, n+1, dtype=float); w /= w.sum()
    return pd.Series(s).rolling(n).apply(lambda x: np.dot(x, w), raw=True)

def hma20(c):
    raw = 2*_wma(c,10) - _wma(c,20)
    return _wma(raw, 4).values

def sma20(c):
    return pd.Series(c).rolling(20, min_periods=20).mean().values

def run(stock, ma_fn, open_filter):
    df = pd.read_csv(os.path.join(DATA_DIR, f'{stock}_5min.csv'))
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date']     = df['datetime'].dt.date
    df = df[df['datetime'].dt.year.between(2022,2025)].copy().reset_index(drop=True)
    pc  = df['close'].shift(1)
    tr  = np.maximum(df['high']-df['low'], np.maximum((df['high']-pc).abs(),(df['low']-pc).abs()))
    atr = tr.rolling(14, min_periods=14).mean().values
    ma  = ma_fn(df['close'].values)
    dates = np.array([d.toordinal() for d in df['date']])
    mins  = (df['datetime'].dt.hour*60 + df['datetime'].dt.minute).values
    op=df['open'].values; hi=df['high'].values; lo=df['low'].values; cl=df['close'].values
    N=len(df); pnls=[]; wins=0; i=24 if ma_fn==hma20 else 20

    while i < N-2:
        m=ma[i]; a=atr[i]
        if np.isnan(m) or np.isnan(a) or lo[i]>m: i+=1; continue
        if open_filter and op[i]<=m: i+=1; continue
        d0=dates[i]; lim=min(i+MAX_TB_GAP+1,N-1); bb=-1
        for j in range(i,lim):
            if dates[j]!=d0: break
            if cl[j]>ma[j]: bb=j; break
        if bb<0: i+=1; continue
        eb=bb+1
        if eb>=N or dates[eb]!=d0 or mins[eb]>=CUT_EXIT: i+=1; continue
        entry=op[eb]; sl=entry-SL_MULT*a; tp=entry+TP_MULT*a; pnl=cl[eb]-entry; oc='EOD-'
        for j in range(eb,N):
            if dates[j]!=d0: pnl=cl[j-1]-entry; oc='EOD+' if pnl>0 else 'EOD-'; break
            if mins[j]>=CUT_EXIT: pnl=op[j]-entry; oc='EOD+' if pnl>0 else 'EOD-'; break
            if lo[j]<=sl and hi[j]>=tp:
                if abs(op[j]-sl)<=abs(op[j]-tp): oc='L'; pnl=-SL_MULT*a
                else: oc='W'; pnl=TP_MULT*a
                break
            if lo[j]<=sl: oc='L'; pnl=-SL_MULT*a; break
            if hi[j]>=tp: oc='W'; pnl=TP_MULT*a; break
        pnls.append(round(pnl,4)); wins+=(1 if oc in('W','EOD+') else 0); i=eb+1

    arr=np.asarray(pnls); n=len(arr)
    wr = wins/n*100 if n>0 else 0
    gp=arr[arr>0].sum(); gl=abs(arr[arr<0].sum())
    pf=float(gp/gl) if gl>0 else 9999.0
    aw=arr[arr>0].mean() if (arr>0).any() else 0
    al=arr[arr<0].mean() if (arr<0).any() else 0
    be=(-al)/(aw-al)*100 if (aw>0 and al<0) else 0
    return n, wr, be, arr.sum(), pf

def print_table(title, rows):
    rows_s = sorted(rows, key=lambda x: x[5], reverse=True)
    print(f'\n{title}')
    print('='*64)
    print(f"  {'Stock':<13} {'N':>6}  {'WR%':>6}  {'BE%':>6}  {'Net PnL':>10}  {'PF':>7}")
    print('-'*64)
    for stock,n,wr,be,net,pf in rows_s:
        mk='+' if pf>=1.0 else ' '
        print(f"  {mk}{stock:<12} {n:>6,}  {wr:>5.1f}%  {be:>5.1f}%  {net:>10,.1f}  {pf:>7.3f}")
    print('='*64)

rows_a=[]; rows_b=[]
for stock in STOCKS:
    n,wr,be,net,pf = run(stock, sma20, open_filter=False)
    rows_a.append((stock,n,wr,be,net,pf))
    n,wr,be,net,pf = run(stock, hma20, open_filter=True)
    rows_b.append((stock,n,wr,be,net,pf))
    print(f'  {stock} done', flush=True)

print_table('SMA20 raw (no open filter) — sorted by PF', rows_a)
print_table('HMA20 raw + open>MA — sorted by PF', rows_b)
