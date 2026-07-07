import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.style.use('dark_background')

fig, axes = plt.subplots(1, 5, figsize=(18, 6))
fig.suptitle('Touch Candle Types — Approach from Above MA20', fontsize=14, color='white', y=1.02)

MA_Y = 5.0
MA_COLOR = '#00bcd4'

titles = [
    '1. Wick Touch\n(body above)',
    '2. Wick Pierce\n(body above)',
    '3. Body Touch\n(close at MA)',
    '4. Body Cross\n(bearish close)',
    '5. Gap Down\n(open below MA)',
]

# Each candle: (open, close, high, low)
candles = [
    (7.0, 6.5, 7.5, 5.0),   # 1. wick just touches MA
    (7.0, 6.5, 7.5, 3.5),   # 2. wick pierces deep below MA
    (7.0, 5.0, 7.5, 4.0),   # 3. close exactly at MA
    (7.0, 3.5, 7.5, 3.0),   # 4. open above, close below MA
    (3.5, 2.5, 4.0, 2.0),   # 5. gap down — opens below MA (prev close was above)
]

# Previous candle (always above MA) for context
prev = (8.5, 7.5, 9.0, 7.0)

for ax, title, (o, c, h, l) in zip(axes, titles, candles):
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 11)
    ax.set_title(title, color='white', fontsize=9, pad=8)
    ax.axis('off')

    # MA20 line
    ax.axhline(y=MA_Y, xmin=0, xmax=1, color=MA_COLOR, linewidth=1.5, linestyle='--')
    ax.text(3.8, MA_Y + 0.15, 'MA20', color=MA_COLOR, fontsize=7, ha='right')

    # Previous candle (green, above MA)
    po, pc, ph, pl = prev
    ax.plot([1.0, 1.0], [pl, ph], color='white', linewidth=1)
    body_color = '#26a69a' if pc >= po else '#ef5350'
    rect = mpatches.FancyBboxPatch((0.7, min(po, pc)), 0.6, abs(pc - po),
                                    boxstyle="square,pad=0", linewidth=0,
                                    facecolor='#26a69a', alpha=0.6)
    ax.add_patch(rect)

    # Touch candle
    body_color = '#26a69a' if c >= o else '#ef5350'
    ax.plot([2.5, 2.5], [l, h], color='white', linewidth=1)
    rect2 = mpatches.FancyBboxPatch((2.2, min(o, c)), 0.6, max(abs(c - o), 0.15),
                                     boxstyle="square,pad=0", linewidth=0,
                                     facecolor=body_color)
    ax.add_patch(rect2)

    # Highlight the low piercing MA
    if l <= MA_Y:
        ax.plot([2.5], [l], marker='o', color='yellow', markersize=5, zorder=5)

    # Gap down indicator on type 5
    if title.startswith('5'):
        ax.annotate('', xy=(2.5, o), xytext=(2.5, prev[1]),
                    arrowprops=dict(arrowstyle='->', color='orange', lw=1.5))
        ax.text(3.0, (o + prev[1]) / 2, 'gap', color='orange', fontsize=7)

plt.tight_layout()
out = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\reports\screenshots\touch_types.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
print(f'Saved: {out}')
