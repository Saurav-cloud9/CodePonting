# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SIF.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Continued the alpha/beta CAPM regression math-mode thread (VM session, 2026-08-22/23): built a
   new `52_mathmode_full_derivation_expanded.md` (every algebra line shown, companion to the
   existing compact `_chronological.md`), fully deriving Steps 0-6 with a parabola-shape aside/
   cross-check, the Cov(x,y)/Var(x) expansion proof, and two understanding-checkpoint summaries
2. Deep-dived Step 6's n-2 degrees-of-freedom correction with a concrete 10-residual worked
   example (8 free + 2 forced by the two normal-equation constraints) plus a matplotlib dark-mode
   chart comparing Var(n) vs Var(n-2) — `52_mathmode_variance_dof_example.py`/`.png`
3. Continued conversationally through Steps 7-12 (weighted-sum rewrite, Cov(ȳ,β)=0 proof, general
   SE(ŷ at x0) formula, SE(α) special case, confidence-interval-vs-prediction-interval
   distinction) — not yet written into the expanded file; chronological file already has all 14
   steps in compact form
4. Renamed the "SS"/"save state" shorthand to "SIF"/"save information" project-wide across all
   CLAUDE.md files on the VM (main + kite_oracle_live_trading x2 + kite_oracle_papertrading +
   backtesting), including `kbss`→`kbsif` and `SSD`→`SIFD` in the main file
5. Fixed a PostToolUse hook bug (`log_modified.py` invoked via relative path, broke when a prior
   Bash `cd` changed the shell's cwd) by switching to an absolute path in `settings.local.json`;
   also added a VM-hostname-based skip to the git-sync Stop-hook reminder (not needed mid-session
   on the VM itself, since it's the primary workspace now)

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Live bot now has a confirmed-working full daily lifecycle on local PC AND on the VM: connect → warm-up → trade → EOD tick-exit → auto-stop
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), crash-safe position recovery, warmup-boundary duplicate/gap bug fully fixed, and data-loss-on-restart fixed — all tested and confirmed working on real market data (2026-07-23/24)
5. Model C (online PA learning) conclusively shown to have no transferable edge on real trading data (BTC vs POWERGRID eta0 sweeps share zero overlap) — establishes that raw signal strength (Pearson r) must be verified before any model-complexity investment, reinforcing the same rigor bar set by the NIFTY50-gate debunking (2026-08-16)
