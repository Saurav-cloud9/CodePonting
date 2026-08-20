# GITHUB COPILOT TRAINING ROADMAP
**For: Algorithmic Trading Bot Development**  
**Level: Beginner to Intermediate Python**  
**Focus: Building towards MA Bounce Bot skills**

---

## 📋 COPY THIS TO GITHUB COPILOT

```
I'm learning Python for algorithmic trading. I need 
progressive challenges that build trading bot skills. 
Start SIMPLE, then gradually add complexity.

PHASE 1: FOUNDATIONS (Lists, Dicts, Loops)
==========================================
Create challenges around:
- Working with lists of numbers (stock prices)
- Dictionaries with keys like 'open', 'high', 
  'low', 'close', 'volume'
- Looping through data
- Calculating averages (moving averages)
- Finding max/min values

Example starter: 
"Create a list of 20 stock prices. Calculate the 
average of the last 10 prices."

Then make it harder:
"Now do it with a list of dictionaries where each 
has 'timestamp' and 'close' keys."

PHASE 2: FUNCTIONS & DATA CONVERSION
=====================================
Build towards:
- Converting data formats (arrays to dictionaries)
- Grouping data (1-min candles → 5-min candles)
- Nested loops and conditionals
- Return values and error handling

Example challenge:
"Given 100 one-minute candles, group every 5 into 
proper OHLC 5-minute candles."

PHASE 3: API INTERACTIONS (MOCK DATA)
======================================
Use mock API responses:
- Parse JSON-like dictionaries
- Navigate nested data structures
- Handle status codes (200 = success, 400 = error)
- Extract specific data from complex responses

Example mock data:
{
  'status': 'success',
  'data': {
    'candles': [[timestamp, open, high, low, 
                 close, volume], ...]
  }
}

Challenge: "Extract all 'close' prices from this 
mock API response."

PHASE 4: TRADING LOGIC
======================
Implement simple strategies:
- Detect when price crosses above/below MA
- Identify volume spikes (current > 2x average)
- Check volatility (range comparison)
- Combine conditions with AND/OR logic

Example:
"Write a function that returns True if price is 
within 0.5% of MA20 AND price > MA20."

PHASE 5: MINI BOT
=================
Combine everything:
- Fetch mock data (simulate API call)
- Calculate indicators
- Generate buy/sell signals
- Track a simple position

Final challenge:
"Build a simple MA bounce detector that scans a 
list of stocks and returns which ones have buy 
signals."

========================================
RULES FOR ALL CHALLENGES:
========================================
1. Start SIMPLEST version (hardcoded data)
2. Add ONE new concept at a time
3. Include clear test cases with expected output
4. Build on previous challenges 
5. Use trading terminology (candles, OHLC, 
   volume, MA)
6. Explain what real-world trading concept each 
   challenge teaches

AVOID:
- Complex math libraries initially 
  (numpy, pandas)
- Real API calls (use mock data)
- Object-oriented programming 
  (keep it functional)
- Advanced topics like threading, async

START HERE:
Give me Challenge #1 for PHASE 1. Make it simple 
but relevant to trading.
```

---

## 🎯 EXAMPLE CHALLENGE PROGRESSION

### **PHASE 1: FOUNDATIONS**

#### **Challenge 1: Calculate Average Price**

```python
# Given: List of 10 closing prices
prices = [52.00, 52.50, 51.80, 52.20, 52.60, 
          51.90, 52.30, 52.80, 52.10, 52.40]

# Task: Calculate the average price
# Expected output: 52.26

# Your code here:




# Solution:
total = sum(prices)
average = total / len(prices)
print(f"Average: ₹{average:.2f}")
```

**What it teaches:** 
- Using sum() and len()
- Basic list operations
- f-string formatting with decimal places

---

#### **Challenge 2: Find Highest and Lowest**

```python
# Given: List of 10 closing prices
prices = [52.00, 52.50, 51.80, 52.20, 52.60, 
          51.90, 52.30, 52.80, 52.10, 52.40]

# Task: Find the highest and lowest price
# Expected output: High: 52.80, Low: 51.80

# Your code here:




# Solution:
highest = max(prices)
lowest = min(prices)
print(f"High: ₹{highest}, Low: ₹{lowest}")
```

**What it teaches:**
- max() and min() functions
- Working with list data

---

#### **Challenge 3: Calculate Moving Average**

