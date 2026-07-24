"""
Step 13 — year-wise breakdown of the online-learning (SGDRegressor) single
-feature model's results, to check if the promising filtered subset
(N=479, ZPF=1.01 overall) holds up consistently year by year, or if it's
another average-masking-noise situation like the earlier static bucket finding.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

IN_DIR = Path(__file__).resolve().parent
TRADE_LOG = IN_DIR / 'TATAMOTORS_2015-2025_trade_log_with_memory_feature.csv'
N_WARMUP = 100


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
    scaler.fit(trades['hidden_atr_pct_rollmean40'].to_numpy()[:N_WARMUP].reshape(-1, 1))

    model = SGDRegressor(loss='epsilon_insensitive', epsilon=0.1, penalty=None,
                          learning_rate='constant', eta0=0.01, random_state=42)

    records = []
    for _, row in trades.iterrows():
        x = scaler.transform(np.array([[row['hidden_atr_pct_rollmean40']]]))
        y_hat = model.predict(x)[0] if hasattr(model, 'coef_') else 0.0
        signal = np.sign(y_hat) if y_hat != 0 else 1
        records.append({**row.to_dict(), 'y_hat': y_hat, 'signal': signal})
        model.partial_fit(x, [row['pnl']])

    results = pd.DataFrame(records)
    eval_df = results.iloc[N_WARMUP:].reset_index(drop=True)
    eval_df['year'] = eval_df['entry_dt'].dt.year

    print(f'{"Year":<6} {"Baseline":>28}   {"Filtered (signal=+1)":>28}')
    print(f'{"":<6} {"N":>5} {"PF":>7} {"ZPF":>7} {"WR":>6}   {"N":>5} {"PF":>7} {"ZPF":>7} {"WR":>6}')
    for yr in sorted(eval_df['year'].unique()):
        sub = eval_df[eval_df['year'] == yr]
        n_b, pf_b, zpf_b, wr_b = calc_metrics(sub)
        filt = sub[sub['signal'] > 0]
        n_f, pf_f, zpf_f, wr_f = calc_metrics(filt)
        flag = 'OK' if zpf_f >= 1.0 else ('~' if zpf_f >= 0.9 else 'X')
        print(f'{yr:<6} {n_b:>5} {pf_b:>7} {zpf_b:>7} {wr_b:>5}%   {n_f:>5} {pf_f:>7} {zpf_f:>7} {wr_f:>5}%  {flag}')

    print()
    n_all, pf_all, zpf_all, wr_all = calc_metrics(eval_df)
    filtered_all = eval_df[eval_df['signal'] > 0]
    n_f, pf_f, zpf_f, wr_f = calc_metrics(filtered_all)
    print(f'OVERALL  Baseline: N={n_all} PF={pf_all} ZPF={zpf_all} WR={wr_all}%')
    print(f'OVERALL  Filtered: N={n_f} PF={pf_f} ZPF={zpf_f} WR={wr_f}%')


if __name__ == '__main__':
    main()
