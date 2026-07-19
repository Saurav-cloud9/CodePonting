# Handoff Note — 2026-07-18

## Current State
- backtesting_rules_v2.md finalized and aligned; LONG charge direction note added
- Broker switched to Zerodha; metrics are now ZPF + ZSh(D) (daily Sharpe ×√252)
- SHORT baselines locked: baseline SL=1.5/TGT=4.0, v1 SL=2.0/TGT=4.5
- iteration_log.md covers Run 1 (baseline) + Run 2 (v1 clean-touch); v1_vwap not swept yet

## Next Step (START HERE)
1. **P1 — Script fixes**: (a) update Sharpe to daily in all sweep scripts; (b) add `hour[i+1] >= 15` entry skip
2. **P2 — Cloud engine**: build backtesting REST API on Oracle Cloud for mobile/remote use
3. **P3 — Lock baselines**: copy ma_bounce.py + ma_rejection.py → baseline_reserve/

## Known Issues
- All CC Sharpe values to date use monthly method — not comparable to ZSh(D) until scripts updated
- v1_vwap (ma_30_rejection_v1_vwap.py) has no sweep; SL/TGT not locked
- Old broken two-phase sweep scripts (sl_tgt_sweep_short.py, sl_tgt_sweep_long.py) still exist in sweep/ — can be deleted
