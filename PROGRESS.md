# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. HMA20 bounce backtest created (hma_bounce_backtest.py) — 30 stocks, PF=0.944 raw
2. fv2 baseline confirmed: no volume filter better (PF 0.918, N=51k vs 0.906 with vol)
3. BHARTIARTL adopted as reference stock; TGT-WR/PFT-WR terminology locked
4. Trading ABC (TV community script) explored: 5-step logic dissected, screenshot taken
5. Trading ABC Step 4 (bounce check) identified as bounce-dedicated sub-signal

── MILESTONES (5 most important) ────────────────────────────
1. fv2 direction locked — 3-gate system (G1/G2/G3) addressing structural gaps vs true MA bounce
2. MA Bounce parked — ITC W/(W+L) decays 34.4%→22% across 2022-2025; no filter fixes it
3. Kijun Bounce backtested — 50-day HL optimal; Top 6 PF=1.489; too low frequency for standalone
4. Data rule established — fv2 backtests use only fv2 CSV (5-min resampled to daily); no DS3/fv1 parquets
5. Kijun period sweep complete — 50-day confirmed optimal; shorter periods all fail (WR < BE)
