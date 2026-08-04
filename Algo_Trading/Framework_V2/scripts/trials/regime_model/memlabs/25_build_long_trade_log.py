"""
Step 25 — build TATAMOTORS' full-history LONG (bounce) trade log, same
methodology as the existing SHORT trade log
(TATAMOTORS_2015-2025_trade_log_with_memory_feature.csv), but using
ma_30_bounce_v1.py's exact wick-only-touch logic (SL=2.0x, TP=5.5x) instead
of the rejection/short side. Needed to test MemLabs Model A as a day-level
regime gate across BOTH fv2 strategies (short + long), not just short alone.

zerodha_long() copied verbatim from
Framework_V2/baseline_reserve/baseline_reserve_lock/ma_30_bounce.py — same
formula family as the SHORT side's zerodha_short(), just STT-on-exit and
stamp-on-entry swapped (standard long-vs-short difference).
"""
import pandas as pd
import numpy as np

DS3_PATH = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V1\data\historical\intraday_5min_DS3\TATAMOTORS.parquet'
SYMBOL = 'TATAMOTORS'
SL_MULT = 2.0
TP_MULT = 5.5
EOD_HOUR = 15


def zerodha_long(entry, exit_px):
    brok = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt = exit_px * 0.00025
    txn = (entry + exit_px) * 0.0000307
    sebi = (entry + exit_px) * 0.000001
    stamp = entry * 0.000003
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def load_bars():
    df = pd.read_parquet(DS3_PATH)
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].apply(lambda x: x.replace(tzinfo=None))
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour

    high, low, close = df['high'], df['low'], df['close']
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    df['atr14'] = tr.rolling(14).mean()
    df['ma20'] = close.rolling(20).mean()
    return df


def run_backtest(df):
    trades = []
    i = 0
    n = len(df)
    while i < n:
        row = df.iloc[i]
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
            entry_bar = df.iloc[entry_idx]
            if entry_bar['date'] != touch_date:
                i += 1
                continue
            entry = entry_bar['open']
            entry_dt = entry_bar['datetime']
            sl = entry - SL_MULT * atr
            tp = entry + TP_MULT * atr
            for k in range(entry_idx, n):
                k_bar = df.iloc[k]
                if k_bar['date'] != touch_date:
                    prev = df.iloc[k - 1]
                    exit_price = prev['close']
                    pnl = exit_price - entry
                    outcome = 'EOD+' if pnl > 0 else 'EOD-'
                    exit_dt = prev['datetime']
                    break
                if k_bar['hour'] >= EOD_HOUR:
                    exit_price = k_bar['open']
                    pnl = exit_price - entry
                    outcome = 'EOD+' if pnl > 0 else 'EOD-'
                    exit_dt = k_bar['datetime']
                    break
                if k_bar['low'] <= sl:
                    exit_price = sl
                    pnl = sl - entry
                    outcome = 'L'
                    exit_dt = k_bar['datetime']
                    break
                if k_bar['high'] >= tp:
                    exit_price = tp
                    pnl = tp - entry
                    outcome = 'W'
                    exit_dt = k_bar['datetime']
                    break
            trades.append({
                'symbol': SYMBOL, 'entry_dt': entry_dt, 'entry': entry, 'sl': sl, 'tp': tp,
                'exit_dt': exit_dt, 'exit_price': exit_price, 'outcome': outcome, 'pnl': pnl,
            })
            i = k + 1
        else:
            i += 1
    return trades


def main():
    bars = load_bars()
    trades = run_backtest(bars)
    tdf = pd.DataFrame(trades)
    tdf['zpnl'] = tdf.apply(lambda r: r['pnl'] - zerodha_long(r['entry'], r['exit_price']), axis=1)

    out_path = 'TATAMOTORS_2015-2025_trade_log_LONG_bounce_v1.csv'
    tdf.to_csv(out_path, index=False)

    gp = tdf[tdf['pnl'] > 0]['pnl'].sum()
    gl = -tdf[tdf['pnl'] <= 0]['pnl'].sum()
    pf = gp / gl if gl > 0 else 0
    zw = tdf[tdf['zpnl'] > 0]['zpnl'].sum()
    zl = -tdf[tdf['zpnl'] <= 0]['zpnl'].sum()
    zpf = zw / zl if zl > 0 else 0
    print(f'Saved {len(tdf)} LONG trades to {out_path}')
    print(f'N={len(tdf)}  PF={pf:.3f}  ZPF={zpf:.3f}  Net PnL={tdf["pnl"].sum():.2f}  Net ZPnL={tdf["zpnl"].sum():.2f}')
    print(f'Date range: {tdf["entry_dt"].min()} -> {tdf["entry_dt"].max()}')


if __name__ == '__main__':
    main()
