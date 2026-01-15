# MA BOUNCE STRATEGY - CORE LOGIC v1.0

## ENTRY SIGNAL (TRUE BOUNCE)

```
Step 1: TOUCH CHECK
if candle['low'] <= ma20:
    → Price touched MA20 support

Step 2: BOUNCE CONFIRMATION  
if candle['close'] > ma20:
    → Price bounced back up
    → ✅ ENTRY SIGNAL

Step 3: DISTANCE THRESHOLD (Optional)
if (close - ma20) / ma20 > 0.001:  # 0.1% above
    → Strong bounce confirmation
```

**Current Code (WRONG):**
```python
distance = abs(close - ma20) / ma20
if distance <= 0.005 and close >= ma20:
    # Detects "proximity" not "bounce"
```

**Correct Code (TRUE BOUNCE):**
```python
if low <= ma20:  # Touch
    if close > ma20:  # Bounce
        # SIGNAL!
```

---

## EXIT RULES ---> Tested with incorrect bounce logic

**Target:** 1.5% (validated: 85% of Top 10 appearances)
**Stop Loss:** 0.5% (1:3 risk/reward)
**Time Limit:** 80 candles (6.5 hours) → EOD square-off

---

## FILTERS (Tested in backtest) ---> Tested with incorrect bounce logic

- **No Filter** (94% of Top 10) ← WINNER
- MA50/100/200 filters (6% combined)

**Decision:** No additional filters needed

---

## EFFICIENCY METRIC (CORRECTED)

**WRONG (Current backtest):**
```python
efficiency = (net_profit / avg_price) × 100
# Compares monthly profit to daily avg price
```

**CORRECT (Capital-based):**
```python
efficiency = (net_profit / total_capital_deployed) × 100
# Where: total_capital = sum(entry_price × qty for all trades)
```

---

## KEY PARAMETERS

- **MA Period:** 20 (5-min candles)
- **Volume:** 1.2× avg (currently not in live bot)
- **Bounce Zone:** 0.5% around MA20
- **Confirmation:** Close > MA20 after touch
