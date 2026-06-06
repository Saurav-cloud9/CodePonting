# Session Log — 2026-06-05

## CCP
Context catch-up: picked up from regime problem confirmation, Voice Bridge built, 5 survivors identified.

## MA Sweep
- Wrote run_ma_sweep.py (Framework_V2/scripts/)
- First version used .iloc — too slow (~2 min/stock). Rewrote with numpy arrays.
- Results: 10 MA variants across 30 stocks, 2022-2025, best-combo params (tb3)
- EMA15: PF 0.914 (+0.021 vs SMA20 baseline) — top by PF
- EMA25: PF 0.912, Net PNL -4,333 (+0.020 vs SMA20) — top by net PNL
- All MAs still loss-making (PF < 1.0) — MA type is not the fix
- Decision: do NOT switch to EMA25 yet; fix regime first

## Opus Advisor — Regime Filter Plan
Key findings from Opus call:
- Bounce rate as live filter = circular/lagging = fv1 trap. Use only as y-variable.
- Three independent regime metrics: ER + MA20 run-length + Variance Ratio
- Architecture: per-stock daily pre-condition, frozen at prior day's close
- Biggest risk: overfitting on 5 hand-picked survivor stocks (48 monthly buckets)
- Mitigation: lock threshold on 2022-23, test cold on 2024-25 + 25 discarded stocks
- If OOS fails → MA bounce has no edge → pivot to ORB

## Shareable Brief
Full Claude.ai context brief written (paste-ready) covering: problem, three metrics,
architecture, 5-step sequence, risks, file paths, next task.

## Strategy Discussion
- ORB and MA bounce have opposite regime profiles — they're complements
- Agreed: run regime filter test first (1-2 sessions), then decide
- If regime filter fails OOS → pivot to ORB (reuse all fv2 infra)
