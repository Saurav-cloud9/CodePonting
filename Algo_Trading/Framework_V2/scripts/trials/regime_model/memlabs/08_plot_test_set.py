"""
Step 8 — plot the TEST set (5 unseen trades) against the SAME fitted line
from training (07_train_test_small_sample.py's w/b), color-coded by
whether the prediction was correct or not.
"""
from pathlib import Path

import matplotlib.pyplot as plt
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
    w, b = np.polyfit(X_train, y_train, 1)

    X_test = test['hidden_atr_pct_rollmean40'].to_numpy()
    y_test = test['pnl'].to_numpy()
    y_hat_test = w * X_test + b
    signal_test = np.sign(y_hat_test)
    correct = np.array([(s > 0 and y > 0) or (s < 0 and y <= 0) for s, y in zip(signal_test, y_test)])

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor('#0d1117'); ax.set_facecolor('#0d1117')

    # The SAME fitted line from training - extended across the test x-range too
    x_all = np.concatenate([X_train, X_test])
    x_line = np.linspace(x_all.min(), x_all.max(), 100)
    ax.plot(x_line, w * x_line + b, color='#f78166', linewidth=2, zorder=2,
            label=f'Fitted line (from TRAIN): y_hat = {w:.2f}x + {b:.2f}')
    ax.axhline(0, color='#888', linewidth=0.8, linestyle='--', zorder=1)

    # Faded train points for context
    ax.scatter(X_train, y_train, color='#484f58', s=50, zorder=2, label='Train points (used to fit line)')

    # Test points - green if correct, red if wrong
    ax.scatter(X_test[correct], y_test[correct], color='#3fb950', s=140, zorder=4,
               edgecolors='white', linewidths=1.2, marker='o', label='Test - correct prediction')
    ax.scatter(X_test[~correct], y_test[~correct], color='#f85149', s=140, zorder=4,
               edgecolors='white', linewidths=1.2, marker='X', label='Test - wrong prediction')

    for x_i, y_i in zip(X_test, y_test):
        ax.plot([x_i, x_i], [y_i, w * x_i + b], color='#666', linewidth=0.7, linestyle=':', zorder=1)

    ax.set_xlabel('hidden_atr_pct_rollmean40 (X)', color='#aaa')
    ax.set_ylabel('pnl (y)', color='#aaa')
    ax.set_title(f'Test set (unseen) against the TRAIN-fitted line — {correct.sum()}/{N_TEST} correct',
                 color='white', fontsize=12)
    ax.legend(facecolor='#161b22', edgecolor='#333', labelcolor='white', fontsize=9, loc='upper right')
    ax.tick_params(colors='#aaa')
    for spine in ax.spines.values():
        spine.set_color('#333')

    out_path = IN_DIR / 'ols_test_set_plot.png'
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f'Saved plot to {out_path}')
    print(f'Correct: {correct.sum()}/{N_TEST}')


if __name__ == '__main__':
    main()
