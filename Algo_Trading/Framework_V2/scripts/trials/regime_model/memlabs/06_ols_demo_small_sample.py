"""
Step 6 — visual demo of how w and b get calculated (OLS), using a very
small real sample (first 10 trades) from the TATAMOTORS 2023 trade log.
X = hidden_atr_pct_rollmean40 (the memory-encoded feature)
y = pnl (what we're trying to predict)
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

IN_DIR = Path(__file__).resolve().parent
TRADE_LOG = IN_DIR / 'TATAMOTORS_2023_trade_log_with_memory_feature.csv'
N_SAMPLE = 10


def main():
    trades = pd.read_csv(TRADE_LOG)
    trades.columns = trades.columns.str.strip()
    for col in trades.columns:
        if trades[col].dtype == object:
            trades[col] = trades[col].str.strip()

    sample = trades.head(N_SAMPLE).reset_index(drop=True)
    X = sample['hidden_atr_pct_rollmean40'].to_numpy()
    y = sample['pnl'].to_numpy()

    # OLS: w (slope) and b (intercept) that minimize squared error
    w, b = np.polyfit(X, y, 1)
    y_hat = w * X + b

    print(f'Sample of {N_SAMPLE} trades:')
    print(sample[['entry_dt', 'hidden_atr_pct_rollmean40', 'pnl']].to_string(index=False))
    print(f'\nFitted:  w = {w:.4f}   b = {b:.4f}')
    print(f'\ny_hat per trade (w * X + b):')
    for x_i, y_i, yh_i in zip(X, y, y_hat):
        print(f'  hidden={x_i:.4f}  actual_pnl={y_i:>7.2f}  y_hat={yh_i:>7.2f}  signal={"+1 (predict win)" if yh_i > 0 else "-1 (predict loss)"}')

    # --- Plot ---
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor('#0d1117'); ax.set_facecolor('#0d1117')

    ax.scatter(X, y, color='#58a6ff', s=80, zorder=3, label='Actual trades (X=hidden, y=pnl)')
    x_line = np.linspace(X.min(), X.max(), 100)
    ax.plot(x_line, w * x_line + b, color='#f78166', linewidth=2, zorder=2,
            label=f'Fitted line: y_hat = {w:.2f}·X + {b:.2f}')
    ax.axhline(0, color='#888', linewidth=0.8, linestyle='--', zorder=1)

    for x_i, y_i in zip(X, y):
        ax.plot([x_i, x_i], [y_i, w * x_i + b], color='#888', linewidth=0.7, linestyle=':', zorder=1)

    ax.set_xlabel('hidden_atr_pct_rollmean40 (X)', color='#aaa')
    ax.set_ylabel('pnl (y)', color='#aaa')
    ax.set_title(f'OLS fit on {N_SAMPLE} trades — how w and b are found', color='white', fontsize=12)
    ax.legend(facecolor='#161b22', edgecolor='#333', labelcolor='white')
    ax.tick_params(colors='#aaa')
    for spine in ax.spines.values():
        spine.set_color('#333')

    out_path = IN_DIR / 'ols_demo_small_sample.png'
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f'\nSaved plot to {out_path}')


if __name__ == '__main__':
    main()
