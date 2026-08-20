# GITHUB COPILOT HANDOVER - YESBANK BACKTEST

## MISSION
Build a Python script that backtests MA bounce strategy on YESBANK 5-min data with 7 trend filters and 3 profit targets.

## INPUT DATA ALREADY AVAILABLE
You have 750 5-min candles from Kite API (Dec 19, 2025 - Jan 2, 2026).
Data format: `{"date":"2025-12-19T09:15:00+05:30","open":21.45,"high":21.65,"low":21.48,"close":21.58,"volume":1672262}`

## DAILY MAs (STATIC PER DAY)
```python
daily_mas = {
    '2025-12-19': {'ma50': 22.58, 'ma100': 21.33, 'ma200': 20.21},
    '2025-12-22': {'ma50': 22.57, 'ma100': 21.36, 'ma200': 20.24},
    '2025-12-23': {'ma50': 22.52, 'ma100': 21.38, 'ma200': 20.27},
    '2025-12-24': {'ma50': 22.48, 'ma100': 21.40, 'ma200': 20.29},
    '2025-12-26': {'ma50': 22.44, 'ma100': 21.43, 'ma200': 20.32},
    '2025-12-29': {'ma50': 22.40, 'ma100': 21.46, 'ma200': 20.34},
    '2025-12-30': {'ma50': 22.37, 'ma100': 21.48, 'ma200': 20.36},
    '2025-12-31': {'ma50': 22.35, 'ma100': 21.51, 'ma200': 20.39},
    '2026-01-01': {'ma50': 22.33, 'ma100': 21.54, 'ma200': 20.41},
    '2026-01-02': {'ma50': 22.32, 'ma100': 21.57, 'ma200': 20.44}
}
```

## BOUNCE DETECTION LOGIC

### Step 1: Calculate MA20 on 5-min chart
```python
# For each candle i (starting from candle 20):
ma20 = sum(last_20_closes) / 20
```

### Step 2: Detect MA20 touch
```python
if candle[i]['low'] <= ma20:
    touch_detected = True
    touch_index = i
```

### Step 3: Confirm bounce within 15 mins (3 candles)
```python
for j in range(touch_index + 1, touch_index + 4):
    threshold = ma20 * 1.01  # 1% above MA20
    breakdown = ma20 * 0.99  # 1% below MA20
    
    if candle[j]['close'] > threshold:
        # BOUNCE CONFIRMED!
        entry_price = candle[j]['close']
        entry_index = j
        break
    elif candle[j]['close'] < breakdown:
        # Breakdown, cancel
        break
```

### Step 4: Check trend filters
For each bounce, test which of 7 filters it passes:

```python
filters = {
    'No Filter': True,  # Always passes
    'MA50': close > daily_mas[date]['ma50'],
    'MA100': close > daily_mas[date]['ma100'],
    'MA200': close > daily_mas[date]['ma200'],
    'MA50+100': close > ma50 and close > ma100,
    'MA50+200': close > ma50 and close > ma200,
    'MA50+100+200': close > ma50 and close > ma100 and close > ma200
}
```

### Step 5: Track outcome for 3 targets
For each bounce entry, watch next 75 candles (1 trading day max):

```python
targets = [1.01, 1.02, 1.03]  # 1%, 2%, 3%
sl = 0.99  # -1% stop loss

for target_pct in targets:
    target_price = entry_price * target_pct
    sl_price = entry_price * sl
    
    for k in range(entry_index + 1, entry_index + 76):
        if candle[k]['high'] >= target_price:
            result[target_pct] = 'WIN'
            break
        elif candle[k]['low'] <= sl_price:
            result[target_pct] = 'LOSS'
            break
```

## OUTPUT FORMAT REQUIRED

```
==========================================================================================
YESBANK BACKTEST RESULTS
Period: Dec 19, 2025 - Jan 2, 2026 (10 trading days)
==========================================================================================

TARGET: 1% (₹0.21 per win, -₹0.21 per loss)
------------------------------------------------------------------------------------------
MVP                  | Trades | Wins | Loss |  Win% |  Net Profit | Rank
------------------------------------------------------------------------------------------
No Filter            |    XX  |  XX  |  XX  |  XX.X | ₹     XX.XX |  X
MA50                 |    XX  |  XX  |  XX  |  XX.X | ₹     XX.XX |  X
MA100                |    XX  |  XX  |  XX  |  XX.X | ₹     XX.XX |  X
MA200                |    XX  |  XX  |  XX  |  XX.X | ₹     XX.XX |  X
MA50+100             |    XX  |  XX  |  XX  |  XX.X | ₹     XX.XX |  X
MA50+200             |    XX  |  XX  |  XX  |  XX.X | ₹     XX.XX |  X
MA50+100+200         |    XX  |  XX  |  XX  |  XX.X | ₹     XX.XX |  X

[Repeat for TARGET: 2% and TARGET: 3%]

==========================================================================================
🏆 ABSOLUTE WINNER
==========================================================================================
Filter: [FILTER_NAME]
Target: [X]%
Net Profit: ₹XX.XX over 10 days
Trades: XX (X.X per day)
Win Rate: XX.X%
==========================================================================================
```

## NET PROFIT CALCULATION
```python
# Assume 1 share per trade, stock price ~₹21.50
win_amount = wins * (stock_price * target_pct - stock_price)  # e.g., 1% = ₹0.215
loss_amount = losses * (stock_price - stock_price * 0.99)     # 1% SL = ₹0.215
net_profit = win_amount - loss_amount
```

## DELIVERABLES
1. Python script: `yesbank_backtest.py`
2. CSV file: `yesbank_5min_candles.csv` (with the 750 candles)
3. Output: Console printout of results table

## IMPORTANT NOTES
- Start MA20 calculation from candle #20 onwards
- Only 1 active trade at a time (no new entries while in trade)
- Extract date from timestamp: `2025-12-19T09:15:00+05:30` → `2025-12-19`
- Bounce window: Max 3 candles (15 mins) to confirm bounce
- Outcome tracking: Max 75 candles (1 day) per trade

## SUCCESS CRITERIA
✅ Script processes all 750 candles
✅ Calculates MA20 correctly (rolling 20)
✅ Detects bounces with proper logic
✅ Tests all 7 filters
✅ Tracks 3 targets independently
✅ Outputs clean formatted table
✅ Shows absolute winner with highest net profit

---
**READY TO CODE!** 🚀
