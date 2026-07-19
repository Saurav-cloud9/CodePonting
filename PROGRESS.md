# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Kite Connect auth built + validated (kite_auth.py); AVG antivirus SSL interception found and removed
2. TATAMOTORS demerger discovered (→TMPV/TMCV, Nov 2025); DS3 data confirmed unaffected, no rebuild needed
3. Paper-bot data architecture decided: ticks-only live engine; historical_data reserved for offline reconciliation only
4. SL=2.0x/TP=4.5x locked (renamed SL/TGT→SL/TP going forward); re-validated against iteration_log.md
5. Offline paper-trading engine built + validated (bar-by-bar, live-shaped): PF=1.135/Sharpe=2.358 exact match vs reference, N within 0.004% (floating-point tie-break, root cause diagnosed, corroborated by Grok)

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Kite paper-trading bot architecture established: tick-based live engine + offline/reconciliation split (Algo_Trading/kite_oracle_papertrading/)
3. LONG confirmed dead (PF<1.0 across all 90 combos, baseline and v1); SHORT is the only viable direction
4. Zerodha adopted as primary broker metric (ZPF/ZSh(D)); NPF/Kotak archived
5. TATAMOTORS→TMPV corporate action resolved; DS3 dataset confirmed unaffected
