"""
MA sweep — SMA10/15/20/25/30 + EMA10/15/20/25/30
Gates: p05[0.0-1.6] | p06<=55 | p08>=0.5 | p11=1 | tb3 | 2022-2025
Each stock CSV is read once; all 10 MA variants share the same read.
Uses numpy arrays for all inner loops — no .iloc overhead.
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

MA_VARIANTS = [
    ('SMA10', 'SMA', 10),
    ('SMA15', 'SMA', 15),
    ('SMA20', 'SMA', 20),
    ('SMA25', 'SMA', 25),
    ('SMA30', 'SMA', 30),
    ('EMA10', 'EMA', 10),
    ('EMA15', 'EMA', 15),
    ('EMA20', 'EMA', 20),
    ('EMA25', 'EMA', 25),
    ('EMA30', 'EMA', 30),
]

STOCKS = [
    'ADANIPORTS','ASHOKLEY','AXISBANK','BAJFINANCE','BANDHANBNK',
    'BHARTIARTL','CIPLA','COALINDIA','DABUR','DIVISLAB',
    'HDFCBANK','HINDALCO','ICICIBANK','INDUSINDBK','INFY',
    'ITC','JSWSTEEL','NATIONALUM','NTPC','ONGC',
    'PNB','POWERGRID','RELIANCE','SBIN','SUNPHARMA',
    'TATAMOTORS','TATASTEEL','TECHM','VEDL','WIPRO',
]


def _pf(pnls):
    arr = np.asarray(pnls)
    gp = arr[arr > 0].sum()
    gl = abs(arr[arr < 0].sum())
    return float(gp / gl) if gl > 0 else 9999.0


def _load_stock(stock):
    """Read CSV once; return dict of numpy arrays for fast indexing."""
    path = os.path.join(DATA_DIR, f"{stock}_5min.csv")
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date']     = df['datetime'].dt.date

    yr = df['datetime'].dt.year
    df = df[yr.between(2022, 2025)].copy().reset_index(drop=True)

    prev_close     = df['close'].shift(1)
    tr             = np.maximum(df['high'] - df['low'],
                     np.maximum((df['high'] - prev_close).abs(),
                                (df['low']  - prev_close).abs()))
    atr14          = tr.rolling(14, min_periods=14).mean()
    vol_ma20       = df['volume'].rolling(20, min_periods=20).mean()
    vr             = df['volume'] / vol_ma20

    # pre-encode dates as integer (day ordinal) for fast same-day check
    dates_ord = np.array([d.toordinal() for d in df['date']])

    # time-of-day as minutes since midnight
    minutes = (df['datetime'].dt.hour * 60 + df['datetime'].dt.minute).values

    return {
        'open':      df['open'].values,
        'high':      df['high'].values,
        'low':       df['low'].values,
        'close':     df['close'].values,
        'atr14':     atr14.values,
        'vr':        vr.values,
        'dates_ord': dates_ord,
        'minutes':   minutes,
        'n':         len(df),
    }


def _compute_ma(close_series, ma_type, period):
    if ma_type == 'SMA':
        return pd.Series(close_series).rolling(period, min_periods=period).mean().values
    else:
        return pd.Series(close_series).ewm(span=period, adjust=False, min_periods=period).mean().values


def _run_ma(s, ma):
    """Backtest with numpy arrays. s = stock dict, ma = numpy array."""
    op = s['open']; hi = s['high']; lo = s['low']; cl = s['close']
    atr = s['atr14']; vr = s['vr']
    dates = s['dates_ord']; mins = s['minutes']
    N = s['n']

    CUT_ENTRY = 14 * 60 + 40   # 14:40
    CUT_EXIT  = 15 * 60        # 15:00

    pnls = []
    wins = 0
    i = 20

    while i < N - 2:
        ma_i = ma[i]; atr_i = atr[i]; vr_i = vr[i]
        if np.isnan(ma_i) or np.isnan(atr_i) or np.isnan(vr_i):
            i += 1; continue

        if lo[i] > ma_i:
            i += 1; continue

        T0   = i
        d0   = dates[i]

        # find bounce bar
        bounce_bar = -1
        lim = min(T0 + MAX_TB_GAP + 1, N - 1)
        for j in range(T0, lim):
            if dates[j] != d0: break
            if cl[j] > ma[j]:
                bounce_bar = j; break

        if bounce_bar < 0:
            i += 1; continue

        eb = bounce_bar + 1
        if eb >= N or dates[eb] != d0:
            i += 1; continue

        if mins[eb] >= CUT_ENTRY:
            i += 1; continue

        # gate checks
        cr   = hi[i] - lo[i]
        p05  = (ma_i - lo[i]) / atr_i if atr_i > 0 else np.nan
        p06  = abs(cl[i] - op[i]) / cr * 100 if cr > 0 else 100.0
        vr_b = vr[bounce_bar]
        p08  = vr_b if not np.isnan(vr_b) else np.nan
        p11 = 1 if op[eb] > cl[bounce_bar] else 0

        if np.isnan(p05) or not (P05_MIN <= p05 <= P05_MAX): i += 1; continue
        if p06 > P06_MAX:                                     i += 1; continue
        if np.isnan(p08) or p08 < P08_MIN:                   i += 1; continue
        if p11 != 1:                                     i += 1; continue

        entry_price = op[eb]
        sl     = entry_price - SL_MULT  * atr_i
        target = entry_price + TP_MULT * atr_i
        outcome = 'EOD-'
        pnl     = cl[-1] - entry_price

        for j in range(eb, N):
            lo_j = lo[j]; hi_j = hi[j]
            hit_sl  = lo_j <= sl
            hit_tp = hi_j >= target
            if hit_sl and hit_tp:
                if abs(op[j] - sl) <= abs(op[j] - target):
                    outcome = 'L'; pnl = -SL_MULT  * atr_i
                else:
                    outcome = 'W'; pnl =  TP_MULT * atr_i
                break
            if hit_sl:
                outcome = 'L'; pnl = -SL_MULT  * atr_i; break
            if hit_tp:
                outcome = 'W'; pnl =  TP_MULT * atr_i; break
            if mins[j] >= CUT_EXIT:
                pnl = op[j] - entry_price
                outcome = 'EOD+' if pnl > 0 else 'EOD-'
                break
            if dates[j] != d0:
                pnl = cl[j - 1] - entry_price
                outcome = 'EOD+' if pnl > 0 else 'EOD-'
                break

        pnls.append(round(pnl, 4))
        if outcome in ('W', 'EOD+'):
            wins += 1
        i = eb + 1

    return pnls, wins


# ── Run ────────────────────────────────────────────────────────────────────────
print("Running MA sweep (numpy arrays)...\n")

variant_results = {name: {'n': 0, 'wins': 0, 'pnls': []} for name, _, _ in MA_VARIANTS}

for stock in STOCKS:
    print(f"  {stock}...", end=' ', flush=True)
    s = _load_stock(stock)
    for ma_name, ma_type, period in MA_VARIANTS:
        ma = _compute_ma(s['close'], ma_type, period)
        pnls, wins = _run_ma(s, ma)
        variant_results[ma_name]['n']    += len(pnls)
        variant_results[ma_name]['wins'] += wins
        variant_results[ma_name]['pnls'].extend(pnls)
    print("done")

# ── Comparison table ──────────────────────────────────────────────────────────
baseline = variant_results['SMA20']
base_n   = baseline['n']
base_pf  = _pf(baseline['pnls'])
base_pnl = sum(baseline['pnls'])

print()
print("=" * 82)
print(f"  MA SWEEP — 30 stocks | 2022-2025 | p05[0.0-1.6] p06<=55 p08>=0.5 p11 | tb3")
print("=" * 82)
print(f"  {'MA':<8} {'Signals':>8} {'WR':>7} {'Net PNL':>13} {'PF':>7}  {'vs SMA20':>9}")
print("-" * 82)

scores = []
for ma_name, _, _ in MA_VARIANTS:
    r   = variant_results[ma_name]
    n   = r['n']
    wr  = r['wins'] / n if n > 0 else 0.0
    pf  = _pf(r['pnls']) if r['pnls'] else 0.0
    pnl = sum(r['pnls'])
    dpf = pf - base_pf
    scores.append((ma_name, n, wr, pnl, pf, dpf))

    marker       = " <- BASELINE" if ma_name == 'SMA20' else ""
    dpf_str      = f"{dpf:+.3f}" if ma_name != 'SMA20' else "    -"
    print(f"  {ma_name:<8} {n:>8,} {wr:>7.1%} {pnl:>13,.1f} {pf:>7.3f}  {dpf_str:>9}{marker}")

print("=" * 82)

# ── Top 3 & Bottom 3 ──────────────────────────────────────────────────────────
non_base = [s for s in scores if s[0] != 'SMA20']
ranked   = sorted(non_base, key=lambda x: x[4], reverse=True)

print()
print("  TOP 3 by Profit Factor (vs SMA20 baseline):")
for rank, (name, n, wr, pnl, pf, dpf) in enumerate(ranked[:3], 1):
    print(f"  #{rank}  {name:<8}  PF={pf:.3f}  WR={wr:.1%}  Net PNL={pnl:,.1f}  (vs SMA20: {dpf:+.3f})")

print()
print("  BOTTOM 3 by Profit Factor:")
for rank, (name, n, wr, pnl, pf, dpf) in enumerate(ranked[-3:], 1):
    print(f"  #{rank}  {name:<8}  PF={pf:.3f}  WR={wr:.1%}  Net PNL={pnl:,.1f}  (vs SMA20: {dpf:+.3f})")

print()
