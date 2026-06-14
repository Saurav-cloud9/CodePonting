"""
Big Beluga regime tagger — fv2
Replicates Regime Filter [BigBeluga] Pine Script formula.
Tags H5 signals with trend + voltrend + regime at touch, bounce, and entry bars.

Params (matching Pine Script defaults):
  HMA period : 15
  Len        : 20
  Coeff      : 10/20 = 0.5

Quadrants:
  R = trend < 0, voltrend > 0  (downtrend + high volume)
  Y = trend < 0, voltrend <= 0 (downtrend + low volume)
  G = trend >= 0, voltrend > 0 (uptrend + high volume)
  B = trend >= 0, voltrend <= 0 (uptrend + low volume)
"""

import pandas as pd
import numpy as np
import os

STOCK   = 'POWERGRID'
YEAR    = 2022
TB      = 3
HMA_N   = 15
LEN     = 20
COEFF   = 10.0 / LEN  # 0.5

DATA_DIR    = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min"
SIGNALS_DIR = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\signals"
OUT_DIR     = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\backtest\regime"
os.makedirs(OUT_DIR, exist_ok=True)


# ── HMA ────────────────────────────────────────────────────────────────────────

def wma(series, n):
    weights = np.arange(1, n + 1, dtype=float)
    return series.rolling(n).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

def hma(series, n):
    raw = 2 * wma(series, n // 2) - wma(series, n)
    return wma(raw, int(round(np.sqrt(n))))


# ── Beluga score ───────────────────────────────────────────────────────────────

def beluga_score(hma_series, len_param=LEN):
    """Pine Script: for i=0 to len: trend += (hma > hma[i]) ? 1 : -1; trend *= coeff"""
    score = pd.Series(0.0, index=hma_series.index)
    for i in range(0, len_param + 1):          # 0 to len inclusive = 21 iterations
        cmp = (hma_series > hma_series.shift(i)).astype(int) * 2 - 1
        score += cmp
    return score * COEFF


# ── Load price data ────────────────────────────────────────────────────────────

csv_path = os.path.join(DATA_DIR, f"{STOCK}_5min.csv")
df = pd.read_csv(csv_path)
df.columns = df.columns.str.strip()
df['datetime'] = pd.to_datetime(df['datetime'])
df = df[df['datetime'].dt.year == YEAR].copy().reset_index(drop=True)

# Compute Beluga indicators
hlc3         = (df['high'] + df['low'] + df['close']) / 3
df['trend']    = beluga_score(hma(hlc3, HMA_N))
df['voltrend'] = beluga_score(hma(df['volume'], HMA_N))

# Regime quadrant
df['regime'] = 'B'
df.loc[(df['trend'] < 0) & (df['voltrend'] > 0),  'regime'] = 'R'
df.loc[(df['trend'] < 0) & (df['voltrend'] <= 0), 'regime'] = 'Y'
df.loc[(df['trend'] >= 0) & (df['voltrend'] > 0), 'regime'] = 'G'

beluga_df = df[['datetime', 'trend', 'voltrend', 'regime']].copy()
print(f"Beluga computed: {len(beluga_df)} bars")


# ── Load H5 signals ────────────────────────────────────────────────────────────

sig_path = os.path.join(SIGNALS_DIR, f"{STOCK.lower()}_{YEAR}_h5_signals_tb{TB}.csv")
sig = pd.read_csv(sig_path)
sig['datetime']        = pd.to_datetime(sig['datetime'])
sig['bounce_datetime'] = pd.to_datetime(sig['bounce_datetime'])
sig['entry_datetime']  = pd.to_datetime(sig['entry_datetime'])
print(f"Signals loaded: {len(sig)}")


# ── Merge Beluga values at T0, bounce, entry ───────────────────────────────────

def merge_beluga(signals, signal_col, prefix):
    lookup = beluga_df.rename(columns={
        'datetime':  signal_col,
        'trend':     f'trend_{prefix}',
        'voltrend':  f'voltrend_{prefix}',
        'regime':    f'regime_{prefix}',
    })
    return signals.merge(lookup, on=signal_col, how='left')

sig = merge_beluga(sig, 'datetime',        'touch')
sig = merge_beluga(sig, 'bounce_datetime', 'bounce')
sig = merge_beluga(sig, 'entry_datetime',  'entry')

sig['trend_delta'] = sig['trend_entry'] - sig['trend_touch']

# Check for unmatched rows
unmatched = sig['trend_touch'].isna().sum()
if unmatched:
    print(f"WARNING: {unmatched} signals had no Beluga match (check datetime alignment)")


# ── Save output ────────────────────────────────────────────────────────────────

out_path = os.path.join(OUT_DIR, f"{STOCK.lower()}_{YEAR}_beluga_tagged.csv")
sig.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")


# ── Quick analysis ─────────────────────────────────────────────────────────────

print("\n=== W/L/EOD by regime at TOUCH ===")
sig['outcome_simple'] = sig['outcome'].str.replace(r'^EOD.*', 'EOD', regex=True)
tbl = sig.groupby(['regime_touch', 'outcome_simple']).size().unstack(fill_value=0)
tbl.columns.name = None
# Add W% and total columns
tbl['Total'] = tbl.sum(axis=1)
for col in ['W', 'L', 'EOD']:
    if col not in tbl.columns:
        tbl[col] = 0
tbl = tbl[['W', 'L', 'EOD', 'Total']]
tbl['W%'] = (tbl['W'] / tbl['Total'] * 100).round(1)
print(tbl.to_string())

print("\n=== Mean trend / voltrend by outcome ===")
print(sig.groupby('outcome_simple')[['trend_touch', 'voltrend_touch', 'trend_delta']].mean().round(2).to_string())

print("\n=== Regime flip (touch->entry) counts ===")
flip = sig.groupby(['regime_touch', 'regime_entry', 'outcome_simple']).size().unstack(fill_value=0)
flip.columns.name = None
print(flip.to_string())
