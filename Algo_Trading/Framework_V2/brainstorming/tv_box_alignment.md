# TV Box Alignment Problem
**Status:** Stuck — CC needs Codex's input  
**File:** `Algo_Trading/Framework_V2/scripts/fv2_signal.pine`

---

## What we are trying to do

In TradingView Pine Script v5, we want to draw a colored box that **precisely wraps the body (open→close) of a specific candle** on a 5-minute chart.

We draw two boxes per signal:
- **Orange box** → wraps the "touch candle" (where price touched MA20)
- **Blue box** → wraps the "bounce candle" (where price confirmed bounce)

The box height is correct (uses `math.max(open,close)` / `math.min(open,close)` — body only, no wicks).  
**The problem is horizontal alignment — the box is consistently shifted to the right of the target candle.**

---

## Key facts about the environment

- Chart: 5-minute bars on NSE (Indian market)
- Bar duration: 300,000 ms (5 min × 60 sec × 1000 ms)
- In Pine Script v5: `time` = bar's **open time** in UNIX milliseconds
- We are using `xloc=xloc.bar_time` for the boxes
- TradingView appears to map `time` (bar open) to the bar's **visual center** on the x-axis (confirmed empirically — see experiments below)

---

## What we've tried (chronological)

| Code | Result |
|------|--------|
| `box.new(time, top, time+300000, bot, xloc=xloc.bar_time)` | Box shifted RIGHT — T label to the left |
| `box.new(time-150000, top, time+150000, bot, xloc=xloc.bar_time)` | Still shifted right — T label to the left |
| `box.new(time-300000, top, time, bot, xloc=xloc.bar_time)` | T label lands at box RIGHT EDGE — too far left |
| `box.new(time-150000, top, time+150000, bot, xloc=xloc.bar_time)` | **Currently compiled — not yet confirmed** |
| `box.new(bar_index[k], top, bar_index[k]+1, bot, xloc=xloc.bar_index)` | Shifted right by ~half bar |
| `box.new(bar_index[k]-1, top, bar_index[k], bot, xloc=xloc.bar_index)` | Shifted left by ~half bar |

### Ground truth method used to diagnose
We added a `label.new(bar_index[touch_k], high[touch_k], "T")` — labels drawn with `xloc.bar_index` are **always pixel-perfect** on their candle. The T label reliably lands at the visual center of the touch candle. We then compare where the orange box is relative to the T label.

**Finding from `time-300000` to `time`:** T label was at the box's RIGHT EDGE.  
This means: `time` in TV's `xloc.bar_time` coordinate system = the bar's visual right edge (not center, not left edge).

---

## Current hypothesis

If TV maps `time` (bar open) to the bar's **right edge** in `xloc.bar_time` space, then:
- Bar visual right edge = `time`
- Bar visual left edge = `time - 300000`
- Bar visual center = `time - 150000`

Therefore correct box = `time - 300000` to `time`... but that was "too left" in earlier tests (before the touch candle detection logic was fixed).

**OR** the mapping is: `time` = bar center, which would make `time - 150000` to `time + 150000` correct.

The inconsistency comes from earlier tests being done with a **bug in the touch candle detection** (it was picking the wrong candle), so those earlier "too left" results may not be reliable.

---

## Current Pine Script (relevant section only)

