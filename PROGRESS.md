# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Reviewed backtesting_rules_v2.md — aligned with CC; LONG charge flip note added
2. Built 6BCE SHORT 90-combo sweep; best ZPF=0.888 — strategy confirmed dead
3. Created ZPF spaghetti chart (chart_spaghetti_6bce.py) + cache system (sweep_cache_6bce.npz)
4. Extended cache to include yearly_zshd_grid; built ZSh(D) spaghetti chart
5. Best consistency combo: SL=6.0/TGT=5.5 (ZPF=0.887); 6BCE dead — moving on

── MILESTONES (5 most important) ────────────────────────────
1. SHORT bare confirmed edge: PF=1.116 Sharpe=2.275 (DS3 11yr, 172k trades)
2. v1 clean-touch improves SHORT: PF=1.135 Sharpe=2.358 (110k trades — cleaner signal)
3. LONG confirmed dead: PF<1.0 across all 90 combos at both baseline and v1
4. Zerodha adopted as primary broker metric (ZPF/ZSh(D)); NPF/Kotak archived
5. Cloud backtesting engine (Oracle primary) identified as next major build target
