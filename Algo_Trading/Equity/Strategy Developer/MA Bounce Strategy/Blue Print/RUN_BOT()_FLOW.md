# RUN_BOT() FLOWCHART

START run_bot()
    ↓
Initialize Dashboard (empty metrics)
    ↓
Load Past Trades from CSV
    ↓
Rebuild Dashboard (traded symbols, buy prices)
    ↓
Print Dashboard
    ↓
┌─────────────────────────────────────┐
│      MAIN LOOP (while True)         │
├─────────────────────────────────────┤
│                                     │
│  Get Current Time                   │
│      ↓                              │
│  Check Market Hours (09:15-15:30)   │
│      ↓ (if outside) → sleep         │
│      ↓ (if inside)                  │
│  Check Max Positions                │
│      ↓ (if full) → monitor exits    │
│      ↓                              │
│  Check Time Window (< 14:30)        │
│      ↓ (if late) → monitor exits    │
│      ↓                              │
│  FOR EACH symbol in WATCHLIST:      │
│      ↓                              │
│      Scan for Signal                │
│      ↓ (check_signal)               │
│      ↓                              │
│      IF signal + not traded:        │
│          Place Order                │
│          Update Dashboard           │
│      ↓                              │
│  Monitor Open Positions (exits)     │
│      ↓                              │
│  Sleep 30 seconds                   │
│      ↓                              │
└─────┘ (loop back)

---

# How the Signal Scanning and Position Monitoring Work Together


┌─────────────────────────────────────────────────────────────┐
│                    MAIN LOOP (every 30 sec)                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  PARALLEL OPERATIONS (same loop)      │
        └───────────────────────────────────────┘
                ↓                       ↓
    ┌───────────────────┐    ┌──────────────────────┐
    │  SIGNAL SCANNING  │    │ POSITION MONITORING  │
    │   (New entries)   │    │   (Active trades)    │
    └───────────────────┘    └──────────────────────┘
                ↓                       ↓

┌──────────────────────────────────────┐
│       SIGNAL SCANNING LOGIC          │
├──────────────────────────────────────┤
│                                      │
│ 9:15:00 → New 5-min candle forms    │
│           (at broker's server)       │
│     ↓                                │
│ 9:15:30 → Bot wakes up, fetches     │
│           last 50 candles from API   │
│     ↓                                │
│ API returns:                         │
│   [9:00-9:05] ✅ complete           │
│   [9:05-9:10] ✅ complete           │
│   [9:10-9:15] ✅ complete (NEW!)    │
│   [9:15-9:20] ⏳ forming...         │
│     ↓                                │
│ check_signal() analyzes:             │
│   - Looks at [9:10-9:15] candle     │
│   - Checks if it touched MA20       │
│   - Checks if [9:15-9:20] bouncing  │
│     ↓                                │
│ If bounce found → place_order()      │
│     ↓                                │
│ sleep(30)                            │
│     ↓                                │
│ 9:16:00 → Loop again                │
│           Fetches candles again      │
│           Same [9:10-9:15] seen     │
│           No new signal (already    │
│           checked this candle)       │
│     ↓                                │
│ 9:20:00 → New candle [9:15-9:20]   │
│           completes!                 │
│     ↓                                │
│ 9:20:30 → Bot fetches, sees new     │
│           candle, checks for signal  │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│     POSITION MONITORING LOGIC        │
├──────────────────────────────────────┤
│                                      │
│ (Happens EVERY loop, continuously)   │
│                                      │
│ 9:15:30 → Check open positions      │
│     ↓                                │
│ FOR each position:                   │
│   Get LIVE price (tick data)        │
│   ↓                                  │
│   TATAMOTORS bought @ ₹350          │
│   Current price: ₹352 (live)        │
│   Target: ₹355.25                   │
│   ↓                                  │
│   352 >= 355.25? NO → continue      │
│   352 <= 346.50? NO → continue      │
│     ↓                                │
│ sleep(30)                            │
│     ↓                                │
│ 9:16:00 → Check again               │
│   Current price: ₹354.50 (live)     │
│   354.50 >= 355.25? NO              │
│     ↓                                │
│ 9:16:30 → Check again               │
│   Current price: ₹355.50 (live)     │
│   355.50 >= 355.25? YES! ✅         │
│   → SELL and exit                   │
└──────────────────────────────────────┘