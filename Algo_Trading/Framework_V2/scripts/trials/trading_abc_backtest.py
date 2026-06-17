# Trading ABC fv2 Backtest — long only
# Signal : Trading ABC (TV community) — trend cloud + zigzag ABC + Fib check + MA bounce
# Entry  : next bar's open after triangle bar
# SL     : 2.5x ATR14   TGT : 4.5x ATR14 (R:R=1.8, fv2 baseline convention)
# EOD    : 15:00

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from datetime import time as dt_time

SYMBOL    = 'BHARTIARTL'
ZZ_LEN    = 8
FIB_LO    = 0.382
FIB_HI    = 0.618
ERR_RATE  = 0.05
MAX_BARS  = 6          # abc_bar_count window
ATR_LEN   = 14
SL_MULT   = 2.5
TGT_MULT  = 4.5
EOD       = dt_time(15, 0)

DATA_5MIN = 'Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'

FIB_LO_EFF = FIB_LO * (1 - ERR_RATE)
FIB_HI_EFF = FIB_HI * (1 + ERR_RATE)


def compute_atr(df):
    prev_c = df['close'].shift(1)
    tr = pd.concat([df['high'] - df['low'],
                    (df['high'] - prev_c).abs(),
                    (df['low']  - prev_c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / ATR_LEN, adjust=False).mean()


def load(symbol):
    df = pd.read_csv(f'{DATA_5MIN}/{symbol}_5min.csv')
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime']).apply(
        lambda x: x.replace(tzinfo=None) if x.tzinfo else x)
    df = df.sort_values('datetime').reset_index(drop=True)
    df['t'] = df['datetime'].dt.time
    df['date'] = df['datetime'].dt.date

    # ── 6 MAs ─────────────────────────────────────────────
    df['sma50']  = df['close'].rolling(50).mean()
    df['sma100'] = df['close'].rolling(100).mean()
    df['sma150'] = df['close'].rolling(150).mean()
    df['sma200'] = df['close'].rolling(200).mean()
    df['ema20']  = df['close'].ewm(span=20, adjust=False).mean()
    df['ema40']  = df['close'].ewm(span=40, adjust=False).mean()
    df['atr']    = compute_atr(df)

    # ── ZigZag pivots (window=ZZ_LEN, lookback only) ────────
    df['ph'] = df['high'] == df['high'].rolling(ZZ_LEN).max()
    df['pl'] = df['low']  == df['low'].rolling(ZZ_LEN).min()

    df = df.dropna(subset=['sma200', 'atr']).reset_index(drop=True)
    return df


def run(symbol):
    df = load(symbol)
    ma_cols = ['sma50', 'sma100', 'sma150', 'sma200', 'ema20', 'ema40']

    n = len(df)
    high = df['high'].values; low = df['low'].values
    close = df['close'].values; open_ = df['open'].values
    ma_vals = df[ma_cols].values
    ph = df['ph'].values; pl = df['pl'].values

    # trend state
    trend = 0
    up_streak = 0
    down_streak = 0

    # zigzag state: list of [idx, price, type]  type: 'H' or 'L'
    zigzag = []
    last_zz_point = None     # active C's price (low, for long)
    abc_bar_count = 0
    lowest_since_c = np.inf

    long_signal = np.zeros(n, dtype=bool)

    for i in range(n):
        body_hi = max(open_[i], close[i])
        body_lo = min(open_[i], close[i])
        upper = (ma_vals[i] >= body_hi).sum()
        lower = (ma_vals[i] <= body_lo).sum()

        cond_up   = lower > 0 and upper == 0
        cond_down = upper > 0 and lower == 0
        up_streak   = up_streak + 1 if cond_up else 0
        down_streak = down_streak + 1 if cond_down else 0
        if up_streak >= 2:
            trend = 1
        elif down_streak >= 2:
            trend = -1

        # ── ZigZag update ────────────────────────────────
        changed = False
        candidate_type = 'H' if ph[i] else ('L' if pl[i] else None)
        if candidate_type is not None:
            price = high[i] if candidate_type == 'H' else low[i]
            if not zigzag:
                zigzag.append([i, price, candidate_type])
                changed = True
            else:
                _, last_val, last_type = zigzag[-1]
                if candidate_type == last_type:
                    if (candidate_type == 'H' and price > last_val) or \
                       (candidate_type == 'L' and price < last_val):
                        zigzag[-1] = [i, price, candidate_type]
                        changed = True
                else:
                    zigzag.append([i, price, candidate_type])
                    changed = True
            if len(zigzag) > 10:
                zigzag = zigzag[-10:]

        # ── ABC fire check (long side only) ────────────────
        there_is_abc = False
        if changed and candidate_type == 'L' and trend == 1 and len(zigzag) >= 5:
            a_price = zigzag[-1][1]   # C (newest)
            b_price = zigzag[-3][1]   # B
            c_price = zigzag[-5][1]   # A
            if low[i] < ma_vals[i].max() and (b_price - c_price) != 0:
                rate = (a_price - b_price) / (c_price - b_price)
                if FIB_LO_EFF <= rate <= FIB_HI_EFF:
                    last_zz_point = a_price
                    abc_bar_count = 0
                    lowest_since_c = low[i]
                    there_is_abc = True

        if not there_is_abc:
            abc_bar_count += 1
            if last_zz_point is not None:
                lowest_since_c = min(lowest_since_c, low[i])

        # ── Bounce check (Step 4) ────────────────────────────
        lbounced = False
        if i >= 1:
            low2 = min(low[i], low[i - 1])
            if close[i] > open_[i]:
                for ma in ma_vals[i]:
                    if low2 <= ma and close[i] > ma:
                        lbounced = True
                        break

        # ── Final signal ──────────────────────────────────
        if (last_zz_point is not None and trend == 1 and abc_bar_count <= MAX_BARS
                and lbounced and lowest_since_c >= last_zz_point):
            long_signal[i] = True

    df['long_signal'] = long_signal

    # ── Simulation ──────────────────────────────────────────
    results = []
    in_trade = False
    ep = sl = tgt = entry_date = None

    for i in range(1, n):
        row = df.iloc[i]

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

        elif not in_trade and df.iloc[i - 1]['long_signal']:
            if row['t'] >= EOD:
                continue
            ep = row['open']
            atr_val = df.iloc[i - 1]['atr']
            sl = ep - SL_MULT * atr_val
            tgt = ep + TGT_MULT * atr_val
            entry_date = row['date']
            in_trade = True

    return pd.DataFrame(results)


def summarise(r):
    if r.empty:
        print("No trades generated.")
        return
    w = r['win'].sum(); l = (~r['win']).sum()
    wr = w / (w + l) * 100
    avg_w = r[r['win']]['pnl'].mean()
    avg_l = r[~r['win']]['pnl'].mean()
    pnl = r['pnl'].sum()
    pf = (w * avg_w) / (-l * avg_l) if l and avg_l < 0 else float('inf')
    be = (-avg_l) / (avg_w - avg_l) * 100 if (avg_w > 0 and avg_l < 0) else 0

    print(f"\nTrading ABC fv2 Backtest — {SYMBOL}  SL={SL_MULT}x  TGT={TGT_MULT}x  ATR{ATR_LEN}")
    print(f"Theoretical BE = {SL_MULT/(SL_MULT+TGT_MULT)*100:.1f}%\n")
    print(f"{'Trades':>7}  {'Wins':>5}  {'Losses':>6}  {'WR%':>6}  {'Net PnL':>10}  {'PF':>6}  {'BE%':>6}")
    print(f"{len(r):>7}  {w:>5}  {l:>6}  {wr:>5.1f}%  {pnl:>10.2f}  {pf:>6.3f}  {be:>5.1f}%")

    by_year = r.groupby('year').agg(n=('pnl', 'size'),
                                     wins=('win', 'sum'),
                                     pnl=('pnl', 'sum'))
    by_year['wr'] = by_year['wins'] / by_year['n'] * 100
    print(f"\n{'Year':<6} {'N':>5}  {'WR%':>6}  {'PnL':>10}")
    for yr, row in by_year.iterrows():
        print(f"{yr:<6} {row['n']:>5.0f}  {row['wr']:>5.1f}%  {row['pnl']:>10.2f}")

    print(f"\nExit breakdown: {r['exit'].value_counts().to_dict()}")


if __name__ == '__main__':
    res = run(SYMBOL)
    summarise(res)
