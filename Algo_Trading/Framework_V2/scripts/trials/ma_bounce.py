import pandas as pd
import os
import glob

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'

MA_COL = 'ma20'
SL_MULT = 2.5
TGT_MULT = 4.5
MAX_TB_GAP = 3
EOD_HOUR = 15


def run_backtest(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    for col in ['open', 'high', 'low', 'close', 'ma20', 'atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour

    trades = []
    i = 0
    while i < len(df):
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']):
            i += 1; continue
        if row['low'] <= row['ma20']:
            if row['hour'] >= EOD_HOUR:
                i += 1
                continue
            touch_date = row['date']
            atr = row['atr14']
            bounce_bar = None
            for j in range(i, i + MAX_TB_GAP + 1):
                b = df.iloc[j]
                if b['date'] != touch_date:
                    break
                if b['hour'] >= EOD_HOUR:
                    break
                if b['close'] > b['ma20']:
                    bounce_bar = b
                    break
            if bounce_bar is None:
                i += 1
                continue
            entry_idx = j + 1
            if entry_idx >= len(df): i += 1; continue
            entry_bar = df.iloc[entry_idx]
            if entry_bar['date'] != touch_date:
                i += 1
                continue
            entry = entry_bar['open']
            sl = entry - SL_MULT * atr
            tgt = entry + TGT_MULT * atr
            for k in range(entry_idx, len(df)):
                k_bar = df.iloc[k]
                if k_bar['hour'] >= EOD_HOUR:
                    pnl = k_bar['open'] - entry
                    outcome = 'EOD+' if pnl > 0 else 'EOD-'
                    break
                if k_bar['high'] >= tgt:
                    pnl = tgt - entry
                    outcome = 'W'
                    break
                if k_bar['low'] <= sl:
                    pnl = sl - entry
                    outcome = 'L'
                    break
            trades.append({'pnl': pnl, 'outcome': outcome, 'exit_dt': k_bar['datetime']})
            i = k + 1
        else:
            i += 1
    return trades


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
                 'PF': round(pf, 3), 'Net': round(net, 2)})
    all_trades.extend(trades)

summary = pd.DataFrame(rows)
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
print(f"TOTAL  N={n_all}  Prof_WR={prof_all/n_all*100:.1f}%  BE_prof={be_prof_all:.1f}%  Pure_WR={pure_all/n_all*100:.1f}%  BE_pure={be_pure:.1f}%  PF={pf_all:.3f}  Net={all_df['pnl'].sum():.2f}")
