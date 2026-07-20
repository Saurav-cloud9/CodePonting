# Session Log — 2026-07-20

## Kite Paper Trading Bot — first live test (Algo_Trading/kite_oracle_papertrading/)

### Core logic extracted
- ma_rejection_v1_core.py created: StockState, process_bar(), update_indicators(),
  is_shortable() (stub). Data-source agnostic — used by both offline and live scripts
- ma_30_rejection_v1_offline.py refactored to import from core module (no behavior change,
  already-validated logic preserved)

### Live engine built (ma_30_rejection_v1_live.py)
- KiteTicker-based: builds own 5-min bars from real ticks (bucket by timestamp),
  feeds shared core logic for signal/entry, monitors open positions tick-by-tick
  for SL/TP (real-time, not bar-close-only)
- Startup warm-up via historical_data (last 20 candles, wide window) — seeds
  rolling MA20/ATR14 without triggering stale signals
- Reconnect handling: re-runs warm-up to patch any gap (simplified full re-warm,
  not surgical gap-only patch)
- Fixed a path bug during setup: .env path used .parent instead of .parents[1]
  (script lives in scripts/, .env is at the papertrading root)

### First live connection test (market hours, ~12:30pm-3:10pm IST)
- Got fresh Kite access token (daily re-auth via kite_auth.py)
- Confirmed working end-to-end: instrument resolution (30 stocks + TMPV mapping),
  warm-up, KiteTicker connect/subscribe, tick-based bar building, signal detection
- Real signals fired: DABUR, WIPRO, JSWSTEEL (13:55) — first live proof the
  wick-touch signal logic works on real market data, not just DS3 replay
- First live trade closed: WIPRO hit SL. Manually verified the math: entry
  176.23, exit 176.5314286 (= sl exactly), pnl -0.3014286 ✓; SL/TP distance
  ratio = 2.25, matching TP_MULT/SL_MULT (4.5/2.0) exactly ✓

### Two real bugs found and fixed live
1. **CSV PermissionError crash** — periodic/exit CSV save crashed the whole
   script when live_bars.csv was open in Excel. Fixed: wrapped both save paths
   in try/except PermissionError (skip + retry next cycle, no data lost since
   full in-memory list is written each time)
2. **EOD-hour exit was ~5 min late** — original design only checked
   `hour >= EOD_HOUR` when a bar closed (needs the next bucket's first tick to
   detect), meaning a position wouldn't exit until ~15:05 instead of ~15:00.
   Fixed: added a tick-based EOD check (mirrors the SL/TP tick-exit design) —
   fires the instant we cross into an hour>=15 bucket, exits at that instant's
   price (which is that bucket's true open). Fix applied but NOT tested live
   yet (applied after today's session was manually stopped ~15:09 rather than
   restart mid-test) — needs live confirmation tomorrow

### Reconciliation script built (ma_rejection_v1_reconcile.py)
- Bar-level check: our live-built bars vs Kite's official historical_data for
  the same window
- Trade-level check: replay core logic on official bars, compare vs live_trades.csv
- First real run (today's session, 14:25-15:10 window):
  - Bars: 270 official = 270 live (no missing bars either side), but 48/270
    (17.8%) had real OHLC differences up to ₹4.50 (DIVISLAB) — much bigger
    than the DS3 floating-point tie-break scale found earlier
  - Trades: 13 live vs 11 official-replay, only 7 matched
  - Hypothesized causes (not yet fully confirmed with a concrete example):
    (a) first-bar-of-session mid-bucket-start effect (many 14:25 mismatches
    specifically on open price — bot's recorded open = first tick it saw on
    reconnect, not the bucket's true earlier open)
    (b) ticks may be periodic snapshots, not literal 1:1 per exchange trade
    (matches earlier theoretical discussion) — could mean our tick-built bars
    miss brief high/low spikes that Kite's official server-side candle caught
  - Trade-level gap is partly expected by design: live uses tick-precise
    SL/TP exits, official-replay uses bar-close-based checks (same as backtest)
    — some divergence here is intentional, not purely a bug

### Known gap
- live_bars.csv / live_trades.csv get OVERWRITTEN each time the live script
  runs — no persistence across days unless manually archived first. Today's
  session data was NOT auto-archived; user saving it manually. Plan: build
  CSV archival (dated folder) + recon output-to-file saving tomorrow

### Deferred (reaffirmed today, unchanged)
- Position sizing (1% risk, compounding) — still per-share PnL only
- Shortability check — still stubbed as always-True

## Key Numbers
- WIPRO SL trade: entry=176.23, exit=176.5314286, pnl=-0.3014286
- Locked combo: SL=2.0x/TP=4.5x
- Today's recon: 270/270 bars matched (count), 48 with real OHLC diff (max 4.50);
  13 live trades vs 11 official-replay, 7 matched
