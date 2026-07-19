import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

plt.style.use('dark_background')

YEARS    = list(range(2015, 2026))
SL_VALS  = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
TGT_VALS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]

# Load cached sweep results
cache = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sweep_cache_6bce.npz'))
yearly_grid  = cache['yearly_grid']   # shape: (10, 9, 11)
overall_grid = cache['overall_grid']  # shape: (10, 9)

# Smoothness = lowest std(yearly ZPF) across 11 years
std_grid = yearly_grid.std(axis=2)    # shape: (10, 9)

# Top 3 smoothest and bottom 3 most volatile
flat_std   = std_grid.ravel()
smooth_idx = [np.unravel_index(i, std_grid.shape) for i in np.argsort(flat_std)[:3]]
rough_idx  = [np.unravel_index(i, std_grid.shape) for i in np.argsort(flat_std)[-3:]]

fig, ax = plt.subplots(figsize=(14, 7))

# Gray spaghetti — all 90 combos
for si in range(len(SL_VALS)):
    for ti in range(len(TGT_VALS)):
        ax.plot(YEARS, yearly_grid[si, ti], color='#555555',
                linewidth=0.6, alpha=0.35, zorder=1)

# Top 3 smoothest — highlighted in color
smooth_colors = ['#00ffcc', '#33ddff', '#88bbff']
for ci, idx in enumerate(smooth_idx):
    sl_v  = SL_VALS[idx[0]]; tgt_v = TGT_VALS[idx[1]]
    std_v = std_grid[idx];   zpf_v = overall_grid[idx]
    ax.plot(YEARS, yearly_grid[idx[0], idx[1]],
            color=smooth_colors[ci], linewidth=2.2, marker='o', markersize=4.5,
            zorder=4, label=f'#{ci+1} smoothest  SL={sl_v}/TGT={tgt_v}  std={std_v:.4f}  ZPF={zpf_v:.3f}')

# Bottom 3 most volatile — shown in muted red for contrast
for ci, idx in enumerate(rough_idx):
    sl_v  = SL_VALS[idx[0]]; tgt_v = TGT_VALS[idx[1]]
    std_v = std_grid[idx];   zpf_v = overall_grid[idx]
    ax.plot(YEARS, yearly_grid[idx[0], idx[1]],
            color='#cc3333', linewidth=1.2, linestyle='--', alpha=0.55,
            zorder=3, label=f'Volatile #{ci+1}  SL={sl_v}/TGT={tgt_v}  std={std_v:.4f}  ZPF={zpf_v:.3f}')

# Reference lines
ax.axhline(1.0, color='#ff4444', linewidth=1.5, linestyle='--', alpha=0.85, label='ZPF = 1.0 target')
ax.axhline(0.9, color='#ff8888', linewidth=0.8, linestyle=':',  alpha=0.45, label='ZPF = 0.9')

ax.set_xticks(YEARS)
ax.set_xticklabels([str(y) for y in YEARS], fontsize=10)
ax.set_xlabel('Year', fontsize=12, labelpad=8)
ax.set_ylabel('ZPF (per year)', fontsize=12, labelpad=8)
ax.set_title('6BCE SHORT — Year-wise ZPF: all 90 combos\n'
             'Cyan = smoothest 11-yr run  |  Red dashed = most volatile  |  Gray = remaining 84',
             fontsize=12, pad=12)
ax.grid(True, linestyle='--', alpha=0.18, linewidth=0.7)
ax.legend(fontsize=8.5, loc='lower left', framealpha=0.25)

plt.tight_layout()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chart_spaghetti_6bce.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f'Saved: {out}')
