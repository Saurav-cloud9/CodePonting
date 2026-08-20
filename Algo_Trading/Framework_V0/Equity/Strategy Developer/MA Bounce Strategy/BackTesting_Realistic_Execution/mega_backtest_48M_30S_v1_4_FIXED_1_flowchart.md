START
  ↓
┌─────────────────────────────────────┐
│ SETUP                               │
│ - 30 stocks                         │
│ - 8 filters (No Filter → MA50+100+200)│
│ - 4 ATR configs (Sideways → Extreme)│
│ - 48 months (Jan 2022 - Dec 2025)  │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ FOR EACH STOCK (30 iterations)     │
└──────────────┬──────────────────────┘
               ↓
       ┌───────────────┐
       │ DATA FETCH    │
       │ - 5-min OHLCV │ (48 API calls per stock)
       │ - Daily MAs   │ (1 API call per stock)
       └───────┬───────┘
               ↓
       ┌────────────────────────────────┐
       │ PROCESS DATA                   │
       │ - Merge daily MA50/100/200     │
       │ - Calculate ATR, MA20, vol_avg │
       └───────┬────────────────────────┘
               ↓
       ┌────────────────────────────────────────┐
       │ FOR EACH CONFIG (32 combos)           │
       │   Filter × ATR_Config                  │
       └───────┬────────────────────────────────┘
               ↓
         ┌─────────────────────────┐
         │ DETECT BOUNCES          │
         │ 1. Touch MA20?          │
         │ 2. Above MA filter?     │
         │ 3. Volume > 1.2x avg?   │
         │ 4. Bounce in 3 candles? │
         │ → Entry at next open    │
         └─────┬───────────────────┘
               ↓
         ┌─────────────────────────┐
         │ SIMULATE TRADES         │
         │ - SL: entry - (ATR × mult)│
         │ - Target: entry + (ATR × mult)│
         │ - Exit: SL/Target/EOD   │
         └─────┬───────────────────┘
               ↓
         ┌──────────────────────────┐
         │ STORE RESULTS            │
         │ [(stock, filter, atr)] = │
         │   {trades, win%, profit} │
         └─────┬────────────────────┘
               ↓
       ┌────────────────────────┐
       │ END CONFIG LOOP        │
       └───────┬────────────────┘
               ↓
┌──────────────────────────────┐
│ END STOCK LOOP               │
└──────────┬───────────────────┘
           ↓
┌────────────────────────────────────┐
│ AGGREGATE & SAVE                   │
│ - Group by (filter, atr_config)    │
│ - Sum trades, avg win_rate, profit │
│ - Save CSV: backtest_results.csv   │
└──────────┬─────────────────────────┘
           ↓
┌────────────────────────────────────┐
│ PRINT TOP 10                       │
│ - Sort by Net_Profit descending    │
│ - Display best configs             │
└──────────┬─────────────────────────┘
           ↓
          END