"""
Step 28 — 30-stock version of the regime-gating test (steps 25-27), one
stock at a time: build SHORT trade log (live ma_rejection_v1_core.py logic),
build LONG trade log (ma_30_bounce_v1.py wick-only-touch logic, SL=2.0/TP=5.5),
fit Model A / MA-alone / Model B daily regime signals (Train-only fit,
chronological 75/25 split, same rigor as notebook 22/24), gate both trade
logs by each model's daily signal, report Train vs Test PF/ZPF for
SHORT/LONG/COMBINED baseline vs gated.

VERIFICATION MODE: SYMBOLS is currently set to just ['TATAMOTORS'] so this
can be checked against the known-good result from
27_regime_gated_comparison_all_models_results.csv (Model B | TEST | SHORT
gated should be: N=403, PF=1.559, ZPnL=11.18, ZPF=1.022) before running the
full 30-symbol list.

Output: ONE long-format CSV, all stocks stacked, 'symbol' as first column —
not 30 separate files, not an Excel workbook with per-stock sheets.
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

DS3_DIR = Path(r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V1\data\historical\intraday_5min_DS3')
OUT_DIR = Path(__file__).resolve().parent

SYMBOLS = ['ADANIPORTS','ASHOKLEY','AXISBANK','BAJFINANCE','BANDHANBNK','BHARTIARTL',
           'CIPLA','COALINDIA','DABUR','DIVISLAB','HDFCBANK','HINDALCO','ICICIBANK',
           'INDUSINDBK','INFY','ITC','JSWSTEEL','NATIONALUM','NTPC','ONGC','PNB',
           'POWERGRID','RELIANCE','SBIN','SUNPHARMA','TATAMOTORS','TATASTEEL','TECHM',
           'VEDL','WIPRO']

SHORT_SL_MULT, SHORT_TP_MULT = 2.0, 4.5   # matches ma_rejection_v1_core.py (locked live)
LONG_SL_MULT, LONG_TP_MULT = 2.0, 5.5     # matches ma_30_bounce_v1.py (locked v1 sweep)
EOD_HOUR = 15


def zerodha_short(entry, exit_px):
    brok = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt = entry * 0.00025
    txn = (entry + exit_px) * 0.0000307
    sebi = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def zerodha_long(entry, exit_px):
    brok = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt = exit_px * 0.00025
    txn = (entry + exit_px) * 0.0000307
    sebi = (entry + exit_px) * 0.000001
    stamp = entry * 0.000003
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def load_bars(symbol):
    f = DS3_DIR / f'{symbol}.parquet'
    df = pd.read_parquet(f, columns=['datetime', 'open', 'high', 'low', 'close'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].apply(lambda x: x.replace(tzinfo=None))
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df.loc[df[col] <= 0, col] = np.nan  # DS3 has some bad zero-price ticks (e.g. ICICIBANK)
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df.sort_values('datetime', inplace=True, kind='mergesort')
    df.reset_index(drop=True, inplace=True)
    return df


def build_short_trades(symbol, bars):
    """Live ma_rejection_v1_core.py logic — full DS3 history, no year filter."""
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


def build_long_trades(symbol, bars):
    """ma_30_bounce_v1.py wick-only-touch logic, SL=2.0x/TP=5.5x."""
    high, low, close = bars['high'], bars['low'], bars['close']
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    bars = bars.copy()
    bars['atr14'] = tr.rolling(14).mean()
    bars['ma20'] = close.rolling(20).mean()

    trades = []
    i = 0
    n = len(bars)
    while i < n:
        row = bars.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']):
            i += 1
            continue
        if row['low'] <= row['ma20'] and row['open'] > row['ma20'] and row['close'] > row['ma20']:
            if row['hour'] >= EOD_HOUR:
                i += 1
                continue
            touch_date = row['date']
            atr = row['atr14']
            entry_idx = i + 1
            if entry_idx >= n:
                i += 1
                continue
            entry_bar = bars.iloc[entry_idx]
            if entry_bar['date'] != touch_date:
                i += 1
                continue
            entry = entry_bar['open']
            entry_dt = entry_bar['datetime']
            sl = entry - LONG_SL_MULT * atr
            tp = entry + LONG_TP_MULT * atr
            for k in range(entry_idx, n):
                k_bar = bars.iloc[k]
                if k_bar['date'] != touch_date:
                    prev = bars.iloc[k - 1]
                    exit_price = prev['close']
                    pnl = exit_price - entry
                    exit_dt = prev['datetime']
                    break
                if k_bar['hour'] >= EOD_HOUR:
                    exit_price = k_bar['open']
                    pnl = exit_price - entry
                    exit_dt = k_bar['datetime']
                    break
                if k_bar['low'] <= sl:
                    exit_price = sl
                    pnl = sl - entry
                    exit_dt = k_bar['datetime']
                    break
                if k_bar['high'] >= tp:
                    exit_price = tp
                    pnl = tp - entry
                    exit_dt = k_bar['datetime']
                    break
            trades.append({'symbol': symbol, 'entry_dt': entry_dt, 'entry': entry,
                            'exit_dt': exit_dt, 'exit_price': exit_price, 'pnl': pnl})
            i = k + 1
        else:
            i += 1
    tdf = pd.DataFrame(trades)
    if len(tdf) == 0:
        return tdf
    tdf['zpnl'] = tdf.apply(lambda r: r['pnl'] - zerodha_long(r['entry'], r['exit_price']), axis=1)
    return tdf


def load_daily(bars):
    daily = bars.set_index('datetime')['close'].resample('D').last().dropna().to_frame()
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
    return combined[['signal', 'split']]


def summarize(tdf, symbol, model_name, split, bucket):
    n = len(tdf)
    row = {'symbol': symbol, 'model': model_name, 'split': split, 'bucket': bucket, 'n': n}
    if n == 0:
        row.update({'pnl': 0.0, 'pf': 0.0, 'zpnl': 0.0, 'zpf': 0.0})
        return row
    gp = tdf[tdf['pnl'] > 0]['pnl'].sum()
    gl = -tdf[tdf['pnl'] <= 0]['pnl'].sum()
    pf = gp / gl if gl > 0 else 0.0
    zw = tdf[tdf['zpnl'] > 0]['zpnl'].sum()
    zl = -tdf[tdf['zpnl'] <= 0]['zpnl'].sum()
    zpf = zw / zl if zl > 0 else 0.0
    row.update({'pnl': round(tdf['pnl'].sum(), 2), 'pf': round(pf, 3),
                'zpnl': round(tdf['zpnl'].sum(), 2), 'zpf': round(zpf, 3)})
    return row


def process_symbol(symbol):
    print(f'--- {symbol} ---')
    bars = load_bars(symbol)
    short = build_short_trades(symbol, bars)
    long = build_long_trades(symbol, bars)
    daily = load_daily(bars)

    if len(short) == 0 or len(long) == 0:
        print(f'  Skipping {symbol}: no trades on one side (short={len(short)}, long={len(long)})')
        return []

    short['entry_date'] = short['entry_dt'].dt.normalize()
    long['entry_date'] = long['entry_dt'].dt.normalize()

    rows = []
    for model_name, features in [
        ('Model A', ['close_log_return_lag_1']),
        ('MA-alone', ['close_log_return_ma_lag_1']),
        ('Model B', ['close_log_return_lag_1', 'close_log_return_ma_lag_1']),
    ]:
        daily_signal = build_signal(daily, features)
        s = short.join(daily_signal, on='entry_date').dropna(subset=['signal'])
        l = long.join(daily_signal, on='entry_date').dropna(subset=['signal'])

        for split in ['train', 'test']:
            s_split = s[s['split'] == split]
            l_split = l[l['split'] == split]
            combined_baseline = pd.concat([s_split[['pnl', 'zpnl']], l_split[['pnl', 'zpnl']]])
            combined_gated = pd.concat([
                s_split[s_split['signal'] == -1][['pnl', 'zpnl']],
                l_split[l_split['signal'] == 1][['pnl', 'zpnl']],
            ])
            rows.append(summarize(s_split, symbol, model_name, split, 'SHORT baseline'))
            rows.append(summarize(s_split[s_split['signal'] == -1], symbol, model_name, split, 'SHORT gated'))
            rows.append(summarize(l_split, symbol, model_name, split, 'LONG baseline'))
            rows.append(summarize(l_split[l_split['signal'] == 1], symbol, model_name, split, 'LONG gated'))
            rows.append(summarize(combined_baseline, symbol, model_name, split, 'COMBINED baseline'))
            rows.append(summarize(combined_gated, symbol, model_name, split, 'COMBINED gated'))
    print(f'  short trades={len(short)}  long trades={len(long)}')
    return rows


def main():
    all_rows = []
    for symbol in SYMBOLS:
        all_rows.extend(process_symbol(symbol))

    result = pd.DataFrame(all_rows)
    out_path = OUT_DIR / '28_regime_gate_30stock_sweep_results.csv'
    result.to_csv(out_path, index=False)
    print()
    print(f'Saved {len(result)} rows ({result["symbol"].nunique()} symbols) to {out_path}')

    # One line per symbol: best-ZPF gate among the 3 models, Test split, COMBINED gated bucket
    check = result[(result['split'] == 'test') & (result['bucket'] == 'COMBINED gated')]
    best = check.loc[check.groupby('symbol')['zpf'].idxmax()].sort_values('zpf', ascending=False)
    print(best[['symbol', 'model', 'n', 'pf', 'zpnl', 'zpf']].to_string(index=False))


if __name__ == '__main__':
    main()
