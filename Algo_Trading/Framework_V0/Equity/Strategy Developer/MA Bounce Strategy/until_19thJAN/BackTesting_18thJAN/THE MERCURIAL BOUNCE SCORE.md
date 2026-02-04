**🎯 THE BOUNCE QUALITY SCORE - LET'S BUILD IT!**

**From your notes (Jan 13):**
```
Volume ratio (40 pts) + Momentum (30 pts) + Time left (20 pts) + Wick pattern (10 pts) = 0-100 score
```

**Let's break down each component:**

---

## **1. VOLUME RATIO (40 points) - Institutional vs Retail**

**Logic:**
```python
volume_ratio = bounce_volume / avg_volume_20

if volume_ratio >= 2.0:      # 2x = Strong institutional
    volume_score = 40
elif volume_ratio >= 1.5:    # 1.5x = Good
    volume_score = 30
elif volume_ratio >= 1.2:    # 1.2x = Acceptable (current filter)
    volume_score = 20
else:                         # < 1.2x = Weak
    volume_score = 0
```

**Why 40 points?** Volume = most reliable indicator of conviction

---

## **2. MOMENTUM (30 points) - Bounce Strength**

**Options to measure:**

**Option A - Candle size:**
```python
bounce_move = (bounce_close - touch_low) / touch_low * 100
# If bounce recovers 1%+ in one candle = strong

if bounce_move >= 1.0:       # 1%+ recovery
    momentum_score = 30
elif bounce_move >= 0.5:     # 0.5-1% recovery
    momentum_score = 20
elif bounce_move >= 0.2:     # 0.2-0.5% recovery
    momentum_score = 10
else:
    momentum_score = 0
```

**Option B - Follow-through (next candle confirms):**
```python
if next_candle_close > bounce_close:  # Continued momentum
    momentum_score += 10
```

Which momentum measure feels more reliable to you?

---

## **3. TIME LEFT (20 points) - Enough runway for target**

**Logic:**
```python
current_time = bounce_time  # e.g., "10:30"
hours_left = calculate_hours_until_3pm(current_time)

if hours_left >= 3.0:        # 3+ hours = plenty of time
    time_score = 20
elif hours_left >= 2.0:      # 2-3 hours = good
    time_score = 15
elif hours_left >= 1.0:      # 1-2 hours = tight
    time_score = 10
else:                         # < 1 hour = too late
    time_score = 0
```

**Why 20 points?** Your Jan 13 trades showed late entries = minimal profit

---

## **4. WICK PATTERN (10 points) - Rejection strength**

**Logic:**
```python
# Touch candle wick analysis
lower_wick = touch_low - touch_open  # How far it dipped
body_size = abs(touch_close - touch_open)
wick_ratio = lower_wick / body_size if body_size > 0 else 0

if wick_ratio >= 2.0:        # Long wick = strong rejection
    wick_score = 10
elif wick_ratio >= 1.0:      # Moderate wick
    wick_score = 5
else:                         # Small/no wick
    wick_score = 0
```

**Why 10 points?** Nice-to-have but least reliable (many bounces work without wicks)

---

## **TOTAL SCORE THRESHOLDS:**

```python
total_score = volume_score + momentum_score + time_score + wick_score

if total_score >= 80:        # 80-100 = EXCELLENT
    quality = "EXCELLENT"
elif total_score >= 60:      # 60-79 = GOOD
    quality = "GOOD"
elif total_score >= 40:      # 40-59 = ACCEPTABLE
    quality = "ACCEPTABLE"
else:                         # 0-39 = SKIP
    quality = "SKIP"
```

**Trading rules:**
- EXCELLENT (80+): Trade with full position size
- GOOD (60-79): Trade with 75% position size
- ACCEPTABLE (40-59): Trade with 50% position size
- SKIP (0-39): No trade

---

## **QUESTIONS FOR YOU:**

1. **Momentum measurement:** Candle size (Option A) or follow-through (Option B)?

2. **Score thresholds:** Agree with 80/60/40 cutoffs or adjust?

3. **Position sizing:** Should we actually reduce quantity or just skip weak signals?

4. **Manual approval:** Keep user confirmation for ACCEPTABLE (40-59) scores only?

5. **Backtesting:** Should we add bounce_score column to 48-month backtest output?

**What's your take on the scoring logic?** Too complex or just right? 🤔