"""
Step 27 — same regime-gating test as step 26 (Model A), repeated for MA-alone
and Model B, so all three can be compared side by side on real fv2 SHORT/LONG
trade PnL and ZPnL. Same rigor: Train-only fit, Train/Test reported
separately, Test-period numbers are the ones that matter.
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


def load_daily():
    raw = pd.read_parquet(DS3_PATH)
    raw['datetime'] = pd.to_datetime(raw['datetime'])
    if raw['datetime'].dt.tz is not None:
        raw['datetime'] = raw['datetime'].apply(lambda x: x.replace(tzinfo=None))
    raw.set_index('datetime', inplace=True)
    daily = raw['close'].resample('D').last().dropna().to_frame()
    daily.rename(columns={'close': 'c'}, inplace=True)
    daily['close_log_return'] = np.log(daily['c'] / daily['c'].shift())
    daily['close_log_return_lag_1'] = daily['close_log_return'].shift()
    daily['close_log_return_ma_lag_1'] = daily['close_log_return_lag_1'].rolling(40).mean()
    return daily


def build_signal(daily, features, test_split=0.25):
    df = daily.dropna(subset=features + ['close_log_return'])
    df_train, df_test = train_test_split(df, test_size=test_split, shuffle=False)
    model = LinearRegression()
    model.fit(df_train[features], df_train['close_log_return'])

    combined = df.copy()
    combined['y_hat'] = model.predict(combined[features])
    combined['signal'] = np.sign(combined['y_hat'])
    combined['split'] = 'train'
    combined.loc[df_test.index, 'split'] = 'test'
    return combined[['signal', 'split']], model, len(df_train), len(df_test)


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


def run_for_model(model_name, daily_signal, short, long):
    short_m = short.join(daily_signal, on='entry_date').dropna(subset=['signal'])
    long_m = long.join(daily_signal, on='entry_date').dropna(subset=['signal'])

    rows = []
    for split in ['train', 'test']:
        s = short_m[short_m['split'] == split]
        l = long_m[long_m['split'] == split]

        combined_baseline = pd.concat([s[['pnl', 'zpnl']], l[['pnl', 'zpnl']]])
        combined_gated = pd.concat([s[s['signal'] == -1][['pnl', 'zpnl']], l[l['signal'] == 1][['pnl', 'zpnl']]])

        rows.append(summarize(s, f'{model_name} | {split.upper()} | SHORT baseline'))
        rows.append(summarize(s[s['signal'] == -1], f'{model_name} | {split.upper()} | SHORT gated'))
        rows.append(summarize(l, f'{model_name} | {split.upper()} | LONG baseline'))
        rows.append(summarize(l[l['signal'] == 1], f'{model_name} | {split.upper()} | LONG gated'))
        rows.append(summarize(combined_baseline, f'{model_name} | {split.upper()} | COMBINED baseline'))
        rows.append(summarize(combined_gated, f'{model_name} | {split.upper()} | COMBINED gated'))
    return rows


def main():
    daily = load_daily()

    short = pd.read_csv(SHORT_TRADES_CSV)
    short.columns = short.columns.str.strip()
    short['entry_dt'] = pd.to_datetime(short['entry_dt'])
    short['entry_date'] = short['entry_dt'].dt.normalize()
    short['zpnl'] = short.apply(lambda r: r['pnl'] - zerodha_short(r['entry'], r['exit_price']), axis=1)

    long = pd.read_csv(LONG_TRADES_CSV)
    long['entry_dt'] = pd.to_datetime(long['entry_dt'])
    long['entry_date'] = long['entry_dt'].dt.normalize()

    all_rows = []
    for model_name, features in [
        ('Model A', ['close_log_return_lag_1']),
        ('MA-alone', ['close_log_return_ma_lag_1']),
        ('Model B', ['close_log_return_lag_1', 'close_log_return_ma_lag_1']),
    ]:
        daily_signal, model, n_tr, n_te = build_signal(daily, features)
        print(f'{model_name}: coef_={model.coef_}  intercept_={model.intercept_}  train_n={n_tr}  test_n={n_te}')
        all_rows.extend(run_for_model(model_name, daily_signal, short, long))

    result = pd.DataFrame(all_rows)
    print()
    print(result.to_string(index=False))
    result.to_csv('27_regime_gated_comparison_all_models_results.csv', index=False)
    print()
    print('Saved to 27_regime_gated_comparison_all_models_results.csv')


if __name__ == '__main__':
    main()