```python
# Given: 20 stock prices
prices = [50.0, 51.0, 52.0, 51.5, 52.0, 
          52.5, 53.0, 52.8, 52.9, 53.1,
          53.2, 53.0, 52.8, 53.2, 53.5, 
          53.3, 53.4, 53.6, 53.5, 53.7]

# Task: Calculate MA of last 10 prices
# Expected output: 53.16

# Your code here:




# Solution:
last_10 = prices[-10:]  # Get last 10
ma10 = sum(last_10) / len(last_10)
print(f"MA 10: ₹{ma10:.2f}")
```

**What it teaches:**
- Negative indexing and slicing
- Moving average concept
- Real trading indicator!

---

#### **Challenge 4: Work with Dictionary**

```python
# Given: A candle as a dictionary
candle = {
    'timestamp': '9:15',
    'open': 52.00,
    'high': 52.50,
    'low': 51.80,
    'close': 52.20,
    'volume': 125000
}

# Task: Calculate the range (high - low)
# Expected output: 0.70

# Your code here:




# Solution:
candle_range = candle['high'] - candle['low']
print(f"Range: ₹{candle_range:.2f}")
```

**What it teaches:**
- Dictionary key access
- OHLC candle structure
- Range = volatility measure

---

#### **Challenge 5: Loop Through Candles**

```python
# Given: List of candles
candles = [
    {'open': 52.00, 'high': 52.10, 
     'low': 51.95, 'close': 52.05, 
     'volume': 10000},
    {'open': 52.05, 'high': 52.15, 
     'low': 52.00, 'close': 52.10, 
     'volume': 12000},
    {'open': 52.10, 'high': 52.20, 
     'low': 52.05, 'close': 52.15, 
     'volume': 11000},
]

# Task: Calculate average volume 
# across all candles
# Expected output: 11000

# Your code here:




# Solution:
total_volume = 0
for candle in candles:
    total_volume += candle['volume']

avg_volume = total_volume / len(candles)
print(f"Average Volume: {avg_volume:,.0f}")
```

**What it teaches:**
- Looping through list of dictionaries
- Accumulator pattern
- Volume analysis basics

---

### **PHASE 2: DATA CONVERSION**

#### **Challenge 6: Convert Array to Dictionary**

```python
# Given: Candles as arrays (API format)
candles_raw = [
    ['9:15', 52.00, 52.10, 51.95, 52.05, 10000],
    ['9:16', 52.05, 52.15, 52.00, 52.10, 12000],
    ['9:17', 52.10, 52.20, 52.05, 52.15, 11000],
]

# Task: Convert to list of dictionaries 
# with keys: 'timestamp', 'open', 'high', 
# 'low', 'close', 'volume'

# Expected output:
# [
#   {'timestamp': '9:15', 'open': 52.00, 
#    'high': 52.10, 'low': 51.95, 
#    'close': 52.05, 'volume': 10000},
#   ...
# ]

# Your code here:




# Solution:
candles = []
for raw in candles_raw:
    candle = {
        'timestamp': raw[0],
        'open': raw[1],
        'high': raw[2],
        'low': raw[3],
        'close': raw[4],
        'volume': raw[5]
    }
    candles.append(candle)

print(candles)
```

**What it teaches:**
- Data format conversion
- EXACTLY what your bot does with API data!
- Building dictionaries programmatically

---

#### **Challenge 7: Group Candles (1min → 5min)**

```python
# Given: 15 one-minute candles
candles_1min = [
    {'open': 52.00, 'high': 52.05, 'low': 51.95, 
     'close': 52.02, 'volume': 1000},
    {'open': 52.02, 'high': 52.08, 'low': 52.00, 
     'close': 52.05, 'volume': 1200},
    {'open': 52.05, 'high': 52.10, 'low': 52.03, 
     'close': 52.08, 'volume': 1100},
    {'open': 52.08, 'high': 52.15, 'low': 52.05, 
     'close': 52.12, 'volume': 1300},
    {'open': 52.12, 'high': 52.18, 'low': 52.10, 
     'close': 52.15, 'volume': 1400},
    # ... 10 more candles
]

# Task: Group every 5 candles into one 5-min 
# OHLC candle
# Rules:
# - Open = first candle's open
# - High = max of all highs
# - Low = min of all lows
# - Close = last candle's close
# - Volume = sum of all volumes

# Expected: 3 five-minute candles

# Your code here:




# Solution:
candles_5min = []

for i in range(0, len(candles_1min), 5):
    group = candles_1min[i:i+5]
    
    if len(group) == 5:
        candle_5min = {
            'open': group[0]['open'],
            'high': max(c['high'] for c in group),
            'low': min(c['low'] for c in group),
            'close': group[-1]['close'],
            'volume': sum(c['volume'] for c in group)
        }
        candles_5min.append(candle_5min)

print(f"Created {len(candles_5min)} 5-min candles")
```

