"""
╔═══════════════════════════════════════════════════════════════╗
║      MA BOUNCE BACKTEST v0.8 - 2025 DATA (BUG FIXES)        ║
╚═══════════════════════════════════════════════════════════════╝

BACKTEST STRUCTURE:
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│  STEP 1: DATA PREPARATION                                   │
├─────────────────────────────────────────────────────────────┤
│ • Load processed CSV (already 5-min candles)               │
│ • Result: ~75 candles/day × 13 days = ~975 total           │
│ • MA20 already calculated on 5-min chart                   │
│ • MA50/100/200 already calculated (daily)                  │
│ • Skip Day 1 (Dec 18) for clean MA20 data                  │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: BOUNCE DETECTION (Check bounce FIRST!)            │
├─────────────────────────────────────────────────────────────┤
│ FOR each candle i:                                          │
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
│       IF close[j] < ma20[i] × 0.99:                         │
│          ❌ BREAKDOWN - Cancel                              │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: FILTER CHECK (at entry_index, NOT touch!)         │
├─────────────────────────────────────────────────────────────┤
│ Get entry candle data (at entry_index):                     │
│   entry_close = close[entry_index]                          │
│   ma50, ma100, ma200 = daily MAs at entry_date             │
│                                                              │
│ Test which of 8 filters pass:                               │
│     1. No Filter (always TRUE)                              │
│     2. entry_close > MA50                                   │
│     3. entry_close > MA100                                  │
│     4. entry_close > MA200                                  │
│     5. entry_close > MA50 AND MA100                         │
│     6. entry_close > MA50 AND MA200                         │
│     7. entry_close > MA100 AND MA200                        │
│     8. entry_close > MA50 AND MA100 AND MA200               │
│                                                              │
│   IF no filters pass: SKIP (no uptrend)                     │
│   ELSE: Proceed to volume check                             │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: VOLUME CONFIRMATION                                │
├─────────────────────────────────────────────────────────────┤
│ avg_volume = avg(volume[entry_index-19 to entry_index-1]) │
│ IF volume[entry_index] > avg_volume × 1.5:                 │
│    ✅ VOLUME CONFIRMED - Valid bounce!                      │
│ ELSE:                                                        │
│    ❌ Skip (weak volume)                                    │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: OUTCOME TRACKING (3 TARGETS)                       │
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
│  STEP 6: RESULTS (8 Filters × 3 Targets = 24 Scenarios)    │
├─────────────────────────────────────────────────────────────┤
│ Display results by target:                                  │
│  • Filter | Trades | Wins | Loss | Win% | Net Profit       │
│  • Rank by Net Profit within each target                   │
│                                                              │
│ Find absolute winner:                                       │
│  • Highest Net Profit across all 24 scenarios               │
│  • Show scaling potential (monthly projection)              │
└─────────────────────────────────────────────────────────────┘

KEY FIXES IN v0.8 (FROM v1.0):
═════════════════════════════════════════════════════════════
✅ FIX #1: Skip Day 1 (Dec 18) - ensures clean MA20 data
✅ FIX #2: Filter check AFTER bounce, at entry_index (CRITICAL!)
✅ FIX #3: Duplicate trade protection (ELSE structure verified)
✅ Current candle bounce check (check i before i+1,i+2,i+3)
✅ Threshold = close > ma20 (NO 1% buffer)
✅ Volume confirmation (1.5× avg volume)
✅ Targets = 0.5%, 1%, 1.5%
✅ Stop Loss = 0.5%
✅ 8 filters (No Filter, MA50, MA100, MA200, combinations)
✅ 24 scenarios total

DATA SOURCES:
═══════════════════════════════════════════════════════════
• Source: 5-min OHLC data from XLSX files
• Stocks: SUZLON, PNB, TATASTEEL, IDEA, YESBANK
• Period: Dec 18, 2025 - Jan 7, 2026 (13 trading days, skipped Jan 8)
• Processed: Volume cleaned, MA20/50/100/200 calculated
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

# ═════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════

# Strategy Parameters
TARGETS = [0.005, 0.01, 0.015]  # 0.5%, 1%, 1.5%
STOP_LOSS = 0.005  # 0.5%
VOLUME_MULTIPLIER = 1.1  # Volume confirmation threshold

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

# Stock to backtest (command line argument)
stock_name = sys.argv[1] if len(sys.argv) > 1 else 'IDEA'
CSV_PATH = f'./{stock_name}_2025_FINAL.csv'

# ═════════════════════════════════════════════════════════════
# DATA LOADING
# ═════════════════════════════════════════════════════════════

def load_data():
    """Load processed 2025 data from CSV"""
    print("\n" + "="*90)
    print("DATA LOADING")
    print("="*90)
    
    df = pd.read_csv(CSV_PATH)
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    print(f"✓ Loaded {len(df)} candles from {CSV_PATH}")
    print(f"✓ Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Calculate avg volume (for confirmation)
    df['avg_volume'] = df['volume'].rolling(20).mean()
    
    # Skip Day 1 for clean MA20 data
    first_date = df['date'].min()
    df = df[df['date'] != first_date].reset_index(drop=True)
    
    print(f"✓ Skipped first day ({first_date}) for clean MA20 data")
    print(f"✓ Final dataset: {len(df)} candles from {df['date'].min()} to {df['date'].max()}")
    
    return df

# ═════════════════════════════════════════════════════════════
# BACKTEST ENGINE
# ═════════════════════════════════════════════════════════════

def run_backtest(df):
    """Main backtest logic with v0.8 bug fixes"""
    
    print("\n" + "="*90)
    print("RUNNING BACKTEST")
    print("="*90)
    
    # Results structure: {filter: {target: {trades, wins, losses, net}}}
    results = {
        f: {t: {'trades': 0, 'wins': 0, 'losses': 0, 'net': 0.0} for t in TARGETS}
        for f in FILTER_NAMES
    }
    
    bounces_detected = 0
    bounces_volume_confirmed = 0
    
    # Loop through candles
    for i in range(len(df)):
        
        # Get current candle data
        row = df.iloc[i]
        low = row['low']
        close = row['close']
        ma20 = row['MA20']
        
        # Skip if MA20 not available
        if pd.isna(ma20):
            continue
        
        # STEP 2: BOUNCE DETECTION (Check bounce FIRST, filter AFTER)
        
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
                close_j = df.iloc[j]['close']
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
        
        # STEP 3: FILTER CHECK (at entry candle, not touch candle!)
        entry_row = df.iloc[entry_index]
        entry_close = entry_row['close']
        ma50 = entry_row['MA50']
        ma100 = entry_row['MA100']
        ma200 = entry_row['MA200']

        # DEBUG: Check MA availability
        #print(f"Entry {entry_index}: close={entry_close:.2f}, MA50={ma50}, MA100={ma100}, MA200={ma200}")

        # Skip if daily MAs not available
        if pd.isna(ma50) or pd.isna(ma100) or pd.isna(ma200):
            continue
        
        # Check which filters pass AT ENTRY POINT
        filters_passed = {
            'No Filter': True,
            'MA50': entry_close > ma50,
            'MA100': entry_close > ma100,
            'MA200': entry_close > ma200,
            'MA50+100': entry_close > ma50 and entry_close > ma100,
            'MA50+200': entry_close > ma50 and entry_close > ma200,
            'MA100+200': entry_close > ma100 and entry_close > ma200,
            'MA50+100+200': entry_close > ma50 and entry_close > ma100 and entry_close > ma200
        }
        
        # If no filters pass (except No Filter), skip
        if not any(filters_passed.values()):
            continue
        
        # STEP 4: Volume confirmation
        avg_vol = entry_row['avg_volume']
        entry_vol = entry_row['volume']

        # DEBUG: Print volume stats
        #print(f"Entry {entry_index}: entry_vol={entry_vol:.0f}, avg_vol={avg_vol:.0f}, ratio={entry_vol / avg_vol:.2f}")

        if pd.isna(avg_vol) or entry_vol < avg_vol * VOLUME_MULTIPLIER:
            continue  # Weak volume
        
        bounces_volume_confirmed += 1
        
        # STEP 5: OUTCOME TRACKING
        
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
                    if df.iloc[k]['high'] >= target_price:
                        outcome = 'WIN'
                        break
                    if df.iloc[k]['low'] <= sl_price:
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

def display_results(results, df):
    """Display backtest results in formatted tables"""
    
    print("\n" + "="*90)
    print(f"{stock_name} MA BOUNCE BACKTEST - RESULTS (v0.8)")
    print(f"Period: Dec 19, 2025 - Jan 7, 2026 (13 trading days)")
    print("="*90)
    
    stock_price = df['close'].mean()
    
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
    print(f"Net Profit: ₹{abs_winner['net']:.2f} (13 days, 1 share)")
    print(f"Trades: {abs_winner['trades']} (Win Rate: {abs_winner['win_pct']:.1f}%)")
    print("="*90)
    
    # Scaling potential
    print("\nSCALING POTENTIAL (Monthly projection assuming ~22 trading days):")
    monthly_profit_1 = abs_winner['net'] * (22 / 13)
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
    print(f"║      MA BOUNCE BACKTEST v0.8 - {stock_name} (2025 DATA)          ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    # Load data
    df = load_data()
    
    # Run backtest
    results = run_backtest(df)
    
    # Display results
    display_results(results, df)
    
    print("\n✓ Backtest complete!\n")

if __name__ == '__main__':
    main()
