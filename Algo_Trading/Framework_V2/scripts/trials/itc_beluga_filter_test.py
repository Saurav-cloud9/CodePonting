"""
ITC 2022 tb3 — Beluga filter test. One filter at a time.
Current: voltrend_touch > 5
Break-even W/(W+L) = 35.7%
"""
import pandas as pd
import numpy as np

STOCK    = 'ITC'
YEAR     = 2022
HMA_N    = 15
LEN      = 20
COEFF    = 10.0 / LEN
BREAKEVEN = 35.7

DATA_DIR    = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min"
SIGNALS_DIR = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\signals"

def wma(series, n):
    weights = np.arange(1, n + 1, dtype=float)
    return series.rolling(n).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

def hma(series, n):
    raw = 2 * wma(series, n // 2) - wma(series, n)
    return wma(raw, int(round(np.sqrt(n))))

def beluga_score(hma_series):
    score = pd.Series(0.0, index=hma_series.index)
    for i in range(0, LEN + 1):
        cmp = (hma_series > hma_series.shift(i)).astype(int) * 2 - 1
        score += cmp
    return score * COEFF

def show(subset, label):
    decided = subset[subset['outcome'].isin(['W', 'L'])]
    W  = (decided['outcome'] == 'W').sum()
    L  = (decided['outcome'] == 'L').sum()
    WL = W + L
    wp = W / WL * 100 if WL > 0 else 0
    eod_plus  = (subset['outcome'] == 'EOD+').sum()
    eod_minus = (subset['outcome'] == 'EOD-').sum()
    flag = "  ** ABOVE BREAKEVEN **" if wp > BREAKEVEN else ""
    print(f"\n  {label}")
    print(f"  Total signals : {len(subset)}")
    print(f"  W             : {W}")
    print(f"  L             : {L}")
    print(f"  EOD+          : {eod_plus}")
    print(f"  EOD-          : {eod_minus}")
    print(f"  W/(W+L)       : {wp:.1f}%  (need > {BREAKEVEN}%){flag}")

# ── Load data ─────────────────────────────────────────────────────────────────

df = pd.read_csv(f"{DATA_DIR}\\{STOCK}_5min.csv")
df.columns = df.columns.str.strip()
df['datetime'] = pd.to_datetime(df['datetime'])
df = df[df['datetime'].dt.year == YEAR].copy().reset_index(drop=True)

hlc3 = (df['high'] + df['low'] + df['close']) / 3
df['trend']    = beluga_score(hma(hlc3, HMA_N))
df['voltrend'] = beluga_score(hma(df['volume'], HMA_N))

sig = pd.read_csv(f"{SIGNALS_DIR}\\{STOCK.lower()}_{YEAR}_h5_signals_tb3.csv")
sig['datetime'] = pd.to_datetime(sig['datetime'])
sig = sig.merge(
    df[['datetime', 'trend', 'voltrend']].rename(
        columns={'trend': 'trend_touch', 'voltrend': 'voltrend_touch'}),
    on='datetime', how='left'
)

# ── Results ───────────────────────────────────────────────────────────────────

print("=" * 55)
print("ITC 2022 tb3 — Beluga Filter Test")
print("=" * 55)

show(sig, "BASELINE — no filter")
show(sig[sig['voltrend_touch'] > 5], "FILTER: voltrend_touch > 5")
show(sig[sig['voltrend_touch'] <= 5], "REMOVED: voltrend_touch <= 5  (what we discard)")
show(sig[sig['voltrend_touch'] < 0],  "FILTER: voltrend_touch < 0")
show(sig[sig['voltrend_touch'] < 4],  "FILTER: voltrend_touch < 4")
show(sig[sig['voltrend_touch'] <  4], "FILTER: voltrend_touch <  4")
show(sig[sig['voltrend_touch'] <= 4], "FILTER: voltrend_touch <= 4")
show(sig[sig['voltrend_touch'] <  5], "FILTER: voltrend_touch <  5")
show(sig[sig['voltrend_touch'] <= 3], "FILTER: voltrend_touch <= 3")
show(sig[sig['voltrend_touch'] <  3], "FILTER: voltrend_touch <  3")
show(sig[sig['voltrend_touch'] <= 2], "FILTER: voltrend_touch <= 2")
show(sig[sig['voltrend_touch'] <  2], "FILTER: voltrend_touch <  2")
show(sig[sig['voltrend_touch'] <= 1], "FILTER: voltrend_touch <= 1")
show(sig[sig['voltrend_touch'] <  1], "FILTER: voltrend_touch <  1")
show(sig[sig['voltrend_touch'] <= 0], "FILTER: voltrend_touch <= 0")