**What it teaches:**
- Exactly what convert_to_5min_candles() does!
- Grouping data with range(start, end, step)
- OHLC aggregation logic

---

### **PHASE 3: MOCK API INTERACTIONS**

#### **Challenge 8: Parse Mock API Response**

```python
# Mock API response (like Upstox returns)
response = {
    'status': 'success',
    'data': {
        'candles': [
            ['2025-12-21T09:15:00', 52.00, 52.10, 
             51.95, 52.05, 10000, 0],
            ['2025-12-21T09:16:00', 52.05, 52.15, 
             52.00, 52.10, 12000, 0],
            ['2025-12-21T09:17:00', 52.10, 52.20, 
             52.05, 52.15, 11000, 0],
        ]
    }
}

# Task 1: Check if API call succeeded
# Task 2: Extract all close prices
# Expected: [52.05, 52.10, 52.15]

# Your code here:




# Solution:
if response['status'] == 'success':
    candles_raw = response['data']['candles']
    
    close_prices = []
    for candle in candles_raw:
        close_prices.append(candle[4])  # Index 4 = close
    
    print(f"Close prices: {close_prices}")
else:
    print("API call failed!")
```

**What it teaches:**
- Navigating nested dictionaries
- Checking status codes
- Extracting data from API responses

---

### **PHASE 4: TRADING LOGIC**

#### **Challenge 9: Detect MA Bounce**

```python
# Given: Current price and MA20
current_price = 52.15
ma20 = 52.00
threshold_pct = 0.5  # 0.5%

# Task: Return True if:
# 1. Price is within 0.5% of MA20
# 2. Price is above or equal to MA20

# Expected: True (bounce detected!)

# Your code here:




# Solution:
def check_bounce(price, ma, threshold_pct):
    # Calculate dynamic threshold
    threshold = price * (threshold_pct / 100)
    
    # Calculate distance from MA
    distance = abs(price - ma)
    
    # Check conditions
    if price >= ma and distance <= threshold:
        return True
    return False

result = check_bounce(current_price, ma20, 
                      threshold_pct)
print(f"Bounce detected: {result}")
```

**What it teaches:**
- Your actual MA bounce logic!
- Percentage-based thresholds
- Boolean return values

---

#### **Challenge 10: Volume Spike Detection**

```python
# Given: Current and historical volumes
volumes = [10000, 12000, 11000, 13000, 14000]
current_volume = 28000

# Task: Return True if current volume is 
# 2x the average of previous volumes

# Expected: True (28000 > 2 × 12000)

# Your code here:




# Solution:
def detect_volume_spike(current, historical, 
                        multiplier=2.0):
    avg_volume = sum(historical) / len(historical)
    
    if current >= (avg_volume * multiplier):
        return True
    return False

result = detect_volume_spike(current_volume, 
                             volumes)
print(f"Volume spike: {result}")
print(f"Current: {current_volume:,}, "
      f"Average: {sum(volumes)/len(volumes):,.0f}")
```

**What it teaches:**
- Your volume spike detection!
- Comparing current vs historical
- Using multipliers

---

#### **Challenge 11: Combine Multiple Signals**

```python
# Given: Multiple indicators
price = 52.15
ma20 = 52.00
current_volume = 28000
avg_volume = 12000
is_uptrend = True  # Price rising

# Task: Generate BUY signal if:
# - (Volume spike OR high activity) 
# - AND uptrend

# Where:
# - Volume spike = current > 2x average
# - Uptrend = True

# Expected: True (BUY signal!)

# Your code here:




# Solution:
def generate_signal(price, ma, curr_vol, 
                   avg_vol, is_uptrend):
    # Check volume spike
    has_vol_spike = curr_vol >= (avg_vol * 2)
    
    # Signal logic
    if has_vol_spike and is_uptrend:
        return "BUY"
    return "WAIT"

signal = generate_signal(price, ma20, 
                        current_volume, 
                        avg_volume, is_uptrend)
print(f"Signal: {signal}")
```

**What it teaches:**
- Your late scalp logic!
- Combining multiple conditions
- AND/OR boolean logic

---

### **PHASE 5: MINI BOT**

#### **Challenge 12: Simple Stock Scanner**

