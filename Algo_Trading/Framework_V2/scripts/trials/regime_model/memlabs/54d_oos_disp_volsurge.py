"""
54d_oos_disp_volsurge.py — out-of-sample test of the one combined-rule that survived
the max-of-24 correction: dispersion LOW AND volume_surge HIGH (low-high quadrant),
in-sample r=-0.0709, n=452 days, net_zpnl=-1590 (~65% of the strategy's total loss
from ~18% of days).

Same discipline as 54c_oos_dispersion_gate.py: chronological 70/30 split, thresholds
(medians) computed on TRAIN ONLY, frozen rule applied to the untouched TEST period.
"""
import pandas as pd
import numpy as np

trades = pd.read_csv('54c_trade_log_with_features.csv', parse_dates=['signal_dt'])
trades['date'] = trades['signal_dt'].dt.date
daily = trades.groupby('date').agg(
    daily_zpnl=('zpnl', 'sum'),
    dispersion=('dispersion', 'first'),
    volume_surge=('volume_surge', 'first'),
).reset_index().dropna(subset=['dispersion', 'volume_surge', 'daily_zpnl']).sort_values('date').reset_index(drop=True)

n_days = len(daily)
split_idx = int(n_days * 0.70)
train = daily.iloc[:split_idx]
test = daily.iloc[split_idx:]
print(f"Total days: {n_days} | Train: {len(train)} ({train['date'].min()} -> {train['date'].max()}) "
      f"| Test: {len(test)} ({test['date'].min()} -> {test['date'].max()})")

# thresholds from TRAIN only
disp_med_train = train['dispersion'].median()
vol_med_train = train['volume_surge'].median()
print(f"\nTrain-derived medians: dispersion={disp_med_train:.4f}  volume_surge={vol_med_train:.4f}")
print(f"(original full-sample medians were ~1.50 / ~1.00, for comparison)")

def apply_rule(df):
    return (df['dispersion'] <= disp_med_train) & (df['volume_surge'] > vol_med_train)

# --- sanity check: does the train-derived rule reproduce the pattern on TRAIN itself? ---
train_flag = apply_rule(train)
print("\n--- TRAIN (in-sample, sanity check) ---")
for label, sub in [('rule days (low disp, high vol)', train[train_flag]), ('rest of train', train[~train_flag])]:
    print(f"  {label:32s}: {len(sub):>5} days, mean_zpnl={sub['daily_zpnl'].mean():>7.3f}, "
          f"net_zpnl={sub['daily_zpnl'].sum():>9.0f}")
print(f"  (train population mean_zpnl: {train['daily_zpnl'].mean():.3f})")

# --- the real test: TEST period, using the TRAIN-derived thresholds (no peeking) ---
test_flag = apply_rule(test)
print("\n--- TEST (out-of-sample, thresholds fixed from TRAIN) ---")
for label, sub in [('rule days (low disp, high vol)', test[test_flag]), ('rest of test', test[~test_flag])]:
    print(f"  {label:32s}: {len(sub):>5} days, mean_zpnl={sub['daily_zpnl'].mean():>7.3f}, "
          f"net_zpnl={sub['daily_zpnl'].sum():>9.0f}")
print(f"  (test population mean_zpnl: {test['daily_zpnl'].mean():.3f})")

rule_mean_test = test[test_flag]['daily_zpnl'].mean()
pop_mean_test = test['daily_zpnl'].mean()
ratio = rule_mean_test / pop_mean_test if pop_mean_test != 0 else float('nan')
print(f"\nVERDICT: rule-flagged test days averaged {rule_mean_test:.3f} vs test population average "
      f"{pop_mean_test:.3f} ({ratio:.2f}x)")
print(f"In-sample (full dataset, original medians) showed ~3.7x worse (-3.52 vs -0.95).")
print(f"{'HOLDS UP' if ratio > 1.5 and rule_mean_test < pop_mean_test else 'DOES NOT HOLD UP'} "
      f"out of sample by this rough bar (rule should be at least ~1.5x worse than test's own average).")
