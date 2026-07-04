import pandas as pd
import os


DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
SYMBOL = 'TATAMOTORS'
csv = os.path.join(DATA_DIR, f'{SYMBOL}_5min.csv')

df = pd.read_csv(csv)
df.columns = df.columns.str.strip()
df['datetime'] = pd.to_datetime(df['datetime'])
df['date'] = df['datetime'].dt.date
df['hour'] = df['datetime'].dt.hour

MA_COL = 'ma20'
SL_MULT = 2.5
TGT_MULT = 4.5
MAX_TB_GAP = 3
EOD_TIME = 15

i = 0
trades = []
while i < len(df):
    row = df.iloc[i]
    if row['low'] <= row['ma20']:
        if row['hour'] >= 15:
            i += 1
            continue
        touch_bar = row
        touch_date = touch_bar['date']
        atr = touch_bar['atr14']
        bounce_bar = None
        for j in range(i, i + MAX_TB_GAP + 1):
            b = df.iloc[j]
            if b['date'] != touch_date:
                break
            if b['close'] > b['ma20']:
                bounce_bar = b
                break
        if bounce_bar is None:
            i += 1
            continue
        entry_idx = j + 1
        entry_bar = df.iloc[entry_idx]
        if entry_bar['date'] != touch_date:
            i += 1
            continue
        entry = entry_bar['open']
        sl = entry - SL_MULT * atr
        tgt = entry + TGT_MULT * atr
        for k in range(entry_idx, len(df)):
            k_bar = df.iloc[k]
            if k_bar['hour'] >= EOD_TIME:
                pnl = k_bar['open'] - entry
                outcome = 'EOD+' if k_bar['open'] > entry else 'EOD-'               
                break
            if k_bar['high'] >= tgt:
                pnl = tgt - entry
                outcome = 'W'
                break
            if k_bar['low'] <= sl:
                pnl = sl - entry
                outcome = 'L'
                break
        trades.append({'pnl': pnl, 'outcome': outcome})       
        i = k + 1
    else:
        i += 1
results = pd.DataFrame(trades)
print(f"Trades: {len(results)}")
print(f"Net Pnl: {results['pnl'].sum():.2f}")
wins = results[results['pnl'] > 0].shape[0]
gross_profit = results[results['pnl'] > 0]['pnl'].sum()
gross_loss = abs(results[results['pnl'] < 0]['pnl'].sum())
pf = gross_profit / gross_loss if gross_loss > 0 else 999
print(f"Profitable Trades: {wins}")
print(f"WR: {wins/len(results)*100:.1f}%")
print(f"PF: {pf:.3f}")

