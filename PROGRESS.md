# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Completed 90-combo sweep for baseline SHORT/LONG + v1 clean-touch SHORT/LONG (DS3 11yr)
2. Locked SHORT baselines: baseline SL=1.5/TGT=4.0 (PF=1.116), v1 SL=2.0/TGT=4.5 (PF=1.135)
3. Updated ma_30_rejection_v1.py with locked combo; iteration_log.md finalized with all 4 runs
4. Reviewed and aligned backtesting_rules_v2.md with CC setup; identified 2 P1 script fixes
5. Updated TODO.md: cloud engine as P2, new signal exploration as P4, ZPF/ZSh(D) fixes as P1

── MILESTONES (5 most important) ────────────────────────────
1. SHORT bare confirmed edge: PF=1.116 Sharpe=2.275 (DS3 11yr, 172k trades)
2. v1 clean-touch improves SHORT: PF=1.135 Sharpe=2.358 (110k trades — cleaner signal)
3. LONG confirmed dead: PF<1.0 across all 90 combos at both baseline and v1
4. Zerodha adopted as primary broker metric (ZPF/ZSh(D)); NPF/Kotak archived
5. Cloud backtesting engine (Oracle primary) identified as next major build target
