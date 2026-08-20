# HANDOVER: MA Filter Backtest Project
## Date: January 2, 2026

---

## WHERE WE ARE

### ✅ COMPLETED TODAY
1. **Concept Clarity Achieved**
   - Saurav fully understands the MA filter strategy
   - Daily MA50/100/200 on daily charts = Trend confirmation
   - MA20 bounce on 5-min charts = Entry signal
   - Strategy will work BOTH directions: LONG in uptrends, SHORT in downtrends

2. **Data Collected**
   - YESBANK daily data: 252 days (Jan 2, 2025 → Jan 2, 2026)
   - YESBANK 5-min data: 10 trading days (Dec 22, 2025 → Jan 2, 2026)
   - Saved: `YESBANK_daily_data_252days.csv`

3. **MA Calculations Verified**
   - Current YESBANK price: ₹22.29
   - MA20:  ₹21.74 ✅ PASS (Price above)
   - MA50:  ₹22.32 ❌ FAIL (Price below by ₹0.03)
   - MA100: ₹21.57 ✅ PASS (Price above)
   - MA200: ₹20.44 ✅ PASS (Price above)
   - Trend: 3/4 filters = MODERATE UPTREND

---

## THE 7 FILTER COMBINATIONS TO TEST

We will backtest these filters to find the MVP (best win rate):

1. **No Filter** (v0.8 baseline - trades all MA20 bounces)
2. Price > MA50 only
3. Price > MA100 only
4. Price > MA200 only
5. Price > MA50 + MA100
6. Price > MA50 + MA200
7. Price > MA50 + MA100 + MA200

**Goal:** Find which filter gives **highest win rate** while keeping **enough trading signals**

**Process:**
- Backtest all 7 on 10-day YESBANK data
- Rank them MVP1 to MVP7 (best to worst)
- Forward test MVP3-5 on live data next week
- Validate if backtested win rates match live performance

---

## NEXT SESSION TASKS

### **PRIORITY 1: Generate Full CSV File**

**What we need:**
```
File: YESBANK_5min_with_MA_10days.csv
Rows: ~605 candles (10 trading days × 75 candles/day)
Columns: Date, Time, Open, High, Low, Close, Volume, MA20, MA50, MA100, MA200
```

**How to create it:**
You need a Python script that:
1. Fetches 5-min YESBANK data from Kite (Dec 22 - Jan 2)
2. Loads daily MA lookup from `YESBANK_daily_data_252days.csv`
3. For each 5-min candle:
   - Extract date from timestamp
   - Match to daily MAs for that date
   - Write row with: OHLC + Volume + MA20 + MA50 + MA100 + MA200

**Script structure needed:**
```python
import csv
from datetime import datetime

# 1. Build MA lookup dictionary from daily data
# 2. Fetch 5-min data from Kite API
# 3. For each 5-min candle:
#    - Extract date (e.g., "2025-12-22")
#    - Get MAs from lookup[date]
#    - Write CSV row
# 4. Save as YESBANK_5min_with_MA_10days.csv
```

### **PRIORITY 2: Backtest Analysis**

Once CSV is ready, write backtest script to:
1. Load the CSV
2. For each of the 7 filters:
   - Count total MA20 bounce signals
   - Count how many hit target (+2%)
   - Calculate win rate
3. Rank filters by win rate
4. Output comparison table

**Expected output:**
```
Filter                      | Signals | Wins | Win Rate | Trades/Day
========================== | ======= | ==== | ======== | ==========
No Filter (v0.8)           |   150   |  78  |   52%    |    15
Price > MA50               |   120   |  70  |   58%    |    12
Price > MA50+100           |    90   |  59  |   65%    |     9
Price > MA50+100+200       |    70   |  51  |   73%    |     7  ← MVP1
```

### **PRIORITY 3: Expand to 5 Stocks**

Repeat Priority 1 & 2 for:
- SUZLON
- PNB
- TATASTEEL
- IDEA

Find best filter combination across all stocks.

---

## FILES IN CURRENT DIRECTORY

**Available Now:**
1. `YESBANK_daily_data_252days.csv` - 252 days of daily OHLC + calculated MAs
2. `create_full_csv.py` - Starter script (incomplete, needs full logic)