```python
# Mock stock data
stocks = [
    {
        'symbol': 'YESBANK',
        'price': 20.15,
        'ma20': 20.00,
        'volume': 200000,
        'avg_volume': 100000
    },
    {
        'symbol': 'SUZLON',
        'price': 52.80,
        'ma20': 52.00,
        'volume': 150000,
        'avg_volume': 120000
    },
    {
        'symbol': 'RPOWER',
        'price': 15.20,
        'ma20': 15.50,
        'volume': 180000,
        'avg_volume': 100000
    },
]

# Task: Scan all stocks and return list of 
# stocks with BUY signals
# BUY if:
# 1. Price within 0.5% of MA20
# 2. Price >= MA20
# 3. Volume > 1.5x average

# Expected: ['YESBANK', 'SUZLON']

# Your code here:




# Solution:
def scan_stocks(stocks):
    buy_signals = []
    
    for stock in stocks:
        # Calculate threshold
        threshold = stock['price'] * 0.005
        distance = abs(stock['price'] - stock['ma20'])
        
        # Check conditions
        near_ma = distance <= threshold
        above_ma = stock['price'] >= stock['ma20']
        vol_spike = stock['volume'] > (stock['avg_volume'] * 1.5)
        
        if near_ma and above_ma and vol_spike:
            buy_signals.append(stock['symbol'])
            print(f"✅ {stock['symbol']}: "
                  f"Price: ₹{stock['price']}, "
                  f"MA: ₹{stock['ma20']}")
    
    return buy_signals

signals = scan_stocks(stocks)
print(f"\nBuy signals: {signals}")
```

**What it teaches:**
- THIS IS YOUR ACTUAL BOT!
- Scanning multiple stocks
- Applying strategy logic
- Filtering for signals

---

## 🎮 GAMIFICATION: NUMBER GUESSING → TRADING BOT

### **Level 1: Basic Guessing Game**

```python
secret_number = 42
guess = int(input("Guess the number (1-100): "))

if guess == secret_number:
    print("🎉 Correct!")
elif guess < secret_number:
    print("📈 Too low!")
else:
    print("📉 Too high!")
```

---

### **Level 2: Stock Direction Game**

```python
# Instead of numbers, guess stock direction!

current_price = 52.00
ma20 = 51.50

user_guess = input("Will stock go UP or DOWN? "
                   ).upper()

# Trading logic: price > MA = likely UP
actual = "UP" if current_price > ma20 else "DOWN"

if user_guess == actual:
    print(f"✅ Correct! Price: ₹{current_price}, "
          f"MA: ₹{ma20}")
else:
    print(f"❌ Wrong! Since price > MA, "
          f"direction is {actual}")
```

---

### **Level 3: Add Volume Check**

```python
current_price = 52.00
ma20 = 51.50
current_volume = 200000
avg_volume = 100000

user_guess = input("BUY or WAIT? ").upper()

# Complex logic
vol_spike = current_volume > (avg_volume * 2)
price_above = current_price > ma20

if vol_spike and price_above:
    actual = "BUY"
else:
    actual = "WAIT"

if user_guess == actual:
    print(f"✅ Correct!")
    print(f"Volume spike: {vol_spike}, "
          f"Price > MA: {price_above}")
else:
    print(f"❌ Wrong! Signal: {actual}")
```

---

### **Level 4: Turn It Into a Function**

```python
def check_trading_signal(price, ma, volume, 
                        avg_vol):
    """Returns 'BUY' or 'WAIT'"""
    
    # Calculate conditions
    distance = abs(price - ma)
    threshold = price * 0.005
    
    near_ma = distance <= threshold
    above_ma = price >= ma
    vol_spike = volume >= (avg_vol * 2)
    
    # Decision logic
    if near_ma and above_ma and vol_spike:
        return "BUY"
    
    return "WAIT"

# Test it!
signal = check_trading_signal(52.15, 52.00, 
                              200000, 100000)
print(f"Signal: {signal}")
```

**CONGRATULATIONS!** You just built trading bot logic! 🎯

---

## 📚 LEARNING TIPS

**Practice Order:**
1. Do challenges in sequence (don't skip!)
2. Try solving before looking at solution
3. Understand WHY, not just HOW
4. Modify challenges (change numbers, add features)
5. Build confidence, then move to next phase

**When Stuck:**
- Break problem into smaller steps
- Use print() to see what's happening
- Google specific Python functions
- Ask Copilot for hints, not full solutions

**Key Concepts to Master:**
- Lists and dictionaries
- Loops (for, while)
- Conditionals (if, elif, else)
- Functions (def, return)
- String formatting (f-strings)
- Basic math operations
- Boolean logic (and, or, not)

---

## 🎯 END GOAL

After completing all phases, you'll be able to:

✅ Read and understand your MA Bounce Bot code  
✅ Modify trading logic confidently  
✅ Debug issues independently  
✅ Add new features to your bot  
✅ Build new trading strategies from scratch  

**START WITH CHALLENGE #1 AND BUILD UP!**

Good luck! 🚀
