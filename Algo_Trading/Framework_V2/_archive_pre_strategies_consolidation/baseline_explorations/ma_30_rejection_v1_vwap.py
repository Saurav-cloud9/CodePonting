import pandas as pd
import numpy as np
import os
import glob

# v1 + VWAP filter: wick-only touch from below MA20, split by VWAP context
# Run A: touch bar close < vwap  (below VWAP — bearish context)
# Run B: touch bar close >= vwap (above VWAP — bullish context, still rejected)
# SL/TP locked: SL=2.5x · TP=4.0x
DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3'

SL_MULT   = 2.5
TP_MULT  = 4.0
EOD_HOUR  = 15


def prepare(df):
    df['tp']      = (df['high'] + df['low'] + df['close']) / 3
    df['cum_tpv'] = df.groupby('date').apply(
        lambda g: (g['tp'] * g['volume']).cumsum(), include_groups=False
    ).reset_index(level=0, drop=True)
    df['cum_vol'] = df.groupby('date')['volume'].cumsum()
    df['vwap']    = df['cum_tpv'] / df['cum_vol']
    return df


def run_backtest(csv_path, below_vwap):
    df = pd.read_parquet(csv_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].apply(lambda x: x.replace(tzinfo=None))
    for col in ['open', 'high', 'low', 'close', 'ma20', 'atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df = prepare(df)

    trades = []
    i = 0
    while i < len(df):
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']):
            i += 1
            continue
        vwap_cond = (row['close'] < row['vwap']) if below_vwap else (row['close'] >= row['vwap'])
        if (row['high'] >= row['ma20'] and row['open'] < row['ma20'] and row['close'] < row['ma20']
                and vwap_cond):
            if row['hour'] >= EOD_HOUR:
                i += 1
                continue
            touch_date = row['date']
            atr = row['atr14']
            entry_idx = i + 1
            if entry_idx >= len(df):
                i += 1
                continue
            entry_bar = df.iloc[entry_idx]
            if entry_bar['date'] != touch_date:
                i += 1
                continue
            entry = entry_bar['open']
            sl  = entry + SL_MULT  * atr
            tp = entry - TP_MULT * atr
            for k in range(entry_idx, len(df)):
                k_bar = df.iloc[k]
                if k_bar['date'] != touch_date:
                    prev = df.iloc[k - 1]
                    pnl = entry - prev['close']
                    outcome = 'EOD+' if pnl > 0 else 'EOD-'
                    exit_dt = prev['datetime']
                    break
                if k_bar['hour'] >= EOD_HOUR:
                    pnl = entry - k_bar['open']
                    outcome = 'EOD+' if pnl > 0 else 'EOD-'
                    exit_dt = k_bar['datetime']
                    break
                if k_bar['high'] >= sl:
                    pnl = entry - sl
                    outcome = 'L'
                    exit_dt = k_bar['datetime']
                    break
                if k_bar['low'] <= tp:
                    pnl = entry - tp
                    outcome = 'W'
                    exit_dt = k_bar['datetime']
                    break
            trades.append({'pnl': pnl, 'outcome': outcome, 'exit_dt': exit_dt})
            i = k + 1
        else:
            i += 1
    return trades


def sharpe(trades):
    if len(trades) < 2: return 0
    tdf = pd.DataFrame(trades)
    tdf['exit_dt'] = pd.to_datetime(tdf['exit_dt'], utc=True).dt.tz_localize(None)
    m = tdf.resample('ME', on='exit_dt')['pnl'].sum()
    return round((m.mean() / m.std()) * np.sqrt(12), 3) if m.std() > 0 else 0


def run_all(below_vwap, label):
    csv_files = sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet')))
    all_trades = []
    for csv_path in csv_files:
        trades = run_backtest(csv_path, below_vwap)
        all_trades.extend(trades)

    all_df = pd.DataFrame(all_trades)
    n_all     = len(all_df)
    prof_all  = (all_df['pnl'] > 0).sum()
    pure_all  = (all_df['outcome'] == 'W').sum()
    avg_win   = all_df[all_df['pnl'] > 0]['pnl'].mean()
    avg_loss  = abs(all_df[all_df['pnl'] < 0]['pnl'].mean())
    be_prof   = avg_loss / (avg_win + avg_loss) * 100
    be_pure   = SL_MULT / (SL_MULT + TP_MULT) * 100
    gp = all_df[all_df['pnl'] > 0]['pnl'].sum()
    gl = abs(all_df[all_df['pnl'] < 0]['pnl'].sum())
    pf = gp / gl if gl > 0 else 999

    print(f"\n=== {label} ===")
    print(f"N={n_all}  Prof_WR={prof_all/n_all*100:.1f}%  BE_prof={be_prof:.1f}%  Pure_WR={pure_all/n_all*100:.1f}%  BE_pure={be_pure:.1f}%  PF={pf:.3f}  Sharpe={sharpe(all_trades)}  Net={all_df['pnl'].sum():.2f}")

    all_df['exit_dt'] = pd.to_datetime(all_df['exit_dt'], utc=True).dt.tz_localize(None)
    all_df['year'] = all_df['exit_dt'].dt.year
    yr_rows = []
    for yr, g in all_df.groupby('year'):
        gp_y = g[g['pnl'] > 0]['pnl'].sum()
        gl_y = abs(g[g['pnl'] < 0]['pnl'].sum())
        pf_y = gp_y / gl_y if gl_y > 0 else 999
        m_y  = g.resample('ME', on='exit_dt')['pnl'].sum()
        sh_y = round((m_y.mean() / m_y.std()) * np.sqrt(12), 3) if m_y.std() > 0 else 0
        yr_rows.append({'Year': yr, 'N': len(g), 'PF': round(pf_y, 3), 'Sharpe': sh_y, 'Net': round(g['pnl'].sum(), 2)})
    print(pd.DataFrame(yr_rows).to_string(index=False))


run_all(below_vwap=True,  label='Run A — Below VWAP (close < vwap)')
run_all(below_vwap=False, label='Run B — Above VWAP (close >= vwap)')
