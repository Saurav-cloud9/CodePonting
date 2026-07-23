# Handoff Note — 2026-07-22

## Current State — fv2 backtesting / regime model thread
- No change since 2026-07-21 — untouched this session (Kite bot VM deployment was the focus)
- 6BCE baseline + VWAP variant both confirmed dead (ZPF<1.0 all combos)
- Strategic pivot: pursue regime-adaptive online learning model (MemLabs video 2)
- MemLabs notebook ($5.50 on Patreon) — purchase attempted, card declined, still needs retry

## Current State — Kite paper trading bot (Algo_Trading/kite_oracle_papertrading/)
- **VM deployment achieved for the first time**: WSL/Ubuntu installed on laptop, SSH to
  Oracle Cloud VM (161.118.164.160, ubuntu@instance-20260712-0412) working, venv +
  dependencies set up, live bot files copied over (only the 2 files actually needed:
  ma_30_rejection_v1_live.py + ma_rejection_v1_core.py, plus .env + kite_auth.py)
- **Rate-limit bug found and fixed**: 30 sequential unbatched Kite API calls (worked by
  accident locally due to network latency, broke on the VM's faster connection) — fixed by
  batching instrument resolution into 1 call and adding a delay to the warm-up loop
- **Two NEW unresolved issues found on the VM specifically** (not present when running
  locally, need to be fixed before the VM can be trusted for real use):
  1. VM's system timezone causes Kite tick timestamps to resolve in UTC instead of IST
     (masked locally because the laptop's own clock is already IST) — this also means
     EOD_HOUR would fire at the wrong real-world time on the VM as-is. Fix identified
     (`timedatectl set-timezone Asia/Kolkata`) but not yet applied
  2. The bot process silently exited after ~2 bar cycles on the VM, with no crash visible
     yet — CSV data through that point is intact (rules out a mid-cycle freeze), but the
     process itself stopped existing. Root cause unknown, needs checking the original
     launch terminal's final state/error output
- Older items from 2026-07-21, still open, unchanged: reconcile script's fetch-window bug
  (misses EOD-triggered trades), MA20/ATR14+touch-eval logging not yet added,
  SUNPHARMA reconstruction mismatch unresolved
- TODO.md: Kite bot still P1, no reprioritization needed this session

## Next Step (START HERE)

### Kite bot thread (P1)
1. **Check the VM's original bot-launch terminal** for whatever error/exit reason caused
   the silent process death — top priority, since an unattended VM bot dying silently is a
   real operational risk once this runs unsupervised
2. **Fix VM timezone**: `sudo timedatectl set-timezone Asia/Kolkata` on the VM, then
   re-verify bar timestamps show correct IST (not UTC) on the next run
3. **Re-run a full-day test on the VM** once both above are resolved — today's was cut
   short by the silent exit
4. **Run the recon script (locally) against the VM's live_bars.csv/live_trades.csv** once a
   clean full VM run exists — same reconciliation workflow as local-PC runs
5. Fix the reconcile script's fetch-window bug (extend to session_end inclusive)
6. Add MA20/ATR14 + touch-eval logging to live_bars.csv
7. Resolve the SUNPHARMA reconstruction mismatch using real captured warm-up data
8. Once VM is fully stable: discuss/plan actual cron job deployment

### Regime model thread (P2)
1. **Buy MemLabs notebook** — patreon.com/cw/MemLabs, $5.50, retry the declined card
2. **Build regime-adaptive model for NSE** — adapt online learning (passive aggressive
   regressor) to MA rejection SHORT signal; features: ATR%, vol, regime state; target:
   trade win/loss outcome

## Known Issues
- Kite bot: VM's system timezone (UTC) causes incorrect bar timestamps and would make
  EOD_HOUR fire at the wrong real-world time — fix known, not yet applied
- Kite bot: live bot process silently exited on the VM after ~2 bar cycles, root cause
  unknown — needs the original terminal's output to diagnose
- Kite bot: reconcile script's fetch-window bug (misses EOD trades) — not yet fixed
- Kite bot: SUNPHARMA reconstruction mismatch unresolved — needs live-captured warm-up data
- Kite bot: MODE_FULL fix shows no red flags but not yet validated over a full trading day
  (every VM/local test so far has been partial-day, not a genuine full session)
- Old baseline sweep scripts still use monthly Sharpe — not compliant with ZSh(D) standard
- Both baselines (ma_bounce.py + ma_rejection.py) not yet copied to baseline_reserve/
- MemLabs notebook purchase blocked on a declined card, needs retry
