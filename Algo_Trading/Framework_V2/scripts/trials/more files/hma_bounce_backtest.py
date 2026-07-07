# HMA Bounce Backtest — fv2
# Replaces SMA20 with HMA20 (Hull Moving Average, period=20)
# Raw signal only — no gate filters. tb3 touch->bounce->entry.
# SL=2.5x ATR14  TGT=4.5x ATR14  EOD=15:00  2022-2025

import pandas as pd
import numpy as np
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR  = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min"
HMA_N     = 20
MAX_TB_GAP = 3
SL_MULT   = 2.5
TGT_MULT  = 4.5
CUT_EXIT  = 15 * 60        # 15:00 in minutes

STOCKS = [
    'ADANIPORTS','ASHOKLEY','AXISBANK','BAJFINANCE','BANDHANBNK',
    'BHARTIARTL','CIPLA','COALINDIA','DABUR','DIVISLAB',
    'HDFCBANK','HINDALCO','ICICIBANK','INDUSINDBK','INFY',
    'ITC','JSWSTEEL','NATIONALUM','NTPC','ONGC',
    'PNB','POWERGRID','RELIANCE','SBIN','SUNPHARMA',
    'TATAMOTORS','TATASTEEL','TECHM','VEDL','WIPRO',
]


# ── HMA formula ───────────────────────────────────────────────────────────────
def _wma(series, n):
    weights = np.arange(1, n + 1, dtype=float)
    weights /= weights.sum()
    return pd.Series(series).rolling(n).apply(lambda x: np.dot(x, weights), raw=True).values

def compute_hma(close, n=HMA_N):
    half   = n // 2
    sqrtn  = int(round(n ** 0.5))
    wma1   = _wma(close, half)      # WMA(close, 10)
    wma2   = _wma(close, n)         # WMA(close, 20)
    raw    = 2 * wma1 - wma2        # lag-cancelled series
    return _wma(raw, sqrtn)         # HMA20 = WMA(raw, 4)


# ── Load stock ────────────────────────────────────────────────────────────────
def _load_stock(stock):
    path = os.path.join(DATA_DIR, f"{stock}_5min.csv")
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date']     = df['datetime'].dt.date

    yr = df['datetime'].dt.year
    df = df[yr.between(2022, 2025)].copy().reset_index(drop=True)

    prev_close = df['close'].shift(1)
    tr = np.maximum(df['high'] - df['low'],
         np.maximum((df['high'] - prev_close).abs(),
                    (df['low']  - prev_close).abs()))
    atr14 = tr.rolling(14, min_periods=14).mean()

    dates_ord = np.array([d.toordinal() for d in df['date']])
    minutes   = (df['datetime'].dt.hour * 60 + df['datetime'].dt.minute).values

    hma = compute_hma(df['close'].values)

    return {
        'open':      df['open'].values,
        'high':      df['high'].values,
        'low':       df['low'].values,
        'close':     df['close'].values,
        'atr14':     atr14.values,
        'hma':       hma,
        'dates_ord': dates_ord,
        'minutes':   minutes,
        'n':         len(df),
    }


# ── Profit factor helper ──────────────────────────────────────────────────────
def _pf(pnls):
    arr = np.asarray(pnls)
    gp  = arr[arr > 0].sum()
    gl  = abs(arr[arr < 0].sum())
    return float(gp / gl) if gl > 0 else 9999.0


# ── Backtest one stock ────────────────────────────────────────────────────────
def _run(s):
    op = s['open']; hi = s['high']; lo = s['low']; cl = s['close']
    atr = s['atr14']; hma = s['hma']
    dates = s['dates_ord']; mins = s['minutes']
    N = s['n']

    pnls = []; wins = 0
    i = HMA_N + int(round(HMA_N ** 0.5))   # warmup: 20 + 4 = 24 bars

    while i < N - 2:
        hma_i = hma[i]; atr_i = atr[i]
        if np.isnan(hma_i) or np.isnan(atr_i):
            i += 1; continue

        if lo[i] > hma_i:
            i += 1; continue

        # touch found at bar i
        d0  = dates[i]
        lim = min(i + MAX_TB_GAP + 1, N - 1)

        bounce_bar = -1
        for j in range(i, lim):
            if dates[j] != d0: break
            if cl[j] > hma[j]:
                bounce_bar = j; break

        if bounce_bar < 0:
            i += 1; continue

        eb = bounce_bar + 1
        if eb >= N or dates[eb] != d0:
            i += 1; continue

        if mins[eb] >= CUT_EXIT:
            i += 1; continue

        # entry
        entry = op[eb]
        sl    = entry - SL_MULT  * atr_i
        tgt   = entry + TGT_MULT * atr_i
        pnl   = cl[eb] - entry
        outcome = 'EOD-'

        for j in range(eb, N):
            if dates[j] != d0:
                pnl = cl[j - 1] - entry
                outcome = 'EOD+' if pnl > 0 else 'EOD-'
                break
            if mins[j] >= CUT_EXIT:
                pnl = op[j] - entry
                outcome = 'EOD+' if pnl > 0 else 'EOD-'
                break
            if lo[j] <= sl and hi[j] >= tgt:
                if abs(op[j] - sl) <= abs(op[j] - tgt):
                    outcome = 'L'; pnl = -SL_MULT  * atr_i
                else:
                    outcome = 'W'; pnl =  TGT_MULT * atr_i
                break
            if lo[j] <= sl:
                outcome = 'L'; pnl = -SL_MULT  * atr_i; break
            if hi[j] >= tgt:
                outcome = 'W'; pnl =  TGT_MULT * atr_i; break

        pnls.append(round(pnl, 4))
        if outcome in ('W', 'EOD+'):
            wins += 1
        i = eb + 1

    return pnls, wins


# ── Run all stocks ────────────────────────────────────────────────────────────
print(f"\nHMA{HMA_N} Bounce  SL={SL_MULT}x  TGT={TGT_MULT}x  ATR14  EOD=15:00  tb{MAX_TB_GAP}  raw (no gates)")
print("=" * 62)
print(f"  {'Stock':<12} {'N':>5}  {'WR':>7}  {'Net PnL':>12}  {'PF':>7}")
print("-" * 62)

all_pnls = []; all_wins = 0; all_n = 0

stock_rows = []
for stock in STOCKS:
    s = _load_stock(stock)
    pnls, wins = _run(s)
    n = len(pnls)
    wr = wins / n if n > 0 else 0.0
    pf = _pf(pnls) if pnls else 0.0
    net = sum(pnls)
    stock_rows.append((stock, n, wins, wr, net, pf))
    all_pnls.extend(pnls); all_wins += wins; all_n += n

for stock, n, wins, wr, net, pf in stock_rows:
    marker = '+' if pf >= 1.0 else ' '
    print(f"  {marker}{stock:<11} {n:>5}  {wr:>6.1%}  {net:>12,.1f}  {pf:>7.3f}")

print("=" * 62)
total_pf  = _pf(all_pnls)
total_wr  = all_wins / all_n if all_n > 0 else 0.0
total_net = sum(all_pnls)
print(f"  {'TOTAL':<12} {all_n:>5}  {total_wr:>6.1%}  {total_net:>12,.1f}  {total_pf:>7.3f}")
print("=" * 62)
print(f"  + = PF >= 1.0")

# ── SMA20 baseline reminder ───────────────────────────────────────────────────
print(f"""
SMA20 baseline (from run_ma_sweep.py, same params, with gates p05/p06/p08/p11):
  Refer to previous run_ma_sweep results for direct comparison.
  Note: this HMA run has NO gates — compare against SMA20 raw for apples-to-apples.
""")
