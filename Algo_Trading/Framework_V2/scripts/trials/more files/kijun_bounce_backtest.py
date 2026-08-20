# Kijun fv2 Bounce — Python Backtest
# Signal : Daily Kijun (50-day) 2-bar bounce, long only
# SL     : 2.5x ATR14   TP : 3.0x ATR14   EOD : 15:00

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from datetime import time as dt_time

STOCKS     = [
    'ADANIPORTS', 'ASHOKLEY',   'AXISBANK',   'BAJFINANCE', 'BANDHANBNK',
    'BHARTIARTL', 'CIPLA',      'COALINDIA',  'DABUR',      'DIVISLAB',
    'HDFCBANK',   'HINDALCO',   'ICICIBANK',  'INDUSINDBK', 'INFY',
    'ITC',        'JSWSTEEL',   'NATIONALUM', 'NTPC',       'ONGC',
    'PNB',        'POWERGRID',  'RELIANCE',   'SBIN',       'SUNPHARMA',
    'TATAMOTORS', 'TATASTEEL',  'TECHM',      'VEDL',       'WIPRO',
]
KIJUN_LEN  = 50
ATR_LEN    = 14
SL_MULT    = 2.5
TP_MULT   = 3.0
EOD        = dt_time(15, 0)

DATA_5MIN  = 'Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'


