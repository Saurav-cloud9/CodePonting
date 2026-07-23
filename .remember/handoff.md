# Handoff Note — 2026-07-23

## Current State — fv2 backtesting / regime model thread
- No change since 2026-07-21 — untouched again today (Kite bot VM hardening was the focus)
- Strategic direction still: regime-adaptive online learning model (MemLabs video)
- MemLabs notebook ($5.50 on Patreon) — still needs card retry, untouched today

## Current State — Kite paper trading bot (Algo_Trading/kite_oracle_papertrading/)
- **VM hardened for unattended operation**: timezone fixed (Asia/Kolkata), systemd service
  (kitebot.service) built + enabled for auto-start on reboot, crash-alert via ntfy.sh push
  (topic: codeponting-kitebot-x7j2m9) tested end-to-end on both desktop (PWA) and phone
  (native app) - fires correctly on kill -9
- **Crash-safety built and validated on real market data**: event-driven position-recovery
  (open_positions.json) + reconcile_gap_positions() (replays historical_data since entry to
  check SL/TP hit during downtime). Full real test today: 6 open positions, Ctrl+C, restart -
  all 6 restored, 1 (SUNPHARMA) correctly gap-closed via SL hit, independently re-verified
  against official Kite data
- **EOD exit validated**: live (clean auto-stop at 15:00, all positions closed) + simulation
- **Full-day testing done, archived**: data/trades/daily data/23rdJuly/iteration1-4/
- **New script built**: ma_rejection_v1_trade_check.py - custom --start/--end window,
  full-universe replay (existing ma_rejection_v1_reconcile.py left untouched)
- **Key open question - ATR14 divergence**: official-replay's independently-computed ATR14
  differs from live's actual ATR (live's ATR is partly built from its own tick-based bars,
  which have known high/low discrepancies vs official bars - unlike MA20 which is close-only
  and matches well). This causes SL/TP mismatches in trade-level validation even when the
  underlying signal logic is correct. Only 2/17 trades checked today matched official-replay
  exactly (NTPC, PNB@14:05) - most "mismatches" are NOT real bugs, they trace back to this
  ATR issue, position-guard blocking (recovered positions blocking new signals), or the bot
  simply not being connected yet during a given touch bar
- **New data-integrity finding**: live_trades.csv silently loses old trades - the save logic
  only overwrites the CSV once the current run's in-memory `trades` list is non-empty, so old
  trades vanish (not appended/merged) once a new run's first trade closes and triggers a write
- TODO.md: Kite bot still P1, reprioritized with today's findings

## Next Step (START HERE)

### Kite bot thread (P1)
1. **Decide how to handle the ATR14 divergence** for trade-level validation to be meaningful -
   options: tolerance band on SL/TP comparison, or find a way to reconstruct live's actual
   ATR retroactively (would need the live bot to log its own ATR at touch time, not currently
   logged)
2. **Dig into remaining unexplained mismatches** once ATR question settled: 6 "only in live"
   trades (ASHOKLEY, BHARTIARTL, JSWSTEEL, NATIONALUM, PNB, VEDL - all in window 3) and
   AXISBANK/HINDALCO "only in official-replay" cases with no obvious explanation yet
3. **Confirm which live.py version is actually on the VM** - today's position-recovery +
   gap-check code was pushed once for testing; verify it's staying there permanently
4. **Fix the live_trades.csv data-loss issue** - old trades get silently dropped on restart,
   should merge/append instead of blind overwrite-when-nonempty
5. Older items still open: reconcile script's fetch-window bug (misses EOD-triggered trades),
   MA20/ATR14+touch-eval logging not yet added to live_bars.csv
6. SUNPHARMA reconstruction mismatch (from 2026-07-21, local/pre-VM) - likely superseded by
   today's live SUNPHARMA gap-check validation; re-check if still relevant or can be dropped

### Regime model thread (P2)
1. **Buy MemLabs notebook** — patreon.com/cw/MemLabs, $5.50, retry the declined card
2. **Build regime-adaptive model for NSE** — adapt online learning (passive aggressive
   regressor) to MA rejection SHORT signal; features: ATR%, vol, regime state; target:
   trade win/loss outcome

## Known Issues
- Kite bot: ATR14 divergence between live's actual (tick-built) ATR and any pure-official-data
  replay's ATR — structural, not a bug, but blocks clean trade-level validation until handled
- Kite bot: live_trades.csv silently drops old trades on restart (overwrite-when-nonempty, no
  merge) — should be fixed before relying on it as a full-day source of truth
- Kite bot: reconcile script's (original) fetch-window bug (misses EOD trades) — not yet fixed
- Kite bot: MA20/ATR14 + touch-eval not logged to live_bars.csv — would make future debugging
  of exactly this kind of mismatch much easier if added
- Kite bot: 6 "only in live" + 2 "only in official" trade mismatches from today still
  unexplained pending the ATR question
- MemLabs notebook purchase blocked on a declined card, needs retry
- Old baseline sweep scripts still use monthly Sharpe — not compliant with ZSh(D) standard
- Both baselines (ma_bounce.py + ma_rejection.py) not yet copied to baseline_reserve/
