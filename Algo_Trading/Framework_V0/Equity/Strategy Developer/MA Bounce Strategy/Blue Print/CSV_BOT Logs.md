┌─────────────────────────────────────────────────────────────┐
│ BOT STARTUP (Jan 15, 2026)                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ CREATE FILENAME VARIABLES                                    │
├─────────────────────────────────────────────────────────────┤
│ today = "20260115"                                          │
│ LOG_FILE = "bot_activity_20260115.log"                      │
│ TRADES_LOG_FILE = "trades_log_20260115.csv"  (daily)       │
│ TRADES_MASTER_FILE = "trades_log_master.csv"  (permanent)  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ CHECK: Does TRADES_LOG_FILE exist?                          │
└─────────────────────────────────────────────────────────────┘
         ↓ YES                           ↓ NO
┌──────────────────────┐      ┌──────────────────────┐
│ LOAD EXISTING DATA   │      │ START FRESH          │
│ (Bot restarted)      │      │ (First run today)    │
├──────────────────────┤      ├──────────────────────┤
│ Read CSV:            │      │ trades_today = 0     │
│ - Count BUY orders   │      │ traded_symbols = {}  │
│ - Extract symbols    │      └──────────────────────┘
│ ↓                    │
│ Update dashboard:    │
│ - trades_today = 2   │
│ - traded_symbols =   │
│   {TATAMOTORS,VEDL}  │
└──────────────────────┘
         ↓                               ↓
         └───────────────┬───────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ TRADING LOOP RUNS                                            │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ SIGNAL DETECTED → BUY ORDER                                  │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ WRITE TO BOTH CSV FILES                                      │
├─────────────────────────────────────────────────────────────┤
│ log_trade_to_csv(...) writes to:                            │
│                                                              │
│ 1. TRADES_LOG_FILE (trades_log_20260115.csv)               │
│    ├─ Daily file                                            │
│    ├─ Gets deleted/archived eventually                      │
│    └─ Used for: Load today's metrics on restart             │
│                                                              │
│ 2. TRADES_MASTER_FILE (trades_log_master.csv)              │
│    ├─ Permanent file (never deleted)                        │
│    ├─ Accumulates ALL days                                  │
│    └─ Used for: Long-term analysis, backtesting             │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ EXAMPLE: After 2 trades                                      │
├─────────────────────────────────────────────────────────────┤
│ trades_log_20260115.csv (today only):                       │
│ 2026-01-15 14:35:00,TATAMOTORS,BUY,450.25,...              │
│ 2026-01-15 14:55:00,VEDL,BUY,280.50,...                    │
│                                                              │
│ trades_log_master.csv (all history):                        │
│ 2026-01-14 13:20:00,ONGC,BUY,245.00,...   (yesterday)      │
│ 2026-01-14 14:10:00,ONGC,SELL,247.50,...  (yesterday)      │
│ 2026-01-15 14:35:00,TATAMOTORS,BUY,450.25,... (today)      │
│ 2026-01-15 14:55:00,VEDL,BUY,280.50,...   (today)          │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT CRASHES & RESTARTS (2:30 PM same day)                   │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ load_today_metrics_from_csv()                               │
├─────────────────────────────────────────────────────────────┤
│ Reads: trades_log_20260115.csv                             │
│ Finds: 2 BUY orders (TATAMOTORS, VEDL)                     │
│ Updates dashboard: trades_today = 2                         │
│ Bot knows: "Already traded these 2 today, skip them!"      │
└─────────────────────────────────────────────────────────────┘