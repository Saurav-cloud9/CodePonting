# Session Log — 2026-05-27

## What was done
- CCP review: confirmed 5-stock Optuna batch results (tb3 wins 3-2 PF, N 10-14% healthy)
- Discussed visual review vs Optuna scaling — decided to scale first, visual review on failures
- Explored all 10 Optuna JSON results: p11 ON in every single variant (universal signal)
- Found and fixed h5_full.html rendering bug: empty-string p04 → `+''=0` → failed range check instead of NA
  - Fix: `r.p04==='' ? NaN : +r.p04` for pbMin/pbMax in parseSignalRow (line 133)
- Found NTPC tb3 discrepancy: JSON=162, HTML=179 — deferred to tomorrow
- Discussed walk-forward plan: train 2022 → validate 2023/2024/2025; 2025 = most valuable OOS year

## Tomorrow
1. Fix NTPC 162 vs 179 discrepancy
2. Walk through h5_optuna_batch.py
3. Scale to 30-stock universe (2022)