def compute_atr(df):
    prev_c = df['close'].shift(1)
    tr = pd.concat([df['high'] - df['low'],
                    (df['high'] - prev_c).abs(),
                    (df['low']  - prev_c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/ATR_LEN, adjust=False).mean()


def run(symbol, kijun_mode='hl'):
    # ── Load 5-min CSV (single source of truth) ──────────────
    df = pd.read_csv(f'{DATA_5MIN}/{symbol}_5min.csv')
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime']).apply(
        lambda x: x.replace(tzinfo=None) if x.tzinfo else x)
    df = df.sort_values('datetime').reset_index(drop=True)
    df['date'] = df['datetime'].dt.date
    df['t']    = df['datetime'].dt.time

    # ── Daily Kijun from 5-min resample ──────────────────────
    daily = df.set_index('datetime').resample('D').agg(
        high=('high', 'max'), low=('low', 'min'), close=('close', 'last')
    ).dropna()
    if kijun_mode == 'hl':
        daily['kijun'] = (daily['high'].rolling(KIJUN_LEN).max() +
                          daily['low'].rolling(KIJUN_LEN).min()) / 2
    else:
        daily['kijun'] = (daily['close'].rolling(KIJUN_LEN).max() +
                          daily['close'].rolling(KIJUN_LEN).min()) / 2
    # shift(1) → use previous day's completed Kijun (no lookahead)
    daily['kijun'] = daily['kijun'].shift(1)
    kijun_map = daily.dropna(subset=['kijun'])['kijun']
    kijun_map.index = kijun_map.index.date
    df['kijun'] = df['date'].map(kijun_map)
    df = df.dropna(subset=['kijun','open','high','low','close']).reset_index(drop=True)
    df['atr'] = compute_atr(df)

    # ── Signal detection ─────────────────────────────────────
    # touch: low crosses under kijun AND open above kijun
    df['touch'] = ((df['low'].shift(1) >= df['kijun'].shift(1)) &
                   (df['low'] < df['kijun']) &
                   (df['open'] > df['kijun']))
    # confirmed: prev bar was touch, low back above kijun, close > low
    df['confirmed'] = (df['touch'].shift(1) &
                       (df['low'] > df['kijun']) &
                       (df['close'] > df['low']))

    # ── Simulation ───────────────────────────────────────────
    results = []
    in_trade = False
    ep = sl = tp = entry_date = None

    for i in range(2, len(df)):
        row  = df.iloc[i]
        prev = df.iloc[i - 1]

        if in_trade:
            hit_sl  = row['low']  <= sl
            hit_tp = row['high'] >= tp
            is_eod  = row['t'] >= EOD or row['date'] != entry_date

            if hit_sl and hit_tp:
                pnl, ex = sl - ep, 'SL'
            elif hit_tp:
                pnl, ex = tp - ep, 'TP'
            elif hit_sl:
                pnl, ex = sl - ep, 'SL'
            elif is_eod:
                pnl, ex = row['close'] - ep, 'EOD'
            else:
                continue

            results.append({'symbol': symbol, 'year': entry_date.year,
                            'pnl': round(pnl, 4), 'exit': ex, 'win': pnl > 0})
            in_trade = False

        elif not in_trade and prev['confirmed']:
            if row['t'] >= EOD:
                continue
            ep         = row['open']
            atr_val    = prev['atr']
            sl         = ep - SL_MULT  * atr_val
            tp        = ep + TP_MULT * atr_val
            entry_date = row['date']
            in_trade   = True

    return pd.DataFrame(results)


# ── Helper ───────────────────────────────────────────────────
def summarise(results_list):
    rows = []
    for r in results_list:
        if r.empty: continue
        sym   = r['symbol'].iloc[0]
        w     = r['win'].sum(); l = (~r['win']).sum()
        wl    = w / (w + l) * 100 if (w + l) > 0 else 0
        avg_w = r[r['win']]['pnl'].mean()   if w else 0
        avg_l = r[~r['win']]['pnl'].mean()  if l else 0
        pf    = (w * avg_w) / (-l * avg_l)  if l and avg_l < 0 else float('inf')
        be    = (-avg_l) / (avg_w - avg_l) * 100 if (avg_w > 0 and avg_l < 0) else 0
        rows.append((sym, len(r), w, l, wl, pf, be))
    return rows


# ── Run both modes ────────────────────────────────────────────
print(f"\nKijun fv2 Bounce  SL={SL_MULT}x  TP={TP_MULT}x  ATR{ATR_LEN}  Theoretical BE={SL_MULT/(SL_MULT+TP_MULT)*100:.1f}%")

res_hl  = [run(s, 'hl')   for s in STOCKS]
res_cc  = [run(s, 'cc')   for s in STOCKS]
sum_hl  = summarise(res_hl)
sum_cc  = summarise(res_cc)

hdr = f"{'Symbol':<12} {'N':>4}  {'WR%':>6}  {'BE%':>6}  {'PF':>6}"
sep = "="*46

print(f"\n{'HIGH/LOW Kijun (traditional)':^46}  {'CLOSE/CLOSE Kijun (Pine Script)':^46}")
print(f"{sep}  {sep}")
print(f"{hdr}  {hdr}")
print(f"{sep}  {sep}")

for (s1,n1,w1,l1,wl1,pf1,be1), (s2,n2,w2,l2,wl2,pf2,be2) in zip(sum_hl, sum_cc):
    flag1 = '+' if (pf1 >= 1 and wl1 >= be1) else ' '
    flag2 = '+' if (pf2 >= 1 and wl2 >= be2) else ' '
    print(f"{flag1}{s1:<12} {n1:>4}  {wl1:>5.1f}%  {be1:>5.1f}%  {pf1:>6.3f}  "
          f"{flag2}{s2:<12} {n2:>4}  {wl2:>5.1f}%  {be2:>5.1f}%  {pf2:>6.3f}")

print(f"{sep}  {sep}")
print("+ = PF>1 and WR above actual BE")

# ── Portfolio totals ──────────────────────────────────────────
def portfolio_totals(results_list):
    all_trades = pd.concat([r for r in results_list if not r.empty])
    n     = len(all_trades)
    wins  = all_trades['win']
    w     = wins.sum(); l = (~wins).sum()
    wr    = w / n * 100
    avg_w = all_trades[wins]['pnl'].mean()
    avg_l = all_trades[~wins]['pnl'].mean()
    pnl   = all_trades['pnl'].sum()
    pf    = (w * avg_w) / (-l * avg_l) if l and avg_l < 0 else float('inf')
    be    = (-avg_l) / (avg_w - avg_l) * 100 if (avg_w > 0 and avg_l < 0) else 0
    return n, w, l, wr, pnl, pf, be

print(f"\n{'PORTFOLIO TOTALS':^97}")
print(f"{'-'*97}")
hdr2 = f"{'Formula':<18} {'Trades':>7}  {'Wins':>5}  {'Losses':>6}  {'WR%':>6}  {'Net PnL':>10}  {'PF':>6}  {'BE%':>6}"
print(hdr2)
print(f"{'-'*97}")
for label, res in [('Kijun-HL', res_hl), ('Kijun-Close', res_cc)]:
    n, w, l, wr, pnl, pf, be = portfolio_totals(res)
    flag = '+' if (pf >= 1 and wr >= be) else ' '
    print(f"{flag}{label:<17} {n:>7}  {w:>5}  {l:>6}  {wr:>5.1f}%  {pnl:>10.2f}  {pf:>6.3f}  {be:>5.1f}%")
print(f"{'-'*97}")

print(f"{sep}  {sep}")
print("** = above breakeven")
