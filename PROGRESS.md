# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Cleaned and rebuilt two standalone baselines: ma_bounce.py (LONG) + ma_rejection.py (SHORT)
2. LONG bare confirmed: N=49,062 PF=0.922 Sharpe=-1.458
3. SHORT bare confirmed: N=47,787 PF=1.079 Sharpe=1.455 — positive all 4 years, 27/30 stocks
4. baseline_reserve/ma_bounce.py locked clean; CLAUDE.md rule added for folder protection
5. Next: lock both baselines → analyse SHORT edge → build SHORT v1 (wick-only mirror)

── MILESTONES (5 most important) ────────────────────────────
1. fv2 LONG bare locked: N=49,062 PF=0.922 | 30 stocks 2022-2025
2. fv2 SHORT bare confirmed: PF=1.079 Sharpe=1.455 | positive edge all 4 years
3. v1.1 (v1 + Above VWAP + Below EMA100): PF=1.010 N=8,377 — best long edge found
4. SHORT structural direction confirmed: rejects MA more reliably than bounces — 27/30 stocks
5. Version hierarchy: ma_bounce=LONG bare, ma_rejection=SHORT bare — two clean reference scripts
