import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np
import glob, os
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm

plt.style.use('dark_background')

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3'
EOD_HOUR = 15
WINDOW   = 6
YEARS    = list(range(2015, 2026))

SL_VALS  = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
TGT_VALS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]


def zerodha_charge(entry, exit_px):
    brok  = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt   = entry  * 0.00025
    txn   = (entry + exit_px) * 0.0000307
    sebi  = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst   = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def load_stocks():
    stocks = []
    for f in sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet'))):
        import pandas as pd
        df = pd.read_parquet(f)
        df['datetime'] = pd.to_datetime(df['datetime'])
        if df['datetime'].dt.tz is not None:
            df['datetime'] = df['datetime'].dt.tz_localize(None)
        for col in ['open', 'high', 'low', 'close', 'atr14']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['date'] = df['datetime'].dt.date
        df['hour'] = df['datetime'].dt.hour
        stocks.append({
            'open':  df['open'].values,
            'high':  df['high'].values,
            'low':   df['low'].values,
            'close': df['close'].values,
            'atr14': df['atr14'].values,
            'hour':  df['hour'].values,
            'date':  df['date'].values,
            'year':  df['datetime'].dt.year.values,
            'n':     len(df),
        })
    return stocks


def run_combo(stocks, sl_m, tgt_m):
    """Single-pass sweep collecting overall + year-wise zpnl buckets + daily zpnl for ZSh(D)."""
    overall_gp = 0.0;  overall_gl = 0.0
    yr_gp = {yr: 0.0 for yr in YEARS}
    yr_gl = {yr: 0.0 for yr in YEARS}
    daily = defaultdict(lambda: defaultdict(float))  # {year: {date: daily_zpnl}}

    for s in stocks:
        close = s['close']; high = s['high']; low  = s['low']
        open_ = s['open'];  atr  = s['atr14']
        hour  = s['hour'];  date = s['date']
        year  = s['year'];  n    = s['n']

        i = WINDOW - 1
        while i < n:
            if np.isnan(atr[i]) or hour[i] >= EOD_HOUR:
                i += 1; continue
            window = close[i - WINDOW + 1: i + 1]
            if np.any(np.isnan(window)) or close[i] < np.max(window):
                i += 1; continue
            ei = i + 1
            if ei >= n or date[ei] != date[i] or hour[ei] >= EOD_HOUR:
                i += 1; continue

            entry_px   = open_[ei]
            sl         = entry_px + sl_m * atr[i]
            tgt        = entry_px - tgt_m * atr[i]
            trade_date = date[i]
            exit_year  = year[i]
            exit_dt    = date[i]

            k = ei
            exit_px = entry_px
            while k < n:
                if date[k] != trade_date:
                    exit_px = close[k - 1]; exit_year = year[k - 1]; exit_dt = date[k - 1]; break
                if hour[k] >= EOD_HOUR:
                    exit_px = open_[k]; exit_year = year[k]; exit_dt = date[k]; break
                if high[k] >= sl:
                    exit_px = sl; exit_year = year[k]; exit_dt = date[k]; break
                if low[k] <= tgt:
                    exit_px = tgt; exit_year = year[k]; exit_dt = date[k]; break
                k += 1
            else:
                exit_px = close[k - 1]; exit_year = year[k - 1]; exit_dt = date[k - 1]

            zpnl = (entry_px - exit_px) - zerodha_charge(entry_px, exit_px)
            daily[exit_year][exit_dt] += zpnl
            if zpnl > 0:
                overall_gp += zpnl
                if exit_year in yr_gp: yr_gp[exit_year] += zpnl
            else:
                overall_gl += abs(zpnl)
                if exit_year in yr_gl: yr_gl[exit_year] += abs(zpnl)
            i = k + 1

    overall_zpf = round(overall_gp / overall_gl, 4) if overall_gl > 0 else 0.0
    yr_zpf = {}
    for yr in YEARS:
        gp = yr_gp[yr]; gl = yr_gl[yr]
        yr_zpf[yr] = round(gp / gl, 4) if gl > 0 else 0.0

    yr_zshd = {}
    for yr in YEARS:
        vals = list(daily[yr].values())
        if len(vals) >= 2:
            arr = np.array(vals)
            s = arr.std()
            yr_zshd[yr] = round((arr.mean() / s) * np.sqrt(252), 4) if s > 0 else 0.0
        else:
            yr_zshd[yr] = 0.0

    return overall_zpf, yr_zpf, yr_zshd


# ── RUN ───────────────────────────────────────────────────────────────────────
print('Loading stocks...')
stocks = load_stocks()
print(f'{len(stocks)} stocks. Running 90 combos with year-wise tracking...\n')

overall_grid    = np.zeros((len(SL_VALS), len(TGT_VALS)))
yearly_grid     = np.zeros((len(SL_VALS), len(TGT_VALS), len(YEARS)))
yearly_zshd_grid = np.zeros((len(SL_VALS), len(TGT_VALS), len(YEARS)))

for si, sl in enumerate(SL_VALS):
    for ti, tgt in enumerate(TGT_VALS):
        ozpf, yr_zpf, yr_zshd = run_combo(stocks, sl, tgt)
        overall_grid[si, ti] = ozpf
        for yi, yr in enumerate(YEARS):
            yearly_grid[si, ti, yi]      = yr_zpf[yr]
            yearly_zshd_grid[si, ti, yi] = yr_zshd[yr]
    print(f'  SL={sl} done')

