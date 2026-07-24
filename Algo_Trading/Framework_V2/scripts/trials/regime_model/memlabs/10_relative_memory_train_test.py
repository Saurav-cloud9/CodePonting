"""
Step 10 — "Modelling Relative Memory" (the author's 2-feature version):
y_hat = w1*atr_pct_at_touch + w2*hidden_atr_pct_rollmean40 + b
Same chronological train/test split as step 9, same TATAMOTORS full dataset,
to see if combining raw + memory-encoded beats either alone.
"""
from pathlib import Path

import numpy as np
import pandas as pd

IN_DIR = Path(__file__).resolve().parent
TRADE_LOG = IN_DIR / 'TATAMOTORS_2015-2025_trade_log_with_memory_feature.csv'
TRAIN_END_YEAR = 2022


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

    train = trades[trades['entry_dt'].dt.year <= TRAIN_END_YEAR].reset_index(drop=True)
    test = trades[trades['entry_dt'].dt.year > TRAIN_END_YEAR].reset_index(drop=True)
    print(f'Train: {len(train)} trades   Test: {len(test)} trades\n')

    # --- Fit multiple linear regression: y_hat = w1*x1 + w2*x2 + b ---
    X_train = train[['atr_pct_at_touch', 'hidden_atr_pct_rollmean40']].to_numpy()
    y_train = train['pnl'].to_numpy()
    X_train_design = np.column_stack([X_train, np.ones(len(X_train))])  # add bias column
    coeffs, *_ = np.linalg.lstsq(X_train_design, y_train, rcond=None)
    w1, w2, b = coeffs
    print(f'Fitted on train: w1(raw)={w1:.4f}  w2(hidden)={w2:.4f}  b={b:.4f}\n')

    # --- Apply to TEST ---
    X_test = test[['atr_pct_at_touch', 'hidden_atr_pct_rollmean40']].to_numpy()
    y_test = test['pnl'].to_numpy()
    y_hat_test = w1 * X_test[:, 0] + w2 * X_test[:, 1] + b
    signal_test = np.sign(y_hat_test)
    test = test.copy()
    test['signal'] = signal_test

    correct = ((signal_test > 0) & (y_test > 0)) | ((signal_test <= 0) & (y_test <= 0))
    print(f'Directional accuracy on TEST: {correct.sum()}/{len(test)} ({correct.mean()*100:.1f}%)\n')

    n_all, pf_all, zpf_all, wr_all = calc_metrics(test)
    print(f'TEST baseline (no filter):      N={n_all:>5}  PF={pf_all}  ZPF={zpf_all}  Win rate={wr_all}%')

    filtered = test[test['signal'] > 0]
    n_f, pf_f, zpf_f, wr_f = calc_metrics(filtered)
    print(f'TEST filtered (signal=+1 only): N={n_f:>5}  PF={pf_f}  ZPF={zpf_f}  Win rate={wr_f}%')

    skipped = test[test['signal'] <= 0]
    n_s, pf_s, zpf_s, wr_s = calc_metrics(skipped)
    print(f'TEST skipped (signal=-1, sanity check): N={n_s:>5}  PF={pf_s}  ZPF={zpf_s}  Win rate={wr_s}%')


if __name__ == '__main__':
    main()
