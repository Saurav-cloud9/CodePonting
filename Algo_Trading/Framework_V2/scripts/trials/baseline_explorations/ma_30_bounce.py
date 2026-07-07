import pandas as pd
import numpy as np
import os
import glob

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'

SL_MULT    = 2.5
TGT_MULT   = 4.5
MAX_TB_GAP = 3
EOD_HOUR   = 15


def run_backtest(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    for col in ['open', 'high', 'low', 'close', 'ma20', 'atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour

    opens  = df['open'].values
    highs  = df['high'].values
    lows   = df['low'].values
    closes = df['close'].values
    ma20s  = df['ma20'].values
    atrs   = df['atr14'].values
    hours  = df['hour'].values
    dates  = df['date'].values
    dts    = df['datetime'].values

    trades = []
    i = 0
    n = len(df)
    while i < n:
        if pd.isna(ma20s[i]) or pd.isna(atrs[i]):
            i += 1
            continue
        if lows[i] <= ma20s[i]:
            if hours[i] >= EOD_HOUR:
                i += 1
                continue
            touch_date = dates[i]
            atr = atrs[i]
            bounce_idx = -1
            for j in range(i, min(i + MAX_TB_GAP + 1, n)):
                if dates[j] != touch_date:
                    break
                if hours[j] >= EOD_HOUR:
                    break
                if closes[j] > ma20s[j]:
                    bounce_idx = j
                    break
            if bounce_idx < 0:
                i += 1
                continue
            entry_idx = bounce_idx + 1
            if entry_idx >= n:
                i += 1
                continue
            if dates[entry_idx] != touch_date:
                i += 1
                continue
            entry = opens[entry_idx]
            sl  = entry - SL_MULT  * atr
            tgt = entry + TGT_MULT * atr
            for k in range(entry_idx, n):
                if hours[k] >= EOD_HOUR or dates[k] != touch_date:
                    pnl = opens[k] - entry
                    outcome = 'EOD+' if pnl > 0 else 'EOD-'
                    break
                if highs[k] >= tgt:
                    pnl = tgt - entry
                    outcome = 'W'
                    break
                if lows[k] <= sl:
                    pnl = sl - entry
                    outcome = 'L'
                    break
            trades.append({'pnl': pnl, 'outcome': outcome, 'exit_dt': dts[k]})
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


csv_files = sorted(glob.glob(os.path.join(DATA_DIR, '*_5min.csv')))

all_trades = []
rows = []

for csv_path in csv_files:
    symbol = os.path.basename(csv_path).replace('_5min.csv', '')
    trades = run_backtest(csv_path)
    df_t = pd.DataFrame(trades)
    n = len(df_t)
    net = df_t['pnl'].sum()
    prof_wins = (df_t['pnl'] > 0).sum()
    pure_wins = (df_t['outcome'] == 'W').sum()
    prof_wr = prof_wins / n * 100 if n > 0 else 0
    pure_wr = pure_wins / n * 100 if n > 0 else 0
    avg_win = df_t[df_t['pnl'] > 0]['pnl'].mean() if prof_wins > 0 else 0
    avg_loss = abs(df_t[df_t['pnl'] < 0]['pnl'].mean()) if (df_t['pnl'] < 0).sum() > 0 else 0
    be_prof = avg_loss / (avg_win + avg_loss) * 100 if (avg_win + avg_loss) > 0 else 0
    gp = df_t[df_t['pnl'] > 0]['pnl'].sum()
    gl = abs(df_t[df_t['pnl'] < 0]['pnl'].sum())
    pf = gp / gl if gl > 0 else 999
    rows.append({'Symbol': symbol, 'N': n,
                 'Prof_WR%': round(prof_wr, 1), 'BE_prof%': round(be_prof, 1),
                 'Pure_WR%': round(pure_wr, 1),
                 'PF': round(pf, 3), 'Sharpe': sharpe(trades), 'Net': round(net, 2)})
    all_trades.extend(trades)

summary = pd.DataFrame(rows).sort_values('PF', ascending=False).reset_index(drop=True)
print(summary.to_string(index=False))

print()
all_df = pd.DataFrame(all_trades)
n_all = len(all_df)
prof_all = (all_df['pnl'] > 0).sum()
pure_all = (all_df['outcome'] == 'W').sum()
avg_win_all = all_df[all_df['pnl'] > 0]['pnl'].mean()
avg_loss_all = abs(all_df[all_df['pnl'] < 0]['pnl'].mean())
be_prof_all = avg_loss_all / (avg_win_all + avg_loss_all) * 100
be_pure = SL_MULT / (SL_MULT + TGT_MULT) * 100
gp_all = all_df[all_df['pnl'] > 0]['pnl'].sum()
gl_all = abs(all_df[all_df['pnl'] < 0]['pnl'].sum())
pf_all = gp_all / gl_all if gl_all > 0 else 999
print(f"TOTAL  N={n_all}  Prof_WR={prof_all/n_all*100:.1f}%  BE_prof={be_prof_all:.1f}%  Pure_WR={pure_all/n_all*100:.1f}%  BE_pure={be_pure:.1f}%  PF={pf_all:.3f}  Sharpe={sharpe(all_trades)}  Net={all_df['pnl'].sum():.2f}")

print()
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
