# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. h5_full.html p10 slider max fixed 9→3 (3 places: slider, default state, reset button)
2. WFA replayed for 5 stocks — confirmed 2022 params degrade across 2023/2024/2025
3. Regime analysis: ATR% and Vol_StdDev% are the strongest separators (best vs worst years)
4. Universal Optuna attempted (30 stocks × 4 years) — abandoned; regime problem prevents any useful universal set
5. Regime filter WFA: ATR14%≥2.25 + Vol_StdDev20%≥65 — 3/5 worst years have zero valid days; NATIONALUM 2024 barely crosses PF 1.0 (0.954→1.004)

── MILESTONES (5 most important) ────────────────────────────
1. fv2 direction locked — 3-gate system (G1/G2/G3) addressing structural gaps vs true MA bounce
2. p11 lookahead fixed → p11_open; p12 dropped — results now live-compatible
3. 30-stock sweep: 9/30 cleared PF≥1.3; 5 both-variant survivors with live-compatible params
4. Regime dependency confirmed — signal works in mean-reverting markets (2022/2023), breaks in trending (2024/2025)
5. Regime filters confirmed as go/no-go gate (not day-level signal filter) — worst years eliminated entirely, not improved
