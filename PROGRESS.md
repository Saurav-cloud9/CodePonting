# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. DS3 gap-fill (Jan-Jul 2026, all 30 stocks + NIFTY50 daily) delegated to Grok via new CCG_ORCHESTRATION.md pattern, validated directly — row counts, indicator continuity, zero duplicates all clean. One flagged anomaly (VEDL, -3 bars) confirmed as a real corporate action (Vedanta 1:5 demerger, 2026-04-30), not a data issue
2. NIFTY50-as-shared-gate hypothesis (fv2 SHORT trades gated by NIFTY50's own Model A/B daily signal) built, tested, and debunked — initial single-split result looked promising (mean ZPF=1.008) but full WFA (9-fold + 4-fold rolling windows, delegated to Grok) showed every single fold net-negative in real pooled money terms; top "winners" traced to one dominant historical event (2024-06-04 election crash) and Train/Test-boundary sensitivity, not real edge
3. Established/corrected key validation methodology: pooled (sum-of-wins/sum-of-losses) vs mean-of-ratios ZPF/PF — pooled is the honest metric for combining multiple buckets; rolling fixed-size (not expanding) Train/Test windows for genuine WFA robustness testing
4. CLAUDE.md data architecture updated: DS3 primary repointed to Framework_V2's copy (ma20/atr14 precomputed); fv1's copy archived. NIFTY50.parquet moved to fv2's daily folder, extended through 2026-07-31
5. Started Pearson's r feature screening (notebook 35) as the new active thread — RSI(14, lagged) tested on NIFTY50 (not significant) and TATAMOTORS (r=0.0548, p=0.012, significant but r²≈0.3%, still very weak) — screening more candidates (volume, gap-size) before any full model build

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Live bot now has a confirmed-working full daily lifecycle on local PC AND on the VM: connect → warm-up → trade → EOD tick-exit → auto-stop
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), crash-safe position recovery, warmup-boundary duplicate/gap bug fully fixed, and data-loss-on-restart fixed — all tested and confirmed working on real market data (2026-07-23/24)
5. NIFTY50-as-regime-gate hypothesis fully validated end-to-end (single-split → outlier check → data-refresh sensitivity → full WFA) and conclusively debunked — establishes the rigor bar (pooled ZPF, rolling WFA, outlier-dependency) all future MemLabs findings must clear before being trusted (2026-08-06)
