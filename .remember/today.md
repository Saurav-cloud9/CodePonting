# Session Log — 2026-07-23

## Kite Paper Trading Bot — VM hardening + position-recovery + validation

### Local desktop setup
- Installed kiteconnect package on desktop (was missing); created desktop's own .env with
  KITE_API_KEY/SECRET (pulled from Kite Connect developer console, app "CodePonting-fv2")
- Fixed the same rate-limit bug locally (batched 30 kite.ltp() calls into 1) that had already
  been found/fixed on the VM
- Discovered `.env` is gitignored by design (`.env`/`*.env` in .gitignore) - laptop's .env never
  synced to desktop via git, had to be recreated manually here

### Position-recovery safety net (event-driven)
- Built `save_positions()`/`load_positions()` in ma_30_rejection_v1_live.py: snapshots all open
  positions to `open_positions.json` on every open/close event (not polled) - so a crash never
  loses more than the position mid-write
- Built `reconcile_gap_positions()`: on restart, for any restored position, replays
  `historical_data` since entry against the fixed SL/TP (no indicator dependency needed) to
  check if it was actually hit during the downtime - closes retroactively if so, else leaves open
- Sanity-checked via static code read-through (all position-mutation sites call save_positions),
  then live-tested end-to-end: 6 real open positions on the VM, Ctrl+C stop, restart -> correctly
  restored all 6, gap-check found SUNPHARMA had hit SL during downtime, closed it retroactively
  with the exact correct historical exit price/time - independently re-verified against official
  Kite historical_data (SL breach confirmed at the 13:35 bar, matching exactly)

### systemd + crash alerting
- Built `/etc/systemd/system/kitebot.service` (wraps the live bot) + `kitebot-alert.service`
  (OnFailure hook, curls a push to ntfy.sh on crash) - `systemctl enable`'d for auto-start on
  VM reboot too
- Chose ntfy.sh as the notification channel (free, no account, pub/sub over HTTP) - installed
  as a PWA on desktop (Chrome/Edge, needs browser running in background after reboot) and as
  the native app on phone (survives phone reboots, unlike the desktop PWA)
- Tested end-to-end: killed the bot with `kill -9`, confirmed both desktop and phone got the
  push notification within seconds

### Full-day VM testing (multiple iterations, archived to data/trades/daily data/23rdJuly/)
- iteration1/iteration2: early runs (13:00-13:10, 13:00-13:30) - same continuous bot process,
  not restarts, learned that `live_bars.csv`/`live_trades.csv` only get overwritten once their
  in-memory list is non-empty (a `if trades:` guard), not literally every save cycle - this is
  why old trades (NTPC/JSWSTEEL from ~11am) persisted in early pulls but vanished by iteration4
- iteration3_1/3_2: captured the exact moment position-recovery kicked in after a real restart
  with 6 open positions - 3_1 pulled before the new run's first bar closed (still showed old
  stale live_bars.csv), 3_2 pulled after (fresh data, confirmed gap-check + 2 new live signals)
- iteration4: final end-of-day snapshot after EOD auto-stop - confirmed clean shutdown
  (open_positions.json = {}, all 15 trades in that file properly closed via SL/TP/EOD)

### Recon validation
- Ran original recon script (bar-level + trade-level) against iteration4's full 14:00-15:00
  session - bar-level clean (0 missing bars, diffs mostly on first-bar-post-connect, close
  prices matched exactly in most cases); trade-level showed real mismatches worth investigating
- Independently spot-verified SUNPHARMA (gap-check trade), NTPC and JSWSTEEL (morning trades)
  against raw official historical_data - all confirmed correct on SL/TP price and timing
- Investigated JSWSTEEL's morning entry mismatch (live: 11:05, official: 10:55) - traced to the
  bot likely not being connected yet at the true touch bar (10:50), consistent with unknown
  exact startup time that morning
- Built simulation test for tick-to-bar aggregation logic (bucket_start + OHLC accumulation) -
  confirmed correct in isolation
- Built simulation test for tick-based EOD exit logic - confirmed fires on the exact
  boundary-crossing tick, no duplicate exits, correct PnL/outcome classification

### New script: ma_rejection_v1_trade_check.py
- Built a second, separate reconciliation script (existing ma_rejection_v1_reconcile.py left
  untouched) - accepts --start/--end for a custom time window + --trades-file to point at any
  archived iteration's data, replays the FULL 30-stock universe (not just symbols live traded)
  so it can also catch signals live missed entirely
- Ran it against the 3 known bot-uptime windows today (10:50-11:53, 12:55-13:39, 13:55-15:00) -
  only 2 of 17 checked trades matched exactly (NTPC, PNB@14:05)

### Key finding: ATR14 divergence (real, structural - not a bug)
- Investigating why SUNPHARMA showed 0 official-replay trades in the window-2 check (should
  have matched, we'd already verified it) - found the replay's independently-computed ATR
  (3.107) differs from the live bot's actual ATR (2.986), producing a different SL threshold
  (1940.11 replay vs 1939.87 live) - official bar's high (1940.0) sits between the two,
  meaning replay says "not hit" while live correctly said "hit"
- Root cause: MA20 only uses close prices (which match well between live-tick bars and
  official bars), but ATR14 uses high/low too (which diverge more) - so a pure-official-data
  replay's ATR will never exactly match live's real ATR (built partly from its own live-tick
  bars), even when both are using "correct" data. This is why most trade-level mismatches
  trace back here, not to genuine signal-detection bugs

### Git/VS Code housekeeping (side task)
- Pulled a save-state commit from origin (stashed local WIP first, popped back cleanly)
- Resolved a Settings Sync merge conflict (desktop vs laptop VS Code settings) - merged via
  Accept Combination; excluded workbench.colorTheme from sync (`settingsSync.ignoredSettings`)
  since desktop uses Dark+ and laptop uses Dark Modern intentionally

## Key numbers
- ntfy topic: codeponting-kitebot-x7j2m9
- 3 verified bot-uptime windows today: ~11:00-11:52:28, 13:00-13:39, 14:00-15:00
- 17 trades checked across those windows, only 2 matched exactly against official-replay
- Position-recovery: 6/6 positions restored correctly, 1/6 correctly gap-closed (SUNPHARMA)

## Next session priorities
1. Decide how to handle the ATR14 divergence for trade-level validation to be meaningful
   (options: accept some tolerance band, or find a way to reconstruct live's actual ATR)
2. Dig into remaining unexplained mismatches (6 "only in live", AXISBANK/HINDALCO "only in
   official") once the ATR question is settled
3. Confirm the updated live.py (position-recovery + gap-check) is the version staying on the VM
4. Fix the live_trades.csv silent-data-loss issue (old trades vanish once a new run's first
   save overwrites the file - no merge/append happens)
5. Older carried-forward items: reconcile script's fetch-window bug, MA20/ATR14+touch-eval
   logging not yet added
