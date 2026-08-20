"""
[MATH-MODE] Population density analogy — dummy example, no trading data.

Purpose: illustrate "density x width = count" (the same idea as
"probability density x width = probability") with a tiny made-up
example. Standalone teaching aid, unrelated to the alpha/beta CAPM
notebook (52_alpha_beta_concept_and_powergrid.ipynb) — see the
matching write-up in 52_t_and_T_explained.md.

Dummy setup: a 10 km road, split into 2 segments with different
(but constant-within-segment) population density:
  - km 0 to 4:  density = 100 people/km
  - km 4 to 10: density = 50  people/km

Headcount in any window = area under the density curve over that
window (sum of rectangle areas, one per segment it overlaps).
"""
import matplotlib.pyplot as plt
import numpy as np

plt.style.use('dark_background')

# --- dummy density function (step function, km -> people/km) ---
def density(km):
    return np.where(km < 4, 100, 50)

# --- whole-road headcount check ---
total = 100 * 4 + 50 * 6
print(f"Total population, km 0-10: {total} people  (100*4 + 50*6)")

# --- headcount in a window that crosses BOTH segments: km 2 to 6 ---
a, b = 2, 6
piece1 = 100 * (4 - a)   # km 2 to 4, density 100
piece2 = 50 * (b - 4)    # km 4 to 6, density 50
window_count = piece1 + piece2
print(f"Headcount in [{a},{b}] km = {piece1} + {piece2} = {window_count} people")

# --- plot ---
km = np.linspace(0, 10, 1000)
d = density(km)

fig, ax = plt.subplots(figsize=(8, 5))
ax.step(km, d, where='post', color='#4fc3f7', lw=2, label='population density (people/km)')
ax.fill_between(km, d, where=(km >= a) & (km <= b), step='post',
                 color='#ffca28', alpha=0.5,
                 label=f'window [{a},{b}] km -> {window_count} people (the "area")')
ax.axvline(4, color='gray', lw=0.8, ls='--', label='segment boundary (km 4)')
ax.set_xlabel('position along road (km)  <-- plays the role of "x", the outcome axis')
ax.set_ylabel('density (people per km)  <-- NOT a headcount by itself')
ax.set_title('[MATH-MODE] Density x width = count\n(same shape as: probability density x width = probability)')
ax.legend(fontsize=9)
ax.set_ylim(0, 130)
plt.tight_layout()
out_path = '/mnt/c/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/52_mathmode_population_density_example.png'
plt.savefig(out_path, dpi=110)
print(f"Saved: {out_path}")
