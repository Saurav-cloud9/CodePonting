# PROGRESS.md — CodePonting fv1 Sandbox
# One line per completed step. Status only. No lengthy details.
# Update: add new line at bottom when a step completes.
# ─────────────────────────────────────────────────────────────

Step 1    ✅  fv1 code review — 13 verdicts documented in fv1_pending_changes.md
Step 2    ✅  Sandbox blockers implemented (Changes 1–6)
Step 3.1  ✅  16-combo brute-force feature sweep
Step 3.2  ✅  SL variant Optuna — winner: SL=A, PG+CP+AF, CAGR=-2.15% (DS3)
Step 3.3  ✅  Slippage + charges merged — baseline: -8.62% raw CAGR
Step 4.1  ✅  Regime filter Optuna 2022–2025 — overfit (PF9+TF4, zero trades 2015–2020)
Step 4.2  ✅  Regime filter Optuna 2015–2025 — exhausted, no viable regime signal found
Step 4.3  ✅  BQS export: 9 metrics on 28,085 trades; M5/M6/M8 = HIGH signal
Step 4.3b ✅  BQS validation: all 9 metrics ROBUST on 2015-2025 (77,028 trades)

── DATA & INFRA ──────────────────────────────────────────────
DS3 migration  ✅  All 13 sandbox scripts migrated to intraday_5min_DS3
Daily data     ✅  Built from DS3 5-min resample (2015–2025) + yfinance warmup for 28/29 stocks
CLAUDE.md      ✅  Updated with full master plan, baselines, sandbox config, clarification protocol
CLAUDE.md      ✅  Added PROGRESS/TODO protocol + context file links
