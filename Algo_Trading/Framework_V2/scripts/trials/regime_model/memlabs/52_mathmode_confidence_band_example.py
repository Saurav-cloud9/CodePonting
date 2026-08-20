"""
[MATH-MODE] Confidence band around a fitted line — dummy example, no trading data.

Purpose: explain WHY the shaded band in Steps 5-6 of
52_alpha_beta_concept_and_powergrid.ipynb is narrow near the middle of the
data and wide at the edges. Standalone teaching aid — 5 tiny hand-picked
(x, y) points, integers, no market_return/strategy_return anywhere.
See write-up: 52_mathmode_confidence_band_explained.md
"""
import matplotlib.pyplot as plt
import numpy as np

plt.style.use('dark_background')

# --- tiny dummy dataset (5 points, clean numbers) ---
x = np.array([-2, -1, 0, 1, 2])
y = np.array([1, 2, 4, 5, 7])
n = len(x)

# --- fit line: beta (slope), alpha (intercept) ---
x_bar, y_bar = x.mean(), y.mean()
cov_xy = np.mean((x - x_bar) * (y - y_bar))
var_x = np.mean((x - x_bar) ** 2)
beta = cov_xy / var_x
alpha = y_bar - beta * x_bar
print(f"x_bar={x_bar}, y_bar={y_bar}, beta={beta}, alpha={alpha}")

# --- residuals + Var(error), n-2 ---
fitted = alpha + beta * x
error = y - fitted
var_error = np.sum(error ** 2) / (n - 2)
Sxx = np.sum((x - x_bar) ** 2)
print(f"errors={error}, sum={error.sum():.4f}, var_error={var_error}, Sxx={Sxx}")

# --- SE(y_hat at x0), swept across x ---
def se_at(x0):
    return np.sqrt(var_error * (1 / n + (x0 - x_bar) ** 2 / Sxx))

se_center = se_at(0)      # x0 = x_bar = pivot point
se_edge = se_at(2)        # x0 = furthest data point
print(f"SE at center (x=0) = {se_center:.4f}")
print(f"SE at edge   (x=2) = {se_edge:.4f}")

x_line = np.linspace(-3, 3, 200)
y_line = alpha + beta * x_line
se_line = se_at(x_line)

fig, ax = plt.subplots(figsize=(8, 5.5))
ax.scatter(x, y, color='#4fc3f7', s=70, zorder=3, label='dummy data points')
ax.plot(x_line, y_line, color='#ff8a65', lw=2, label=f'fitted line: y = {alpha:.1f} + {beta:.1f}*x')
ax.fill_between(x_line, y_line - se_line, y_line + se_line, color='#ff8a65', alpha=0.3, label='+/- 1 SE band')
ax.axvline(x_bar, color='gray', lw=0.8, ls='--', label=f'pivot point: mean(x) = {x_bar}')

# annotate width at center vs edge
ax.annotate('', xy=(0, alpha + se_center), xytext=(0, alpha - se_center),
            arrowprops=dict(arrowstyle='<->', color='#ffca28', lw=1.5))
ax.text(0.1, alpha, f'narrow here\nSE={se_center:.2f}', color='#ffca28', fontsize=9, va='center')

y_at_2 = alpha + beta * 2
ax.annotate('', xy=(2, y_at_2 + se_edge), xytext=(2, y_at_2 - se_edge),
            arrowprops=dict(arrowstyle='<->', color='#66bb6a', lw=1.5))
ax.text(2.1, y_at_2, f'wide here\nSE={se_edge:.2f}', color='#66bb6a', fontsize=9, va='center')

ax.set_xlabel('x (generic, not market_return)')
ax.set_ylabel('y (generic, not strategy_return)')
ax.set_title('[MATH-MODE] Confidence band: narrow at the pivot, wide at the edges')
ax.legend(fontsize=8, loc='upper left')
plt.tight_layout()
out_path = '/mnt/c/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/52_mathmode_confidence_band_example.png'
plt.savefig(out_path, dpi=110)
print(f"Saved: {out_path}")