# Consistency score = mean(yearly ZPF) - std(yearly ZPF)  [higher = more stable]
consistency = yearly_grid.mean(axis=2) - yearly_grid.std(axis=2)

# Best combos
best_cs_idx  = np.unravel_index(np.argmax(consistency),   consistency.shape)
best_zpf_idx = np.unravel_index(np.argmax(overall_grid),  overall_grid.shape)

print(f'\nBest by consistency : SL={SL_VALS[best_cs_idx[0]]} / TGT={TGT_VALS[best_cs_idx[1]]}  '
      f'cs={consistency[best_cs_idx]:.4f}  ZPF={overall_grid[best_cs_idx]:.4f}')
print(f'Best by overall ZPF : SL={SL_VALS[best_zpf_idx[0]]} / TGT={TGT_VALS[best_zpf_idx[1]]}  '
      f'cs={consistency[best_zpf_idx]:.4f}  ZPF={overall_grid[best_zpf_idx]:.4f}')

# Save cache for downstream chart scripts
cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sweep_cache_6bce.npz')
np.savez(cache_path, overall_grid=overall_grid, yearly_grid=yearly_grid,
         yearly_zshd_grid=yearly_zshd_grid)
print(f'Cache saved: {cache_path}')

# ── CHART ─────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
fig.suptitle('6BCE SHORT — Consistency Analysis  |  30 stocks · DS3 2015–2025',
             fontsize=13, color='white', y=1.01)

sl_colors = cm.plasma(np.linspace(0.15, 0.92, len(SL_VALS)))

# ── LEFT: Scatter — overall ZPF vs consistency score ─────────────────────────
for si, sl in enumerate(SL_VALS):
    ax1.scatter(overall_grid[si, :], consistency[si, :],
                color=sl_colors[si], s=55, alpha=0.85, zorder=3, label=f'SL={sl}')

ax1.scatter(overall_grid[best_cs_idx],  consistency[best_cs_idx],
            color='#00ffcc', s=180, zorder=6, marker='*',
            label=f'★ Best consistency  SL={SL_VALS[best_cs_idx[0]]}/TGT={TGT_VALS[best_cs_idx[1]]}')
ax1.scatter(overall_grid[best_zpf_idx], consistency[best_zpf_idx],
            color='#ff6b35', s=150, zorder=6, marker='D',
            label=f'◆ Best overall ZPF  SL={SL_VALS[best_zpf_idx[0]]}/TGT={TGT_VALS[best_zpf_idx[1]]}')

ax1.axvline(1.0, color='#ff4444', linewidth=1.2, linestyle='--', alpha=0.7, label='ZPF = 1.0 target')
ax1.set_xlabel('Overall ZPF', fontsize=11, labelpad=8)
ax1.set_ylabel('Consistency Score\n(mean yearly ZPF − std yearly ZPF)', fontsize=10, labelpad=8)
ax1.set_title('ZPF vs Consistency — all 90 combos', fontsize=11, pad=10)
ax1.grid(True, linestyle='--', alpha=0.18, linewidth=0.7)
ax1.legend(fontsize=7.5, loc='lower right', framealpha=0.2, ncol=2)

# ── RIGHT: Year-wise ZPF — top 3 by consistency + best by ZPF ────────────────
top3_cs = [np.unravel_index(i, consistency.shape)
           for i in np.argsort(consistency.ravel())[::-1][:3]]

plot_combos = list(top3_cs)
if best_zpf_idx not in plot_combos:
    plot_combos.append(best_zpf_idx)

line_colors = ['#00ffcc', '#44ddaa', '#88bb77', '#ff6b35']
line_styles = ['-', '-', '-', '--']
for ci, idx in enumerate(plot_combos):
    sl_v  = SL_VALS[idx[0]]; tgt_v = TGT_VALS[idx[1]]
    yr_vals = yearly_grid[idx[0], idx[1], :]
    cs_val  = consistency[idx[0], idx[1]]
    tag = '★ ' if ci < 3 else '◆ '
    kind = 'cons' if ci < 3 else 'ZPF'
    lbl = f'{tag}SL={sl_v}/TGT={tgt_v}  [{kind}={cs_val:.3f}]'
    ax2.plot(YEARS, yr_vals, color=line_colors[ci], linewidth=2.0 if ci == 0 else 1.5,
             linestyle=line_styles[ci], marker='o', markersize=4.5, label=lbl)

ax2.axhline(1.0, color='#ff4444', linewidth=1.5, linestyle='--', alpha=0.85, label='ZPF = 1.0 target')
ax2.axhline(0.9, color='#ff8888', linewidth=0.8, linestyle=':',  alpha=0.5,  label='ZPF = 0.9')
ax2.set_xticks(YEARS)
ax2.set_xticklabels([str(y) for y in YEARS], rotation=35, fontsize=9)
ax2.set_xlabel('Year', fontsize=11, labelpad=8)
ax2.set_ylabel('ZPF (per year)', fontsize=11, labelpad=8)
ax2.set_title('Year-wise ZPF — most consistent combos vs best overall', fontsize=11, pad=10)
ax2.grid(True, linestyle='--', alpha=0.18, linewidth=0.7)
ax2.legend(fontsize=8.5, loc='lower left', framealpha=0.25)

plt.tight_layout()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chart_consistency_6bce.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f'\nSaved: {out}')
