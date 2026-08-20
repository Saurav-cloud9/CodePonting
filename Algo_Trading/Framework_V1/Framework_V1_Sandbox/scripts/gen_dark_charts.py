"""gen_dark_charts.py
Regenerate dark-mode optuna PNGs with better readability.
Run: py -X utf8 scripts/gen_dark_charts.py
"""
import warnings, optuna
warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

DB  = Path(__file__).resolve().parents[1] / "outputs" / "optuna" / "optuna_study.db"
OUT = DB.parent

study = optuna.load_study(study_name="fv1_regime_optuna", storage=f"sqlite:///{DB}")
complete = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
trials   = np.array([t.number for t in complete])
values   = np.array([t.value  for t in complete])
print(f"Complete trials: {len(complete)}")

best_so_far = []
best = -999.0
for v in values:
    if v > best:
        best = v
    best_so_far.append(best)

# ── Colours ───────────────────────────────────────────────────────────────────
BG        = "#0d1117"
AX        = "#161b22"
GRID      = "#21262d"
GT_COL    = "#58a6ff"
BEST_LINE = "#3fb950"
DOT_POS   = "#3fb950"
DOT_NEG   = "#8b949e"
DOT_PEN   = "#f0883e"
DOT_ZERO  = "#484f58"

mask_zero = values <= -100
mask_pen  = (values > -100) & (values < -0.5)
mask_neg  = (values >= -0.5) & (values < 0)
mask_pos  = values >= 0


# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 -- Optimisation History (split: zoomed top + full-range bottom)
# ══════════════════════════════════════════════════════════════════════════════
fig, (ax_top, ax_bot) = plt.subplots(
    2, 1, figsize=(14, 8),
    gridspec_kw={"height_ratios": [3, 1], "hspace": 0.06},
    facecolor=BG,
)

