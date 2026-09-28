"""
54c_oos_dispersion_gate.py — Out-of-sample test of the Q5 dispersion gate
(Fable Finding 2: trade-level ZPF by lagged-dispersion quintile, Q5 only >1.0,
in-sample). This script re-does that split honestly: cutoff chosen ONLY on the
first ~70% of trading days (chronological), then scored on the untouched last
~30% — never mixed.

Input: 54c_trade_log_with_features.csv (14,270 trades, from 54c_regime_features.py)
"""
import pandas as pd
import numpy as np

df = pd.read_csv('54c_trade_log_with_features.csv', parse_dates=['date'])
df = df.dropna(subset=['dispersion']).copy()

def zpf(zpnl):
    pos = zpnl[zpnl > 0].sum()
    neg = zpnl[zpnl < 0].sum()
    return pos / abs(neg) if neg != 0 else np.nan

# one dispersion value per day (lagged feature is day-level, not trade-level)
daily = df.groupby('date')['dispersion'].first().sort_index()
n_days = len(daily)
split_idx = int(n_days * 0.70)
train_days = daily.index[:split_idx]
test_days = daily.index[split_idx:]

print(f"Total days: {n_days} | Train: {len(train_days)} ({train_days.min().date()} -> {train_days.max().date()}) "
      f"| Test: {len(test_days)} ({test_days.min().date()} -> {test_days.max().date()})")

# cutoff computed ONLY on train
cutoff = daily.loc[train_days].quantile(0.80)
print(f"\nCutoff (80th pctile of TRAIN-only dispersion): {cutoff:.4f}  "
      f"(original full-sample cutoff was 1.997, for comparison)")

# --- Sanity check: in-sample, does the train-derived cutoff reproduce Q5-like behavior on TRAIN itself? ---
train_trades = df[df['date'].isin(train_days)].copy()
train_trades['bucket'] = np.where(train_trades['dispersion'] > cutoff, 'high', 'low')
print("\n--- TRAIN (in-sample, sanity check) ---")
for b in ['low', 'high']:
    sub = train_trades[train_trades['bucket'] == b]
    print(f"  {b:>4}: {len(sub):>5} trades, {sub['date'].nunique():>4} days, "
          f"ZPF={zpf(sub['zpnl']):.3f}, net_zpnl={sub['zpnl'].sum():>9.0f}")

# --- The real test: TEST period, using the TRAIN-derived cutoff (no peeking) ---
test_trades = df[df['date'].isin(test_days)].copy()
test_trades['bucket'] = np.where(test_trades['dispersion'] > cutoff, 'high', 'low')
print("\n--- TEST (out-of-sample, cutoff fixed from TRAIN) ---")
for b in ['low', 'high']:
    sub = test_trades[test_trades['bucket'] == b]
    print(f"  {b:>4}: {len(sub):>5} trades, {sub['date'].nunique():>4} days, "
          f"ZPF={zpf(sub['zpnl']):.3f}, net_zpnl={sub['zpnl'].sum():>9.0f}")

print(f"\nAll TEST trades combined: {len(test_trades)} trades, ZPF={zpf(test_trades['zpnl']):.3f}, "
      f"net_zpnl={test_trades['zpnl'].sum():.0f}")

verdict_high = zpf(test_trades[test_trades['bucket']=='high']['zpnl'])
print(f"\nVERDICT: test-period high-dispersion ZPF = {verdict_high:.3f} "
      f"({'CLEARS' if verdict_high > 1.0 else 'DOES NOT CLEAR'} 1.0)")
