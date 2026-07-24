"""
Step 11 — online learning (the author's fix for the "always predicts one
direction" problem). Instead of one static OLS fit, walk through trades
chronologically and update w/b incrementally after each one, using
SGDRegressor with partial_fit(). Single feature only (hidden_atr_pct_rollmean40).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

IN_DIR = Path(__file__).resolve().parent
TRADE_LOG = IN_DIR / 'TATAMOTORS_2015-2025_trade_log_with_memory_feature.csv'


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

    # Scale X - SGDRegressor is sensitive to feature scale, fit scaler on
    # a small initial warm-up slice only (can't know the full distribution
    # in advance in a true online setting, but this is close enough for demo)
    scaler = StandardScaler()
    scaler.fit(trades['hidden_atr_pct_rollmean40'].to_numpy()[:100].reshape(-1, 1))

    model = SGDRegressor(loss='epsilon_insensitive', epsilon=0.1, penalty=None,
                          learning_rate='constant', eta0=0.01, random_state=42)

    records = []
    for _, row in trades.iterrows():
        x = scaler.transform(np.array([[row['hidden_atr_pct_rollmean40']]]))
        y = row['pnl']

        if hasattr(model, 'coef_'):
            y_hat = model.predict(x)[0]
        else:
            y_hat = 0.0  # model not yet fit on anything

        signal = np.sign(y_hat) if y_hat != 0 else 1  # default to "take" before model warms up
        records.append({**row.to_dict(), 'y_hat': y_hat, 'signal': signal,
                         'w': model.coef_[0] if hasattr(model, 'coef_') else 0.0})

        model.partial_fit(x, [y])

    results = pd.DataFrame(records)

    # Skip the first 100 trades (warm-up, same as scaler fit window) for fair evaluation
    eval_df = results.iloc[100:].reset_index(drop=True)

    correct = ((eval_df['signal'] > 0) & (eval_df['pnl'] > 0)) | ((eval_df['signal'] <= 0) & (eval_df['pnl'] <= 0))
    print(f'Directional accuracy (trades 101 onward, online learning): {correct.sum()}/{len(eval_df)} ({correct.mean()*100:.1f}%)\n')

    n_all, pf_all, zpf_all, wr_all = calc_metrics(eval_df)
    print(f'Baseline (no filter):      N={n_all:>5}  PF={pf_all}  ZPF={zpf_all}  Win rate={wr_all}%')

    filtered = eval_df[eval_df['signal'] > 0]
    n_f, pf_f, zpf_f, wr_f = calc_metrics(filtered)
    print(f'Filtered (signal=+1 only): N={n_f:>5}  PF={pf_f}  ZPF={zpf_f}  Win rate={wr_f}%')

    # How often does the weight actually flip sign over time? (adaptiveness check)
    w_series = results['w'].iloc[100:]
    flips = (np.sign(w_series).diff().fillna(0) != 0).sum()
    print(f'\nWeight sign flips after warm-up: {flips} (out of {len(w_series)} trades)')
    print(f'Weight range: min={w_series.min():.4f}  max={w_series.max():.4f}')


if __name__ == '__main__':
    main()
