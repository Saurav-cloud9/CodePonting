# GSS v5.0 OPTION A VALIDATION WORKFLOW

## HIGH-LEVEL PIPELINE
```
run_option_a.py
    ↓
    ├─→ Step 1: threshold_sweep.py (Nifty 2015-2025)
    │       ↓
    │   threshold_sweep_results.csv (best_threshold = 45)
    │
    ├─→ Step 2: multistock_validation.py (30 stocks, 2022-2025)
    │       ↓
    │   multistock_trading_results.csv (P&L per stock)
    │
    └─→ Step 3: final_report.py
            ↓
        GSS_v5_Refinement_Report.md (PASS/FAIL decision)
```

## STEP 1: THRESHOLD SWEEP (Nifty Daily Data)
```
┌─────────────────────────────────────────────────────┐
│ 1. Download Nifty daily data (2015-2025)           │
│    Source: yfinance                                 │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│ 2. prepare_data() - Calculate indicators:          │
│    - MA38, EMA220                                   │
│    - ADX, +DI, -DI                                  │
│    - RSI, ATR                                       │
│    - Volume_MA, Price_Proximity                     │
│    - Returns: Clean DataFrame (dropna applied)     │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│ 3. Ground Truth Labeling                           │
│    - For each candle: Look 5 days ahead            │
│    - If price moves >1.5*ATR → Label = "BULL"      │
│    - Store in df['Actual_Regime']                  │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│ 4. Test thresholds 45-60                           │
│    For each threshold:                              │
│      For each candle i:                             │
│        ├─→ calculate_gss() → score                 │
│        ├─→ map_score_to_regime() → "BULL/BEAR/SW"  │
│        └─→ If predicted "BULL" & actual "BULL"     │
│               → correct++                           │
│    Calculate: test_precision = correct/total       │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│ 5. Save results                                     │
│    threshold_sweep_results.csv                      │
│    Best: threshold=45, precision=31.8%              │
└─────────────────────────────────────────────────────┘
```

