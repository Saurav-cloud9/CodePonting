# Handoff Note — 2026-07-04

## Current State
- Two clean standalone baselines in scripts/trials/baseline_explorations/:
  - ma_bounce.py: LONG bare, N=49,062, PF=0.922, Sharpe=-1.458
  - ma_rejection.py: SHORT bare, N=47,787, PF=1.079, Sharpe=1.455
- Both have: bounds check in j-loop, date guard in k-loop, no dead variables
- baseline_reserve/ma_bounce.py is clean and locked (bounce_bar=None sentinel confirmed)
- SHORT edge confirmed across all 4 years (2022-2025), 27/30 stocks PF>1.0

## Next Step (START HERE)
1. **Lock both baselines into baseline_reserve/** — copy ma_bounce.py + ma_rejection.py from baseline_explorations/ into baseline_reserve/ as the v0 LONG and SHORT reference files
2. **Analyse SHORT vs LONG edge** — structural reasons why rejection beats bounce; use TV visualisation
3. **Build SHORT v1** — wick-only SHORT (mirror of LONG v1 structural modification); proper clean build this time
4. **Equity curve + drawdown + NPF** — on SHORT side before iterating further

## Known Issues
- NPF for SHORT bare ~0.7 (not yet tradeable — need PF ~1.4-1.5 after filters)
- Runner scripts (run_baseline_v*.py in scripts/) still have minor errors — parked P2
- compare_v0_v2.py still has wrong LONG signal — parked, superseded by standalone scripts