```pine
//@version=5
indicator("fv2 MA Bounce Signal", overlay=true, max_labels_count=500, max_boxes_count=500)

// bar open time in ms = time
// 5-min bar = 300000 ms

bool in_window = time >= box_from and time <= box_to
if signal_fire and in_window
    float t_top = math.max(open[touch_k], close[touch_k])
    float t_bot = math.min(open[touch_k], close[touch_k])
    float b_top = math.max(open, close)
    float b_bot = math.min(open, close)

    // Touch candle — orange (ALIGNMENT ISSUE HERE)
    box.new(time[touch_k] - 150000, t_top, time[touch_k] + 150000, t_bot,
            border_color=#FFB300, border_width=3,
            bgcolor=color.new(#FFB300, 70), xloc=xloc.bar_time)

    // Bounce candle — blue (SAME ALIGNMENT ISSUE)
    box.new(time - 150000, b_top, time + 150000, b_bot,
            border_color=#1E90FF, border_width=3,
            bgcolor=color.new(#1E90FF, 70), xloc=xloc.bar_time)

    // Ground truth labels — always pixel-perfect (bar_index = correct position)
    label.new(bar_index[touch_k], high[touch_k], "T",
              color=#FFB300, textcolor=color.black,
              style=label.style_label_down, size=size.tiny)
    label.new(bar_index, high, "B",
              color=#1E90FF, textcolor=color.white,
              style=label.style_label_down, size=size.tiny)
```

---

## What we need from Codex

1. **What is the correct `xloc.bar_time` formula** to draw a box that spans exactly one 5-minute bar, aligned with how TradingView visually renders that bar?

2. Specifically: in `xloc.bar_time` coordinates, does Pine's `time` (bar open time in ms) correspond to the bar's **left edge**, **center**, or **right edge** on the visual chart?

3. Is there a **definitive Pine Script v5 reference** or known community solution for this?

4. **Alternative approach:** Is there a way to use `xloc.bar_index` with non-integer coordinates (e.g. `bar_index - 0.5` to `bar_index + 0.5`) to get sub-bar precision? Or any other clean approach?

5. If the correct answer is `time - 300000` to `time` (right-edge aligned), please confirm — CC's earlier tests may have been unreliable due to a now-fixed bug in touch candle detection.

---

## Codex response area

*Please write your findings/suggestion below this line:*

---
The clean fix is to stop fighting `xloc.bar_time` for this use case and use `xloc.bar_index` with whole-bar boundaries:

```pine
box.new(bar_index[touch_k], t_top, bar_index[touch_k] + 1, t_bot, xloc=xloc.bar_index, ...)
box.new(bar_index,          b_top, bar_index + 1,          b_bot, xloc=xloc.bar_index, ...)
```

That is the most reliable way to draw a box that visually spans exactly one rendered candle body. The current `fv2_signal.pine` already uses this shape, and that is the version I would keep.

Findings:

1. For exact visual one-candle alignment, `xloc.bar_index` is the better coordinate system.
   `bar_index -> bar_index + 1` gives one full bar slot. In practice this is the stable way to make the box wrap the candle you intend.

2. I would not treat `time` in `xloc.bar_time` as a dependable "left/center/right pixel edge" primitive for candle-width drawing.
   `time` is definitively the bar's opening timestamp, but the chart's rendered candle width depends on TradingView's visual time-axis layout, zoom, and session spacing. That makes `bar_time` much less trustworthy for "draw exactly one candle wide" than `bar_index`.

3. If you must use `xloc.bar_time`, the only formula I would consider correct is:

```pine
box.new(time[touch_k], t_top, time_close[touch_k], t_bot, xloc=xloc.bar_time, ...)
box.new(time,          b_top, time_close,          b_bot, xloc=xloc.bar_time, ...)
```

Use `time_close`, not `time + 300000`. `time_close` is the proper bar-ending timestamp and avoids hardcoding interval math.

4. There is no clean sub-bar `bar_index - 0.5` style solution here.
   `xloc.bar_index` drawing coordinates are integer bar positions for practical purposes, so fractional "half-bar" alignment is not the intended path.

5. Because the goal is to wrap the rendered candle body, my recommendation is:
   keep the current `xloc.bar_index` implementation in `fv2_signal.pine` and treat that as the fix.

Bottom line:
`time - 300000` to `time` is not the fix I would ship with confidence.
`time` to `time_close` is the only defensible `bar_time` form.
For precise visual alignment, `bar_index[k]` to `bar_index[k] + 1` is the right solution, and your current script is already on that path.
