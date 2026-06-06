# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. MA sweep (10 variants, 30 stocks, 2022-2025): EMAs beat SMAs; EMA15 best PF (0.914), EMA25 best net PNL
2. Confirmed: switching MA type does not fix regime problem (all MAs still PF < 1.0)
3. Opus advisor called — regime filter plan defined: ER + MA20 run-length + VR as independent metrics
4. Bounce rate ruled out as live filter (circular/lagging — the fv1 trap); use as validation target only
5. Regime filter 5-step sequence locked; shareable Claude.ai brief written

── MILESTONES (5 most important) ────────────────────────────
1. fv2 direction locked — 3-gate system (G1/G2/G3) addressing structural gaps vs true MA bounce
2. p11 lookahead fixed → p11_open; p12 dropped — results now live-compatible
3. 30-stock sweep: 9/30 cleared PF≥1.3; 5 both-variant survivors with live-compatible params
4. Regime dependency confirmed — signal works in mean-reverting markets (2022/2023), breaks in trending (2024/2025)
5. Regime filter plan locked (Opus): ER + MA20 run-length + VR; fit on 2022-23, OOS on 2024-25 + 25 rejects
