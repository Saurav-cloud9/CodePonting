# Session Log — 2026-07-21

## 6BCE VWAP — validation + charts

### Grok script validated
- Logic review: VWAP formula correct (TP=(H+L+C)/3, intraday reset), strict close<VWAP, exit priority correct, Zerodha SHORT charges correct, daily ZSh(D) correct
- Spot-check SL=4.0/TP=6.0: CC got N=71,873 / ZPF=0.895 / ZSh(D)=-1.319 — exact match with Grok
- Minor flag: np.isnan(vwap) doesn't catch inf (if volume=0), low risk in practice

### ConsScr computed and verified
- SL=4.0/TP=6.0 (Best ZPF): ConsScr=-2.905 — matches Grok exactly
- SL=6.0/TP=6.0 (Best ConsScr): ConsScr=-2.709 — matches Grok exactly
- Locked SL=6.0/TP=6.0 as best combo for 6BCE VWAP variant

### Equity + drawdown chart
- chart_equity_6bce_vwap.py built and run
- N=70,269 / ZPF=0.8916 / PeakEquity=₹1,122 / MaxDD=₹-16,288
- VWAP filter nearly halves max drawdown vs baseline (₹-28,494)
- Both still FAIL (ZPF<1.0)

## Terminology
- SL/TP locked as standard going forward (replacing SL/TGT)
- Glossary updated in TODO.md

## Strategic direction — regime adaptive model
- 6 months of static regime filter attempts all failed OOS
- MemLabs video 2 (How to handle Regime Changes) identified as the right approach
  - 4 methods: sliding window, hidden states, online learning, RL+entropy
  - Online learning (passive aggressive regressor) most directly applicable
  - Key idea: model updates weights on every new data point, not frozen after training
- Concept is instrument-agnostic — confirmed applicable to NSE stocks
- MemLabs notebook ($5.50) attempted purchase — card declined, retry tomorrow
- Decision: buy notebook as reference, adapt to NSE stocks with CC

## Key numbers
- 6BCE baseline best: SL=6.0/TP=6.0, ZPF=0.888, MaxDD=₹-28,494
- 6BCE VWAP best consistency: SL=6.0/TP=6.0, ZPF=0.892, MaxDD=₹-16,288

---

## Kite Paper Trading Bot (CC session, Algo_Trading/kite_oracle_papertrading/)

### Root cause found: MODE_QUOTE never provides exchange_timestamp
- Read pykiteconnect's ticker.py source directly: exchange_timestamp/last_trade_time are
  only populated in FULL-mode packets (184 bytes), never in QUOTE-mode packets (44 bytes)
- Live script was subscribing in MODE_QUOTE — meaning `t.get('exchange_timestamp')` was
  silently returning None on every tick, all of yesterday, falling back to `datetime.now()`
  (local receipt time, not the exchange's actual trade time) for bucketing ticks into bars
- Fixed: switched to `ws.set_mode(ws.MODE_FULL, tokens)` — no other code change needed,
  the existing `t.get('exchange_timestamp') or datetime.now()` line now gets the real value

### EOD hard-stop added and confirmed live (two tests)
- Added `eod_reached` threading.Event + grace-period logic: once any symbol crosses into an
  hour>=EOD_HOUR bucket, wait ~60s (2 cycles) for all 30 symbols to individually close out,
  then fully shut down (close websocket, final save, exit process) — not just idle
- Test 1: temporarily set EOD_HOUR=14 (13:06 start, ~50min wait avoided by testing at next
  whole hour since EOD_HOUR only supports hour-granularity). 3 positions (INFY, JSWSTEEL,
  SUNPHARMA) open at 13:55 all closed via TICK EXIT (EOD+/EOD-) exactly at 14:00:00, then
  bot auto-stopped cleanly
- Test 2 (real EOD_HOUR=15, reverted after test 1): 3 positions (ICICIBANK, CIPLA,
  NATIONALUM) open at 14:55 all closed via TICK EXIT at 15:00:00/15:00:02, bot auto-stopped
- Both fixes confirmed working at actual market hours, not just theoretically

### Reconciliation script improvements
- Now saves both fetched bars (official_bars_<date>.csv) and findings (recon_<date>.md) to
  new data/recon/ folder, instead of console-only output. Gitignore updated (official_bars_*.csv)
- Re-ran against yesterday's (2026-07-20) session: identical numbers to the manual run,
  confirms determinism
- Ran against today's short EOD-test session (13:40-14:00, 120 bars): 32/120 mismatched,
  but 27 of those are all at 13:40 (first bar of session, known mid-bucket-startup artifact,
  unrelated to the MODE_FULL fix) — only 5 scattered elsewhere, smaller than yesterday's.
  Sample too short (4 bars/stock) to confirm the timestamp fix definitively; needs a full-day run

### Real bug found in reconcile script: fetch window excludes the EOD bar
- `if dt >= session_end: continue` means the script never fetches/processes the bar at
  session_end itself — so it can NEVER see an hour>=EOD_HOUR bar and NEVER records an
  EOD-triggered trade, regardless of whether entry signals matched live or not
- This alone explains most of today's "3 live trades vs 0 recon trades" gap, since ALL 3 of
  today's live trades were EOD exits (not SL/TP hits) — needs fixing (extend fetch to
  session_end inclusive, or one bar past it)

