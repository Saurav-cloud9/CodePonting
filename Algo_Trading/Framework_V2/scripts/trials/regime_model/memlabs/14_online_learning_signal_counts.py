"""
Step 14 - same online-learning model as step 11, but reporting what the
author's video shows directly: how many times the model predicted a
positive PnL (signal=+1, "take") vs negative (signal=-1, "skip"), overall
and year-wise, alongside how many of each were actually right.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

IN_DIR = Path(__file__).resolve().parent
TRADE_LOG = IN_DIR / 'TATAMOTORS_2015-2025_trade_log_with_memory_feature.csv'
N_WARMUP = 100


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

    records = []
    for _, row in trades.iterrows():
        x = scaler.transform(np.array([[row['hidden_atr_pct_rollmean40']]]))
        y = row['pnl']

        y_hat = model.predict(x)[0] if hasattr(model, 'coef_') else 0.0
        signal = np.sign(y_hat) if y_hat != 0 else 1

        records.append({'entry_dt': row['entry_dt'], 'symbol': row['symbol'],
                         'pnl': y, 'y_hat': y_hat, 'signal': signal})
        model.partial_fit(x, [y])

    results = pd.DataFrame(records).iloc[N_WARMUP:].reset_index(drop=True)
    results['year'] = results['entry_dt'].dt.year
    results['predicted_win'] = results['signal'] > 0
    results['actual_win'] = results['pnl'] > 0
    results['correct'] = results['predicted_win'] == results['actual_win']

    def summarize(df):
        n = len(df)
        n_pos = (df['signal'] > 0).sum()
        n_neg = (df['signal'] <= 0).sum()
        pos_correct = ((df['signal'] > 0) & df['actual_win']).sum()
        neg_correct = ((df['signal'] <= 0) & ~df['actual_win']).sum()
        pos_acc = pos_correct / n_pos * 100 if n_pos > 0 else float('nan')
        neg_acc = neg_correct / n_neg * 100 if n_neg > 0 else float('nan')
        return n, n_pos, n_neg, pos_acc, neg_acc

    n, n_pos, n_neg, pos_acc, neg_acc = summarize(results)
    print('=== Overall (trades 101 onward) ===')
    print(f'Total trades evaluated: {n}')
    print(f'Predicted positive (signal=+1, "take"): {n_pos}  ({n_pos/n*100:.1f}%)  -> correct {pos_acc:.1f}% of the time')
    print(f'Predicted negative (signal=-1, "skip"): {n_neg}  ({n_neg/n*100:.1f}%)  -> correct {neg_acc:.1f}% of the time')
    print()

    print('=== Year-wise ===')
    print(f'{"Year":>6} {"N":>6} {"Pred+":>7} {"Pred-":>7} {"Pred+ %":>9} {"Pred+ Acc%":>11} {"Pred- Acc%":>11}')
    for yr, grp in results.groupby('year'):
        n, n_pos, n_neg, pos_acc, neg_acc = summarize(grp)
        pos_pct = n_pos / n * 100 if n > 0 else 0
        pos_acc_s = f'{pos_acc:.1f}' if n_pos > 0 else 'n/a'
        neg_acc_s = f'{neg_acc:.1f}' if n_neg > 0 else 'n/a'
        print(f'{yr:>6} {n:>6} {n_pos:>7} {n_neg:>7} {pos_pct:>8.1f}% {pos_acc_s:>11} {neg_acc_s:>11}')


if __name__ == '__main__':
    main()
