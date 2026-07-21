# Handoff Note — 2026-07-21

## Current State — fv2 backtesting / regime model thread
- 6BCE baseline + VWAP variant both confirmed dead (ZPF<1.0 all combos)
- All charts built: zpf_lines, consistency, spaghetti (ZPF+ZSh(D)), equity+drawdown for both variants
- Strategic pivot: pursue regime-adaptive online learning model (MemLabs video 2)
- MemLabs notebook ($5.50 on Patreon) — purchase attempted, card declined, retry
- SL/TP terminology locked project-wide (was SL/TGT) — no change this update

## Current State — Kite paper trading bot (Algo_Trading/kite_oracle_papertrading/)
- **MODE_FULL fix confirmed root-caused and applied**: MODE_QUOTE never provides
  exchange_timestamp (verified from pykiteconnect source), so ticks were bucketed by local
  datetime.now() instead of real exchange time. Fixed by subscribing in MODE_FULL instead
- **EOD hard-stop confirmed working live**, twice: a temporary 14:00 test cutoff and the
  real 15:00 cutoff (2026-07-21) — tick-based exit fires instantly at the boundary, bot
  waits ~60s grace period for all symbols to close out, then fully terminates itself
- **Reconciliation script improved**: now saves fetched bars + findings to data/recon/
  (was console-only). But has a real bug: fetch window excludes the session_end bar itself,
  so it can never capture an EOD-triggered trade — needs fixing
- **3-vs-0 trade mismatch (today's short test) traced to two causes**, not fully resolved:
  the fetch-window bug above (confirmed sole cause for JSWSTEEL, whose signal timing
  otherwise matched exactly), and the startup-corrupted first bar affecting actual signal
  detection for INFY (suppressed a real signal) and SUNPHARMA (opposite: unclear, my
  reconstruction attempt didn't even match what live actually did — unresolved)
- **warmup_bars.csv logging added** — future analysis won't need error-prone
  after-the-fact warm-up reconstruction like the SUNPHARMA dead-end above
- Oracle Cloud VM setup started: SSH key found (oracle key/ssh-key-2026-07-11.key, valid),
  WSL confirmed NOT installed, install deferred to avoid a restart killing today's live test
- TODO.md reprioritized: Kite bot promoted to P1 (was P3)

## Next Step (START HERE)

### Kite bot thread (now P1 — do this first)
1. **Install WSL + Ubuntu**, then SSH into the Oracle Cloud VM using the found key file —
   this needs a system restart, do it before other work that day
2. **Fix the reconcile script's fetch-window bug** — extend to session_end inclusive (or one
   bar past) so EOD-triggered trades can actually be captured and compared
3. **Add MA20/ATR14 + touch-eval logging** to live_bars.csv — eliminates the manual
   reconstruction that's been needed 3x already (INFY/SUNPHARMA/NATIONALUM), planned but
   not yet done
4. **Resolve the SUNPHARMA reconstruction mismatch** using real captured warm-up data
   (now available going forward) instead of after-the-fact guessing
5. Run a full-day live test to properly validate whether MODE_FULL actually reduced the
   boundary-tick mismatch rate (today's test was only 20 minutes / 4 bars, too short)
6. Discuss/plan cron job deployment once VM is reachable

### Regime model thread (now P2)
1. **Buy MemLabs notebook** — patreon.com/cw/MemLabs, $5.50, retry the declined card
2. **Build regime-adaptive model for NSE** — adapt online learning (passive aggressive
   regressor) to MA rejection SHORT signal; features: ATR%, vol, regime state; target:
   trade win/loss outcome

## Known Issues
- Kite bot: reconcile script's fetch-window bug (misses EOD trades) — not yet fixed
- Kite bot: SUNPHARMA reconstruction mismatch unresolved — needs live-captured warm-up data
- Kite bot: MODE_FULL fix shows no red flags but not yet validated over a full trading day
- Kite bot: WSL not installed, Oracle VM SSH connection not yet established
- Old baseline sweep scripts still use monthly Sharpe — not compliant with ZSh(D) standard
- Both baselines (ma_bounce.py + ma_rejection.py) not yet copied to baseline_reserve/
- MemLabs notebook purchase blocked on a declined card, needs retry
