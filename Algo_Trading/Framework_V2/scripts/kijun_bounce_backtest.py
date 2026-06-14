# Kijun fv2 Bounce — Python Backtest
# Signal : Daily Kijun (50-day) 2-bar bounce, long only
# SL     : 2.5x ATR14   TGT : 3.0x ATR14   EOD : 15:15

import pandas as pd
import numpy as np
from datetime import time as dt_time

STOCKS     = ['ITC', 'TATAMOTORS', 'HDFCBANK', 'RELIANCE', 'INFY']
KIJUN_LEN  = 50
ATR_LEN    = 14
SL_MULT    = 2.5
TGT_MULT   = 3.0
EOD        = dt_time(15, 15)

DATA_5MIN  = 'Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'
DATA_DAILY = 'Algo_Trading/Framework_V1/data/historical/daily'


def compute_atr(df):
    prev_c = df['close'].shift(1)
    tr = pd.concat([df['high'] - df['low'],
                    (df['high'] - prev_c).abs(),
                    (df['low']  - prev_c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/ATR_LEN, adjust=False).mean()


def run(symbol, kijun_mode='hl'):
    # ── Daily Kijun ──────────────────────────────────────────
    daily = pd.read_parquet(f'{DATA_DAILY}/{symbol}.parquet')
    daily = daily.sort_values('datetime').reset_index(drop=True)
    daily['date'] = pd.to_datetime(daily['datetime']).dt.date
    if kijun_mode == 'hl':   # traditional: highest HIGH + lowest LOW
        daily['kijun'] = (daily['high'].rolling(KIJUN_LEN).max() +
                          daily['low'].rolling(KIJUN_LEN).min()) / 2
    else:                    # pine script: highest CLOSE + lowest CLOSE
        daily['kijun'] = (daily['close'].rolling(KIJUN_LEN).max() +
                          daily['close'].rolling(KIJUN_LEN).min()) / 2
    kijun_map = daily.dropna(subset=['kijun']).set_index('date')['kijun']

    # ── 5-min data ───────────────────────────────────────────
    df = pd.read_csv(f'{DATA_5MIN}/{symbol}_5min.csv')
    df['datetime'] = pd.to_datetime(df['datetime']).apply(
        lambda x: x.replace(tzinfo=None) if x.tzinfo else x)
    df = df.sort_values('datetime').reset_index(drop=True)
    df['date'] = df['datetime'].dt.date
    df['t']    = df['datetime'].dt.time
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
    ep = sl = tgt = entry_date = None

    for i in range(2, len(df)):
        row  = df.iloc[i]
        prev = df.iloc[i - 1]

        if in_trade:
            hit_sl  = row['low']  <= sl
            hit_tgt = row['high'] >= tgt
            is_eod  = row['t'] >= EOD or row['date'] != entry_date

            if hit_sl and hit_tgt:
                pnl, ex = sl - ep, 'SL'
            elif hit_tgt:
                pnl, ex = tgt - ep, 'TGT'
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
            tgt        = ep + TGT_MULT * atr_val
            entry_date = row['date']
            in_trade   = True

    return pd.DataFrame(results)


# ── Helper ───────────────────────────────────────────────────
def summarise(results_list):
    rows = []
    for r in results_list:
        if r.empty: continue
        sym = r['symbol'].iloc[0]
        w   = r['win'].sum(); l = (~r['win']).sum()
        wl  = w / (w + l) * 100 if (w + l) > 0 else 0
        avg_w = r[r['win']]['pnl'].mean()  if w else 0
        avg_l = r[~r['win']]['pnl'].mean() if l else 0
        pf  = (w * avg_w) / (-l * avg_l) if l and avg_l < 0 else float('inf')
        rows.append((sym, len(r), w, l, wl, pf))
    return rows


# ── Run both modes ────────────────────────────────────────────
BE = SL_MULT / (SL_MULT + TGT_MULT) * 100
print(f"\nKijun fv2 Bounce  SL={SL_MULT}x  TGT={TGT_MULT}x  ATR{ATR_LEN}  Breakeven={BE:.1f}%")

res_hl  = [run(s, 'hl')   for s in STOCKS]
res_cc  = [run(s, 'cc')   for s in STOCKS]
sum_hl  = summarise(res_hl)
sum_cc  = summarise(res_cc)

hdr = f"{'Symbol':<12} {'N':>4}  {'W/(W+L)':>8}  {'PF':>6}"
sep = "="*40

print(f"\n{'HIGH/LOW Kijun (traditional)':^40}  {'CLOSE/CLOSE Kijun (Pine Script)':^40}")
print(f"{sep}  {sep}")
print(f"{hdr}  {hdr}")
print(f"{sep}  {sep}")

for (s1,n1,w1,l1,wl1,pf1), (s2,n2,w2,l2,wl2,pf2) in zip(sum_hl, sum_cc):
    flag1 = '**' if wl1 >= BE else '  '
    flag2 = '**' if wl2 >= BE else '  '
    print(f"{s1:<12} {n1:>4}  {wl1:>7.1f}%{flag1}  {pf1:>6.3f}  "
          f"{s2:<12} {n2:>4}  {wl2:>7.1f}%{flag2}  {pf2:>6.3f}")

print(f"{sep}  {sep}")
print("** = above breakeven")
