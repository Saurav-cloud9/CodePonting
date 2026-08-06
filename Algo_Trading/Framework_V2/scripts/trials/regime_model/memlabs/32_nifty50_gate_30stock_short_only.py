"""
Step 32 — scale the NIFTY50-as-shared-gate finding (notebook 31 + in-session
TATAMOTORS check) to all 30 DS3 stocks, SHORT side only.

Single NIFTY50 Model B signal (Train-only fit, c=0, no shift -- the shift
experiments turned out fragile/small-N, c=0 was the most robust result on
TATAMOTORS) computed ONCE, then applied as a shared day-level gate across all
30 stocks' real SHORT (ma_rejection_v1_core.py) trades. This is different
from steps 25-29, which fit a SEPARATE signal per stock -- here every stock
uses the exact same NIFTY50-derived Buy/Sell call for a given calendar day.

Only SHORT is tested here (LONG was already shown not to work with this gate
-- NIFTY50 signal is too Buy-skewed to filter LONG meaningfully).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

KITE_BOT_SCRIPTS = Path(r'C:\Users\Saurav\CodePonting\Algo_Trading\kite_oracle_papertrading\scripts')
sys.path.insert(0, str(KITE_BOT_SCRIPTS))
from ma_rejection_v1_core import StockState, process_bar  # noqa: E402

DS3_DIR = Path(r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3')
NIFTY_PATH = Path(r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\daily\NIFTY50.parquet')
OUT_DIR = Path(__file__).resolve().parent

SYMBOLS = ['ADANIPORTS','ASHOKLEY','AXISBANK','BAJFINANCE','BANDHANBNK','BHARTIARTL',
           'CIPLA','COALINDIA','DABUR','DIVISLAB','HDFCBANK','HINDALCO','ICICIBANK',
           'INDUSINDBK','INFY','ITC','JSWSTEEL','NATIONALUM','NTPC','ONGC','PNB',
           'POWERGRID','RELIANCE','SBIN','SUNPHARMA','TATAMOTORS','TATASTEEL','TECHM',
           'VEDL','WIPRO']


def zerodha_short(entry, exit_px):
    brok = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt = entry * 0.00025
    txn = (entry + exit_px) * 0.0000307
    sebi = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def build_nifty_signal():
    daily = pd.read_parquet(NIFTY_PATH)
    daily['datetime'] = pd.to_datetime(daily['datetime'])
    if daily['datetime'].dt.tz is not None:
        daily['datetime'] = daily['datetime'].apply(lambda x: x.replace(tzinfo=None))
    daily.set_index('datetime', inplace=True)
    daily.rename(columns={'close': 'c'}, inplace=True)
    daily = daily[['c']]
    daily['close_log_return'] = np.log(daily['c'] / daily['c'].shift())
    daily['close_log_return_lag_1'] = daily['close_log_return'].shift()
    daily['close_log_return_ma_lag_1'] = daily['close_log_return_lag_1'].rolling(40).mean()

    features = ['close_log_return_lag_1', 'close_log_return_ma_lag_1']
    df = daily.dropna(subset=features + ['close_log_return'])
    df_train, df_test = train_test_split(df, test_size=0.25, shuffle=False)
    model = LinearRegression()
    model.fit(df_train[features], df_train['close_log_return'])

    combined = df.copy()
    combined['y_hat'] = model.predict(combined[features])
    combined['signal'] = np.sign(combined['y_hat'])
    combined['split'] = 'train'
    combined.loc[df_test.index, 'split'] = 'test'
    print(f'NIFTY50 Model B: coef_={model.coef_}  intercept_={model.intercept_}')
    print(f'Train: {len(df_train)} days ({df_train.index.min().date()} -> {df_train.index.max().date()})')
    print(f'Test:  {len(df_test)} days ({df_test.index.min().date()} -> {df_test.index.max().date()})')
    return combined[['signal', 'split']]


def load_bars(symbol):
    f = DS3_DIR / f'{symbol}.parquet'
    df = pd.read_parquet(f, columns=['datetime', 'open', 'high', 'low', 'close'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].apply(lambda x: x.replace(tzinfo=None))
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df.loc[df[col] <= 0, col] = np.nan
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df.sort_values('datetime', inplace=True, kind='mergesort')
    df.reset_index(drop=True, inplace=True)
    return df


def build_short_trades(symbol, bars):
    state = StockState()
    trades = []
    for bar in bars.to_dict('records'):
        process_bar(symbol, bar, state, trades)
    tdf = pd.DataFrame(trades)
    if len(tdf) == 0:
        return tdf
    tdf['entry_dt'] = pd.to_datetime(tdf['entry_dt'])
    tdf['zpnl'] = tdf.apply(lambda r: r['pnl'] - zerodha_short(r['entry'], r['exit_price']), axis=1)
    return tdf


def summarize(sub, symbol, split, bucket):
    n = len(sub)
    row = {'symbol': symbol, 'split': split, 'bucket': bucket, 'n': n}
    if n == 0:
        row.update({'pnl': 0.0, 'pf': 0.0, 'zpnl': 0.0, 'zpf': 0.0})
        return row
    gp = sub[sub['pnl'] > 0]['pnl'].sum()
    gl = -sub[sub['pnl'] <= 0]['pnl'].sum()
    pf = gp / gl if gl > 0 else 0.0
    zw = sub[sub['zpnl'] > 0]['zpnl'].sum()
    zl = -sub[sub['zpnl'] <= 0]['zpnl'].sum()
    zpf = zw / zl if zl > 0 else 0.0
    row.update({'pnl': round(sub['pnl'].sum(), 2), 'pf': round(pf, 3),
                'zpnl': round(sub['zpnl'].sum(), 2), 'zpf': round(zpf, 3)})
    return row


def main():
    nifty_signal = build_nifty_signal()
    print()

    all_rows = []
    for symbol in SYMBOLS:
        print(f'--- {symbol} ---')
        bars = load_bars(symbol)
        short = build_short_trades(symbol, bars)
        if len(short) == 0:
            print('  no trades, skipping')
            continue
        short['entry_date'] = short['entry_dt'].dt.normalize()
        short = short.join(nifty_signal, on='entry_date').dropna(subset=['signal'])

        for split in ['train', 'test']:
            s = short[short['split'] == split]
            all_rows.append(summarize(s, symbol, split, 'SHORT baseline'))
            all_rows.append(summarize(s[s['signal'] == -1], symbol, split, 'SHORT gated (NIFTY c=0)'))
        print(f'  {len(short)} short trades total')

    result = pd.DataFrame(all_rows)
    out_path = OUT_DIR / '32_nifty50_gate_30stock_short_only_results.csv'
    result.to_csv(out_path, index=False)
    print()
    print(f'Saved {len(result)} rows to {out_path}')

    test_gated = result[(result['split'] == 'test') & (result['bucket'] == 'SHORT gated (NIFTY c=0)')]
    test_gated = test_gated.sort_values('zpf', ascending=False)
    print()
    print(test_gated[['symbol', 'n', 'pf', 'zpnl', 'zpf']].to_string(index=False))


if __name__ == '__main__':
    main()
