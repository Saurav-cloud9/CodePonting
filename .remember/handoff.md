# Handoff Note — 2026-07-19

## Current State — fv2 backtesting (6BCE / TODO.md thread)
- 6BCE SHORT confirmed dead (best ZPF=0.888, all 90 combos below 1.0, ZSh(D) negative everywhere)
- Cache built: sweep_cache_6bce.npz with overall_grid + yearly_grid + yearly_zshd_grid
- 4 chart scripts in Backtesting Extended/6BCE/ — all working, all load from cache
- Old P1 (Sharpe daily/entry-hour script fixes) is DONE — TODO.md renumbered, cloud engine is now P1

## Current State — Kite paper trading bot (Algo_Trading/kite_oracle_papertrading/)
- Kite auth working (kite_auth.py); TATAMOTORS→TMPV mapping confirmed, DS3 unaffected
- Data architecture locked: ticks-only live engine, historical_data for offline reconciliation only
- SL=2.0x/TP=4.5x locked and re-validated (PF=1.135, Sharpe=2.358, N=110,641)
- Offline paper-trading engine built + validated (own the ~0.0036% N discrepancy — floating-point
  tie-break, root cause fully diagnosed, documented, not a bug — see today.md for detail)
- Full detail/build plan also tracked in Algo_Trading/kite_oracle_papertrading/SESSION_SUMMARY.md

## Next Step (START HERE)

### fv2 backtesting thread
1. **P1 — Cloud engine**: build backtesting REST API on Oracle Cloud (primary) / AWS (fallback)
2. **P2 — baseline_reserve**: copy ma_bounce.py + ma_rejection.py from baseline_explorations/
3. **P3 — New signals via Grok**: feed backtesting_rules_v2.md to Grok; delegate 90-combo sweeps
4. **P4 — v1_vwap sweep**: no fresh 90-combo sweep done yet
5. **P5 — DS3 recompute (parked)**: only revisit if real inconsistencies appear, not the known
   floating-point tie-break already documented

### Kite paper trading bot thread
1. Add position sizing (1% risk, compounding) to the offline engine — currently per-share PnL only
2. Wire up the real shortability/MIS check (currently stubbed as always-True)
3. Build the reconciliation script (script 2) — compares live/paper output vs Kite's official bars
4. Build the actual live script (KiteTicker ingestion, warm-up pull, reconnect handling)
5. Build automation wrapper (cron on Oracle Cloud VM, EOD report generation) — deploy target is
   the Oracle Cloud VM, not local PC (local is dev/test only)

## Known Issues
- Old baseline sweep scripts (baseline_explorations/) still use monthly Sharpe — not compliant with ZSh(D) standard
- v1_vwap (ma_30_rejection_v1_vwap.py) has no 90-combo sweep done yet
- Both baselines (ma_bounce.py + ma_rejection.py) not yet copied to baseline_reserve/
- Kite paper bot: cron cannot automate the actual Zerodha login (2FA/TOTP) — manual login each
  morning to start (option 1); headless automation (option 2, stored creds + pyotp) to test later
- Kite paper bot: first genuine live test can only happen during real market hours — no historical
  tick data API exists to dry-run against beforehand
