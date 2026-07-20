# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Validated Grok's 6BCE VWAP script — logic + spot-check N/ZPF exact match confirmed
2. Computed ConsScr for both VWAP combos; locked SL=6.0/TP=6.0 as best consistency (-2.709)
3. Built equity + drawdown chart for 6BCE VWAP (MaxDD ₹-16,288 vs baseline ₹-28,494)
4. SL/TP terminology locked project-wide (replacing TGT); glossary updated
5. Strategic decision: pursue regime-adaptive online learning model (MemLabs video 2) — 6 months of static filter failures, new angle needed

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired (DABUR/WIPRO/JSWSTEEL), first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Kite paper-trading bot architecture established: shared core logic + offline engine + live engine + reconciliation script (Algo_Trading/kite_oracle_papertrading/)
4. LONG confirmed dead (PF<1.0 across all 90 combos, baseline and v1); SHORT is the only viable direction
5. TATAMOTORS→TMPV corporate action resolved; DS3 dataset confirmed unaffected
