# IMPROVEMENTS QUEUE - v1.1

## PRIORITY 1: CRITICAL FIXES (Deploy Tomorrow)

### 1.1 TRUE Bounce Logic
**Current:**
```python
distance = abs(close - ma20) / ma20
if distance <= 0.005 and close >= ma20:
    # Signal
```

**Fix:**
```python
# Check previous or current candle for touch
if candle['low'] <= ma20:
    # Check if close bounced above
    if candle['close'] > ma20:
        # TRUE BOUNCE SIGNAL
```

**Impact:** Should improve win rate (currently detecting false bounces)

---

### 1.2 Efficiency Metric Fix
**Backtest code change:**
```python
# OLD
efficiency = (net_profit / avg_price) × 100

# NEW
total_capital = sum(entry_price × qty for all trades)
efficiency = (net_profit / total_capital) × 100
```

**Action:** Rerun 48-month backtest with correct metric

---

### 1.3 Volume Check
**Add to live bot:**
```python
avg_volume = mean(last 20 candles volume)
if current_volume < avg_volume × 1.2:
    skip  # Weak volume, no trade
```

**Reason:** Backtest has this, live bot doesn't

---

## PRIORITY 2: ENHANCEMENTS (Week 2+)

### 2.1 Daily Trend Filter
**Concept:** Only trade bounces in direction of daily trend
```python
if daily_close > daily_ma50:
    # Uptrend confirmed
    # Allow bounce trades
```

**Benefit:** Avoid counter-trend trades (like BHARTIARTL today)

---

### 2.2 Rich Dashboard
**Current:** Console with flashing updates
**Target:** Static display with smooth cell updates
**Tools:** Rich library (Python)

---

### 2.3 Multi-Candle Bounce
**Current:** Check single candle
**Enhanced:** Check next 3 candles for delayed bounce
```python
if low[i] <= ma20:
    for j in [i, i+1, i+2, i+3]:
        if close[j] > ma20:
            # Bounce confirmed at candle j
```

---

## PRIORITY 3: VALIDATION NEEDED

### 3.1 Fresh 48-Month Backtest
- Use TRUE bounce logic
- Use capital-based efficiency
- Compare results vs v0.9

**Questions to answer:**
- Do results improve with correct logic?
- Which stocks remain top performers?
- What's real monthly efficiency?

---

### 3.2 Stop Loss Optimization
**Current:** 0.5% (assumed good)
**Test:** 0.25%, 0.5%, 0.75%, 1.0%
**Measure:** Impact on loss magnitude vs false exits

---

## TIMELINE

**Tonight:** Code TRUE bounce logic
**Tomorrow AM:** Backtest + compare results
**Tomorrow PM:** Deploy v1.1 if results validate
**Week 2:** Add daily trend filter + Rich UI
**Week 3:** Options strategy integration

---

## OPEN QUESTIONS

1. Should we add daily MA filter? (Prevents counter-trend trades)
2. What's optimal volume multiplier? (Currently 1.2×)
3. Multi-candle check needed? (Check 3 candles for delayed bounce)
4. Position sizing rules? (Currently manual per-signal)
