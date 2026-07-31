"""
ABC SHORT SL=0.3 TP=0.3 — NPF qty sweep
"""
import sys, io, glob, pandas as pd, numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_DIR  = 'Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'
ZZ_LEN=8; FIB_LO=0.382; FIB_HI=0.618; ERR_RATE=0.05
MAX_BARS=6; ATR_LEN=14; EOD_HOUR=15
MA_SPANS=[50,100,150,200]; EMA_SPANS=[20,40]
FIB_LO_EFF=FIB_LO*(1-ERR_RATE); FIB_HI_EFF=FIB_HI*(1+ERR_RATE)
SL_M=0.3; TP_M=0.3

def load(f):
    df=pd.read_csv(f,low_memory=False); df.columns=df.columns.str.strip()
    df['datetime']=pd.to_datetime(df['datetime']).apply(
        lambda x: x.replace(tzinfo=None) if x.tzinfo else x)
    for col in ['open','high','low','close','volume']:
        df[col]=pd.to_numeric(df[col],errors='coerce')
    df=df.sort_values('datetime').reset_index(drop=True)
    df['date']=df['datetime'].dt.date; df['hour']=df['datetime'].dt.hour
    for sp in MA_SPANS:  df[f'sma{sp}']=df['close'].rolling(sp).mean()
    for sp in EMA_SPANS: df[f'ema{sp}']=df['close'].ewm(span=sp,adjust=False).mean()
    prev_c=df['close'].shift(1)
    tr=pd.concat([df['high']-df['low'],(df['high']-prev_c).abs(),(df['low']-prev_c).abs()],axis=1).max(axis=1)
    df['atr']=tr.ewm(alpha=1/ATR_LEN,adjust=False).mean()
    df['ph']=df['high']==df['high'].rolling(ZZ_LEN).max()
    df['pl']=df['low']==df['low'].rolling(ZZ_LEN).min()
    ma_cols=[f'sma{s}' for s in MA_SPANS]+[f'ema{s}' for s in EMA_SPANS]
    return df.dropna(subset=ma_cols+['atr']).reset_index(drop=True)

def get_short_signals(df):
    ma_cols=[f'sma{s}' for s in MA_SPANS]+[f'ema{s}' for s in EMA_SPANS]
    ma_vals=df[ma_cols].values
    high=df['high'].values; low=df['low'].values
    close=df['close'].values; open_=df['open'].values
    ph=df['ph'].values; pl=df['pl'].values; n=len(df)
    trend=0; up_streak=0; down_streak=0; zigzag=[]
    last_abc_id=None; abc_bar_count=0
    highest_since_c=-np.inf; last_zz_point=None; signals=[]
    for i in range(n):
        body_hi=max(open_[i],close[i]); body_lo=min(open_[i],close[i])
        upper=(ma_vals[i]>=body_hi).sum(); lower=(ma_vals[i]<=body_lo).sum()
        up_streak   =up_streak+1   if lower>0 and upper==0 else 0
        down_streak =down_streak+1 if upper>0 and lower==0 else 0
        if up_streak>=2:    trend=1
        elif down_streak>=2: trend=-1
        changed=False; ctype='H' if ph[i] else ('L' if pl[i] else None)
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
        if changed and ctype=='H' and trend==-1 and len(zigzag)>=5:
            a_price=zigzag[-1][1]; b_price=zigzag[-3][1]; c_price=zigzag[-5][1]
            if high[i]>ma_vals[i].min() and (c_price-b_price)!=0:
                rate=(a_price-b_price)/(c_price-b_price)
                if FIB_LO_EFF<=rate<=FIB_HI_EFF:
                    last_zz_point=a_price; abc_bar_count=0
                    highest_since_c=high[i]; last_abc_id=i; new_abc=True
        if not new_abc:
            abc_bar_count+=1
            if last_zz_point is not None: highest_since_c=max(highest_since_c,high[i])
        if (last_zz_point is not None and trend==-1
                and abc_bar_count<=MAX_BARS and highest_since_c<=last_zz_point
                and last_abc_id is not None):
            sbounced=False
            if i>=1:
                high2=max(high[i],high[i-1])
                if close[i]<open_[i]:
                    for ma in ma_vals[i]:
                        if high2>=ma and close[i]<ma: sbounced=True; break
            if sbounced:
                ei=i+1
                if ei<n and df.iloc[ei]['hour']<EOD_HOUR:
                    signals.append({'entry_i':ei,'atr':df.iloc[i]['atr'],
                                    'date':df.iloc[ei]['date'],
                                    'year':df.iloc[ei]['datetime'].year,
                                    'entry_px':df.iloc[ei]['open']})
                last_abc_id=None
    return signals

