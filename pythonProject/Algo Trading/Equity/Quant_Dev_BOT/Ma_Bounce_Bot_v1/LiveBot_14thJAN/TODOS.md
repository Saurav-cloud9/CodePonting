**v1.3 LIVE BOT - TODO LIST** 📋

## **TODO #1: ADD VOLUME FILTER** 🔇
## **TODO #2: CAPTURE SIGNAL DETAILS** 📊
## **TODO #3: UPDATE CSV COLUMNS** 📝
## **TODO #4: PASS SIGNAL DETAILS TO CSV** 🔗
## **TODO #5: TIME WINDOW FILTER** ⏰
## **TODO #6: POSITION RELOAD ON RESTART** 🔄
## **TODO #7: EOD AUTO-EXIT**

---

EXAMPLE BOUNCE SCORE USAGE ---> HIGHLY RECOMMENDED ⭐

PHASE 1: Manual Mode (Now - Week 1) 👨‍💻
🔔 SIGNAL: TATAMOTORS @ ₹353.35

⭐ BOUNCE QUALITY SCORE: 72/100
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Volume:    ████████░░  35/40 (1.8x avg) 
Momentum:  ███████░░░  22/30 (1 candle)
Time Left: ███░░░░░░░  15/20 (180 mins)
Pattern:   ░░░░░░░░░░   0/10 (long wick)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 RATING: GOOD (70-79 range)
📊 Suggested: Enter 70% position size

Proceed? (yes/no/custom qty):

---

## **TODO #1: ADD VOLUME FILTER** 🔇
**File:** `ma_bounce_bot_v1_2_PRODUCTION.py`
**Location:** Line 381 (inside touch check)
**Code to add:**
```python
# After: if touch_candle['low'] <= ma20_at_touch:
avg_volume = sum(c['volume'] for c in candles[-20:]) / 20
if touch_candle['volume'] < avg_volume * 1.2:
    continue  # Skip weak volume bounce
```
**Impact:** Filters weak signals like today's TMPV/BHARTI

---

## **TODO #2: CAPTURE SIGNAL DETAILS** 📊
**File:** `ma_bounce_bot_v1_2_PRODUCTION.py`
**Location:** Line 388 (when bounce confirmed)
**Code to modify:**
```python
# Calculate signal metrics
avg_volume = sum(c['volume'] for c in candles[-20:]) / 20
volume_ratio = touch_candle['volume'] / avg_volume
candles_gap = j - i  # Gap between touch and bounce

# Return signal details
signal_details = {
    'touch_time': touch_candle['timestamp'],
    'touch_low': touch_candle['low'],
    'touch_volume': touch_candle['volume'],
    'bounce_time': bounce_candle['timestamp'],
    'bounce_close': bounce_candle['close'],
    'bounce_volume': bounce_candle['volume'],
    'avg_volume': avg_volume,
    'volume_ratio': volume_ratio,
    'candles_gap': candles_gap,
    'ma20_at_touch': ma20_at_touch
}

return True, f"✅ BOUNCE! ...", distance_pct, signal_details
```

---

## **TODO #3: UPDATE CSV COLUMNS** 📝
**File:** `ma_bounce_bot_v1_2_PRODUCTION.py`
**Function:** `log_trade_to_csv()`
**Add columns:**
```python
fieldnames = [
    'timestamp', 'symbol', 'action', 'price', 'quantity', 'order_id',
    'strategy', 'target', 'stop_loss',
    # NEW COLUMNS:
    'touch_time', 'touch_low', 'touch_vol',
    'bounce_time', 'bounce_close', 'bounce_vol',
    'avg_vol', 'vol_ratio', 'candles_gap', 'ma20'
]
```

---

## **TODO #4: PASS SIGNAL DETAILS TO CSV** 🔗
**File:** `ma_bounce_bot_v1_2_PRODUCTION.py`
**Location:** Line 462 (place_order function)
**Modify:**
```python
# Change from 3 returns to 4 returns
has_signal, message, ma20_distance, signal_details = check_signal(...)

# Pass to CSV logger
log_trade_to_csv(..., signal_details)
```

---

## **TODO #5: TIME WINDOW FILTER** ⏰
**File:** `ma_bounce_bot_v1_2_PRODUCTION.py`
**Location:** Line ~835 (main loop)
**Code to add:**
```python
# Before scanning stocks
if current_time >= "14:30":
    print("⏸️  NO MORE SIGNALS - Too late in day")
    continue  # Only monitor exits
```

---

## **TODO #6: POSITION RELOAD ON RESTART** 🔄
**File:** `ma_bounce_bot_v1_2_PRODUCTION.py`
**Location:** After CSV load (Line ~200)
**Code to add:**
```python
# After loading CSV trades
open_positions = get_positions()  # Fetch from Upstox
# Rebuild dashboard from open positions
for pos in open_positions:
    if pos['symbol'] in traded_symbols:
        add_position_to_dashboard(...)
```

---

## **TODO #7: EOD AUTO-EXIT**
Problem: Manual exit at 3:05 PM
Fix:
if current_time >= "15:00":  # 3:00 PM
    exit_all_positions()
Already in code but didn't trigger! Need to debug.

---

## **TODO #8:TIME WINDOW FILTER 🕐**
Problem: Late signals (1:55 PM) have no time to hit target
Add:
pythonTRADING_WINDOW_END = "14:30"  # No new signals after 2:30 PM
Reasoning: Need 60+ mins for 1.5% move

---

ADDITIONAL NOTES 🗒️
--->ENTRY CONFIRMATION TIMEOUT ⏱️
Problem: Price changed from ₹353.35 → ₹349.85 during delay
--->BOUNCE QUALITY SCORE ⭐

---

## **TODO #9:Text map + Visual flowchart = Documentation block🕐**

## **TODO #10: Nifty regime filter to v1.3🕐**


---

## **TESTING CHECKLIST** ✅

**After implementing:**
- [ ] Volume filter blocks weak signals
- [ ] CSV has all new columns
- [ ] Signal details logged correctly
- [ ] No signals after 2:30 PM
- [ ] Dashboard shows positions after restart

---

**Priority:** #1, #2, #3, #4 = Critical for tomorrow
**Timeline:** 1-2 hours implementation

