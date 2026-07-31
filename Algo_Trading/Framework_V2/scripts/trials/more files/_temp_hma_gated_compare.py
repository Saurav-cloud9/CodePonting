# Comparison: SMA20 vs HMA20, raw, open>MA touch condition
# + voltrend_touch < 4 and <= 4 variants
# Reports: N, WR%, BE%, Net PnL, PF
# voltrend = Beluga score on HMA(volume, 15)

import pandas as pd, numpy as np, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR   = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
MAX_TB_GAP = 3; SL_MULT = 2.5; TP_MULT = 4.5; CUT_EXIT = 15 * 60
HMA_N = 15; BLEN = 20; BCOEFF = 10.0 / BLEN   # Beluga params

STOCKS = [
    'ADANIPORTS','ASHOKLEY','AXISBANK','BAJFINANCE','BANDHANBNK',
    'BHARTIARTL','CIPLA','COALINDIA','DABUR','DIVISLAB',
    'HDFCBANK','HINDALCO','ICICIBANK','INDUSINDBK','INFY',
    'ITC','JSWSTEEL','NATIONALUM','NTPC','ONGC',
    'PNB','POWERGRID','RELIANCE','SBIN','SUNPHARMA',
    'TATAMOTORS','TATASTEEL','TECHM','VEDL','WIPRO',
]


# ── MA helpers ────────────────────────────────────────────────────────────────
def _wma(s, n):
    w = np.arange(1, n + 1, dtype=float); w /= w.sum()
    return pd.Series(s).rolling(n).apply(lambda x: np.dot(x, w), raw=True)

