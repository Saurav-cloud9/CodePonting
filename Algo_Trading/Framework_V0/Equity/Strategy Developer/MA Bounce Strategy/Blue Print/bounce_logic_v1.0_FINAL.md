╔══════════════════════════════════════════════════════════════════╗
║           MA20 BOUNCE DETECTION LOGIC - FINAL v1.0               ║
╚══════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────┐
│  PREREQUISITES (Must pass before bounce check)                   │
├──────────────────────────────────────────────────────────────────┤
│  1. MA20 calculated (need minimum 20 candles)                    │
│  2. Volume check: current_volume > avg_volume × 1.2              │
│     → Confirms momentum, filters weak signals                    │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  STEP 1: TOUCH DETECTION                                         │
├──────────────────────────────────────────────────────────────────┤
│  FOR each candle i (starting from candle 20):                    │
│                                                                   │
│    IF candle[i].low <= ma20[i]:                                  │
│      ✅ TOUCH CONFIRMED                                          │
│      → Price touched or went below MA20 support line             │
│      → Proceed to Step 2                                         │
│                                                                   │
│    ELSE:                                                          │
│      ❌ NO TOUCH                                                 │
│      → Continue to next candle                                   │
│                                                                   │
│  NOTE: No distance threshold! MA20 is exact line.                │
│        Touch = low <= ma20 (not "within 0.5%")                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  STEP 2: BOUNCE CONFIRMATION (15-Minute Window)                  │
├──────────────────────────────────────────────────────────────────┤
│  Check 4 consecutive candles: [i, i+1, i+2, i+3]                │
│  Time window: Current candle + next 15 minutes (3 × 5min)       │
│                                                                   │
│  FOR j in [i, i+1, i+2, i+3]:                                   │
│                                                                   │
│    IF candle[j].close > ma20[i]:                                │
│      ✅ BOUNCE CONFIRMED at candle j                            │
│      → Entry Signal Generated                                    │
│      → Entry Price = candle[j].close                            │
│      → STOP checking remaining candles                           │
│      → Place trade                                               │
│                                                                   │
│  IF all 4 candles checked and none bounced:                     │
│    ❌ BOUNCE FAILED                                             │
│    → Price touched MA20 but broke down                          │
│    → NO TRADE                                                    │
│    → Continue to next candle (i+4) and repeat                   │
│                                                                   │
│  NOTE: We check against ma20[i] (touch candle's MA)             │
│        not ma20[j] (bounce candle's MA)                         │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  EXAMPLE 1: IMMEDIATE BOUNCE (Best Case)                         │
├──────────────────────────────────────────────────────────────────┤
│  11:00 AM (Candle i):                                            │
│    - MA20: ₹621.50                                               │
│    - Low: ₹621.20  ✅ Touched (621.20 <= 621.50)                │
│    - Close: ₹621.80 ✅ Bounced (621.80 > 621.50)                │
│    - SIGNAL: ENTER at ₹621.80                                    │
│    - Latency: 0 minutes (same candle)                           │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  EXAMPLE 2: DELAYED BOUNCE (i+3)                                 │
├──────────────────────────────────────────────────────────────────┤
│  11:00 AM (Candle i) - TOUCH:                                    │
│    - MA20: ₹621.50                                               │
│    - Low: ₹621.20  ✅ Touched                                    │
│    - Close: ₹621.30 ❌ Below MA (621.30 < 621.50)               │
│                                                                   │
│  11:05 AM (Candle i+1):                                          │
│    - Close: ₹621.40 ❌ Still below (621.40 < 621.50)            │
│                                                                   │
│  11:10 AM (Candle i+2):                                          │
│    - Close: ₹621.45 ❌ Still below (621.45 < 621.50)            │
│                                                                   │
│  11:15 AM (Candle i+3):                                          │
│    - Close: ₹621.80 ✅ BOUNCED! (621.80 > 621.50)               │
│    - SIGNAL: ENTER at ₹621.80                                    │
│    - Latency: 15 minutes after touch                             │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  EXAMPLE 3: FAILED BOUNCE (Breakdown)                            │
├──────────────────────────────────────────────────────────────────┤
│  11:00 AM (Candle i) - TOUCH:                                    │
│    - MA20: ₹621.50                                               │
│    - Low: ₹621.20  ✅ Touched                                    │
│    - Close: ₹621.30 ❌ Below MA                                  │
│                                                                   │
│  11:05 AM (Candle i+1):                                          │
│    - Close: ₹621.25 ❌ Still below                               │
│                                                                   │
│  11:10 AM (Candle i+2):                                          │
│    - Close: ₹621.10 ❌ Going lower                               │
│                                                                   │
│  11:15 AM (Candle i+3):                                          │
│    - Close: ₹620.90 ❌ Breakdown!                                │
│                                                                   │
│  RESULT: ❌ NO TRADE                                             │
│  → MA20 failed as support                                        │
│  → Continue scanning from candle i+4 (11:20 AM)                 │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  PSEUDOCODE                                                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  for i in range(20, len(candles)):                              │
│      candle = candles[i]                                         │
│      ma20 = calculate_ma20(candles, i)                          │
│                                                                   │
│      # Volume check                                              │
│      if candle.volume < avg_volume * 1.2:                       │
│          continue                                                │
│                                                                   │
│      # Touch check                                               │
│      if candle.low <= ma20:                                     │
│                                                                   │
│          # Bounce check (4 candles)                             │
│          for j in [i, i+1, i+2, i+3]:                          │
│              if candles[j].close > ma20:                        │
│                  # BOUNCE CONFIRMED!                            │
│                  entry_price = candles[j].close                 │
│                  entry_time = candles[j].timestamp              │
│                  generate_signal(entry_price, entry_time)       │
│                  break                                           │
│                                                                   │
│          # If loop completes without break = no bounce          │
│          # Continue to next candle                              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  KEY DIFFERENCES FROM PREVIOUS LOGIC                             │
├──────────────────────────────────────────────────────────────────┤
│  OLD (Proximity Logic - WRONG):                                  │
│    - distance = |close - ma20| / ma20                           │
│    - if distance <= 0.5% AND close >= ma20: SIGNAL              │
│    - Problem: No touch confirmation, just proximity             │
│                                                                   │
│  NEW (True Bounce Logic - CORRECT):                             │
│    - Step 1: low <= ma20 (actual touch required)               │
│    - Step 2: close > ma20 (bounce confirmation)                │
│    - Step 3: Check up to 15 min window (delayed bounce)        │
│    - Filters out false signals from consolidation               │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  RATIONALE                                                        │
├──────────────────────────────────────────────────────────────────┤
│  1. TOUCH = Confirms MA20 is being tested as support            │
│  2. BOUNCE = Confirms buyers stepped in at MA20                 │
│  3. 15-MIN WINDOW = Allows for delayed reaction (not instant)   │
│  4. VOLUME CHECK = Ensures momentum behind the move             │
│  5. NO THRESHOLD = MA20 is exact line, not fuzzy zone           │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  EXIT RULES (To be validated)                                    │
├──────────────────────────────────────────────────────────────────┤
│  Target: TEST [0.5%, 1.0%, 1.5%] - Find optimal                 │
│  Stop Loss: -0.5% (fixed for now)                                │
│  Time Limit: 80 candles (6.5 hours) → EOD square-off            │
│                                                                   │
│  Note: Previous backtest (proximity logic) showed 1.5% won       │
│        85% of time. Need to revalidate with true bounce logic.   │
└──────────────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════════╗
║  Document Version: v1.0                                          ║
║  Date: January 12, 2026                                          ║
║  Status: Ready for backtest implementation                       ║
╚══════════════════════════════════════════════════════════════════╝