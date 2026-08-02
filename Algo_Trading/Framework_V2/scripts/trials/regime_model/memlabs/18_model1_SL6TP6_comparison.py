"""
Model 1 (autoregressive PnL) on the SL=6.0/TP=6.0 trade log — recovered from
session transcript e9e1dc13-550d-4fcd-9c75-3da972a3b99a.jsonl (was originally
run ad-hoc via Bash -c, not saved). Saved here now so it isn't lost again.

Same logic as 18_model1_test_vs_baseline_zpnl.py, run against
TATAMOTORS_2015-2025_trade_log_SL6_TP6.csv instead of the live 2.0/4.5 log,
to test whether the autoregressive edge survives at the SL/TP sweep's
"best" combo. Produces 18_model1_SL6TP6_comparison.png (side-by-side PnL
and ZPnL panels).
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


trades = pd.read_csv('TATAMOTORS_2015-2025_trade_log_SL6_TP6.csv')
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
w, b = model.coef_[0], model.intercept_
print(f'w={w:.6f}  b={b:.6f}')

test['y_hat'] = model.predict(test[['prev_trade_pnl']])
test['signal'] = np.sign(test['y_hat'])
test['trade_return'] = test['signal'] * test['pnl']
test['trade_return_z'] = test['signal'] * test['zpnl']

test['cum_baseline'] = test['pnl'].cumsum()
test['cum_model'] = test['trade_return'].cumsum()
test['cum_baseline_z'] = test['zpnl'].cumsum()
test['cum_model_z'] = test['trade_return_z'].cumsum()

plt.style.use('dark_background')
fig, axes = plt.subplots(1, 2, figsize=(16, 5))
for ax, base_col, model_col, label, title in [
    (axes[0], 'cum_baseline', 'cum_model', 'PnL', 'PnL'),
    (axes[1], 'cum_baseline_z', 'cum_model_z', 'ZPnL', 'ZPnL'),
]:
    fig.patch.set_facecolor('#0d1117'); ax.set_facecolor('#0d1117')
    ax.plot(range(len(test)), test[base_col].values, label=f'Baseline {label}', color='#e74c3c', linewidth=2)
    ax.plot(range(len(test)), test[model_col].values, label=f'Model-filtered {label}', color='#2ecc71', linewidth=2)
    ax.axhline(0, color='white', linestyle=':', alpha=0.4)
    ax.set_xlabel('Trade # (Test set only)', color='#aaa')
    ax.set_ylabel(f'Cumulative {label}', color='#aaa')
    ax.set_title(f'SL=6.0/TP=6.0 - {title}', color='white', fontsize=12)
    ax.legend()
plt.tight_layout()
plt.savefig('18_model1_SL6TP6_comparison.png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f'Baseline final PnL: {test["cum_baseline"].iloc[-1]:.2f}   Model final PnL: {test["cum_model"].iloc[-1]:.2f}')
print(f'Baseline final ZPnL: {test["cum_baseline_z"].iloc[-1]:.2f}   Model final ZPnL: {test["cum_model_z"].iloc[-1]:.2f}')