def _hma(s, n):
    raw = 2 * _wma(s, n // 2) - _wma(s, n)
    return _wma(raw, int(round(n ** 0.5)))

def hma20_arr(c):
    return _hma(pd.Series(c), 20).values

def sma20_arr(c):
    return pd.Series(c).rolling(20, min_periods=20).mean().values


# ── Beluga voltrend ───────────────────────────────────────────────────────────
def beluga_voltrend(volume):
    h = _hma(pd.Series(volume), HMA_N)
    score = pd.Series(0.0, index=h.index)
    for i in range(0, BLEN + 1):
        cmp = (h > h.shift(i)).astype(int) * 2 - 1
        score += cmp
    return (score * BCOEFF).values


# ── Stats helper ──────────────────────────────────────────────────────────────
def stats(pnls, wins):
    n = len(pnls)
    if n == 0:
        return 0, 0.0, 0.0, 0.0, 0.0, 0.0
    arr  = np.asarray(pnls)
    wr   = wins / n
    gp   = arr[arr > 0].sum(); gl = abs(arr[arr < 0].sum())
    pf   = float(gp / gl) if gl > 0 else 9999.0
    aw   = arr[arr > 0].mean() if (arr > 0).any() else 0.0
    al   = arr[arr < 0].mean() if (arr < 0).any() else 0.0
    be   = (-al) / (aw - al) * 100 if (aw > 0 and al < 0) else 0.0
    return n, wr * 100, be, arr.sum(), pf


# ── Backtest one stock, one MA array ──────────────────────────────────────────
def run_stock(stock, ma_arr, vt_arr, vt_thresh, vt_op):
    """
    vt_thresh : threshold value (e.g. 4)
    vt_op     : '<' or '<='
    If vt_thresh is None -> no voltrend filter
    """
    df = pd.read_csv(os.path.join(DATA_DIR, f'{stock}_5min.csv'))
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date']     = df['datetime'].dt.date
    df = df[df['datetime'].dt.year.between(2022, 2025)].copy().reset_index(drop=True)

    pc  = df['close'].shift(1)
    tr  = np.maximum(df['high'] - df['low'],
          np.maximum((df['high'] - pc).abs(), (df['low'] - pc).abs()))
    atr = tr.rolling(14, min_periods=14).mean().values

    dates = np.array([d.toordinal() for d in df['date']])
    mins  = (df['datetime'].dt.hour * 60 + df['datetime'].dt.minute).values
    op = df['open'].values; hi = df['high'].values
    lo = df['low'].values;  cl = df['close'].values
    N  = len(df)

    ma = ma_arr(df['close'].values)
    vt = vt_arr(df['volume'].values) if vt_thresh is not None else None

    pnls = []; wins = 0
    warmup = 24 if ma_arr == hma20_arr else 20
    i = warmup

    while i < N - 2:
        m = ma[i]; a = atr[i]
        if np.isnan(m) or np.isnan(a):
            i += 1; continue
        # touch condition: low <= MA AND open > MA
        if lo[i] > m or op[i] <= m:
            i += 1; continue
        # voltrend filter at touch bar
        if vt_thresh is not None:
            v = vt[i]
            if np.isnan(v):
                i += 1; continue
            if vt_op == '<'  and not (v <  vt_thresh): i += 1; continue
            if vt_op == '<=' and not (v <= vt_thresh): i += 1; continue

        d0  = dates[i]; lim = min(i + MAX_TB_GAP + 1, N - 1); bb = -1
        for j in range(i, lim):
            if dates[j] != d0: break
            if cl[j] > ma[j]: bb = j; break
        if bb < 0: i += 1; continue

        eb = bb + 1
        if eb >= N or dates[eb] != d0 or mins[eb] >= CUT_EXIT:
            i += 1; continue

        entry = op[eb]; sl = entry - SL_MULT * a; tp = entry + TP_MULT * a
        pnl = cl[eb] - entry; oc = 'EOD-'

        for j in range(eb, N):
            if dates[j] != d0:
                pnl = cl[j-1] - entry; oc = 'EOD+' if pnl > 0 else 'EOD-'; break
            if mins[j] >= CUT_EXIT:
                pnl = op[j] - entry; oc = 'EOD+' if pnl > 0 else 'EOD-'; break
            if lo[j] <= sl and hi[j] >= tp:
                if abs(op[j] - sl) <= abs(op[j] - tp): oc = 'L'; pnl = -SL_MULT * a
                else:                                    oc = 'W'; pnl =  TP_MULT * a
                break
            if lo[j] <= sl:  oc = 'L'; pnl = -SL_MULT * a; break
            if hi[j] >= tp: oc = 'W'; pnl =  TP_MULT * a; break

        pnls.append(round(pnl, 4))
        if oc in ('W', 'EOD+'): wins += 1
        i = eb + 1

    return pnls, wins


# ── Run all variants ──────────────────────────────────────────────────────────
VARIANTS = [
    ('SMA20  raw+open>MA',        sma20_arr, beluga_voltrend, None, None),
    ('HMA20  raw+open>MA',        hma20_arr, beluga_voltrend, None, None),
    ('SMA20  vt<4',               sma20_arr, beluga_voltrend, 4,    '<'),
    ('SMA20  vt<=4',              sma20_arr, beluga_voltrend, 4,    '<='),
    ('HMA20  vt<4',               hma20_arr, beluga_voltrend, 4,    '<'),
    ('HMA20  vt<=4',              hma20_arr, beluga_voltrend, 4,    '<='),
]

results = {name: {'pnls': [], 'wins': 0} for name, *_ in VARIANTS}

print('Running all variants on 30 stocks...\n')
for stock in STOCKS:
    df_raw = pd.read_csv(os.path.join(DATA_DIR, f'{stock}_5min.csv'))
    df_raw.columns = df_raw.columns.str.strip()
    df_raw['datetime'] = pd.to_datetime(df_raw['datetime'])
    df_raw['date']     = df_raw['datetime'].dt.date
    df_raw = df_raw[df_raw['datetime'].dt.year.between(2022, 2025)].copy().reset_index(drop=True)

    for name, ma_fn, vt_fn, vt_thresh, vt_op in VARIANTS:
        p, w = run_stock(stock, ma_fn, vt_fn, vt_thresh, vt_op)
        results[name]['pnls'].extend(p)
        results[name]['wins'] += w

    print(f'  {stock} done', flush=True)

print()
print('=' * 72)
print(f"  {'Variant':<24} {'N':>7}  {'WR%':>6}  {'BE%':>6}  {'Net PnL':>12}  {'PF':>7}")
print('-' * 72)
for name, *_ in VARIANTS:
    r = results[name]
    n, wr, be, net, pf = stats(r['pnls'], r['wins'])
    marker = '+' if pf >= 1.0 else ' '
    print(f"  {marker}{name:<23} {n:>7,}  {wr:>5.1f}%  {be:>5.1f}%  {net:>12,.1f}  {pf:>7.3f}")
print('=' * 72)
print('  + = PF >= 1.0')
