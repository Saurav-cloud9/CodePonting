"""
fv2 backtest - 30 stocks, 2022-2025, seed defaults + p06=55.
Active gates: p05 [0.0, 1.6] | p06 <= 55 | p08 >= 0.5 | p11 == 1
Detection window: tb3 (max_tb_gap = 3)
PNL unit: raw points (entry_price +/- ATR x mult)
"""
import pandas as pd
import numpy as np
import os

DATA_DIR   = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min"
MAX_TB_GAP = 3
P05_MIN, P05_MAX = 0.0, 1.6
P06_MAX  = 55
P08_MIN  = 0.5
SL_MULT  = 2.5
TP_MULT = 4.5

STOCKS = [
    'ADANIPORTS','ASHOKLEY','AXISBANK','BAJFINANCE','BANDHANBNK',
    'BHARTIARTL','CIPLA','COALINDIA','DABUR','DIVISLAB',
    'HDFCBANK','HINDALCO','ICICIBANK','INDUSINDBK','INFY',
    'ITC','JSWSTEEL','NATIONALUM','NTPC','ONGC',
    'PNB','POWERGRID','RELIANCE','SBIN','SUNPHARMA',
    'TATAMOTORS','TATASTEEL','TECHM','VEDL','WIPRO',
]


def _pf(pnls):
    gp = sum(x for x in pnls if x > 0)
    gl = abs(sum(x for x in pnls if x < 0))
    return gp / gl if gl > 0 else 9999.0


def run_stock(stock):
    csv_path = os.path.join(DATA_DIR, f"{stock}_5min.csv")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date']     = df['datetime'].dt.date

    yr = df['datetime'].dt.year
    df = df[yr.between(2022, 2025)].copy().reset_index(drop=True)

    prev_close   = df['close'].shift(1)
    df['tr']     = np.maximum(df['high'] - df['low'],
                   np.maximum((df['high'] - prev_close).abs(),
                              (df['low']  - prev_close).abs()))
    df['atr14']  = df['tr'].rolling(14, min_periods=14).mean()
    df['vol_ma20'] = df['volume'].rolling(20, min_periods=20).mean()
    df['vr']     = df['volume'] / df['vol_ma20']

    pnls, wins = [], 0
    i = 20

    while i < len(df) - 2:
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']) or pd.isna(row['vol_ma20']):
            i += 1; continue
        if row['low'] > row['ma20']:
            i += 1; continue

        T0      = i
        t0_date = row['date']
        atr     = row['atr14']

        # find bounce bar
        bounce_bar = None
        for j in range(T0, min(T0 + MAX_TB_GAP + 1, len(df) - 1)):
            brow = df.iloc[j]
            if brow['date'] != t0_date: break
            if brow['close'] > brow['ma20']:
                bounce_bar = j; break

        if bounce_bar is None:
            i += 1; continue

        entry_bar = bounce_bar + 1
        if entry_bar >= len(df) or df.iloc[entry_bar]['date'] != t0_date:
            i += 1; continue

        er = df.iloc[entry_bar]
        br = df.iloc[bounce_bar]

        if er['datetime'].time() >= pd.Timestamp('14:40').time():
            i += 1; continue

        # gate evaluations
        cr  = row['high'] - row['low']
        p05 = (row['ma20'] - row['low']) / atr if atr > 0 else np.nan
        p06 = (abs(row['close'] - row['open']) / cr * 100) if cr > 0 else 100.0
        p08 = br['vr'] if pd.notna(br['vr']) else np.nan
        p11 = 1 if er['open'] > br['close'] else 0

        if pd.isna(p05) or not (P05_MIN <= p05 <= P05_MAX): i += 1; continue
        if p06 > P06_MAX:                                   i += 1; continue
        if pd.isna(p08) or p08 < P08_MIN:                  i += 1; continue
        if p11 != 1:                                   i += 1; continue

        # PNL simulation
        entry_price = er['open']
        sl     = entry_price - SL_MULT  * atr
        target = entry_price + TP_MULT * atr
        outcome, pnl = 'EOD-', round(df.iloc[-1]['close'] - entry_price, 4)

        for j in range(entry_bar, len(df)):
            bar = df.iloc[j]
            if bar['low'] <= sl and bar['high'] >= target:
                if abs(bar['open'] - sl) <= abs(bar['open'] - target):
                    outcome, pnl = 'L', round(-SL_MULT  * atr, 4)
                else:
                    outcome, pnl = 'W', round( TP_MULT * atr, 4)
                break
            if bar['low'] <= sl:
                outcome, pnl = 'L', round(-SL_MULT  * atr, 4); break
            if bar['high'] >= target:
                outcome, pnl = 'W', round( TP_MULT * atr, 4); break
            if bar['datetime'].time() >= pd.Timestamp('15:00').time():
                pnl = round(bar['open'] - entry_price, 2)
                outcome = 'EOD+' if bar['open'] > entry_price else 'EOD-'
                break
            if bar['date'] != t0_date:
                last = df.iloc[j - 1]
                pnl = round(last['close'] - entry_price, 2)
                outcome = 'EOD+' if last['close'] > entry_price else 'EOD-'
                break

        pnls.append(pnl)
        if outcome in ('W', 'EOD+'):
            wins += 1
        i = entry_bar + 1

    n = len(pnls)
    if n == 0:
        return dict(stock=stock, n=0, wr=0.0, net_pnl=0.0, pf=0.0, pnls=[])
    return dict(stock=stock, n=n, wr=wins/n, net_pnl=sum(pnls), pf=_pf(pnls), pnls=pnls)


# --- Run ----------------------------------------------------------------------
print("fv2 backtest | p05[0.0-1.6] p06<=55 p08>=0.5 p11=1 | tb3 | 2022-2025\n")
print(f"{'STOCK':<14} {'N':>5} {'WR':>7} {'NET PNL':>12} {'PF':>7}")
print("-" * 52)

results   = []
all_pnls  = []

for stock in STOCKS:
    r = run_stock(stock)
    results.append(r)
    all_pnls.extend(r['pnls'])
    wr_s  = f"{r['wr']:.1%}"    if r['n'] > 0 else "    -"
    pf_s  = f"{r['pf']:.2f}"    if r['n'] > 0 else "   -"
    pnl_s = f"{r['net_pnl']:>12,.1f}"
    print(f"{r['stock']:<14} {r['n']:>5} {wr_s:>7} {pnl_s} {pf_s:>7}")

# aggregate
total_n   = sum(r['n'] for r in results)
total_wins = sum(round(r['wr'] * r['n']) for r in results)
total_pnl  = sum(r['net_pnl'] for r in results)
agg_wr     = total_wins / total_n if total_n > 0 else 0.0
agg_pf     = _pf(all_pnls) if all_pnls else 0.0

print("-" * 52)
print(f"{'TOTAL':<14} {total_n:>5} {agg_wr:.1%} {total_pnl:>12,.1f} {agg_pf:>7.2f}")
print()
