# Handoff Note — 2026-07-24

## Current State — fv2 backtesting / regime model thread
- **Real work started today** (previously just concept discussion): built a full pipeline in
  Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/ testing the MemLabs
  "memory encoding" technique (rolling-40-mean of a feature, applied to ATR% instead of the
  video's returns) on the actual MA rejection SHORT strategy (v1 signal, via
  ma_rejection_v1_core.py - same logic as the live Kite bot)
- **Honest negative result**: tested on TATAMOTORS, full DS3 range (2015-2025, N=3,697
  trades). Neither raw ATR% nor its memory-encoded (rolling-40) version shows a persistent,
  stable regime effect - year-wise breakdown shows every bucket (Low/Mid/High tertile)
  swinging between good and bad years with no consistent winner. A striking-looking 2023-only
  result (raw ATR% High bucket, ZPF=1.442) did NOT replicate across the full history -
  overfitting to one year, not a real pattern
- **What's actually been tested vs not**: only did feature engineering (the memory-encoding
  step itself, done correctly) + bucketing (a descriptive stand-in for a real model). Have
  NOT yet fit an actual regression (w/b/y_hat/sign() - the author's real next step). That's
  the natural next thing to try before concluding the whole approach is dead, OR pivot to
  testing across multiple stocks (single-stock signal may just be inherently too noisy)
- MemLabs notebook ($5.50 on Patreon) — still needs card retry, untouched today
- Grok CLI confirmed available (~/.grok/bin/grok, agentic tool with -p for headless mode,
  cost not a concern) - intended for independent validation of the memlabs trade log build,
  not yet actually invoked

## Current State — baseline_reserve_lock/ (locked folder, touched today with explicit permission)
- Renamed TGT→TP throughout all 4 files (variables, labels, docstrings) for terminology
  consistency - explicitly requested and scoped by the user despite the folder normally being
  off-limits. Two script filenames (sl_tgt_sweep_baseline_*.py) and two output PNG filenames
  still say "tgt" (lowercase) - left untouched since renaming them would ripple into other
  folders (archive/, scripts/trials/baseline_explorations/) that reference them by exact name
  - out of scope, user agreed to leave those
- All 4 .py files verified to still parse correctly after the rename (no behavior change,
  purely cosmetic - these are standalone scripts with no external imports of the renamed
  variables)

## Current State — Kite paper trading bot (Algo_Trading/kite_oracle_papertrading/) - carried from 2026-07-23, untouched today
- VM hardened: timezone fixed, systemd + crash-alert (ntfy) working, position-recovery +
  gap-check validated on real trades, EOD exit validated
- Key open question - ATR14 divergence between live's real ATR (built partly from its own
  tick-based bars) and any pure-official-data replay's ATR (MA20 matches well since it's
  close-only; ATR uses high/low which diverge more) - blocks clean trade-level validation
  until resolved. Only 2/17 trades matched exactly in yesterday's window checks
- New data-integrity finding: live_trades.csv silently drops old trades on restart
  (overwrite-when-nonempty, no merge)
- TODO.md: Kite bot still P1, MemLabs promoted from concept to P2 with real findings now

## Next Step (START HERE)

### MemLabs regime-model thread (upgraded from concept to active, real findings)
1. **Decide direction**: fit the actual OLS regression (the step still missing) as a more
   rigorous test, OR test across multiple stocks (not just TATAMOTORS) to see if single-stock
   noise is the real problem, OR try a feature other than ATR%
2. Use Grok CLI to independently validate the memlabs trade-log build (cross-check pattern,
   same as the earlier Kite bot grok_review.md)
3. Buy MemLabs notebook (Patreon, card declined, retry)

### Kite bot thread (P1, carried from 2026-07-23)
1. Decide how to handle the ATR14 divergence for trade-level validation to be meaningful
2. Dig into remaining unexplained trade mismatches (6 "only in live", 2 "only in official")
3. Confirm the VM's live.py is the updated (position-recovery + gap-check) version permanently
4. Fix the live_trades.csv data-loss issue (merge/append instead of overwrite-when-nonempty)
5. Older items: reconcile script's fetch-window bug, MA20/ATR14+touch-eval logging

## Known Issues
- MemLabs: no persistent regime effect found yet from ATR%-based memory encoding, on a
  single stock, across 11 years - real negative result, not a bug, informs next steps
- Kite bot: ATR14 divergence (structural, not a bug) blocks clean trade-level validation
- Kite bot: live_trades.csv silently drops old trades on restart
- Kite bot: reconcile script's (original) fetch-window bug (misses EOD trades)
- Kite bot: MA20/ATR14 + touch-eval not logged to live_bars.csv
- MemLabs notebook purchase blocked on a declined card, needs retry
- Old baseline sweep scripts still use monthly Sharpe — not compliant with ZSh(D) standard
