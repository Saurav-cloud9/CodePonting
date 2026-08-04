"""
Step 26 — MemLabs Model A as a day-level regime gate on fv2's real TATAMOTORS
trades (both sides): on days Model A predicts DOWN (signal=-1), only count
SHORT (rejection_v1) trades entered that day; on days it predicts UP
(signal=+1), only count LONG (bounce_v1) trades entered that day.

Model A itself: fit ONLY on the chronological first 75% of TATAMOTORS daily
close-to-close log returns (Train), predicted on the full series. Every
number below is reported Train-days vs Test-days SEPARATELY (never blended)
so a Train-period edge can't be mistaken for real predictive power -- same
rigor established in notebook 22/24.

cum_trade_log_return is NOT used here; these are TATAMOTORS' actual fv2 PnL/
ZPnL numbers (from the trade logs built in step 01 and step 25), gated only
by which calendar day each trade was entered on.
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

DS3_PATH = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V1\data\historical\intraday_5min_DS3\TATAMOTORS.parquet'
SHORT_TRADES_CSV = 'TATAMOTORS_2015-2025_trade_log_with_memory_feature.csv'
LONG_TRADES_CSV = 'TATAMOTORS_2015-2025_trade_log_LONG_bounce_v1.csv'


def zerodha_short(entry, exit_px):
    brok = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt = entry * 0.00025
    txn = (entry + exit_px) * 0.0000307
    sebi = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def build_daily_signal():
    raw = pd.read_parquet(DS3_PATH)
    raw['datetime'] = pd.to_datetime(raw['datetime'])
    if raw['datetime'].dt.tz is not None:
        raw['datetime'] = raw['datetime'].apply(lambda x: x.replace(tzinfo=None))
    raw.set_index('datetime', inplace=True)
    daily = raw['close'].resample('D').last().dropna().to_frame()
    daily.rename(columns={'close': 'c'}, inplace=True)
    daily['close_log_return'] = np.log(daily['c'] / daily['c'].shift())
    daily['close_log_return_lag_1'] = daily['close_log_return'].shift()
    df = daily.dropna(subset=['close_log_return_lag_1', 'close_log_return'])

    df_train, df_test = train_test_split(df, test_size=0.25, shuffle=False)
    model = LinearRegression()
    model.fit(df_train[['close_log_return_lag_1']], df_train['close_log_return'])

    combined = df.copy()
    combined['y_hat'] = model.predict(combined[['close_log_return_lag_1']])
    combined['signal'] = np.sign(combined['y_hat'])
    combined['split'] = 'train'
    combined.loc[df_test.index, 'split'] = 'test'

    print(f'coef_={model.coef_}  intercept_={model.intercept_}')
    print(f'Train days: {len(df_train)} ({df_train.index.min().date()} -> {df_train.index.max().date()})')
    print(f'Test  days: {len(df_test)} ({df_test.index.min().date()} -> {df_test.index.max().date()})')
    print()
    return combined[['signal', 'split']]


def summarize(tdf, label):
    n = len(tdf)
    if n == 0:
        return {'label': label, 'n': 0, 'pnl': 0.0, 'pf': 0.0, 'zpnl': 0.0, 'zpf': 0.0}
    gp = tdf[tdf['pnl'] > 0]['pnl'].sum()
    gl = -tdf[tdf['pnl'] <= 0]['pnl'].sum()
    pf = gp / gl if gl > 0 else 0.0
    zw = tdf[tdf['zpnl'] > 0]['zpnl'].sum()
    zl = -tdf[tdf['zpnl'] <= 0]['zpnl'].sum()
    zpf = zw / zl if zl > 0 else 0.0
    return {'label': label, 'n': n, 'pnl': round(tdf['pnl'].sum(), 2), 'pf': round(pf, 3),
            'zpnl': round(tdf['zpnl'].sum(), 2), 'zpf': round(zpf, 3)}


def main():
    daily_signal = build_daily_signal()

    short = pd.read_csv(SHORT_TRADES_CSV)
    short.columns = short.columns.str.strip()
    short['entry_dt'] = pd.to_datetime(short['entry_dt'])
    short['entry_date'] = short['entry_dt'].dt.normalize()
    short['zpnl'] = short.apply(lambda r: r['pnl'] - zerodha_short(r['entry'], r['exit_price']), axis=1)

    long = pd.read_csv(LONG_TRADES_CSV)
    long['entry_dt'] = pd.to_datetime(long['entry_dt'])
    long['entry_date'] = long['entry_dt'].dt.normalize()
    # zpnl already computed in step 25's output

    short = short.join(daily_signal, on='entry_date')
    long = long.join(daily_signal, on='entry_date')

    short = short.dropna(subset=['signal'])
    long = long.dropna(subset=['signal'])

    rows = []
    for split in ['train', 'test']:
        s = short[short['split'] == split]
        l = long[long['split'] == split]

        rows.append(summarize(s, f'{split.upper()} — SHORT baseline (every short trade)'))
        rows.append(summarize(s[s['signal'] == -1], f'{split.upper()} — SHORT gated (only Sell-signal days)'))
        rows.append(summarize(l, f'{split.upper()} — LONG baseline (every long trade)'))
        rows.append(summarize(l[l['signal'] == 1], f'{split.upper()} — LONG gated (only Buy-signal days)'))

        combined_baseline = pd.concat([s[['pnl', 'zpnl']], l[['pnl', 'zpnl']]])
        combined_gated = pd.concat([s[s['signal'] == -1][['pnl', 'zpnl']], l[l['signal'] == 1][['pnl', 'zpnl']]])
        rows.append(summarize(combined_baseline, f'{split.upper()} — COMBINED baseline (both sides, all trades)'))
        rows.append(summarize(combined_gated, f'{split.upper()} — COMBINED gated (regime-matched only)'))

    result = pd.DataFrame(rows)
    print(result.to_string(index=False))
    result.to_csv('26_regime_gated_analysis_results.csv', index=False)
    print()
    print('Saved to 26_regime_gated_analysis_results.csv')


if __name__ == '__main__':
    main()
