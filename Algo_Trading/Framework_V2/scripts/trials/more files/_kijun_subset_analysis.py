import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np
from datetime import time as dt_time

KIJUN_LEN=50; ATR_LEN=14; SL_MULT=2.5; TP_MULT=3.0; EOD=dt_time(15,0)
DATA_5MIN='Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'

def compute_atr(df):
    prev_c = df['close'].shift(1)
    tr = pd.concat([df['high']-df['low'],
                    (df['high']-prev_c).abs(),
                    (df['low']-prev_c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/ATR_LEN, adjust=False).mean()

def run(symbol):
    df = pd.read_csv(f'{DATA_5MIN}/{symbol}_5min.csv')
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime']).apply(
        lambda x: x.replace(tzinfo=None) if x.tzinfo else x)
    df = df.sort_values('datetime').reset_index(drop=True)
    df['date'] = df['datetime'].dt.date
    df['t']    = df['datetime'].dt.time
    daily = df.set_index('datetime').resample('D').agg(
        high=('high','max'), low=('low','min'), close=('close','last')).dropna()
    daily['kijun'] = (daily['high'].rolling(KIJUN_LEN).max() +
                      daily['low'].rolling(KIJUN_LEN).min()) / 2
    daily['kijun'] = daily['kijun'].shift(1)
    km = daily.dropna(subset=['kijun'])['kijun']
    km.index = km.index.date
    df['kijun'] = df['date'].map(km)
    df = df.dropna(subset=['kijun','open','high','low','close']).reset_index(drop=True)
    df['atr'] = compute_atr(df)
    df['touch']     = ((df['low'].shift(1) >= df['kijun'].shift(1)) &
                       (df['low'] < df['kijun']) & (df['open'] > df['kijun']))
    df['confirmed'] = (df['touch'].shift(1) &
                       (df['low'] > df['kijun']) & (df['close'] > df['low']))
    results = []; in_trade = False; ep = sl = tp = entry_date = None
    for i in range(2, len(df)):
        row = df.iloc[i]; prev = df.iloc[i-1]
        if in_trade:
            hit_sl  = row['low']  <= sl
            hit_tp = row['high'] >= tp
            is_eod  = row['t'] >= EOD or row['date'] != entry_date
            if hit_sl and hit_tp: pnl, ex = sl-ep, 'SL'
            elif hit_tp:          pnl, ex = tp-ep, 'TP'
            elif hit_sl:           pnl, ex = sl-ep, 'SL'
            elif is_eod:           pnl, ex = row['close']-ep, 'EOD'
            else: continue
            results.append({'symbol': symbol, 'pnl': round(pnl,4), 'win': pnl>0, 'year': entry_date.year})
            in_trade = False
        elif not in_trade and prev['confirmed']:
            if row['t'] >= EOD: continue
            ep = row['open']; atr_val = prev['atr']
            sl = ep - SL_MULT*atr_val; tp = ep + TP_MULT*atr_val
            entry_date = row['date']; in_trade = True
    return pd.DataFrame(results)

# HL winners sorted by individual PF descending
WINNERS = ['VEDL','SBIN','NTPC','BHARTIARTL','ICICIBANK',
           'ADANIPORTS','NATIONALUM','PNB','ITC','ASHOKLEY','JSWSTEEL']

print("Running HL winners subset analysis...")
results = {s: run(s) for s in WINNERS}

sep = '-' * 76
print(f"\nCumulative portfolio (adding stocks by PF rank, best first):")
print(sep)
print(f"{'Combo':<7} {'N':>5}  {'WR%':>6}  {'BE%':>6}  {'PF':>6}  {'Net PnL':>10}  Stock added")
print(sep)

combined = pd.DataFrame()
for i, s in enumerate(WINNERS):
    combined = pd.concat([combined, results[s]])
    w = combined['win'].sum(); l = (~combined['win']).sum(); n = len(combined)
    wr    = w / n * 100
    avg_w = combined[combined['win']]['pnl'].mean()
    avg_l = combined[~combined['win']]['pnl'].mean()
    pf    = (w*avg_w)/(-l*avg_l) if l and avg_l < 0 else 0
    be    = (-avg_l)/( avg_w - avg_l)*100 if (avg_w > 0 and avg_l < 0) else 0
    pnl   = combined['pnl'].sum()
    flag  = '+' if (pf >= 1 and wr >= be) else ' '
    print(f"{flag}Top {i+1:<2}  {n:>5}  {wr:>5.1f}%  {be:>5.1f}%  {pf:>6.3f}  {pnl:>10.2f}  + {s}")

print(sep)
print("+ = PF>=1 and WR above actual BE")

# ── Year-by-year breakdown ────────────────────────────────────
all_trades = pd.concat(results.values())
YEARS = sorted(all_trades['year'].unique())

print(f"\nYear-by-year trade count — Top 11 HL winners:")
hdr = f"{'Stock':<12}" + "".join(f"  {y}" for y in YEARS) + "  Total"
print('-' * len(hdr))
print(hdr)
print('-' * len(hdr))
totals = {y: 0 for y in YEARS}
for s in WINNERS:
    r = results[s]
    row = f"{s:<12}"
    total = 0
    for y in YEARS:
        n = len(r[r['year'] == y])
        row += f"  {n:>4}"
        totals[y] += n
        total += n
    row += f"  {total:>5}"
    print(row)
print('-' * len(hdr))
total_row = f"{'TOTAL':<12}" + "".join(f"  {totals[y]:>4}" for y in YEARS)
total_row += f"  {sum(totals.values()):>5}"
print(total_row)
print('-' * len(hdr))
