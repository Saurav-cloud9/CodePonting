"""
CBQ — Baseline SHORT mirror (high>=MA20, open<MA20, close<MA20)
Best combo: SL=2.0x TP=3.5x | 30 stocks 2022-2025
"""
import sys, io, glob, pandas as pd, numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_DIR='Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'
ATR_LEN=14; MA_LEN=20; EOD_HOUR=15
SL_M=2.0; TP_M=3.5

def load(f):
    df=pd.read_csv(f,low_memory=False); df.columns=df.columns.str.strip()
    df['datetime']=pd.to_datetime(df['datetime']).apply(lambda x: x.replace(tzinfo=None) if x.tzinfo else x)
    for col in ['open','high','low','close','volume']: df[col]=pd.to_numeric(df[col],errors='coerce')
    df=df.sort_values('datetime').reset_index(drop=True)
    df['date']=df['datetime'].dt.date; df['hour']=df['datetime'].dt.hour
    df['ma20']=df['close'].rolling(MA_LEN).mean()
    prev_c=df['close'].shift(1)
    tr=pd.concat([df['high']-df['low'],(df['high']-prev_c).abs(),(df['low']-prev_c).abs()],axis=1).max(axis=1)
    df['atr']=tr.ewm(alpha=1/ATR_LEN,adjust=False).mean()
    return df.dropna(subset=['ma20','atr']).reset_index(drop=True)

def get_trades(df):
    high=df['high'].values; low=df['low'].values; close=df['close'].values
    open_=df['open'].values; ma=df['ma20'].values; atr=df['atr'].values
    hour=df['hour'].values; date=df['date'].values; n=len(df)
    trades=[]; next_allowed=0
    for i in range(n-1):
        if i < next_allowed: continue
        if (high[i]>=ma[i] and open_[i]<ma[i] and close[i]<ma[i] and hour[i]<EOD_HOUR):
            ei=i+1
            if date[ei]!=date[i]: continue
            entry=open_[ei]
            sl  = entry + SL_M  * atr[i]   # SL above entry
            tp = entry - TP_M * atr[i]   # TP below entry
            for k in range(ei,n):
                if hour[k]>=EOD_HOUR or date[k]!=date[i]: pnl=entry-open_[k]; break
                if low[k]<=tp:  pnl=entry-tp; break
                if high[k]>=sl:  pnl=entry-sl;  break
            next_allowed=k+1
            trades.append({'pnl':pnl,'year':df.iloc[ei]['datetime'].year,
                           'entry':entry,'exit':entry-pnl})
    return trades

files=sorted(glob.glob(f'{CSV_DIR}/*.csv'))
print(f'Loading {len(files)} stocks...')
all_trades=[]
for f in files:
    all_trades.extend(get_trades(load(f)))

raw_w=sum(t['pnl'] for t in all_trades if t['pnl']>0)
raw_l=sum(-t['pnl'] for t in all_trades if t['pnl']<0)
print(f'Baseline SHORT CBQ -- SL={SL_M}x TP={TP_M}x  N={len(all_trades)}  Raw PF={raw_w/raw_l:.3f}')
print()
print(f"{'Qty':>6}  {'NPF':>6}  {'Net PnL':>10}  {'Avg charge':>11}")
print('-'*45)
for qty in [1,2,3,5,10,20,50,100,200,500,1000]:
    net=[]; tc=0
    for t in all_trades:
        e=t['entry']; x=t['exit']; raw=t['pnl']*qty
        brok=min((e+x)*qty*0.0005,40); stt=x*qty*0.00025
        txn=(e+x)*qty*0.0000297; sebi=(e+x)*qty*0.000001
        stamp=e*qty*0.00003; gst=0.18*(brok+txn)
        c=brok+stt+txn+sebi+stamp+gst; tc+=c; net.append(raw-c)
    w=sum(v for v in net if v>0); l=sum(-v for v in net if v<0)
    npf=w/l if l>0 else 0
    marker='  <-- NPF > 1.0' if npf>=1.0 else ''
    print(f'{qty:>6}  {npf:>6.3f}  {sum(net):>10.0f}  {tc/len(all_trades):>11.2f}{marker}')

print()
print('Year-wise at qty=1:')
for yr in [2022,2023,2024,2025]:
    g=[t for t in all_trades if t['year']==yr]
    if not g: continue
    npf_net=[]; tc=0
    for t in g:
        e=t['entry']; x=t['exit']; raw=t['pnl']
        brok=min((e+x)*0.0005,40); stt=x*0.00025
        txn=(e+x)*0.0000297; sebi=(e+x)*0.000001
        stamp=e*0.00003; gst=0.18*(brok+txn)
        c=brok+stt+txn+sebi+stamp+gst; tc+=c; npf_net.append(raw-c)
    w=sum(v for v in npf_net if v>0); l=sum(-v for v in npf_net if v<0)
    gw=sum(t['pnl'] for t in g if t['pnl']>0); gl=sum(-t['pnl'] for t in g if t['pnl']<0)
    print(f'  {yr}  N={len(g)}  Raw PF={gw/gl:.3f}  NPF={w/l if l>0 else 0:.3f}  Net PnL={sum(npf_net):.0f}')
