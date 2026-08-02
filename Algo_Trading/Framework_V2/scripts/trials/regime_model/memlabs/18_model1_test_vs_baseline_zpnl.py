"""
Model 1 (autoregressive PnL) — recovered from session transcript
e9e1dc13-550d-4fcd-9c75-3da972a3b99a.jsonl (was originally run ad-hoc via
Bash -c, not saved). Saved here now so it isn't lost again.

x = previous trade's PnL, y = current trade's PnL. Fit LinearRegression on
first 75% (Train, chronological), predict on remaining 25% (Test).
Decision rule: signal = sign(y_hat); trade_return = signal * zpnl
  - y_hat > 0  -> take the trade as-is (signal=+1)
  - y_hat < 0  -> FLIP the trade's sign (signal=-1), not skip
  - y_hat == 0 -> zero out (signal=0)
Produces 18_model1_test_vs_baseline_zpnl.png
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


def zerodha_short(entry, exit_price):
    brok = min(0.0003 * entry, 20) + min(0.0003 * exit_price, 20)
    stt = entry * 0.00025
    txn = (entry + exit_price) * 0.0000307
    sebi = (entry + exit_price) * 0.000001
    stamp = exit_price * 0.000003
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


trades = pd.read_csv('TATAMOTORS_2015-2025_trade_log_with_memory_feature.csv')
trades.columns = trades.columns.str.strip()
trades['entry_dt'] = pd.to_datetime(trades['entry_dt'])
trades = trades.sort_values('entry_dt').reset_index(drop=True)
trades['zpnl'] = trades.apply(lambda r: r['pnl'] - zerodha_short(r['entry'], r['exit_price']), axis=1)
trades['prev_trade_pnl'] = trades['pnl'].shift(1)
trades = trades.dropna(subset=['prev_trade_pnl']).reset_index(drop=True)

n = len(trades)
train_n = int(n * 0.75)
train = trades.iloc[:train_n]
test = trades.iloc[train_n:].copy()

model = LinearRegression()
model.fit(train[['prev_trade_pnl']], train['pnl'])

test['y_hat'] = model.predict(test[['prev_trade_pnl']])
test['signal'] = np.sign(test['y_hat'])
test['trade_return_z'] = test['signal'] * test['zpnl']

test['cum_baseline_z'] = test['zpnl'].cumsum()
test['cum_model_z'] = test['trade_return_z'].cumsum()

plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(11, 5))
fig.patch.set_facecolor('#0d1117'); ax.set_facecolor('#0d1117')

ax.plot(range(len(test)), test['cum_baseline_z'].values, label='Baseline ZPnL (take every trade)', color='#e74c3c', linewidth=2)
ax.plot(range(len(test)), test['cum_model_z'].values, label='Model-filtered ZPnL (autoregressive PnL)', color='#2ecc71', linewidth=2)
ax.axhline(0, color='white', linestyle=':', alpha=0.4)
ax.set_xlabel('Trade # (Test set only)', color='#aaa')
ax.set_ylabel('Cumulative ZPnL', color='#aaa')
ax.set_title('Model 1 (Autoregressive PnL) vs Baseline - ZPnL, TEST SET ONLY', color='white', fontsize=12, pad=12)
ax.legend()
plt.tight_layout()
plt.savefig('18_model1_test_vs_baseline_zpnl.png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f'w={model.coef_[0]:.6f}  b={model.intercept_:.6f}')
print(f'Baseline final cum ZPnL: {test["cum_baseline_z"].iloc[-1]:.2f}')
print(f'Model final cum ZPnL: {test["cum_model_z"].iloc[-1]:.2f}')
print()
print('First 2 Test-set trades:')
print(test[['entry_dt', 'prev_trade_pnl', 'pnl', 'zpnl', 'y_hat', 'signal', 'trade_return_z']].head(2).to_string())
