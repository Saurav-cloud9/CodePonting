# Handoff Note — 2026-07-19

## Current State
- 6BCE SHORT confirmed dead (best ZPF=0.888, all 90 combos below 1.0, ZSh(D) negative everywhere)
- Cache built: sweep_cache_6bce.npz with overall_grid + yearly_grid + yearly_zshd_grid
- 4 chart scripts in Backtesting Extended/6BCE/ — all working, all load from cache
- Plan: Grok CLI takes sweep/chart work; CC builds cloud backtesting engine

## Next Step (START HERE)
1. **P1 — Script fixes**: (a) daily Sharpe ×√252 in all sweep scripts; (b) entry bar hour check `hour[i+1] >= 15`
   Note: 6BCE scripts already have these correct — fix needed in older baseline scripts
2. **P2 — Cloud engine**: build backtesting REST API on Oracle Cloud (primary) / AWS (fallback)
3. **P4 — New signals via Grok**: feed backtesting_rules_v2.md to Grok; delegate 90-combo sweeps

## Known Issues
- Old baseline sweep scripts (baseline_explorations/) still use monthly Sharpe — not compliant with ZSh(D) standard
- v1_vwap (ma_30_rejection_v1_vwap.py) has no 90-combo sweep done yet
- Both baselines (ma_bounce.py + ma_rejection.py) not yet copied to baseline_reserve/