**To Be Created:**
1. `generate_5min_ma_data.py` - Complete script to create the CSV
2. `YESBANK_5min_with_MA_10days.csv` - The 605-row dataset
3. `backtest_ma_filters.py` - Script to test all 7 filter combinations
4. `filter_results.csv` - Comparison table of all 7 filters

---

## TECHNICAL NOTES

### MA Calculation Logic
```python
def get_ma_at_date(daily_data, target_date, period):
    # Find index of target_date in daily_data
    for i, d in enumerate(daily_data):
        if d['date'] == target_date:
            if i < period - 1:
                return None
            # Calculate MA using previous 'period' days including today
            closes = [daily_data[j]['close'] for j in range(i - period + 1, i + 1)]
            return round(sum(closes) / len(closes), 2)
    return None
```

### Filter Check Logic
```python
# Example: Filter 5 (MA50 + MA100)
def check_filter_5(price, ma50, ma100):
    return price > ma50 and price > ma100
```

### MA20 Bounce Detection (5-min chart)
```python
# Need to implement:
# 1. Price touches/crosses below MA20
# 2. Next candle closes above MA20
# 3. That's a bounce signal
```

---

## KEY INSIGHTS FROM TODAY

1. **Token Efficiency:** Creating CSV in script = 160x more efficient than in chat
2. **Data Quality:** YESBANK has good volume (avg 50M+ per candle)
3. **Trend Validation:** Current price fails MA50 by tiny margin (₹0.03), but passes MA100/200
4. **Strategy Evolution:** v0.8 → v0.9 will add trend filters + ability to go SHORT

---

## IMPORTANT REMINDERS

1. **No MA20 on 5-min chart:** We only use MA20/50/100/200 from DAILY charts
2. **Bounce = Entry signal:** MA20 bounce on 5-min triggers trade
3. **Filters = Trend confirmation:** MA50/100/200 on daily charts confirm trend direction
4. **Goal = Win rate improvement:** From v0.8's ~50% to v0.9's target 70%+

---

## KITE API DETAILS

**Instrument Token:** YESBANK = 3050241

**API Call for 5-min data:**
```python
kite.get_historical_data(
    instrument_token=3050241,
    from_date="2025-12-20 09:15:00",
    to_date="2026-01-02 15:30:00",
    interval="5minute"
)
```

**Returns:** List of dicts with keys: date, open, high, low, close, volume, oi

---

## SUCCESS CRITERIA

**Phase 1 (Next Session):**
- ✅ CSV file with 605 rows created
- ✅ Backtest script working for all 7 filters
- ✅ MVP filter identified for YESBANK

**Phase 2 (After that):**
- ✅ Repeat for all 5 stocks
- ✅ Find universal best filter OR stock-specific filters
- ✅ Integrate into MA Bounce Bot v0.9

**Phase 3 (Live validation):**
- ✅ Deploy v0.9 with MVP filter
- ✅ Run for 5-10 days
- ✅ Compare backtested vs live win rates
- ✅ If match → Success! If not → adjust

---

## QUESTIONS TO ASK NEXT SESSION

1. Did you successfully create the CSV file?
2. What were the backtest results for all 7 filters?
3. Which filter gave the best win rate?
4. How many trades per day does the MVP filter generate?
5. Is the win rate improvement significant enough (>60%)?

---

## ARCHITECTURE NOTES

**Current Bot (v0.8):**
- Only LONG trades
- No trend filter (trades any MA20 touch)
- Win rate: ~50-55%

**Target Bot (v0.9):**
- LONG in uptrends, SHORT in downtrends
- Daily MA filters confirm trend
- MA20 bounce on 5-min = entry
- Target win rate: 70%+

**Logic Flow:**
```
1. Check daily MAs → Determine trend (UP/DOWN/NEUTRAL)
2. If UPTREND → Look for MA20 bounce UP (BUY signal)
3. If DOWNTREND → Look for MA20 bounce DOWN (SELL signal)
4. If NEUTRAL → Skip trade
5. Execute trade with 2% target, 1% SL
```

---

## END OF HANDOVER

**Status:** Ready for next session
**Next Milestone:** Complete CSV + Backtest results
**Long-term Goal:** 70% win rate → ₹40K/month income

🎯 **LET'S BUILD v0.9!** 🚀

---

**Files to preserve for next session:**
1. YESBANK_daily_data_252days.csv (already created)
2. This handover document
3. Kite login credentials ready
4. Python environment with required libraries (csv, datetime, requests)
