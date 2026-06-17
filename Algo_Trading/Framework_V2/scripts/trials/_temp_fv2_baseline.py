# Exact fv2 baseline bounce logic — replicates fv2_batch_build.py
# Touch : low <= MA20
# Bounce: close > MA20 AND volume >= 1.2x vol_ma20, within tb3, same day
# Entry : bounce+1 bar open, same day
# ATR   : from touch bar
# SL    : entry - 2.5 x ATR14
# TGT   : entry + 4.5 x ATR14  (checked before SL on same bar)
# EOD   : last bar of entry day, exit at close

import pandas as pd, numpy as np, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
SL_MULT = 2.5; TGT_MULT = 4.5; MAX_TB_GAP = 3

STOCKS = [
    'ADANIPORTS','ASHOKLEY','AXISBANK','BAJFINANCE','BANDHANBNK',
    'BHARTIARTL','CIPLA','COALINDIA','DABUR','DIVISLAB',
    'HDFCBANK','HINDALCO','ICICIBANK','INDUSINDBK','INFY',
    'ITC','JSWSTEEL','NATIONALUM','NTPC','ONGC',
    'PNB','POWERGRID','RELIANCE','SBIN','SUNPHARMA',
    'TATAMOTORS','TATASTEEL','TECHM','VEDL','WIPRO',
]

all_pnls = []; all_wins_tgt = 0; all_wins_pnl = 0
stock_rows = []

for stock in STOCKS:
    df = pd.read_csv(os.path.join(DATA_DIR, f'{stock}_5min.csv'))
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date']     = df['datetime'].dt.date
    df = df[df['datetime'].dt.year.between(2022, 2025)].copy().reset_index(drop=True)

    pc        = df['close'].shift(1)
    tr        = np.maximum(df['high']-df['low'],
                np.maximum((df['high']-pc).abs(), (df['low']-pc).abs()))
    df['atr14']   = tr.rolling(14, min_periods=14).mean()
    df['ma20']    = df['close'].rolling(20, min_periods=20).mean()
    df['vol_ma20']= df['volume'].rolling(20, min_periods=20).mean()

    eod_dts = set(df.groupby('date')['datetime'].last())

    n = len(df); i = 0; pnls = []; wins_tgt = 0; wins_pnl = 0
    while i < n:
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']) or pd.isna(row['vol_ma20']):
            i += 1; continue
        if row['low'] > row['ma20']:
            i += 1; continue

        touch_idx  = i; touch_date = row['date']; atr = row['atr14']

        bounce_idx = None
        for j in range(touch_idx, min(touch_idx + MAX_TB_GAP + 1, n)):
            b = df.iloc[j]
            if b['date'] != touch_date: break
            if b['close'] > b['ma20'] and b['volume'] >= 1.2 * b['vol_ma20']:
                bounce_idx = j; break

        if bounce_idx is None or bounce_idx + 1 >= n:
            i += 1; continue

        entry_idx = bounce_idx + 1
        entry_row = df.iloc[entry_idx]
        if entry_row['date'] != touch_date:
            i += 1; continue

        entry = entry_row['open']
        sl    = entry - SL_MULT  * atr
        tgt   = entry + TGT_MULT * atr

        exit_reason = None; pnl = 0.0
        for k in range(entry_idx, n):
            krow = df.iloc[k]
            if krow['date'] != touch_date:
                pnl = df.iloc[k-1]['close'] - entry; exit_reason = 'EOD'; break
            if krow['high'] >= tgt:
                pnl = tgt - entry; exit_reason = 'TGT'; break
            if krow['low'] <= sl:
                pnl = sl - entry; exit_reason = 'SL'; break
            if krow['datetime'] in eod_dts:
                pnl = krow['close'] - entry; exit_reason = 'EOD'; break

        if exit_reason is None:
            i = k + 1; continue

        pnl = round(pnl, 4)
        pnls.append(pnl)
        wins_tgt += (1 if exit_reason == 'TGT' else 0)
        wins_pnl += (1 if pnl > 0 else 0)
        i = k + 1

    arr = np.asarray(pnls); sn = len(arr)
    gp = arr[arr>0].sum(); gl = abs(arr[arr<0].sum())
    pf = float(gp/gl) if gl>0 else 9999.0
    aw = arr[arr>0].mean() if (arr>0).any() else 0
    al = arr[arr<0].mean() if (arr<0).any() else 0
    be = (-al)/(aw-al)*100 if (aw>0 and al<0) else 0
    tgt_wr = wins_tgt/sn*100 if sn>0 else 0
    eco_wr = wins_pnl/sn*100 if sn>0 else 0
    stock_rows.append((stock, sn, tgt_wr, eco_wr, be, arr.sum(), pf))
    all_pnls.extend(pnls); all_wins_tgt += wins_tgt; all_wins_pnl += wins_pnl

# Portfolio totals
arr = np.asarray(all_pnls); n = len(arr)
gp=arr[arr>0].sum(); gl=abs(arr[arr<0].sum())
pf=float(gp/gl) if gl>0 else 9999.0
aw=arr[arr>0].mean() if (arr>0).any() else 0
al=arr[arr<0].mean() if (arr<0).any() else 0
be=(-al)/(aw-al)*100 if (aw>0 and al<0) else 0

# Sort by PF, top 10
stock_rows.sort(key=lambda x: x[6], reverse=True)

print('\nfv2 Baseline — no volume filter | 30 stocks | 2022-2025 | sorted by PF')
print('='*78)
print(f"  {'Stock':<13} {'N':>5}  {'TGT-WR':>7}  {'Eco-WR':>7}  {'BE%':>6}  {'Net PnL':>11}  {'PF':>7}")
print('-'*78)
for i,(stock,sn,twr,ewr,be,net,pf) in enumerate(stock_rows):
    mk = '+' if pf>=1.0 else ' '
    marker = ' ← TOP 10' if i < 10 else ''
    print(f"  {mk}{stock:<12} {sn:>5,}  {twr:>6.1f}%  {ewr:>6.1f}%  {be:>5.1f}%  {net:>11,.1f}  {pf:>7.3f}{marker}")
print('='*78)
print(f"  {'TOTAL':<13} {n:>5,}  {all_wins_tgt/n*100:>6.1f}%  {all_wins_pnl/n*100:>6.1f}%  {be:>5.1f}%  {arr.sum():>11,.1f}  {pf:>7.3f}")
print('='*78)
print('  TGT-WR = target hit only | Eco-WR = pnl>0 | BE% = empirical breakeven')