### 3-vs-0 trade mismatch traced (two distinct causes, not one)
- JSWSTEEL: recon's touch pattern (13:40/45/50/55 = False/True/True/False) exactly matches
  live's actual entry (13:50 @ 1266.9, touch at 13:45) — signal timing agrees completely.
  0-in-recon here is purely the fetch-window bug above
- INFY: recon shows touch=True at 13:40 already (would enter at 13:45); live's corrupted
  13:40 bar apparently didn't satisfy the touch condition, so live's engine stayed flat and
  caught the next real touch (13:45) instead, entering one bar later at 13:50
- SUNPHARMA: opposite direction — live's corrupted 13:40 bar appears to have produced a
  signal that ISN'T present in a clean reconstruction. Attempted to verify by replaying
  live's own bars with a freshly-fetched warm-up: reconstruction showed touch=True only at
  13:50, but live's actual trade (entry_dt=13:45) implies its real engine saw the touch at
  13:40 — meaning the reconstruction doesn't even match what live actually did. Root cause
  NOT fully resolved — most likely the warm-up data fetched just now doesn't exactly match
  what live's engine had at its real start time, but this needs live-captured warm-up data
  (see next item) to confirm properly rather than more after-the-fact guessing

### Warm-up bars now logged
- Added warmup_bars.csv output to the live script (tagged with symbol + warmup_run_at) —
  future analysis can use the actual captured warm-up data instead of error-prone
  after-the-fact reconstruction (which is what caused the SUNPHARMA dead-end above)
- Deferred: adding MA20/ATR14 + touch-eval columns directly to live_bars.csv — would
  eliminate manual reconstruction entirely; planned for tomorrow's session

### Automation planning (cron + login)
- Cron mechanics discussed: launches script only, doesn't solve daily manual Kite login
  requirement (option 1). Headless automated login (option 2) technical shape discussed
  (Selenium/Playwright + pyotp for TOTP) but real risks flagged: storing actual account
  credentials (bigger blast radius than API keys), and Zerodha's login flow likely has
  fraud/bot detection (CAPTCHA etc.) since scripted login isn't the sanctioned automation
  path (API+token flow is) — decision: stick with manual login (option 1) for now, try
  option 2 later purely as an experiment, not for production
- Confirmed manual login can be done entirely from phone (browser login + Termius SSH to
  run kite_auth.py on the eventual VM) — closes the loop for cloud-only operation

### Oracle Cloud VM setup — started, paused
- Found SSH key: Framework_V2/oracle key/ssh-key-2026-07-11.key (valid RSA private key)
- Confirmed WSL is NOT installed on this machine (`wsl --status` fails)
- Installing WSL requires a system restart, which would have killed the live bot test in
  progress — deferred actual WSL install until after today's live testing finished
- Not yet done: actually installing WSL/Ubuntu and connecting to the VM — next session

## Key numbers (Kite bot)
- MODE_FULL fix: exchange_timestamp confirmed populated only in 184-byte (FULL) packets,
  never in 44-byte (QUOTE) packets — verified directly from pykiteconnect source
- EOD test 1: 3 trades (INFY +0.60, JSWSTEEL -0.10, SUNPHARMA +0.90) all EOD-exited at 14:00:00
- EOD test 2 (real): 3 trades (ICICIBANK +0.00, CIPLA +1.30, NATIONALUM +0.30) all EOD-exited at 15:00:00-15:00:02
- Recon test (13:40-14:00): 120 bars, 32 mismatched (27 at first-bar-of-session, 5 scattered)
- TODO.md reprioritized: Kite bot now P1
