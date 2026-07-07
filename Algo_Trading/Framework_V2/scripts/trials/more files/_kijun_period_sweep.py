import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np
from datetime import time as dt_time

ATR_LEN=14; SL_MULT=2.5; TGT_MULT=3.0; EOD=dt_time(15,0)
DATA_5MIN='Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'

WINNERS = ['VEDL','SBIN','NTPC','BHARTIARTL','ICICIBANK',
           'ADANIPORTS','NATIONALUM','PNB','ITC','ASHOKLEY','JSWSTEEL']

PERIODS = [10, 20, 30, 40, 50]

def compute_atr(df):
    prev_c = df['close'].shift(1)
    tr = pd.concat([df['high']-df['low'],
                    (df['high']-prev_c).abs(),
                    (df['low']-prev_c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/ATR_LEN, adjust=False).mean()

def run(symbol, kijun_len):
    df = pd.read_csv(f'{DATA_5MIN}/{symbol}_5min.csv')
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime']).apply(
        lambda x: x.replace(tzinfo=None) if x.tzinfo else x)
    df = df.sort_values('datetime').reset_index(drop=True)
    df['date'] = df['datetime'].dt.date
    df['t']    = df['datetime'].dt.time
    daily = df.set_index('datetime').resample('D').agg(
        high=('high','max'), low=('low','min'), close=('close','last')).dropna()
    daily['kijun'] = (daily['high'].rolling(kijun_len).max() +
                      daily['low'].rolling(kijun_len).min()) / 2
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
    results = []; in_trade = False; ep = sl = tgt = entry_date = None
    for i in range(2, len(df)):
        row = df.iloc[i]; prev = df.iloc[i-1]
        if in_trade:
            hit_sl  = row['low']  <= sl
            hit_tgt = row['high'] >= tgt
            is_eod  = row['t'] >= EOD or row['date'] != entry_date
            if hit_sl and hit_tgt: pnl, ex = sl-ep, 'SL'
            elif hit_tgt:          pnl, ex = tgt-ep, 'TGT'
            elif hit_sl:           pnl, ex = sl-ep, 'SL'
            elif is_eod:           pnl, ex = row['close']-ep, 'EOD'
            else: continue
            results.append({'symbol': symbol, 'pnl': round(pnl,4),
                            'win': pnl>0, 'year': entry_date.year})
            in_trade = False
        elif not in_trade and prev['confirmed']:
            if row['t'] >= EOD: continue
            ep = row['open']; atr_val = prev['atr']
            sl = ep - SL_MULT*atr_val; tgt = ep + TGT_MULT*atr_val
            entry_date = row['date']; in_trade = True
    return pd.DataFrame(results) if results else pd.DataFrame(columns=['symbol','pnl','win','year'])

def stock_stats(r):
    if len(r) == 0: return 0, 0, 0, 0, 0
    n = len(r); w = r['win'].sum(); l = n - w
    wr = w/n*100
    avg_w = r[r['win']]['pnl'].mean() if w else 0
    avg_l = r[~r['win']]['pnl'].mean() if l else 0
    pf = (w*avg_w)/(-l*avg_l) if (l and avg_l < 0) else 0
    be = (-avg_l)/(avg_w-avg_l)*100 if (avg_w > 0 and avg_l < 0) else 0
    return n, wr, be, pf, r['pnl'].sum()

SEP  = '=' * 78
sep2 = '-' * 78

for klen in PERIODS:
    print(f'\n{SEP}')
    print(f'  KIJUN-HL  {klen}-DAY  |  Top 11 Winner Stocks  |  2022-2025')
    print(SEP)

    results = {s: run(s, klen) for s in WINNERS}

    # ── 1. Individual stock results ───────────────────────────────
    print(f'\n{"Stock":<12}  {"N":>5}  {"WR%":>6}  {"BE%":>6}  {"PF":>6}  {"Net PnL":>10}')
    print(sep2)
    for s in WINNERS:
        n, wr, be, pf, pnl = stock_stats(results[s])
        flag = '+' if (pf >= 1 and wr >= be) else ' '
        print(f'{flag}{s:<11}  {n:>5}  {wr:>5.1f}%  {be:>5.1f}%  {pf:>6.3f}  {pnl:>10.2f}')
    print(sep2)

    # ── 2. Overall 4-year totals ──────────────────────────────────
    all_trades = pd.concat(results.values())
    n, wr, be, pf, pnl = stock_stats(all_trades)
    print(f' {"ALL 11":<11}  {n:>5}  {wr:>5.1f}%  {be:>5.1f}%  {pf:>6.3f}  {pnl:>10.2f}')
    print(sep2)

    # ── 3. Cumulative portfolio (stacked by PF rank) ──────────────
    print(f'\n{"Combo":<7}  {"N":>5}  {"WR%":>6}  {"BE%":>6}  {"PF":>6}  {"Net PnL":>10}  Stock added')
    print(sep2)
    combined = pd.DataFrame()
    for i, s in enumerate(WINNERS):
        combined = pd.concat([combined, results[s]])
        n, wr, be, pf, pnl = stock_stats(combined)
        flag = '+' if (pf >= 1 and wr >= be) else ' '
        print(f'{flag}Top {i+1:<2}  {n:>5}  {wr:>5.1f}%  {be:>5.1f}%  {pf:>6.3f}  {pnl:>10.2f}  +{s}')
    print(sep2)

    # ── 4. Year-by-year trade count ───────────────────────────────
    YEARS = sorted(all_trades['year'].unique()) if len(all_trades) else []
    print(f'\nYear-by-year trade count:')
    hdr = f'{"Stock":<12}' + ''.join(f'  {y}' for y in YEARS) + '  Total'
    print('-' * len(hdr))
    print(hdr)
    print('-' * len(hdr))
    totals = {y: 0 for y in YEARS}
    for s in WINNERS:
        r = results[s]
        row = f'{s:<12}'
        total = 0
        for y in YEARS:
            cnt = len(r[r['year']==y])
            row += f'  {cnt:>4}'; totals[y] += cnt; total += cnt
        row += f'  {total:>5}'
        print(row)
    print('-' * len(hdr))
    tot_row = f'{"TOTAL":<12}' + ''.join(f'  {totals[y]:>4}' for y in YEARS)
    tot_row += f'  {sum(totals.values()):>5}'
    print(tot_row)
    print('-' * len(hdr))

print(f'\n{SEP}')
print('  PERIOD COMPARISON SUMMARY  (Top 11 combined)')
print(SEP)
print(f'{"Period":<8}  {"N":>5}  {"WR%":>6}  {"BE%":>6}  {"PF":>6}  {"Net PnL":>10}')
print(sep2)
for klen in PERIODS:
    results = {s: run(s, klen) for s in WINNERS}
    all_t = pd.concat(results.values())
    n, wr, be, pf, pnl = stock_stats(all_t)
    flag = '*' if klen == 50 else ' '
    print(f'{flag}{klen}-day{"":<3}  {n:>5}  {wr:>5.1f}%  {be:>5.1f}%  {pf:>6.3f}  {pnl:>10.2f}')
print(sep2)
print('* = current baseline (50-day)')
