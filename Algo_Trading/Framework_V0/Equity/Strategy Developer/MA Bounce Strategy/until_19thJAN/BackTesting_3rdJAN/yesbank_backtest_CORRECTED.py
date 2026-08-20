"""
╔═══════════════════════════════════════════════════════════════╗
║      MA BOUNCE BACKTEST v1.0 - CORRECTED & COMPLETE          ║
╚═══════════════════════════════════════════════════════════════╝

BACKTEST STRUCTURE:
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│  STEP 1: DATA PREPARATION                                   │
├─────────────────────────────────────────────────────────────┤
│ • Fetch 1-min candles from Upstox (Dec 19-Jan 2, 2026)     │
│ • Resample to 5-min candles                                 │
│ • Result: 75 candles/day × 10 days = 750 total             │
│ • Calculate MA20 on 5-min chart (rolling 20 closes)        │
│ • Load daily MAs (MA50/100/200) - hardcoded by date        │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: FILTER CHECK (DO THIS FIRST!)                      │
├─────────────────────────────────────────────────────────────┤
│ FOR each candle i (from candle #20 onwards):                │
│   Get daily MAs for this date                               │
│   Test which of 8 filters pass:                             │
│     1. No Filter (always TRUE)                              │
│     2. close > MA50                                         │
│     3. close > MA100                                        │
│     4. close > MA200                                        │
│     5. close > MA50 AND MA100                               │
│     6. close > MA50 AND MA200                               │
│     7. close > MA100 AND MA200                              │
│     8. close > MA50 AND MA100 AND MA200                     │
│   IF no filters pass: SKIP (no uptrend)                     │
│   ELSE: Proceed to bounce detection                         │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: BOUNCE DETECTION (OPTION 3 - SIMPLE)              │
├─────────────────────────────────────────────────────────────┤
│ (Only on candles that passed filter check)                  │
│                                                              │
│ ✅ TOUCH: IF low[i] <= ma20[i]                              │
│                                                              │
│ ✅ BOUNCE CHECK (Current candle FIRST):                     │
│    IF close[i] > ma20[i]:                                   │
│       ✅ IMMEDIATE BOUNCE at candle i                       │
│    ELSE:                                                     │
│       Check next 3 candles (i+1, i+2, i+3):                │
│       IF close[j] > ma20[i]:                                │
│          ✅ DELAYED BOUNCE at candle j                      │
│                                                              │
│ ✅ VOLUME CONFIRMATION:                                     │
│    avg_volume = avg(volume[i-19 to i-1])                   │
│    IF volume[entry_candle] > avg_volume × 1.5:             │
│       ✅ VOLUME CONFIRMED - Valid bounce!                   │
│    ELSE:                                                     │
│       ❌ Skip (weak volume)                                 │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: OUTCOME TRACKING (3 TARGETS)                       │
├─────────────────────────────────────────────────────────────┤
│ FOR each filter that passed:                                │
│                                                              │
│ Test 3 profit targets:                                      │
│  • 0.5% → target = entry × 1.005                            │
│  • 1.0% → target = entry × 1.01                             │
│  • 1.5% → target = entry × 1.015                            │
│                                                              │
│ Stop Loss: 0.5% → sl = entry × 0.995                        │
│                                                              │
│ Track next 75 candles from entry:                           │
│  FOR k = entry_index+1 to min(entry_index+76, len(df)):    │
│    IF high[k] >= target: WIN! (profit = target - entry)    │
│    IF low[k] <= sl: LOSS! (loss = entry - sl)              │
│  IF no hit: LOSS (timeout)                                  │
│                                                              │
│ NET PROFIT = (Wins × Profit_per_win) - (Losses × Loss_per_SL)            │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: RESULTS (8 Filters × 3 Targets = 24 Scenarios)    │
├─────────────────────────────────────────────────────────────┤
│ Display results by target:                                  │
│  • Filter | Trades | Wins | Loss | Win% | Net Profit       │
│  • Rank by Net Profit within each target                   │
│                                                              │
│ Find absolute winner:                                       │
│  • Highest Net Profit across all 24 scenarios               │
│  • Show scaling potential (monthly projection)              │
└─────────────────────────────────────────────────────────────┘

KEY FIXES FROM PREVIOUS VERSION:
═════════════════════════════════════════════════════════════
✅ Filter check BEFORE bounce detection (efficiency)
✅ Current candle bounce check added
✅ Threshold = close > ma20 (NO 1% buffer)
✅ Volume confirmation (1.5× avg volume)
✅ Targets = 0.5%, 1%, 1.5% (not 1%, 2%, 3%)
✅ Stop Loss = 0.5% (not 1%)
✅ 8 filters (added MA100+200)
✅ 24 scenarios total

DATA SOURCES:
═════════════════════════════════════════════════════════════
• Upstox API: 1-min historical candles
• Resampled to: 5-min OHLCV
• Period: Dec 19, 2025 - Jan 2, 2026 (10 trading days)
• Holidays: 2025/2026 NSE calendar
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

# ═════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════

# Upstox API
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTU4YmM2NGMzMjIxYTZiYWQxZjBjNjAiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NzQyMzA3NiwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY3NDc3NjAwfQ.17-2UVndUsUYIMN9oPktG_rfGKkPl9M9LVACB8ZeUsY"
BASE_URL = "https://api.upstox.com/v2"
INSTRUMENT_KEY = "NSE_EQ|INE528G01035"  # YESBANK

# Date range
FROM_DATE = "2025-12-19"
TO_DATE = "2026-01-02"

# Daily MAs (hardcoded)
DAILY_MAS = {
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

# NSE Holidays (2025-2026)
NSE_HOLIDAYS = [
    '2025-01-26', '2025-02-26', '2025-03-14', '2025-03-31',
    '2025-04-10', '2025-04-14', '2025-04-18', '2025-05-01',
    '2025-08-15', '2025-08-27', '2025-10-02', '2025-10-21',
    '2025-10-22', '2025-11-01', '2025-11-05', '2025-12-25',
    '2026-01-26', '2026-03-03', '2026-03-31', '2026-04-02',
    '2026-04-06', '2026-04-10', '2026-04-14', '2026-05-01'
]

# Strategy Parameters
TARGETS = [0.005, 0.01, 0.015]  # 0.5%, 1%, 1.5%
STOP_LOSS = 0.005  # 0.5%
VOLUME_MULTIPLIER = 1.5  # Volume confirmation threshold

# Filter names
FILTER_NAMES = [
    'No Filter',
    'MA50',
    'MA100', 
    'MA200',
    'MA50+100',
    'MA50+200',
    'MA100+200',
    'MA50+100+200'
]

# ═════════════════════════════════════════════════════════════
# DATA FETCHING
# ═════════════════════════════════════════════════════════════

def fetch_upstox_data():
    """Fetch 1-min data from Upstox and resample to 5-min"""
    print("\n" + "="*90)
    print("FETCHING DATA FROM UPSTOX API")
    print("="*90)
    
    url = f"{BASE_URL}/historical-candle/{INSTRUMENT_KEY}/1minute/{TO_DATE}/{FROM_DATE}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    
    print(f"→ Endpoint: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"✗ API Error: {response.status_code}")
            print(f"  Response: {response.text}")
            sys.exit(1)
        
        data = response.json()
        
        if data.get('status') != 'success':
            print(f"✗ API returned error: {data}")
            sys.exit(1)
        
        # Parse candles
        candles_raw = data['data']['candles']
        
        df = pd.DataFrame(candles_raw, columns=['date', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"✓ Fetched {len(df)} 1-min candles")
        
        # Resample to 5-min
        df_5min = df.set_index('date').resample('5min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna().reset_index()
        
        print(f"✓ Resampled to {len(df_5min)} 5-min candles")
        
        return df_5min
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

# ═════════════════════════════════════════════════════════════
# BACKTEST ENGINE
# ═════════════════════════════════════════════════════════════

def run_backtest(df):
    """Main backtest logic"""
    
    print("\n" + "="*90)
    print("RUNNING BACKTEST")
    print("="*90)
    
    # Calculate MA20
    df['ma20'] = df['close'].rolling(20).mean()
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
    
    # Calculate average volume (for confirmation)
    df['avg_volume'] = df['volume'].rolling(20).mean()
    
    # Results structure: {filter: {target: {trades, wins, losses, net}}}
    results = {
        f: {t: {'trades': 0, 'wins': 0, 'losses': 0, 'net': 0.0} for t in TARGETS}
        for f in FILTER_NAMES
    }
    
    bounces_detected = 0
    bounces_volume_confirmed = 0
    
    # Loop through candles (start from candle 20 - first valid MA20)
    for i in range(20, len(df)):
        
        # Get current candle data
        low = df.at[i, 'low']
        close = df.at[i, 'close']
        ma20 = df.at[i, 'ma20']
        date_str = df.at[i, 'date_str']
        
        # Skip if MA20 not available
        if pd.isna(ma20):
            continue
        
        # STEP 2: FILTER CHECK FIRST
        daily = DAILY_MAS.get(date_str)
        if not daily:
            continue  # No daily MA data for this date
        
        ma50 = daily['ma50']
        ma100 = daily['ma100']
        ma200 = daily['ma200']
        
        # Check which filters pass
        filters_passed = {
            'No Filter': True,
            'MA50': close > ma50,
            'MA100': close > ma100,
            'MA200': close > ma200,
            'MA50+100': close > ma50 and close > ma100,
            'MA50+200': close > ma50 and close > ma200,
            'MA100+200': close > ma100 and close > ma200,
            'MA50+100+200': close > ma50 and close > ma100 and close > ma200
        }
        
        # If no filters pass (except No Filter), skip
        if not any(filters_passed.values()):
            continue
        
        # STEP 3: BOUNCE DETECTION
        
        # Touch check
        if low > ma20:
            continue  # No touch
        
        # Bounce detected at touch
        bounces_detected += 1
        
        # Check bounce confirmation
        bounce_confirmed = False
        entry_price = None
        entry_index = None
        
        # Check CURRENT candle first (i)
        if close > ma20:
            bounce_confirmed = True
            entry_price = close
            entry_index = i
        else:
            # Check next 3 candles (i+1, i+2, i+3)
            for j in range(i+1, min(i+4, len(df))):
                close_j = df.at[j, 'close']
                breakdown = ma20 * 0.99
                
                if close_j > ma20:
                    bounce_confirmed = True
                    entry_price = close_j
                    entry_index = j
                    break
                
                if close_j < breakdown:
                    break  # Breakdown, cancel
        
        if not bounce_confirmed:
            continue
        
        # Volume confirmation
        avg_vol = df.at[entry_index, 'avg_volume']
        entry_vol = df.at[entry_index, 'volume']
        
        if pd.isna(avg_vol) or entry_vol < avg_vol * VOLUME_MULTIPLIER:
            continue  # Weak volume
        
        bounces_volume_confirmed += 1
        
        # STEP 4: OUTCOME TRACKING
        
        # For each filter that passed
        for filter_name, passed in filters_passed.items():
            if not passed:
                continue
            
            # For each target
            for target_pct in TARGETS:
                results[filter_name][target_pct]['trades'] += 1
                
                target_price = entry_price * (1 + target_pct)
                sl_price = entry_price * (1 - STOP_LOSS)
                
                # Track next 75 candles
                outcome = None
                for k in range(entry_index + 1, min(entry_index + 76, len(df))):
                    if df.at[k, 'high'] >= target_price:
                        outcome = 'WIN'
                        break
                    if df.at[k, 'low'] <= sl_price:
                        outcome = 'LOSS'
                        break
                
                # Calculate P&L
                if outcome == 'WIN':
                    results[filter_name][target_pct]['wins'] += 1
                    profit = target_price - entry_price
                    results[filter_name][target_pct]['net'] += profit
                else:  # LOSS or timeout
                    results[filter_name][target_pct]['losses'] += 1
                    loss = entry_price - sl_price
                    results[filter_name][target_pct]['net'] -= loss
    
    print(f"✓ Bounces detected (touch): {bounces_detected}")
    print(f"✓ Bounces volume-confirmed: {bounces_volume_confirmed}")
    
    return results

# ═════════════════════════════════════════════════════════════
# RESULTS DISPLAY
# ═════════════════════════════════════════════════════════════

def display_results(results):
    """Display backtest results in formatted tables"""
    
    print("\n" + "="*90)
    print("YESBANK MA BOUNCE BACKTEST - RESULTS")
    print("Period: Dec 19, 2025 - Jan 2, 2026 (10 trading days, ~750 5-min candles)")
    print("="*90)
    
    stock_price = 21.50  # Approximate average
    
    # Track absolute winner
    abs_winner = {'filter': None, 'target': 0, 'net': -999999}
    
    for target_pct in TARGETS:
        target_name = f"{target_pct*100:.1f}%"
        per_win = stock_price * target_pct
        per_loss = stock_price * STOP_LOSS
        
        print(f"\nTARGET: {target_name} (₹{per_win:.2f} per win, ₹{per_loss:.2f} per loss)")
        print("-"*90)
        print(f"{'Filter':<16} | {'Trades':>6} | {'Wins':>4} | {'Loss':>4} | {'Win%':>5} | {'Net Profit':>11} | Rank")
        print("-"*90)
        
        # Sort by net profit
        sorted_results = sorted(
            [(f, results[f][target_pct]) for f in FILTER_NAMES],
            key=lambda x: x[1]['net'],
            reverse=True
        )
        
        for rank, (filter_name, stats) in enumerate(sorted_results, 1):
            trades = stats['trades']
            wins = stats['wins']
            losses = stats['losses']
            net = stats['net']
            
            win_pct = (wins / trades * 100) if trades > 0 else 0.0
            
            # Track absolute winner
            if net > abs_winner['net']:
                abs_winner = {'filter': filter_name, 'target': target_pct, 'net': net, 
                             'trades': trades, 'wins': wins, 'losses': losses, 'win_pct': win_pct}
            
            if trades == 0:
                print(f"{filter_name:<16} | {trades:>6} | {wins:>4} | {losses:>4} | {'N/A':>5} | ₹{net:>10.2f} | N/A")
            else:
                print(f"{filter_name:<16} | {trades:>6} | {wins:>4} | {losses:>4} | {win_pct:>5.1f} | ₹{net:>10.2f} | {rank}")
    
    # Display absolute winner
    print("\n" + "="*90)
    print("🏆 ABSOLUTE WINNER (Highest Net Profit Across All 24 Scenarios)")
    print("="*90)
    print(f"Filter: {abs_winner['filter']}")
    print(f"Target: {abs_winner['target']*100:.1f}%")
    print(f"Net Profit: ₹{abs_winner['net']:.2f} (10 days, 1 share)")
    print(f"Trades: {abs_winner['trades']} (Win Rate: {abs_winner['win_pct']:.1f}%)")
    print("="*90)
    
    # Scaling potential
    print("\nSCALING POTENTIAL (Monthly projection assuming ~22 trading days):")
    monthly_profit_1 = abs_winner['net'] * 2.2
    print(f"•    1 share: ₹{monthly_profit_1:.2f}/month")
    print(f"•  100 shares: ₹{monthly_profit_1 * 100:,.2f}/month")
    print(f"•  500 shares: ₹{monthly_profit_1 * 500:,.2f}/month")
    print(f"• 1000 shares: ₹{monthly_profit_1 * 1000:,.2f}/month")
    print("="*90)

# ═════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════

def main():
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║      MA BOUNCE BACKTEST v1.0 - YESBANK ANALYSIS              ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    # Fetch data
    df = fetch_upstox_data()
    
    # Run backtest
    results = run_backtest(df)
    
    # Display results
    display_results(results)
    
    print("\n✓ Backtest complete!\n")

if __name__ == '__main__':
    main()
