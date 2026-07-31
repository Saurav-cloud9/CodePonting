"""
CBQ — v1.1 best combo SL=2.5x TP=6.0x
"""
import sys, io, glob, pandas as pd, numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_DIR='Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'
ATR_LEN=14; MA_LEN=20; EMA_SPAN=100; EOD_HOUR=15
SL_M=2.5; TP_M=6.0

def load(f):
    df=pd.read_csv(f,low_memory=False); df.columns=df.columns.str.strip()
    df['datetime']=pd.to_datetime(df['datetime']).apply(lambda x: x.replace(tzinfo=None) if x.tzinfo else x)
    for col in ['open','high','low','close','volume']: df[col]=pd.to_numeric(df[col],errors='coerce')
    df=df.sort_values('datetime').reset_index(drop=True)
    df['date']=df['datetime'].dt.date; df['hour']=df['datetime'].dt.hour
    df['ma20']=df['close'].rolling(MA_LEN).mean()
    df['ema100']=df['close'].ewm(span=EMA_SPAN,adjust=False).mean()
    df['tp']=(df['high']+df['low']+df['close'])/3
    df['cum_tpv']=df.groupby('date').apply(lambda g:(g['tp']*g['volume']).cumsum(),include_groups=False).reset_index(level=0,drop=True)
    df['cum_vol']=df.groupby('date')['volume'].cumsum()
    df['vwap']=df['cum_tpv']/df['cum_vol']
    prev_c=df['close'].shift(1)
    tr=pd.concat([df['high']-df['low'],(df['high']-prev_c).abs(),(df['low']-prev_c).abs()],axis=1).max(axis=1)
    df['atr']=tr.ewm(alpha=1/ATR_LEN,adjust=False).mean()
    return df.dropna(subset=['ma20','ema100','vwap','atr']).reset_index(drop=True)

def get_trades(df, sl_m, tp_m):
    high=df['high'].values; low=df['low'].values; close=df['close'].values
    open_=df['open'].values; ma=df['ma20'].values; ema=df['ema100'].values
    vwap=df['vwap'].values; atr=df['atr'].values
    hour=df['hour'].values; date=df['date'].values; n=len(df)
    trades=[]; next_allowed=0
    for i in range(n-1):
        if i < next_allowed: continue
        if (low[i]<=ma[i] and open_[i]>ma[i] and close[i]>ma[i]
                and close[i]>=vwap[i] and close[i]<ema[i] and hour[i]<EOD_HOUR):
            ei=i+1
            if date[ei]!=date[i]: continue
            entry=open_[ei]; sl=entry-sl_m*atr[i]; tp=entry+tp_m*atr[i]
            for k in range(ei,n):
                if hour[k]>=EOD_HOUR or date[k]!=date[i]: pnl=open_[k]-entry; break
                if high[k]>=tp: pnl=tp-entry; break
                if low[k]<=sl:   pnl=sl-entry;  break
            next_allowed=k+1
            trades.append({'pnl':pnl,'year':df.iloc[ei]['datetime'].year,'entry':entry,'exit':entry+pnl})
    return trades

def run_cbq(trades, label):
    raw_w=sum(t['pnl'] for t in trades if t['pnl']>0)
    raw_l=sum(-t['pnl'] for t in trades if t['pnl']<0)
    print(f'{label}  N={len(trades)}  Raw PF={raw_w/raw_l:.3f}')
    print(f"{'Qty':>6}  {'NPF':>6}  {'Net PnL':>10}  {'Avg charge':>11}")
    print('-'*45)
    for qty in [1,2,3,5,10,20,50,100,200,500,1000]:
        net=[]; tc=0
        for t in trades:
            e=t['entry']; x=t['exit']; raw=t['pnl']*qty
            brok=min((e+x)*qty*0.0005,40); stt=x*qty*0.00025
            txn=(e+x)*qty*0.0000297; sebi=(e+x)*qty*0.000001
            stamp=e*qty*0.00003; gst=0.18*(brok+txn)
            c=brok+stt+txn+sebi+stamp+gst; tc+=c; net.append(raw-c)
        w=sum(v for v in net if v>0); l=sum(-v for v in net if v<0)
        npf=w/l if l>0 else 0
        print(f'{qty:>6}  {npf:>6.3f}  {sum(net):>10.0f}  {tc/len(trades):>11.2f}')

files=sorted(glob.glob(f'{CSV_DIR}/*.csv'))
dfs=[load(f) for f in files]

t_best=[]; t_default=[]
for df in dfs:
    t_best.extend(get_trades(df, 2.5, 6.0))
    t_default.extend(get_trades(df, 2.5, 4.5))

run_cbq(t_default, 'DEFAULT SL=2.5x TP=4.5x')
print()
run_cbq(t_best,    'BEST    SL=2.5x TP=6.0x')
