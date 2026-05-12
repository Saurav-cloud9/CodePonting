# Handoff

## State
Line-by-line review of export_h5_signals.py paused at line 46 (covered 34–46).
Line 46 bug fixed: removed hardcoded `prev['close'] > prev['ma20']` from T0 definition — CSV not yet re-exported.
TODO.md updated: F1 (CC source code exploration) promoted to P5. Former F0 (Claude-in-Claude) renumbered F1, kept parked.

## Next
1. Re-run export_h5_signals.py → regenerate powergrid_2022_h5_signals.csv with fixed T0
2. Continue line-by-line review from line 47
3. After review → H5 Lite chart refinement on claude.ai (P1)

## Context
- CSV is stale — must re-export before any H5 Lite work
- 9:15 signals always p03=0 (no prior bars that day) — P4 TODO, no fix yet
- p03 uses low > ma20 (strict); old line 46 used close > ma20 (loose) — mismatch was root cause
- Saurav stepping away to work on Codedex — unrelated to CodePonting
