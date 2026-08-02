# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. MemLabs: built a genuinely autoregressive model (x=previous trade's PnL, y=current trade's PnL) matching the author's actual technique — found a real, if modest, OOS edge at live SL/TP 2.0/4.5 (Baseline ZPnL -79.18 → Model -50.41), but the edge nearly vanishes at the "best" sweep combo 6.0/6.0 (ZPnL -66.60 → -63.53) — traced to wider SL/TP diluting trade adjacency (holding +81%, gaps +30%), a real collateral-damage tradeoff to keep in mind
2. ATR formula exploration (12 variants: Simple/Wilder × 10/14/20 × Signal/Entry source) delegated to Grok and validated — ZPF spans only 0.760-0.767, current live formula (Simple14/Signal) is already the best of the 12. Closed out: ATR formula/period/source is not a lever that fixes strategy viability
3. Bulk-renamed SL/TGT → SL/TP across the project (~130 files content-edited, 32 renamed) — Framework_V2/V1/V0, baseline_reserve, paper_trading_bot_ec2_backup, CLAUDE.md, TODO.md; excluded kite_oracle_papertrading (already independent SL/TP), worktrees, PROGRESS_HISTORY.md; audited post-run for accidental token/hash corruption — clean
4. Kite bot: deliberately tested 3 real mid-session restarts (09:51, 10:14, 10:35) with open positions live — all successful, validating the weekend's catch-up/discard fix under real conditions. Fixed the PnL summary line (trailing footer after all 30 stocks, catch-up buckets now included) and added `archive_daily_logs()` for automatic EOD CSV archiving
5. MemLabs: computed direct Pearson r across 6 candidate features (ATR%, RSI14, MACD%, EMA100/HMA100/VWAP-relative-position) — ALL showed negligible correlation, confirming no single-feature linear relationship exists for this strategy on TATAMOTORS

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Live bot now has a confirmed-working full daily lifecycle on local PC AND on the VM: connect → warm-up → trade → EOD tick-exit → auto-stop
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), crash-safe position recovery, warmup-boundary duplicate/gap bug fully fixed, and data-loss-on-restart fixed — all tested and confirmed working on real market data (2026-07-23/24)
5. MemLabs autoregressive model (matching author's actual video technique) found a real, if modest, OOS edge on TATAMOTORS at live SL/TP — first genuinely positive ML result after single-feature linear methods (bucketing/OLS/online-learning, 6 features) were fully exhausted with negative verdicts (2026-07-24 to 07-31)
