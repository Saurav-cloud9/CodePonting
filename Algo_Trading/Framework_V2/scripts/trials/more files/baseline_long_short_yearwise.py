"""
Baseline LONG vs SHORT — year-wise comparison
Same SL=2.0x TP=3.5x, position guard, 30 stocks 2022-2025
Long:  low<=MA20, open>MA20, close>MA20
Short: high>=MA20, open<MA20, close<MA20
"""
import sys, io, glob, pandas as pd, numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_DIR='Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'
ATR_LEN=14; MA_LEN=20; EOD_HOUR=15; SL_M=2.0; TP_M=3.5

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

def get_trades(df, side):
    high=df['high'].values; low=df['low'].values; close=df['close'].values
    open_=df['open'].values; ma=df['ma20'].values; atr=df['atr'].values
    hour=df['hour'].values; date=df['date'].values; n=len(df)
    trades=[]; next_allowed=0
    for i in range(n-1):
        if i < next_allowed: continue
        if side == 'long':
            signal = low[i]<=ma[i] and open_[i]>ma[i] and close[i]>ma[i]
        else:
            signal = high[i]>=ma[i] and open_[i]<ma[i] and close[i]<ma[i]
        if signal and hour[i]<EOD_HOUR:
            ei=i+1
            if date[ei]!=date[i]: continue
            entry=open_[ei]
            if side == 'long':
                sl=entry-SL_M*atr[i]; tp=entry+TP_M*atr[i]
            else:
                sl=entry+SL_M*atr[i]; tp=entry-TP_M*atr[i]
            for k in range(ei,n):
                if hour[k]>=EOD_HOUR or date[k]!=date[i]:
                    pnl=(open_[k]-entry) if side=='long' else (entry-open_[k]); break
                if side=='long':
                    if high[k]>=tp: pnl=tp-entry; break
                    if low[k]<=sl:   pnl=sl-entry;  break
                else:
                    if low[k]<=tp:  pnl=entry-tp; break
                    if high[k]>=sl:  pnl=entry-sl;  break
            next_allowed=k+1
            trades.append({'pnl':pnl,'year':df.iloc[ei]['datetime'].year})
    return trades

def summarise(trades, label):
    print(f'\n{label}  (SL={SL_M}x TP={TP_M}x)')
    print(f"{'Year':<6} {'N':>6}  {'PF':>6}  {'Sharpe':>7}  {'WR%':>6}")
    print('-'*38)
    all_t = []
    for yr in [2022,2023,2024,2025]:
        g=[t for t in trades if t['year']==yr]
        if not g: continue
        gw=sum(t['pnl'] for t in g if t['pnl']>0)
        gl=sum(-t['pnl'] for t in g if t['pnl']<0)
        wr=sum(1 for t in g if t['pnl']>0)/len(g)*100
        tdf=pd.DataFrame(g); tdf['date']=pd.to_datetime([f'{yr}-01-01']*len(g))
        # monthly sharpe approximation
        pnls=[t['pnl'] for t in g]
        sh = (np.mean(pnls)/np.std(pnls))*np.sqrt(252*78/12) if np.std(pnls)>0 else 0
        print(f"  {yr}  {len(g):>6}  {gw/gl if gl>0 else 0:>6.3f}  {sh:>7.3f}  {wr:>5.1f}%")
        all_t.extend(g)
    gw=sum(t['pnl'] for t in all_t if t['pnl']>0)
    gl=sum(-t['pnl'] for t in all_t if t['pnl']<0)
    wr=sum(1 for t in all_t if t['pnl']>0)/len(all_t)*100
    # proper monthly sharpe
    tdf=pd.DataFrame(all_t); tdf['month']=tdf['year'].astype(str)+'-01'
    pnls=[t['pnl'] for t in all_t]
    sh=(np.mean(pnls)/np.std(pnls))*np.sqrt(252*78/12) if np.std(pnls)>0 else 0
    print(f"  {'ALL':<4}  {len(all_t):>6}  {gw/gl if gl>0 else 0:>6.3f}  {sh:>7.3f}  {wr:>5.1f}%")

files=sorted(glob.glob(f'{CSV_DIR}/*.csv'))
print(f'Loading {len(files)} stocks...')
long_trades=[]; short_trades=[]
for f in files:
    df=load(f)
    long_trades.extend(get_trades(df,'long'))
    short_trades.extend(get_trades(df,'short'))

summarise(long_trades,  'BASELINE LONG  (low<=MA20, open>MA20, close>MA20)')
summarise(short_trades, 'BASELINE SHORT (high>=MA20, open<MA20, close<MA20)')