for ax in (ax_top, ax_bot):
    ax.set_facecolor(AX)
    ax.grid(True, color=GRID, linewidth=0.6, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for sp in ax.spines.values():
        sp.set_edgecolor("#30363d")
    ax.tick_params(colors="#8b949e", labelsize=9)
    ax.xaxis.label.set_color("#8b949e")
    ax.yaxis.label.set_color("#8b949e")


def sc(ax, mask, color, alpha, size, label=None):
    ax.scatter(trials[mask], values[mask], c=color, alpha=alpha,
               s=size, linewidths=0, label=label, zorder=3)


# ── Top panel: -10 to +12 ────────────────────────────────────────────────────
sc(ax_top, mask_pos, DOT_POS, 0.75, 14, f"CAGR > 0%  ({mask_pos.sum():,})")
sc(ax_top, mask_neg, DOT_NEG, 0.45,  9, f"CAGR -0.5 to 0%  ({mask_neg.sum():,})")
sc(ax_top, mask_pen, DOT_PEN, 0.18,  6, f"Penalised (<27K trades)  ({mask_pen.sum():,})")

ax_top.plot(trials, best_so_far, color=BEST_LINE, lw=2.2, zorder=5,
            label=f"Best so far  (peak {values.max():.2f}%)")

ax_top.axhline(8.95, color=GT_COL,   lw=1.3, ls="--", alpha=0.85, zorder=4)
ax_top.axhline(6.70, color="#d29922", lw=1.1, ls=":",  alpha=0.85, zorder=4)
ax_top.axhline(0,    color="#30363d", lw=0.9, zorder=4)

ax_top.text(3060,  8.95, "GT  +8.95%",    color=GT_COL,   fontsize=8.5, va="center")
ax_top.text(3060,  6.70, "Target +6.70%", color="#d29922", fontsize=8.5, va="center")

n_clipped = int((values < -10).sum())
ax_top.text(0.01, 0.03, f"{n_clipped:,} trials clipped below −10%",
            transform=ax_top.transAxes, color="#8b949e", fontsize=8)

ax_top.set_ylim(-10, 13)
ax_top.set_xlim(-30, 3150)
ax_top.set_ylabel("CAGR  (%)", color="#c9d1d9", fontsize=10)
ax_top.tick_params(labelbottom=False)
ax_top.legend(loc="lower right", fontsize=8.5, facecolor="#21262d",
              edgecolor="#30363d", labelcolor="#c9d1d9", framealpha=0.92)
ax_top.set_title("FV1 Regime Optuna  --  Optimisation History",
                 color="#c9d1d9", fontsize=13, pad=12, fontweight="bold")

# ── Bottom panel: full range ──────────────────────────────────────────────────
sc(ax_bot, mask_pos,  DOT_POS,  0.85, 5)
sc(ax_bot, mask_neg,  DOT_NEG,  0.30, 4)
sc(ax_bot, mask_pen,  DOT_PEN,  0.15, 3)
sc(ax_bot, mask_zero, DOT_ZERO, 0.20, 3)
ax_bot.plot(trials, best_so_far, color=BEST_LINE, lw=1.4, zorder=5)

# shade the zoomed region
ax_bot.axhspan(-10, 13, alpha=0.07, color="#58a6ff", zorder=0)

ax_bot.set_ylim(-108, 12)
ax_bot.set_xlim(-30, 3150)
ax_bot.set_ylabel("Full range", color="#8b949e", fontsize=8)
ax_bot.set_xlabel("Trial", color="#8b949e", fontsize=10)

out1 = OUT / "optimization_history_darkview.png"
fig.savefig(str(out1), dpi=150, bbox_inches="tight", facecolor=BG)
plt.close("all")
print(f"Saved: {out1}")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 -- Feature Importance (custom horizontal bar, top-20 params)
# ══════════════════════════════════════════════════════════════════════════════
import optuna.visualization.matplotlib as vizm

vizm.plot_param_importances(study)
fig_raw = plt.gcf()
ax_raw  = fig_raw.axes[0]

# extract data from the auto-generated axes
labels = [t.get_text() for t in ax_raw.get_yticklabels()]
bars   = ax_raw.patches
bar_widths = [b.get_width() for b in bars]
plt.close("all")

# keep top 20
pairs = sorted(zip(bar_widths, labels), reverse=True)[:20]
widths, lbs = zip(*pairs)
widths = np.array(widths)
lbs    = list(lbs)

# colour by category
def cat_colour(name):
    n = name.lower()
    if n.startswith("thresh"): return "#d29922"
    if n.startswith("gate"):   return "#bc8cff"
    if n.startswith("use"):    return "#4fc3f7"
    if n.startswith("dir"):    return "#f0883e"
    return "#8b949e"

colours = [cat_colour(l) for l in lbs]

fig, ax = plt.subplots(figsize=(10, 8), facecolor=BG)
ax.set_facecolor(AX)
ax.grid(True, axis="x", color=GRID, linewidth=0.6, zorder=0)
for sp in ax.spines.values():
    sp.set_edgecolor("#30363d")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

y_pos = np.arange(len(lbs))
bars  = ax.barh(y_pos, widths[::-1], color=colours[::-1],
                edgecolor="#0d1117", linewidth=0.4, zorder=3, height=0.65)

ax.set_yticks(y_pos)
ax.set_yticklabels(lbs[::-1], fontsize=9, color="#c9d1d9")
ax.tick_params(colors="#8b949e", labelsize=9)
ax.xaxis.label.set_color("#8b949e")
ax.set_xlabel("Importance (FANOVA)", color="#8b949e", fontsize=10)
ax.set_title("FV1 Regime Optuna  --  Parameter Importances  (top 20)",
             color="#c9d1d9", fontsize=13, pad=12, fontweight="bold")

# value labels on bars
for bar, w in zip(bars, widths[::-1]):
    ax.text(w + 0.002, bar.get_y() + bar.get_height() / 2,
            f"{w:.3f}", va="center", fontsize=7.5, color="#8b949e")

# legend for colours
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor="#4fc3f7", label="use_* (ON/OFF)"),
    Patch(facecolor="#f0883e", label="dir_*  (direction)"),
    Patch(facecolor="#d29922", label="thresh_* (threshold)"),
    Patch(facecolor="#bc8cff", label="gate_logic"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=8.5,
          facecolor="#21262d", edgecolor="#30363d",
          labelcolor="#c9d1d9", framealpha=0.92)

plt.tight_layout()
out2 = OUT / "feature_importance_darkview.png"
fig.savefig(str(out2), dpi=150, bbox_inches="tight", facecolor=BG)
plt.close("all")
print(f"Saved: {out2}")

print("Done.")
