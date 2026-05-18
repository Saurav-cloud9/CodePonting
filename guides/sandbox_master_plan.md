# Sandbox Master Plan — fv1 (SCRAPPED after Step 4)

## Completed Steps

**Step 1** — fv1 code review + verdict (COMPLETE ✅)
- 13 verdicts in fv1_pending_changes.md

**Step 2** — Sandbox blockers implemented (COMPLETE ✅)
- Changes 1–6 from fv1_pending_changes.md

**Step 3** — Sandbox feature Optuna (COMPLETE ✅)
- Step 3.1 → 16-combo brute-force feature sweep
- Step 3.2 → Optuna on SL variants (A/B/C/D) + 4 features
  - Winner: SL=A, PG+CP+AF, CAGR=-2.15% (DS3) — merged as permanent sandbox defaults
- Step 3.3 → Transaction costs + slippage merged
  - Slippage: 1-tick entry + SL exit
  - Baseline: -8.62% raw CAGR (slippage only, no charges)

**Step 4** — Regime filter Optuna — COMPLETE ❌ (regime filter exhausted)
- Script: `Framework_V1_Sandbox/scripts/sb_regime_optuna.py`
- Outputs: `Framework_V1_Sandbox/outputs/optuna/`
  - best_params.json, top20_trials.csv, optuna_study.db
  - optimization_history.png, feature_importance.png

  - **Step 4.1** → Regime Filter Optuna — 2022–2025 (COMPLETE ✅)
    - Best: Trial #2827, raw CAGR -4.48%, PF9+TF4, OR gate
    - Finding: overfit — zero trades in 2015–2020
    - Verdict: INVALID as general regime filter

  - **Step 4.2** → Regime Filter Optuna — Full DS3 2015–2025 (COMPLETE ❌)
    - 3000 trials, OR gate, 28 params, TPE + 28 warm-up trials
    - Baseline: -100% raw CAGR (capital wiped — every year losing)
    - Best trial #648: raw CAGR -9.43% (2021–2025 only, 34,685 trades)
    - Objective value: -119.37% (includes -110% retention penalty, 45% of baseline kept)
    - Finding: filters act as time-period selectors, not market regime detectors.
      Strategy loses in every year 2015–2025.
    - Verdict: Regime filter approach exhausted with OR gate + 28 features.

  - **Step 4.3** → Bounce Quality Score (NEXT 🔄)

## Upcoming Steps

| Step | Description | Status |
|---|---|---|
| 5 | Full DS3 backtest 2015–2025 with Step 4 winner params | PENDING |
| 6 | Python Phase 2 viewer | AFTER Step 5 |
| 7 | WFA + Optuna | PENDING |
| 8 | Paper trading | PENDING |
| 9 | Live trading | PENDING |

## Parked Items (revisit at Step 7)
- SL=D (trailing, ACT=3.0, TR=0.5)
- Fixed Fractional sizing (SB-G)
- `dir_*` TPE fix in `sb_regime_optuna.py` → always suggest `dir_*` params regardless of parent `use_*` flag.
  Set `warn_independent_sampling=False` in `TPESampler()`. Apply before next Optuna run, not mid-run.
