"""
Step 52 [MATH-MODE] — standalone visual: the (t,s) grid of Cov(y_t,y_s) values, showing why
independence collapses the double sum down to just its diagonal. n=6 dummy example, no trading
data — just illustrating the structural pattern discussed in chat (Step 9's independence collapse).
"""
import numpy as np
import matplotlib.pyplot as plt

plt.style.use('dark_background')

n = 6
sigma_sq = 1.0  # dummy value, just to have something nonzero on the diagonal

# Build the (t,s) grid: diagonal = sigma^2 (Var(y_t)), off-diagonal = 0 (independence)
grid = np.zeros((n, n))
np.fill_diagonal(grid, sigma_sq)

fig, ax = plt.subplots(figsize=(7, 7))
im = ax.imshow(grid, cmap='inferno', vmin=0, vmax=sigma_sq * 1.2)

# Annotate every cell with its Cov(y_t,y_s) label
for t in range(n):
    for s in range(n):
        val = grid[t, s]
        label = "sigma^2" if t == s else "0"
        color = 'black' if t == s else 'white'
        ax.text(s, t, label, ha='center', va='center', color=color, fontsize=11, fontweight='bold')

ax.set_xticks(range(n))
ax.set_yticks(range(n))
ax.set_xticklabels([f"s={i+1}" for i in range(n)])
ax.set_yticklabels([f"t={i+1}" for i in range(n)])
ax.set_title(f"Cov(y_t, y_s) grid (n={n}) — only the diagonal (t=s) survives independence")
ax.set_xlabel("s")
ax.set_ylabel("t")

# Highlight the diagonal with a border
for i in range(n):
    ax.add_patch(plt.Rectangle((i-0.5, i-0.5), 1, 1, fill=False, edgecolor='#ffca28', linewidth=2.5))

plt.tight_layout()
out_path = __file__.replace('.py', '.png')
plt.savefig(out_path, dpi=130)

n_total = n * n
n_diag = n
n_off = n_total - n_diag
print(f"n = {n}")
print(f"Total (t,s) pairs in the double sum: n^2 = {n_total}")
print(f"Diagonal (t=s) pairs that SURVIVE:    n   = {n_diag}  (each contributes sigma^2)")
print(f"Off-diagonal (t!=s) pairs that VANISH: n^2-n = {n_off}  (each contributes exactly 0)")
print(f"Saved: {out_path}")