def simulate(df, signals):
    trades=[]; high=df['high'].values; low=df['low'].values
    open_=df['open'].values; n=len(df)
    for sig in signals:
        entry=sig['entry_px']; atr=sig['atr']
        sl=entry+SL_M*atr; tp=entry-TP_M*atr
        entry_date=sig['date']
        for k in range(sig['entry_i'],n):
            kb=df.iloc[k]
            if kb['hour']>=EOD_HOUR or kb['date']!=entry_date:
                pnl=entry-open_[k]; break
            if low[k]<=tp:  pnl=entry-tp; break
            if high[k]>=sl:  pnl=entry-sl;  break
        trades.append({'pnl':pnl,'year':sig['year'],
                       'entry':entry,'exit':entry-pnl})
    return trades

def npf_at_qty(trades, qty):
    total_charge=0; net_pnl=0
    for t in trades:
        entry=t['entry']; exit_=t['exit']; raw=t['pnl']*qty
        brok =(entry+exit_)*qty*0.0005
        brok =min(brok, 20*2)          # ₹20 cap per order, 2 orders
        stt  =exit_*qty*0.00025
        txn  =(entry+exit_)*qty*0.0000297
        sebi =(entry+exit_)*qty*0.000001
        stamp=entry*qty*0.00003
        gst  =0.18*(brok+txn)
        charge=brok+stt+txn+sebi+stamp+gst
        total_charge+=charge; net_pnl+=raw-charge
    wins =sum((t['pnl']*qty - c) for t,c in
              zip(trades,[sum([min((t['entry']+t['exit'])*qty*0.0005,40),
                               t['exit']*qty*0.00025,
                               (t['entry']+t['exit'])*qty*0.0000297,
                               (t['entry']+t['exit'])*qty*0.000001,
                               t['entry']*qty*0.00003,
                               0.18*(min((t['entry']+t['exit'])*qty*0.0005,40)+
                                     (t['entry']+t['exit'])*qty*0.0000297)])
                          for t in trades])
              if t['pnl']>0)
    # simpler: compute NPF from net pnl per trade
    net_trades=[]
    for t in trades:
        entry=t['entry']; exit_=t['exit']; raw=t['pnl']*qty
        brok=min((entry+exit_)*qty*0.0005,40)
        stt=exit_*qty*0.00025
        txn=(entry+exit_)*qty*0.0000297
        sebi=(entry+exit_)*qty*0.000001
        stamp=entry*qty*0.00003
        gst=0.18*(brok+txn)
        charge=brok+stt+txn+sebi+stamp+gst
        net_trades.append(raw-charge)
    w=sum(x for x in net_trades if x>0)
    l=sum(-x for x in net_trades if x<0)
    npf_val=w/l if l>0 else 0
    avg_charge=total_charge/len(trades) if trades else 0
    return npf_val, net_pnl, avg_charge

# ── Main ─────────────────────────────────────────────────────────────────────
files=sorted(glob.glob(f'{CSV_DIR}/*.csv'))
print(f'Loading {len(files)} stocks...')
all_data=[(load(f),None) for f in files]
all_data=[(df,get_short_signals(df)) for df,_ in all_data]
all_trades=[]
for df,sigs in all_data: all_trades.extend(simulate(df,sigs))
print(f'Total trades: {len(all_trades)}')

raw_w=sum(t['pnl'] for t in all_trades if t['pnl']>0)
raw_l=sum(-t['pnl'] for t in all_trades if t['pnl']<0)
print(f'Raw PF: {raw_w/raw_l:.3f}')
print()

QTY_LIST=[1,2,3,5,10,20,50,100,200,500,1000]
print(f"{'Qty':>6}  {'NPF':>6}  {'Net PnL':>10}  {'Avg charge':>11}")
print('-'*44)
for qty in QTY_LIST:
    npf_val,net_pnl,avg_c=npf_at_qty(all_trades,qty)
    print(f"{qty:>6}  {npf_val:>6.3f}  {net_pnl:>10.0f}  {avg_c:>11.2f}")
