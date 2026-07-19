import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os

plt.style.use('dark_background')

SL_VALS  = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
TGT_VALS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]

# ZPF grid — rows = SL, cols = TGT (from 6BCE sweep, DS3 30 stocks 2015-2025)
zpf = np.array([
    [0.675, 0.715, 0.739, 0.753, 0.764, 0.772, 0.777, 0.780, 0.782],
    [0.714, 0.754, 0.778, 0.794, 0.807, 0.814, 0.818, 0.820, 0.822],
    [0.734, 0.774, 0.797, 0.812, 0.825, 0.832, 0.834, 0.836, 0.839],
    [0.748, 0.788, 0.811, 0.826, 0.838, 0.845, 0.848, 0.850, 0.851],
    [0.756, 0.797, 0.822, 0.837, 0.850, 0.855, 0.859, 0.861, 0.863],
    [0.763, 0.804, 0.829, 0.845, 0.857, 0.862, 0.866, 0.869, 0.870],
    [0.768, 0.810, 0.835, 0.851, 0.864, 0.869, 0.873, 0.876, 0.878],
    [0.771, 0.813, 0.838, 0.854, 0.866, 0.872, 0.876, 0.880, 0.881],
    [0.775, 0.818, 0.841, 0.857, 0.871, 0.876, 0.880, 0.883, 0.884],
    [0.777, 0.820, 0.845, 0.861, 0.874, 0.881, 0.884, 0.887, 0.888],
])

fig, ax = plt.subplots(figsize=(13, 7))

# Sequential color: low SL = muted cyan, high SL = bright yellow (plasma ramp)
colors = cm.plasma(np.linspace(0.15, 0.92, len(SL_VALS)))

for idx, sl in enumerate(SL_VALS):
    lw   = 1.5 if idx < len(SL_VALS) - 1 else 2.5  # thicker line for best SL
    alpha = 0.55 + 0.045 * idx                       # higher SL = more opaque
    ax.plot(TGT_VALS, zpf[idx], color=colors[idx],
            linewidth=lw, alpha=alpha, marker='o', markersize=4,
            label=f'SL={sl}')

# Viability threshold
ax.axhline(1.0, color='#ff4444', linewidth=1.5, linestyle='--', alpha=0.85, label='ZPF = 1.0 (target)')

# Best combo marker: SL=6.0 / TGT=6.0 → last row, last col
best_tgt = TGT_VALS[-1]
best_zpf = zpf[-1, -1]
ax.scatter(best_tgt, best_zpf, color='#ff6b35', s=140, zorder=5, marker='*')
ax.annotate(f'Best: SL=6.0 / TGT=6.0\nZPF={best_zpf:.3f}',
            xy=(best_tgt, best_zpf),
            xytext=(best_tgt - 1.6, best_zpf + 0.025),
            color='#ff6b35', fontsize=9,
            arrowprops=dict(arrowstyle='->', color='#ff6b35', lw=1.2))

# Axes
ax.set_xlim(1.8, 6.4)
ax.set_ylim(0.64, 1.04)
ax.set_xticks(TGT_VALS)
ax.set_xticklabels([str(t) for t in TGT_VALS], fontsize=10)
ax.set_xlabel('TGT Multiplier (× ATR14)', fontsize=12, labelpad=8)
ax.set_ylabel('ZPF  (Zerodha Profit Factor)', fontsize=12, labelpad=8)
ax.set_title('6BCE SHORT — ZPF vs TGT by SL  |  30 stocks · DS3 2015–2025',
             fontsize=13, pad=14)

# Grid
ax.grid(True, linestyle='--', alpha=0.2, linewidth=0.7)

# Legend — SL lines + threshold
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, fontsize=8.5, loc='lower right',
          framealpha=0.25, ncol=2, title='SL multiplier', title_fontsize=8.5)

# Gap annotation
gap = 1.0 - best_zpf
ax.annotate('', xy=(6.3, 1.0), xytext=(6.3, best_zpf),
            arrowprops=dict(arrowstyle='<->', color='#aaaaaa', lw=1.0))
ax.text(6.32, (1.0 + best_zpf) / 2, f'gap\n{gap:.3f}',
        color='#aaaaaa', fontsize=8, va='center')

plt.tight_layout()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chart_zpf_lines_6bce.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f'Saved: {out}')
