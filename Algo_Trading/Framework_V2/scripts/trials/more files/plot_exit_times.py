import pandas as pd, os, glob, sys, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
from ma_bounce import run_backtest, DATA_DIR

csv_files = sorted(glob.glob(os.path.join(DATA_DIR, '*_5min.csv')))
all_trades = []
for csv_path in csv_files:
    all_trades.extend(run_backtest(csv_path))

df = pd.DataFrame(all_trades)
df['exit_hhmm'] = df['exit_dt'].apply(lambda x: x.hour * 100 + x.minute)

print('Max exit time:', df['exit_hhmm'].max())
print('Post-1500 count:', (df['exit_hhmm'] >= 1500).sum())

# Fixed full NSE timeline 09:15 to 15:30 (5-min bars)
all_times = [h*100+m for h in range(9,16) for m in range(0,60,5) if h*100+m >= 915 and h*100+m <= 1530]
tgt_c = [((df['exit_hhmm']==t) & (df['outcome']=='W')).sum() for t in all_times]
sl_c  = [((df['exit_hhmm']==t) & (df['outcome']=='L')).sum() for t in all_times]
eod_c = [((df['exit_hhmm']==t) & df['outcome'].isin(['EOD+','EOD-'])).sum() for t in all_times]

xlabels = [f'{t//100:02d}:{t%100:02d}' for t in all_times]
x = range(len(all_times))

plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(16, 6))
ax.bar(x, tgt_c, color='#00ff88', label='TGT')
ax.bar(x, sl_c,  bottom=tgt_c, color='#ff4444', label='SL')
ax.bar(x, eod_c, bottom=[t+s for t,s in zip(tgt_c, sl_c)], color='#ff9900', label='EOD')
ax.set_xticks(list(x))
ax.set_xticklabels(xlabels, rotation=90, fontsize=8)
ax.set_title('Exit Time Distribution — 30 Stocks (Fixed: no post-15:00)', fontsize=14)
ax.set_xlabel('Exit Time')
ax.set_ylabel('Trade Count')
ax.legend()
plt.tight_layout()

out = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\reports\exit_time_dist_30stocks.png'
plt.savefig(out, dpi=150)
plt.close()
print(f'Saved: {out}')
