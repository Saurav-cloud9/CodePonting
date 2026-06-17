"""
Trading ABC — 5-Step Visual Explainer
Illustrative diagram using synthetic price data.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Theme ────────────────────────────────────────────────────────────────────
BG    = '#0d1117'
FG    = '#e6edf3'
GREEN = '#26a69a'
RED   = '#ef5350'
BLUE  = '#64b5f6'
ORG   = '#ffa726'
YEL   = '#ffee58'
PURP  = '#ce93d8'

fig = plt.figure(figsize=(16, 9), facecolor=BG)
ax  = fig.add_axes([0.04, 0.08, 0.62, 0.86])   # main chart
ax.set_facecolor(BG)

# ── Synthetic price data (35 bars) ───────────────────────────────────────────
# A (swing low) = bar 4  |  B (swing high) = bar 20  |  C (pullback) = bar 30
np.random.seed(7)
close = np.array([
    # bottom / A zone  (0-5)
    102, 100, 99, 97, 96, 98,
    # uptrend A→B     (6-20)
    100, 103, 106, 108, 111, 113, 116, 118, 120, 123, 125, 127, 128, 130, 131,
    # pullback B→C    (21-30)
    129, 127, 125, 123, 121, 119, 117, 116, 115, 114,
    # bounce + after  (31-34)
    116, 119, 122, 124,
])
n = len(close)
op = np.roll(close, 1); op[0] = close[0]
rng = np.abs(close - op)
hi  = np.maximum(op, close) + np.random.uniform(0.6, 2.2, n)
lo  = np.minimum(op, close) - np.random.uniform(0.6, 2.2, n)

A_b, A_p = 4,  close[4]   # 96
B_b, B_p = 20, close[20]  # 131
C_b, C_p = 30, close[30]  # 114

# ── MA Cloud (6 MAs cluster below candle body in uptrend) ────────────────────
# Simulated as smoothly-rising band that lags price
x = np.arange(n)
cloud_top = 88 + 0.9*x + np.sin(x*0.3)*1.5
cloud_bot = cloud_top - 4.5
# Force C-zone cloud top near 115 so wick can touch it
cloud_top = np.where(x < 10, cloud_top, cloud_top * 0.98 + 2)

ax.fill_between(x, cloud_bot, cloud_top, color=GREEN, alpha=0.18, zorder=1, label='Trend Cloud')
ax.plot(x, cloud_top, color=GREEN, lw=0.8, alpha=0.5, zorder=2)
ax.plot(x, cloud_bot, color=GREEN, lw=0.8, alpha=0.5, zorder=2)

# ── Draw candles ─────────────────────────────────────────────────────────────
for i in range(n):
    bull   = close[i] >= op[i]
    col    = GREEN if bull else RED
    blo    = min(op[i], close[i])
    bhi    = max(op[i], close[i])
    bh     = max(bhi - blo, 0.4)
    # wick
    ax.plot([i, i], [lo[i], hi[i]], color=col, lw=1.0, alpha=0.7, zorder=3)
    # body
    rect = mpatches.FancyBboxPatch((i-0.28, blo), 0.56, bh,
                                    boxstyle='square,pad=0',
                                    linewidth=0.5, edgecolor=col,
                                    facecolor=col, alpha=0.85, zorder=4)
    ax.add_patch(rect)

# ── Bounce bar (bar 30) — highlight + force wick into cloud ──────────────────
lo[C_b]   = cloud_top[C_b] - 0.3          # wick just touches cloud top
hi[C_b]   = close[C_b] + 1.8
op[C_b]   = close[C_b] - 1.2              # bullish body

# Redraw bar 30 with yellow highlight
ax.plot([C_b, C_b], [lo[C_b], hi[C_b]], color=YEL, lw=2.0, zorder=7)
rect = mpatches.FancyBboxPatch((C_b-0.32, op[C_b]), 0.64, close[C_b]-op[C_b]+0.4,
                                boxstyle='square,pad=0',
                                linewidth=2.0, edgecolor=YEL,
                                facecolor=GREEN, alpha=1.0, zorder=8)
ax.add_patch(rect)

# ── ZigZag lines ─────────────────────────────────────────────────────────────
ax.plot([A_b, B_b], [A_p, B_p], color=GREEN, lw=2.2, ls='--', zorder=6, alpha=0.9)
ax.plot([B_b, C_b], [B_p, C_p], color=RED,   lw=2.2, ls='--', zorder=6, alpha=0.9)

# ── A / B / C pivot labels ────────────────────────────────────────────────────
ax.text(A_b-0.8, A_p-4.5, 'A', fontsize=15, color=GREEN, fontweight='bold', zorder=10)
ax.text(B_b-0.5, B_p+1.5, 'B', fontsize=15, color=BLUE,  fontweight='bold', zorder=10)
ax.text(C_b+0.4, C_p-4.5, 'C', fontsize=15, color=ORG,   fontweight='bold', zorder=10)

# ── Fibonacci zone 38.2–61.8% of A→B ────────────────────────────────────────
swing   = B_p - A_p
fib382  = B_p - 0.382 * swing
fib618  = B_p - 0.618 * swing
ax.fill_between(range(B_b, n), fib618, fib382, color=BLUE, alpha=0.08, zorder=2)
ax.hlines(fib382, B_b, n-1, colors=BLUE, lw=1.4, ls='dotted', alpha=0.8, zorder=5)
ax.hlines(fib618, B_b, n-1, colors=BLUE, lw=1.4, ls='dotted', alpha=0.8, zorder=5)
ax.text(B_b+0.4, fib382+0.4, '38.2%', fontsize=8.5, color=BLUE, alpha=0.9)
ax.text(B_b+0.4, fib618-2.2, '61.8%', fontsize=8.5, color=BLUE, alpha=0.9)

# ── Entry arrow (bar 31) ─────────────────────────────────────────────────────
entry_y = op[31]
ax.annotate('', xy=(31, entry_y), xytext=(31, entry_y - 8),
            arrowprops=dict(arrowstyle='->', color=YEL, lw=2.2), zorder=9)
ax.text(31.3, entry_y - 9.5, 'ENTRY\n(bar 31 open)', fontsize=8.5,
        color=YEL, fontweight='bold', zorder=9)

# ── "No new low" zone arrow ───────────────────────────────────────────────────
ax.annotate('', xy=(C_b+1, C_p-1), xytext=(C_b+3, C_p-1),
            arrowprops=dict(arrowstyle='<-', color=PURP, lw=1.5))
ax.text(C_b+3.2, C_p-1, 'no new low\nsince C', fontsize=8, color=PURP, alpha=0.9)

# ── 6-bar window bracket ─────────────────────────────────────────────────────
ax.annotate('', xy=(30, 85), xytext=(34, 85),
            arrowprops=dict(arrowstyle='<->', color=ORG, lw=1.5))
ax.text(31.2, 83, '≤6 bars', fontsize=8, color=ORG)

# ── Axes styling ─────────────────────────────────────────────────────────────
ax.set_xlim(-1, n+1)
ax.set_ylim(78, 145)
ax.set_xticks([]); ax.tick_params(colors=FG, labelsize=8)
ax.yaxis.tick_right(); ax.yaxis.set_tick_params(colors=FG)
for spine in ax.spines.values(): spine.set_color('#30363d')
ax.set_title('Trading ABC — 5-Step Signal Logic', color=FG, fontsize=13,
             fontweight='bold', pad=10)

# ── Step-by-step legend panel (right side) ───────────────────────────────────
ax2 = fig.add_axes([0.68, 0.08, 0.30, 0.86])
ax2.set_facecolor('#161b22'); ax2.set_xticks([]); ax2.set_yticks([])
for spine in ax2.spines.values(): spine.set_color('#30363d')

steps = [
    ('STEP 1', 'Trend Cloud',
     '6 MAs: SMA(50/100/150/200) +\nEMA(20/40)\n\nAll 6 below candle body for\n2 consecutive bars → Trend = +1',
     GREEN, '▓'),
    ('STEP 2', 'ZigZag (period=8)',
     'Detects swing highs & lows.\nKeeps last 5 pivot points.\nLabels oldest→newest as A, B, C.',
     BLUE, '╱╲'),
    ('STEP 3', 'ABC Fib Check',
     '(A – C) / (A – B) must be\nbetween 38.2% and 61.8%\n\nC must retrace 38-62% of A→B\n(±5% error rate allowed)',
     BLUE, '⋯'),
    ('STEP 4 ★', 'Bounce Check',
     'min(low, low[1]) ≤ any MA   ← wick touch\nAND  close > that MA           ← closes above\nAND  close > open                ← bullish bar\n\nChecked against ALL 6 MAs',
     YEL, '▲'),
    ('STEP 5', 'Final Long Signal',
     'trend == +1         (Step 1 ✓)\nABC within last 6 bars (Step 2+3 ✓)\nlbounced == true    (Step 4 ✓)\nno new low since C point',
     ORG, '→'),
]

y = 0.96
for code, title, desc, col, icon in steps:
    ax2.text(0.04, y, f'{icon}  {code} — {title}', transform=ax2.transAxes,
             fontsize=9.5, color=col, fontweight='bold')
    y -= 0.03
    for line in desc.split('\n'):
        ax2.text(0.06, y, line, transform=ax2.transAxes,
                 fontsize=8.2, color=FG, alpha=0.85)
        y -= 0.028
    y -= 0.018
    ax2.axhline(y + 0.005, color='#30363d', lw=0.8, xmin=0.03, xmax=0.97)
    y -= 0.015

# Dead code note
ax2.text(0.04, y-0.01, '⚠  lstoch (Stochastic)', transform=ax2.transAxes,
         fontsize=8.5, color=RED, fontweight='bold')
ax2.text(0.06, y-0.04, 'Computed in Pine Script but\nnever wired into the signal.\nDEAD CODE — ignore.',
         transform=ax2.transAxes, fontsize=8.0, color=FG, alpha=0.7)

# ── Save ─────────────────────────────────────────────────────────────────────
OUT = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\reports\trading_abc_explainer.png'
plt.savefig(OUT, dpi=140, bbox_inches='tight', facecolor=BG)
print(f'Saved: {OUT}')
plt.show()
