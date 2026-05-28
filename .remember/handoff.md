# Handoff Note — 2026-05-27

## State
- h5_full.html: p04 NaN rendering bug fixed (line 133)
- RELIANCE tb3: now shows 153 (correct) after fix
- NTPC tb3: JSON=162, HTML=179 — bug not yet fixed, different root cause (p04 not active)
- All 5-stock Optuna JSONs validated: tb3 wins 3-2, p11 universal across all variants

## Next
1. Fix NTPC discrepancy — check p05/p08/p09/p10/p11 eval logic in HTML vs Python
2. Walk through h5_optuna_batch.py
3. Build 30-stock signal + Optuna batch (2022, tb3)

## Known Issues
- NTPC 162 vs 179: active params are p05/p08/p09/p10/p11 — p09 (bounce_vr_rel) uses null check, possible mismatch
- Walk-forward (2023-2025) is planned after 30-stock sweep confirms breadth generalization
