# python
# Simple visualization of spawnRandomY and onUpdateStatic behavior using matplotlib.
# - Spawns at x=80 with y in [12,56]
# - Per-frame move: dx = -0.6
# - Forests wrap at x < -4 to x=84, others get removed

import random
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

random.seed(1)

SCREEN_MIN_X = -10
SCREEN_MAX_X = 90
SPAWN_X = 80
WRAP_X = 84
WRAP_THRESHOLD = -4
Y_MIN, Y_MAX = 12, 56
DX_PER_FRAME = -0.6
FPS = 60
FRAMES = 180  # 3 seconds @ 60 fps

# Create sample spawns: mix of "forest" and "fence"
spawns = []
for i in range(8):
    typ = "forest" if i % 2 == 0 else "fence"
    y = random.randint(Y_MIN, Y_MAX)
    spawns.append({"type": typ, "x": SPAWN_X + i*4, "y": y})  # stagger x for visibility

fig, ax = plt.subplots(figsize=(8, 3))
ax.set_xlim(SCREEN_MIN_X, SCREEN_MAX_X)
ax.set_ylim(0, 70)
ax.set_yticks([Y_MIN, Y_MAX])
ax.set_xlabel("x (pixels)")
ax.set_title("spawnRandomY: initial spawn at x=80, y in [12,56]; moving left by 0.6 per frame")

scatter = ax.scatter([s["x"] for s in spawns], [s["y"] for s in spawns],
                     c=['green' if s["type"]=="forest" else 'red' for s in spawns],
                     s=80)
labels = [ax.text(s["x"], s["y"]+1, s["type"], fontsize=8, ha='center') for s in spawns]

# Draw spawn line and player marker
ax.axvline(SPAWN_X, color='gray', linestyle='--', linewidth=0.8)
ax.text(SPAWN_X, 66, "spawn x=80", ha='center', fontsize=8)
ax.scatter([20], [34], marker='P', color='blue', s=100)
ax.text(20, 36, "player x=20", ha='center', fontsize=8)

def update(frame):
    # move each spawn left by DX_PER_FRAME
    to_remove = []
    for i, s in enumerate(spawns):
        s["x"] += DX_PER_FRAME
        if s["x"] < WRAP_THRESHOLD:
            if s["type"] == "forest":
                s["x"] = WRAP_X
            else:
                to_remove.append(i)
    # remove destroyed (fence) in reverse order
    for i in reversed(to_remove):
        spawns.pop(i)
    # update scatter and labels
    scatter.set_offsets([[s["x"], s["y"]] for s in spawns])
    # remove old texts
    for txt in labels[:]:
        txt.remove()
    labels[:] = [ax.text(s["x"], s["y"]+1, s["type"], fontsize=8, ha='center') for s in spawns]
    ax.set_title(f"Frame {frame}/{FRAMES}  | objects: {len(spawns)}")
    return scatter, *labels

anim = FuncAnimation(fig, update, frames=FRAMES, interval=1000/FPS, blit=False)
plt.show()
