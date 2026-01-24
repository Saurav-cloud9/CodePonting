# MA BOUNCE BOT - SYSTEM ARCHITECTURE

## CURRENT SYSTEM (v1.4 - As Implemented)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA ACQUISITION LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  • Upstox API: 5-min candles (48 months: Jan 2022 - Dec 2025)  │
│  • Daily candles: MA50/MA100/MA200 calculation                  │
│  • 30 F&O stocks from NSE                                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TECHNICAL INDICATORS                           │
├─────────────────────────────────────────────────────────────────┤
│  • MA20 (5-min): Bounce detection anchor                        │
│  • MA50/100/200 (Daily): Trend filters                          │
│  • Volume: 20-period rolling average                            │
│  • ATR(14): True Range = max(H-L, |H-PC|, |L-PC|)              │
│            → 14-period rolling mean                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SIGNAL GENERATION                             │
├─────────────────────────────────────────────────────────────────┤
│  BOUNCE DETECTION LOGIC:                                        │
│  ├─ STEP 1: Touch → Low ≤ MA20                                 │
│  ├─ STEP 2: Bounce → Close > MA20 (within 15-min window)       │
│  ├─ STEP 3: Volume Filter → Volume > 1.2× avg_volume          │
│  └─ STEP 4: MA Filter → Price > MA50/100/200 (8 combinations) │
│                                                                  │
│  Entry: Next candle OPEN after bounce confirmation              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                 RISK MANAGEMENT (ATR-Based)                      │
├─────────────────────────────────────────────────────────────────┤
│  4 ATR Configurations Tested:                                   │
│  ├─ Sideways:   SL = 1.0×ATR  |  Target = 1.5×ATR             │
│  ├─ Regular-1:  SL = 1.5×ATR  |  Target = 2.0×ATR             │
│  ├─ Regular-2:  SL = 2.0×ATR  |  Target = 3.0×ATR             │
│  └─ Extreme:    SL = 2.5×ATR  |  Target = 4.0×ATR             │
│                                                                  │
│  Exit Triggers:                                                 │
│  ├─ Target Hit: Price ≥ Entry + (ATR × target_mult)           │
│  ├─ SL Hit: Price ≤ Entry - (ATR × sl_mult)                   │
│  └─ EOD: 3:00 PM forced exit                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKTEST ENGINE (Brute Force)                       │
├─────────────────────────────────────────────────────────────────┤
│  • 48 months × 30 stocks = 1,440 month-stock combinations      │
│  • 8 MA filters × 4 ATR configs = 32 combinations per stock    │
│  • Total tested: 1,440 × 32 = 46,080 scenarios                 │
│                                                                  │
│  Optimization Goal: MAX(Capital Efficiency)                     │
│  └─ Capital Efficiency = (Net Profit / Total Capital) × 100%   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT METRICS                              │
├─────────────────────────────────────────────────────────────────┤
│  Per Month-Stock:                                               │
│  ├─ Best Filter (e.g., MA50+200)                               │
│  ├─ Best ATR Config (e.g., Regular-1)                          │
│  ├─ Total Trades, Target Hits, SL Hits, EOD Exits              │
│  ├─ Win% = (Target Hits / Total Trades) × 100                  │
│  ├─ ProTrades% = (Profitable Trades / Total) × 100            │
│  ├─ Capital Efficiency% = (Net₹ / Capital₹) × 100             │
│  └─ Consistency Score = Top-10 appearances / 48 months         │
│                                                                  │
│  NO REGIME FILTERING CURRENTLY                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## FUTURE SYSTEM (v2.0 - GSS-Driven Playbook Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA ACQUISITION LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  • Upstox API: 5-min + Daily candles                            │
│  • NIFTY 50 data: Index regime calculation                      │
│  • 30 F&O stocks from NSE                                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│         GSS (Global Sentiment Score) - REGIME DETECTOR           │
├─────────────────────────────────────────────────────────────────┤
│  INPUT DATA (Daily NIFTY):                                      │
│  ├─ Price vs MA20/EMA200: Trend strength                       │
│  ├─ MA20 Slope: Momentum direction                             │
│  ├─ ADX(14): Trend strength (Wilder's smoothing)               │
│  ├─ Volume Confirmation: Volume > 1.2× 20-day avg              │
│  └─ RSI(14): Momentum oscillator [PLANNED]                     │
│                                                                  │
│  REGIME CLASSIFICATION:                                         │
│  ├─ BULL: Score ≥ 70 (Strong uptrend, high momentum)           │
│  ├─ SIDEWAYS: 30 < Score < 70 (Range-bound, low ADX)           │
│  └─ BEAR: Score ≤ 30 (Downtrend, bearish momentum)             │
│                                                                  │
│  VALIDATION METHOD: Future-Truth                                │
│  └─ Predict regime using N-1 data, validate vs 5-day price move│
│                                                                  │
│  CURRENT ACCURACY (v0.9 with Volume Filter):                   │
│  ├─ SIDEWAYS: 78.3% (462/590) ✓ Strong defense                │
│  ├─ BULL: 21.8% precision (19/87) ✗ Needs RSI fix             │
│  └─ BEAR: [Not yet tested]                                     │
│                                                                  │
│  TARGET ACCURACY (v1.0 with RSI):                              │
│  └─ BULL: 40-50% precision, SIDEWAYS: maintain 75%+           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│           PLAYBOOK BUILDER (Regime-Specific Patterns)            │
├─────────────────────────────────────────────────────────────────┤
│  For Each Regime (BULL / SIDEWAYS / BEAR):                     │
│                                                                  │
│  STEP 1: REGIME FILTERING                                       │
│  └─ Isolate all trading days matching regime (per GSS)         │
│                                                                  │
│  STEP 2: PATTERN ANALYSIS                                       │
│  └─ Run backtest on regime-filtered days only                  │
│  └─ Identify: Which stocks, filters, ATR configs WIN           │
│                                                                  │
│  STEP 3: PLAYBOOK CREATION                                      │
│  ├─ BULL Playbook:                                             │
│  │   ├─ Top 5 stocks (e.g., SBIN, TATASTEEL, RELIANCE)        │
│  │   ├─ Optimal filter (e.g., MA50)                           │
│  │   ├─ ATR config (e.g., Regular-2: 2×/3× for big moves)     │
│  │   └─ Expected: High target hit rate, low EOD exits         │
│  │                                                              │
│  ├─ SIDEWAYS Playbook:                                         │
│  │   ├─ Top 5 stocks (likely different - range traders)       │
│  │   ├─ Tighter filters (e.g., MA50+100+200)                  │
│  │   ├─ ATR config (e.g., Sideways: 1×/1.5× for quick exits)  │
│  │   └─ Expected: More EOD exits, avoid chop                  │
│  │                                                              │
│  └─ BEAR Playbook:                                             │
│      ├─ Conservative stocks / skip trading                     │
│      └─ Focus on capital preservation                          │
│                                                                  │
│  OUTPUT: 3 Regime-Specific Playbooks                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│         PBS (PlaybookStocks) - DAILY STOCK SELECTOR              │
├─────────────────────────────────────────────────────────────────┤
│  MORNING WORKFLOW (Pre-Market):                                 │
│  ├─ STEP 1: Run GSS on NIFTY (yesterday's close data)          │
│  ├─ STEP 2: Get today's regime (BULL/SIDEWAYS/BEAR)            │
│  ├─ STEP 3: Load corresponding Playbook                        │
│  └─ STEP 4: Extract PBS = Top 5 stocks for that regime         │
│                                                                  │
│  EXAMPLE:                                                       │
│  ├─ GSS Output: "BULL (Score: 73)"                             │
│  ├─ Playbook: BULL Playbook                                    │
│  └─ PBS: [SBIN, TATASTEEL, RELIANCE, INFY, AXISBANK]          │
│                                                                  │
│  INTRADAY EXECUTION:                                            │
│  └─ Monitor ONLY PBS stocks for MA20 bounce setups             │
│  └─ Apply Playbook's filter + ATR config                       │
│  └─ Enter trades per signal generation logic                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                ENHANCED SIGNAL GENERATION                        │
├─────────────────────────────────────────────────────────────────┤
│  Same bounce logic as v1.4 BUT:                                │
│  ├─ Applied ONLY to PBS stocks (not all 30)                    │
│  ├─ Uses Playbook-defined filters (regime-optimized)           │
│  └─ Uses Playbook-defined ATR config (stock-specific)          │
│                                                                  │
│  Additional Filters [PLANNED]:                                  │
│  ├─ Bounce Quality Score (wick ratio, candle color)            │
│  ├─ Time-based filters (avoid 3:00-3:20 PM chop)               │
│  └─ NIFTY correlation check (stock moving with index?)         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              RISK MANAGEMENT (Regime-Adaptive)                   │
├─────────────────────────────────────────────────────────────────┤
│  Same ATR-based SL/Targets BUT:                                │
│  └─ Config auto-selected from Playbook (regime-matched)        │
│                                                                  │
│  EXAMPLE:                                                       │
│  ├─ BULL day → Use Regular-2 (2×/3× ATR) for big moves        │
│  └─ SIDEWAYS day → Use Sideways (1×/1.5× ATR) for quick exits │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LIVE DEPLOYMENT SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│  DAILY CYCLE:                                                   │
│  ├─ 08:00 AM: Run GSS → Get regime → Load Playbook → Get PBS  │
│  ├─ 09:15 AM: Monitor PBS stocks for bounce signals            │
│  ├─ 09:15-3:20: Execute trades per Playbook rules              │
│  └─ 03:20 PM: Force exit all positions                         │
│                                                                  │
│  ADAPTIVE INTELLIGENCE:                                         │
│  ├─ Right stocks (PBS based on regime)                         │
│  ├─ Right filters (Playbook-optimized)                         │
│  ├─ Right risk (ATR config matched to regime)                  │
│  └─ Higher win rate (regime-aligned setups)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## KEY DIFFERENCES: CURRENT vs FUTURE

| **Aspect**              | **Current (v1.4)**                      | **Future (v2.0)**                           |
|-------------------------|-----------------------------------------|---------------------------------------------|
| **Stock Selection**     | All 30 stocks every day                | PBS: 5 stocks based on regime              |
| **Regime Awareness**    | None (blind trading)                   | GSS-driven (BULL/SIDEWAYS/BEAR)            |
| **Filter Selection**    | Brute force: test all 8 combinations   | Playbook: pre-optimized per regime         |
| **ATR Config**          | Brute force: test all 4 configs        | Playbook: regime-matched config            |
| **Win Rate Expectation**| ~45-50% (mixed regime noise)           | ~55-60% (regime-aligned trades)            |
| **Capital Efficiency**  | Baseline (no regime filter)            | 15-20% improvement (focused deployment)    |
| **Cognitive Load**      | Trade all setups, hope for best        | Trade only high-probability regime setups  |

---

## DEPENDENCY CHAIN

```
Strong GSS (All Regimes)
    ↓
Accurate Playbook (Regime-Specific Winning Patterns)
    ↓
Quality PBS (5 PlaybookStocks per Regime)
    ↓
Live Deployment (Right Stocks + Right Regime + Right Setup)
    ↓
Higher ROI (More Target Hits, Fewer SL/EOD Exits)
```

**CURRENT BLOCKER:**  
GSS BULL precision = 21.8% → Cannot trust BULL Playbook → Must fix GSS first

**NEXT STEPS:**  
1. Add RSI to GSS for BULL momentum detection (target: 40-50% precision)
2. Re-validate GSS with Future-Truth methodology
3. Build regime-specific Playbooks (backtest on regime-filtered days)
4. Extract PBS per regime
5. Deploy live with regime-aware stock selection

