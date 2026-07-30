"""
Step 15 - corrected online learning, matching the author's actual implementation:
1. Scaler updates incrementally every trade (scaler.partial_fit inside the loop),
   instead of being fit once on the first 100 trades and frozen (fixes both the
   "goes stale over 11 years" issue and the lookahead bias in the warm-up window).
2. learning_rate="pa1" (Passive-Aggressive), so the update step size scales with
   the loss magnitude (capped at eta0), instead of "constant" (fixed eta0 step
   every time regardless of error size).
epsilon=0.1 kept as-is (deliberately, per discussion - already a fairly strict
cushion relative to this data's PnL scale, not loosened to match the author's
log-return-scaled epsilon=0.0002).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

IN_DIR = Path(__file__).resolve().parent
TRADE_LOG = IN_DIR / 'TATAMOTORS_2015-2025_trade_log_with_memory_feature.csv'
N_WARMUP = 100  # still used only to exclude early, unreliable predictions from evaluation


def zerodha_short(entry, exit_px):
    brok = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt = entry * 0.00025
    txn = (entry + exit_px) * 0.0000307
    sebi = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def calc_metrics(tdf):
    if len(tdf) == 0:
        return 0, 0.0, 0.0, 0.0
    tdf = tdf.copy()
    tdf['zpnl'] = tdf.apply(lambda r: r['pnl'] - zerodha_short(r['entry'], r['exit_price']), axis=1)
    gp = tdf[tdf['pnl'] > 0]['pnl'].sum()
    gl = -tdf[tdf['pnl'] <= 0]['pnl'].sum()
    zw = tdf[tdf['zpnl'] > 0]['zpnl'].sum()
    zl = -tdf[tdf['zpnl'] <= 0]['zpnl'].sum()
    pf = round(gp / gl, 3) if gl > 0 else 0.0
    zpf = round(zw / zl, 3) if zl > 0 else 0.0
    win_rate = round((tdf['pnl'] > 0).mean() * 100, 1)
    return len(tdf), pf, zpf, win_rate


def main():
    trades = pd.read_csv(TRADE_LOG)
    trades.columns = trades.columns.str.strip()
    for col in trades.columns:
        if trades[col].dtype == object:
            trades[col] = trades[col].str.strip()
    trades['entry_dt'] = pd.to_datetime(trades['entry_dt'])
    trades = trades.sort_values('entry_dt').reset_index(drop=True)

    scaler = StandardScaler()
    model = SGDRegressor(loss='epsilon_insensitive', epsilon=0.1, penalty=None,
                          learning_rate='pa1', eta0=0.01, random_state=42)

    records = []
    for _, row in trades.iterrows():
        x_raw = np.array([[row['hidden_atr_pct_rollmean40']]])
        y = row['pnl']

        # Scale incrementally: update running mean/std with this trade FIRST,
        # then transform using that just-updated mean/std (no lookahead - only
        # ever uses this trade and everything strictly before it).
        scaler.partial_fit(x_raw)
        x = scaler.transform(x_raw)

        y_hat = model.predict(x)[0] if hasattr(model, 'coef_') else 0.0
        signal = np.sign(y_hat) if y_hat != 0 else 1

        records.append({**row.to_dict(), 'y_hat': y_hat, 'signal': signal,
                         'w': model.coef_[0] if hasattr(model, 'coef_') else 0.0})

        model.partial_fit(x, [y])

    results = pd.DataFrame(records)
    eval_df = results.iloc[N_WARMUP:].reset_index(drop=True)

    correct = ((eval_df['signal'] > 0) & (eval_df['pnl'] > 0)) | ((eval_df['signal'] <= 0) & (eval_df['pnl'] <= 0))
    print(f'Directional accuracy (trades 101 onward, PA1 online learning): {correct.sum()}/{len(eval_df)} ({correct.mean()*100:.1f}%)\n')

    n_all, pf_all, zpf_all, wr_all = calc_metrics(eval_df)
    print(f'Baseline (no filter):      N={n_all:>5}  PF={pf_all}  ZPF={zpf_all}  Win rate={wr_all}%')

    filtered = eval_df[eval_df['signal'] > 0]
    n_f, pf_f, zpf_f, wr_f = calc_metrics(filtered)
    print(f'Filtered (signal=+1 only): N={n_f:>5}  PF={pf_f}  ZPF={zpf_f}  Win rate={wr_f}%')

    w_series = results['w'].iloc[N_WARMUP:]
    flips = (np.sign(w_series).diff().fillna(0) != 0).sum()
    print(f'\nWeight sign flips after warm-up: {flips} (out of {len(w_series)} trades)')
    print(f'Weight range: min={w_series.min():.4f}  max={w_series.max():.4f}')

    # Signal-count breakdown, same as script 14, for direct comparison
    eval_df = eval_df.copy()
    eval_df['year'] = eval_df['entry_dt'].dt.year
    eval_df['predicted_win'] = eval_df['signal'] > 0
    eval_df['actual_win'] = eval_df['pnl'] > 0

    def summarize(df):
        n = len(df)
        n_pos = (df['signal'] > 0).sum()
        n_neg = (df['signal'] <= 0).sum()
        pos_correct = ((df['signal'] > 0) & df['actual_win']).sum()
        neg_correct = ((df['signal'] <= 0) & ~df['actual_win']).sum()
        pos_acc = pos_correct / n_pos * 100 if n_pos > 0 else float('nan')
        neg_acc = neg_correct / n_neg * 100 if n_neg > 0 else float('nan')
        return n, n_pos, n_neg, pos_acc, neg_acc

    n, n_pos, n_neg, pos_acc, neg_acc = summarize(eval_df)
    print(f'\n=== Overall signal counts (trades 101 onward) ===')
    print(f'Predicted positive (signal=+1, "take"): {n_pos}  ({n_pos/n*100:.1f}%)  -> correct {pos_acc:.1f}% of the time')
    print(f'Predicted negative (signal=-1, "skip"): {n_neg}  ({n_neg/n*100:.1f}%)  -> correct {neg_acc:.1f}% of the time')

    print('\n=== Year-wise ===')
    print(f'{"Year":>6} {"N":>6} {"PF":>7} {"ZPF":>7} {"WR%":>6} {"Pred+":>7} {"Pred+ %":>9} {"Pred+ Acc%":>11}')
    for yr, grp in eval_df.groupby('year'):
        n_y, pf_y, zpf_y, wr_y = calc_metrics(grp)
        _, n_pos_y, n_neg_y, pos_acc_y, neg_acc_y = summarize(grp)
        pos_pct = n_pos_y / n_y * 100 if n_y > 0 else 0
        pos_acc_s = f'{pos_acc_y:.1f}' if n_pos_y > 0 else 'n/a'
        print(f'{yr:>6} {n_y:>6} {pf_y:>7} {zpf_y:>7} {wr_y:>6} {n_pos_y:>7} {pos_pct:>8.1f}% {pos_acc_s:>11}')


if __name__ == '__main__':
    main()
