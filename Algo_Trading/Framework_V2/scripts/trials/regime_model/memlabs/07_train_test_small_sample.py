"""
Step 7 — small-sample train/test intuition builder. Fit w/b on a small
TRAIN slice, then apply the SAME fixed w/b to a separate TEST slice the
model never saw, to make the train-vs-predict distinction concrete.
"""
from pathlib import Path

import numpy as np
import pandas as pd

IN_DIR = Path(__file__).resolve().parent
TRADE_LOG = IN_DIR / 'TATAMOTORS_2023_trade_log_with_memory_feature.csv'
N_TRAIN = 10
N_TEST = 5


def main():
    trades = pd.read_csv(TRADE_LOG)
    trades.columns = trades.columns.str.strip()
    for col in trades.columns:
        if trades[col].dtype == object:
            trades[col] = trades[col].str.strip()

    train = trades.iloc[:N_TRAIN].reset_index(drop=True)
    test = trades.iloc[N_TRAIN:N_TRAIN + N_TEST].reset_index(drop=True)

    X_train = train['hidden_atr_pct_rollmean40'].to_numpy()
    y_train = train['pnl'].to_numpy()

    # --- Phase 1: fit w, b on TRAIN only ---
    w, b = np.polyfit(X_train, y_train, 1)
    print(f'Phase 1 - fit on {N_TRAIN} TRAIN trades: w={w:.4f}  b={b:.4f}\n')

    # --- Phase 2: apply the SAME fixed w, b to TEST trades (never seen) ---
    X_test = test['hidden_atr_pct_rollmean40'].to_numpy()
    y_test_actual = test['pnl'].to_numpy()
    y_hat_test = w * X_test + b
    signal_test = np.sign(y_hat_test)

    print(f'Phase 2 - predict on {N_TEST} TEST trades (model never saw these):')
    print(f'{"hidden(x)":>10} {"y_hat":>8} {"signal":>8} {"actual pnl":>11} {"correct?":>9}')
    correct = 0
    for x_i, yh_i, s_i, y_actual in zip(X_test, y_hat_test, signal_test, y_test_actual):
        was_correct = (s_i > 0 and y_actual > 0) or (s_i < 0 and y_actual <= 0)
        correct += was_correct
        print(f'{x_i:>10.4f} {yh_i:>8.2f} {s_i:>8.0f} {y_actual:>11.2f} {"yes" if was_correct else "no":>9}')

    print(f'\nDirectional accuracy on TEST: {correct}/{N_TEST}')


if __name__ == '__main__':
    main()
