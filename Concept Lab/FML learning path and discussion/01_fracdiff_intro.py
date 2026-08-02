"""
Step 1-2 illustration: why fractional differentiation exists.
Synthetic trending price -> compare raw price, returns (d=1), and fracdiff (d=0.4)
"""
import numpy as np
import matplotlib.pyplot as plt

plt.style.use('dark_background')
np.random.seed(42)

# 1. Synthetic trending price series (like TATAMOTORS drifting up over a year)
n = 500
noise = np.random.normal(0, 1, n)
drift = np.linspace(0, 40, n)  # steady uptrend
price = 750 + drift + np.cumsum(noise) * 0.5
price = pd = np.array(price)

# 2. Returns = d=1 full differencing
returns = np.diff(price, prepend=price[0])

# 3. Fractional differentiation, fixed-width window (AFML method)
def frac_diff_weights(d, thresh=1e-4, max_len=200):
    w = [1.0]
    k = 1
    while k < max_len:
        w_k = -w[-1] * (d - k + 1) / k
        if abs(w_k) < thresh:
            break
        w.append(w_k)
        k += 1
    return np.array(w[::-1])  # oldest weight first

d = 0.4
weights = frac_diff_weights(d)
width = len(weights)
fracdiff = np.full(n, np.nan)
for t in range(width - 1, n):
    window = price[t - width + 1: t + 1]
    fracdiff[t] = np.dot(weights, window)

# --- Plot ---
fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)

axes[0].plot(price, color='#4fc3f7')
axes[0].set_title('Raw price — full memory, but NON-stationary (trending mean)', fontsize=11)

axes[1].plot(returns, color='#ff8a65', linewidth=0.8)
axes[1].set_title('Returns (d=1) — stationary, but memory-less (only remembers yesterday)', fontsize=11)

axes[2].plot(fracdiff, color='#81c784', linewidth=0.9)
axes[2].set_title(f'Fractional diff (d={d}) — stationary-ish, keeps partial memory (window={width} bars)', fontsize=11)

for ax in axes:
    ax.axhline(0, color='gray', linewidth=0.5, linestyle='--', alpha=0.5)
    ax.grid(alpha=0.15)

plt.tight_layout()
out = 'fracdiff_step1_illustration.png'
plt.savefig(out, dpi=130)
print(f"saved {out}")
