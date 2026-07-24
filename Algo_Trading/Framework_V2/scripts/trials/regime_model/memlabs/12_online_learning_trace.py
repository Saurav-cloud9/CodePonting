"""
Step 12 — traces the online learning update mechanics step by step for a
handful of real trades, to build intuition for what SGDRegressor.partial_fit
is actually doing differently from the one-shot OLS fit.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

IN_DIR = Path(__file__).resolve().parent
TRADE_LOG = IN_DIR / 'TATAMOTORS_2015-2025_trade_log_with_memory_feature.csv'
N_WARMUP = 100
N_TRACE = 8  # how many trades after warm-up to show in detail


def main():
    trades = pd.read_csv(TRADE_LOG)
    trades.columns = trades.columns.str.strip()
    for col in trades.columns:
        if trades[col].dtype == object:
            trades[col] = trades[col].str.strip()
    trades['entry_dt'] = pd.to_datetime(trades['entry_dt'])
    trades = trades.sort_values('entry_dt').reset_index(drop=True)

    scaler = StandardScaler()
    scaler.fit(trades['hidden_atr_pct_rollmean40'].to_numpy()[:N_WARMUP].reshape(-1, 1))

    model = SGDRegressor(loss='epsilon_insensitive', epsilon=0.1, penalty=None,
                          learning_rate='constant', eta0=0.01, random_state=42)

    # Warm up silently on the first N_WARMUP trades, same as the main script
    for _, row in trades.iloc[:N_WARMUP].iterrows():
        x = scaler.transform(np.array([[row['hidden_atr_pct_rollmean40']]]))
        model.partial_fit(x, [row['pnl']])

    print(f'After {N_WARMUP} warm-up trades: w={model.coef_[0]:.4f}  b={model.intercept_[0]:.4f}\n')
    print('Now tracing the next few trades one at a time:\n')

    for i, row in trades.iloc[N_WARMUP:N_WARMUP + N_TRACE].iterrows():
        raw_x = row['hidden_atr_pct_rollmean40']
        x = scaler.transform(np.array([[raw_x]]))
        actual_y = row['pnl']

        w_before, b_before = model.coef_[0], model.intercept_[0]
        y_hat = model.predict(x)[0]
        error = actual_y - y_hat
        signal = np.sign(y_hat)

        print(f'Trade {row["entry_dt"]} ({row["symbol"]}):')
        print(f'  raw x (hidden)      = {raw_x:.4f}   scaled x = {x[0][0]:.4f}')
        print(f'  w (before) = {w_before:.4f}   b (before) = {b_before:.4f}')
        print(f'  y_hat = w*x + b = {w_before:.4f}*{x[0][0]:.4f} + {b_before:.4f} = {y_hat:.4f}')
        print(f'  signal = sign(y_hat) = {signal:+.0f}')
        print(f'  actual pnl (y) = {actual_y:.4f}')
        print(f'  error = y - y_hat = {actual_y:.4f} - {y_hat:.4f} = {error:.4f}')

        model.partial_fit(x, [actual_y])
        w_after, b_after = model.coef_[0], model.intercept_[0]
        print(f'  -> after partial_fit: w (after) = {w_after:.4f}   b (after) = {b_after:.4f}')
        print(f'  -> w changed by {w_after - w_before:+.4f}, b changed by {b_after - b_before:+.4f}\n')


if __name__ == '__main__':
    main()
