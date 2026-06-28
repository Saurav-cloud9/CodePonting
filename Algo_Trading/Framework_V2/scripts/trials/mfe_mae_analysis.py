import pandas as pd, numpy as np, os, glob, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
BASE_SL=2.5; BASE_TGT=4.5; MAX_TB_GAP=3; EOD_HOUR=15

def run_backtest_mfe_mae(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    for col in ['open','high','low','close','ma20','atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour

    trades = []; i = 0
    while i < len(df):
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']): i += 1; continue
        if row['low'] <= row['ma20']:
            if row['hour'] >= EOD_HOUR: i += 1; continue
            touch_date = row['date']; atr = row['atr14']; bounce_bar = None
            for j in range(i, i + MAX_TB_GAP + 1):
                b = df.iloc[j]
                if b['date'] != touch_date: break
                if b['hour'] >= EOD_HOUR: break
                if b['close'] > b['ma20']: bounce_bar = b; break
            if bounce_bar is None: i += 1; continue
            entry_idx = j + 1
            if entry_idx >= len(df): i += 1; continue
            entry_bar = df.iloc[entry_idx]
            if entry_bar['date'] != touch_date: i += 1; continue
            entry = entry_bar['open']

            mfe = 0.0   # max favourable excursion (ATR units, positive)
            mae = 0.0   # max adverse excursion (ATR units, positive = magnitude)
            outcome = None; k = entry_idx

            while k < len(df):
                kb = df.iloc[k]
                bar_high = (kb['high'] - entry) / atr
                bar_low  = (kb['low']  - entry) / atr
                mfe = max(mfe, bar_high)
                mae = max(mae, -bar_low)   # mae stored as positive magnitude

                if kb['hour'] >= EOD_HOUR:
                    pnl = (kb['open'] - entry) / atr
                    outcome = 'EOD+' if pnl > 0 else 'EOD-'; k += 1; break
                if kb['high'] >= entry + BASE_TGT * atr:
                    outcome = 'W'; k += 1; break
                if kb['low'] <= entry - BASE_SL * atr:
                    outcome = 'L'; k += 1; break
                k += 1

            trades.append({'mfe': mfe, 'mae': mae, 'outcome': outcome})
            i = k
        else:
            i += 1
    return trades

print('Running backtest...')
csv_files = sorted(glob.glob(os.path.join(DATA_DIR, '*_5min.csv')))
all_trades = []
for csv_path in csv_files:
    all_trades.extend(run_backtest_mfe_mae(csv_path))
print(f'Trades: {len(all_trades)}')

df = pd.DataFrame(all_trades)

winners = df[df['outcome'] == 'W']
losers  = df[df['outcome'] == 'L']
eod_pos = df[df['outcome'] == 'EOD+']
eod_neg = df[df['outcome'] == 'EOD-']

from scipy.stats import gaussian_kde

groups = [
    (winners,  '#00e676', 'Target Hit — Winner',   len(winners)),
    (eod_pos,  '#ffe600', 'EOD Exit — Profit',     len(eod_pos)),
    (eod_neg,  '#ff7c00', 'EOD Exit — Loss',       len(eod_neg)),
    (losers,   '#ff1744', 'Stop Loss Hit — Loser', len(losers)),
]

def kde_curve(data, x_range, bw=0.15):
    kde = gaussian_kde(data, bw_method=bw)
    return kde(x_range) * len(data)   # scale to trade count

x_mfe = np.linspace(0, 8, 500)
x_mae = np.linspace(0, 6, 500)

plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
fig.suptitle('Max Favourable Excursion (MFE)  vs  Max Adverse Excursion (MAE)\n'
             'Smooth density curves — all exit types overlaid for comparison   |   Baseline: SL=2.5x ATR,  TGT=4.5x ATR',
             fontsize=13, y=1.01)

for grp, color, label, n in groups:
    # MFE
    y_mfe = kde_curve(grp['mfe'].clip(0.01, 7.99), x_mfe)
    ax1.plot(x_mfe, y_mfe, color=color, linewidth=2.5, label=f'{label}  (n={n:,}  |  median={grp["mfe"].median():.1f}x ATR)')
    ax1.fill_between(x_mfe, y_mfe, alpha=0.12, color=color)

    # MAE
    y_mae = kde_curve(grp['mae'].clip(0.01, 5.99), x_mae)
    ax2.plot(x_mae, y_mae, color=color, linewidth=2.5, label=f'{label}  (n={n:,}  |  median={grp["mae"].median():.1f}x ATR)')
    ax2.fill_between(x_mae, y_mae, alpha=0.12, color=color)

# reference lines
ax1.axvline(BASE_TGT, color='white', linewidth=2, linestyle='--', label=f'Target = {BASE_TGT}x ATR')
ax2.axvline(BASE_SL,  color='white', linewidth=2, linestyle='--', label=f'Stop Loss = {BASE_SL}x ATR')

ax1.set_title('MFE — Best point each trade reached before exit', fontsize=12, pad=10)
ax1.set_xlabel('Best point reached in your favour (ATR multiples)\ne.g. 2.0 = price moved 2× ATR above your entry before reversing', fontsize=10)
ax1.set_ylabel('Trade Count (density scaled)', fontsize=10)
ax1.set_xlim(0, 8); ax1.legend(fontsize=9, loc='upper right')
ax1.tick_params(labelsize=10)

ax2.set_title('MAE — Worst point each trade reached before exit', fontsize=12, pad=10)
ax2.set_xlabel('Worst point reached against you (ATR multiples)\ne.g. 2.0 = price moved 2× ATR below your entry before recovering', fontsize=10)
ax2.set_ylabel('Trade Count (density scaled)', fontsize=10)
ax2.set_xlim(0, 6); ax2.legend(fontsize=9, loc='upper right')
ax2.tick_params(labelsize=10)

plt.tight_layout()
out = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\reports\mfe_mae_analysis.png'
plt.savefig(out, dpi=180, bbox_inches='tight'); plt.close()
print(f'Saved: {out}')

# summary stats
print(f'\nMFE medians — W:{winners["mfe"].median():.2f}  EOD+:{eod_pos["mfe"].median():.2f}  EOD-:{eod_neg["mfe"].median():.2f}  L:{losers["mfe"].median():.2f}')
print(f'MAE medians — W:{winners["mae"].median():.2f}  EOD+:{eod_pos["mae"].median():.2f}  EOD-:{eod_neg["mae"].median():.2f}  L:{losers["mae"].median():.2f}')
print(f'\nMFE % reaching >3x TGT: W={( winners["mfe"]>=3).mean()*100:.1f}%  L={( losers["mfe"]>=3).mean()*100:.1f}%  EOD-={(eod_neg["mfe"]>=3).mean()*100:.1f}%')
print(f'MAE % staying <1x SL:  W={(winners["mae"]<1).mean()*100:.1f}%  EOD+={(eod_pos["mae"]<1).mean()*100:.1f}%')
