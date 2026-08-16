# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Deep-dived MemLabs "Model C" (online/Passive-Aggressive learning) end-to-end: replicated author's BTC numbers (locked eta0=1.0/epsilon=0.0002 via reverse-engineering real screenshots; corrected a second reference-doc error, true hit rate 50.02% not 50.82%), built full toy-walkthrough + 2D/3D visualizations, then tested the same config on POWERGRID (11.5yr DS3) — 50/50b/50c notebooks in memlabs/
2. Found Model C shows NO transferable edge across assets: BTC's best eta0 (0.005, beats buy-and-hold) and POWERGRID's best eta0 (2.0, still loses to buy-and-hold) share zero overlap; BTC's "eta0=1 needs ~3yrs to become profitable" pattern does not repeat on POWERGRID even with 2x the data
3. Root-caused the underperformance to weak underlying signal, not model capacity — Pearson r on close_log_return_lag_1: POWERGRID r=-0.057 (p=0.003, significant but r²<1%), BTC r=-0.037 (p=0.09, not significant); naive "follow yesterday's sign" baseline loses money on both. Confirmed Models A/B/C are all strictly linear, making Pearson r the correctly-matched screening tool
4. Decision: pause Model A/B/C, resume notebook 35 Pearson r feature screening (parallel thread, continued independently — INFY/DIVISLAB data bugs fixed, RSI period sweep done, volume screening done, all weak/negative) as the primary active thread; only return to Model C once notebook 35 finds a meaningfully stronger candidate
5. Mid-derivation, paused: alpha/beta CAPM-style regression (testing POWERGRID eta0=2.0's credibility) — covariance/variance, OLS normal equations, n-2 degrees-of-freedom correction all taught; next step is SE(alpha)/t-stat/p-value. Full recap seeded to `memlabs/50d_full_recap_seed.md` for continuation in a new session (WSL-based, for genuine cross-session messaging)

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Live bot now has a confirmed-working full daily lifecycle on local PC AND on the VM: connect → warm-up → trade → EOD tick-exit → auto-stop
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), crash-safe position recovery, warmup-boundary duplicate/gap bug fully fixed, and data-loss-on-restart fixed — all tested and confirmed working on real market data (2026-07-23/24)
5. Model C (online PA learning) conclusively shown to have no transferable edge on real trading data (BTC vs POWERGRID eta0 sweeps share zero overlap) — establishes that raw signal strength (Pearson r) must be verified before any model-complexity investment, reinforcing the same rigor bar set by the NIFTY50-gate debunking (2026-08-16)