## STEP 2: MULTISTOCK VALIDATION (Intraday 5-min)
```
┌─────────────────────────────────────────────────────┐
│ 1. Read best_threshold from Step 1 (45)            │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│ 2. For each of 30 stocks:                          │
│    run_intraday_validation()                        │
└────────────────┬────────────────────────────────────┘
                 ↓
         ┌───────┴────────────────────────────────────┐
         │ 2a. Month-by-month loop (2022-2025)        │
         │     48 iterations per stock                 │
         └───────┬────────────────────────────────────┘
                 ↓
         ┌───────────────────────────────────────────────┐
         │ 2b. For each month:                           │
         │   ├─→ fetch_5m_data()                         │
         │   │   - Upstox API call                       │
         │   │   - Returns: raw 5-min OHLCV              │
         │   │   - Columns: lowercase                    │
         │   │                                           │
         │   ├─→ fetch_daily_mas()                       │
         │   │   - Fetch daily candles                   │
         │   │   - Calculate: MA50, MA100, MA200         │
         │   │   - Returns: df[date, ma50, ma100, ma200] │
         │   │                                           │
         │   ├─→ Process 5-min data:                     │
         │   │   Step 1: Rename to Title Case            │
         │   │   Step 2: prepare_data() → indicators     │
         │   │   Step 3: Calculate MA20 (bounce line)    │
         │   │   Step 4: Create 'date' column            │
         │   │   Step 5: Merge daily MA50 filter         │
         │   │                                           │
         │   └─→ Now df has:                             │
         │       - 5-min OHLCV (Title Case)              │
         │       - All GSS indicators (MA, EMA, ADX...)  │
         │       - MA20 (for bounce detection)           │
         │       - Daily ma50 (filter condition)         │
         └───────┬───────────────────────────────────────┘
                 ↓
         ┌───────────────────────────────────────────────┐
         │ 2c. Group by date → Daily trading loop        │
         │                                               │
         │   For each date's 5-min candles:              │
         │     in_pos = False                            │
         │     trades_today = 0                          │
         │                                               │
         │     For each 5-min candle i (09:15-15:15):    │
         │                                               │
         │       ┌─ ENTRY LOGIC ─────────────────────┐   │
         │       │ IF not in_pos AND trades<1:       │   │
         │       │                                    │   │
         │       │ 1. MA50 Filter:                    │   │
         │       │    curr['Close'] > curr['ma50']    │   │
         │       │                                    │   │
         │       │ 2. MA20 Bounce:                    │   │
         │       │    prev candle touched MA20        │   │
         │       │    curr candle above MA20          │   │
         │       │                                    │   │
         │       │ 3. GSS Regime Check:               │   │
         │       │    calculate_gss() → score         │   │
         │       │    map_score_to_regime() → regime  │   │
         │       │    regime == "BULL"                │   │
         │       │                                    │   │
         │       │ IF all 3 TRUE:                     │   │
         │       │    Enter Long                      │   │
         │       │    qty = 50000 / entry_price       │   │
         │       │    SL = entry - 1.5*ATR            │   │
         │       │    Target = entry + 3.0*ATR        │   │
         │       └────────────────────────────────────┘   │
         │                                               │
         │       ┌─ EXIT LOGIC ──────────────────────┐   │
         │       │ IF in_pos:                         │   │
         │       │                                    │   │
         │       │ 1. Trailing SL:                    │   │
         │       │    If profit > 1*ATR:              │   │
         │       │       Move SL to breakeven         │   │
         │       │                                    │   │
         │       │ 2. Exit Triggers:                  │   │
         │       │    - Hit SL (Low <= SL)            │   │
         │       │    - Hit Target (High >= Target)   │   │
         │       │    - EOD (time >= 15:15)           │   │
         │       │                                    │   │
         │       │ Calculate P&L:                     │   │
         │       │    (exit_price - entry_price) * qty│   │
         │       │    Append to master_trades[]       │   │
         │       └────────────────────────────────────┘   │
         └───────┬───────────────────────────────────────┘
                 ↓
         ┌───────────────────────────────────────────────┐
         │ 2d. After all months processed:               │
         │     Calculate stock metrics:                  │
         │     - total_trades                            │
         │     - net_pnl                                 │
         │     - win_rate                                │
         │     - wl_ratio                                │
         └───────┬───────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│ 3. Save multistock_trading_results.csv              │
│    30 rows (one per stock)                          │
└─────────────────────────────────────────────────────┘
```

## STEP 3: FINAL REPORT
```
┌─────────────────────────────────────────────────────┐
│ 1. Read both CSVs:                                  │
│    - threshold_sweep_results.csv                    │
│    - multistock_trading_results.csv                 │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│ 2. Calculate:                                       │
│    - total_pnl = sum(all stocks' net_pnl)           │
│    - profitable_count = stocks where net_pnl > 0    │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│ 3. Decision Logic:                                  │
│    IF (profitable >= 3 AND total_pnl > 0):          │
│       Decision = "PASS" ✅                          │
│    ELSE:                                            │
│       Decision = "FAIL" ❌                          │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│ 4. Generate markdown report:                        │
│    GSS_v5_Refinement_Report.md                      │
│    - Summary table                                  │
│    - Per-stock results                              │
│    - Decision: PASS/FAIL                            │
└─────────────────────────────────────────────────────┘
```

## CURRENT PROBLEM DIAGNOSIS

**Symptom:** 100% stocks negative P&L, 11-20% win rates (expected 30%+)

**Your Theory:** Triple MA20 bug (lines 70-71 premature calculation)

**Status:** Lines 70-71 now commented out, but issue persists

**Next Steps:**
1. Verify indicator calculation order in prepare_data()
2. Check MA20 calculation timing (line 154)
3. Validate bounce detection logic (lines 168-169)
4. Add debug logging to see actual entry conditions
