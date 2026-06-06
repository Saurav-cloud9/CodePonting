# Handoff Note — 2026-06-05

## State
- MA sweep complete: 10 variants (SMA10-30, EMA10-30) across 30 stocks 2022-2025
  EMA15 best PF (0.914), EMA25 best net PNL (-4,333); all still loss-making (PF < 1.0)
- Confirmed: MA type change does not fix regime problem
- Opus advisor consulted — regime filter plan fully defined and documented
- Bounce rate ruled out as live filter (circular — the fv1 trap)
- Three independent regime metrics chosen: ER, MA20 run-length, VR
- Shareable Claude.ai brief written (paste-ready, self-contained)
- run_ma_sweep.py created: Framework_V2/scripts/run_ma_sweep.py

## Next
1. Regime filter Step 1 — write analysis script: ER + MA20 run-length + VR per stock per day
   Output: CSV with columns stock, date, ER, run_length_mean, VR
   Pure measurement only. No filtering. No decisions.
2. Step 2 — monthly bounce rate per stock (validation target y-var)
3. Step 3 — correlation test on 2022-2023 only, lock threshold

## Known Issues / Critical Constraints
- Regime problem: 2024/2025 break all param combos found on 2022/2023
- Threshold must be fit ONLY on 2022-23 data, tested cold on 2024-25 + 25 discarded stocks (single shot)
- If OOS fails → pivot to ORB strategy (reuse all fv2 infra — F9 in TODO)
- Voice Bridge end-to-end test still pending (P2)
