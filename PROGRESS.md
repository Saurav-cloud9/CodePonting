# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Pivoted from MA Bounce to Kijun Bounce strategy (community indicator, Pine Wizard, 663 boosts)
2. Ported Kijun fv2 Bounce to Python: SL=2.5x TGT=3.0x ATR, long only, EOD exit
3. Tested 5 stocks: Kijun-HL 4/5 PF>1, Kijun-Close 3/5 PF>1
4. Discovered ~11% price gap: Python CSV = demerger-adjusted, TV = unadjusted by default
5. TV ADJ mode result: PF drops to 0.759 — signal fragility confirmed, Python backtest more reliable

── MILESTONES (5 most important) ────────────────────────────
1. fv2 direction locked — 3-gate system (G1/G2/G3) addressing structural gaps vs true MA bounce
2. MA Bounce parked — ITC W/(W+L) decays 34.4%→22% across 2022-2025; no exit tuning fixes signal
3. Kijun Bounce identified — Daily Kijun (50-period) 2-bar bounce; Kijun-HL 4/5 stocks PF>1 on Python
4. Data issue confirmed — ITC Hotels demerger (Jan 2025) causes ~11% price gap TV vs Python CSV
5. Multi-timeframe insight: daily level (Kijun) + 5-min timing = structurally sounder than intraday MA20
