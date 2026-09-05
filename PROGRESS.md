# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every RS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. All 6 strategies/ variants now locked: ma_short_v1/v2vwap (SL=4.5/TP=3.0), 6bce_v0
   (SL=8.0/TP=3.0, accepted higher EOD% as genuine saturation), 6bce_v1vwap (SL=4.5/TP=3.0),
   ma_long_flip_v0 (SL=7.0/TP=3.0), ma_long_flip_vwap (SL=4.0/TP=3.0). Each family's
   sl_sweet_spot.md now records the full SL-sweep table + decision (previously ephemeral).
2. Archived 4 redundant folders (ATR_exploration/, Backtesting Extended/, baseline_
   explorations/, baseline_reserve/) into strategies/_archive_pre_strategies_consolidation/
   via git mv (history preserved, nothing deleted).
3. Rebuilt monthly_reconciliation.py on the live bot VM: replaced the old debunked raw-ZPF
   variant list with the 6 locked LOCKED_VARIANTS, added 2 new standalone replay engines
   (6bce, ma_long_flip) + a VWAP-extended ma_short replay — live bot's own core files
   untouched. Added exit-mix + net_zpnl columns, dual NIFTY/basket-benchmark outputs, and
   an sl_tp combo column per row.
4. Fixed a real alpha-methodology mismatch: to_capm_series() was normalizing daily zpnl by
   pcap (%-of-capital) instead of the strategies/ folder's raw-₹/day convention — pcap was
   confirmed (via kite_oracle_papertrading/PROGRESS.md) to be a console-monitoring metric
   only, not a deliberate alpha choice. Fixed + added alpha_capm_cumulative (=alpha×n, exact
   by OLS construction).
5. August 2026 results: all 9 sources (LIVE/RECONCILE/FRESH + 6 variants) show negative
   alpha point estimates; only some reach p<0.05 this month (one month of data, not a
   verdict). Confirmed significance depends on alpha/SE, not alpha magnitude alone — driven
   by daily-zpnl volatility, not trade count.

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Found + fixed a systematic EOD-riding artifact affecting every fv2 strategy family's top-ranked SL/TP combo (2026-09-04) — raw ZPF rankings were inflated by wide-SL/TP combos barely binding intraday, not genuine edge; now a mandatory backtesting_rules.md diagnostic (SL%/TP%/EOD+%/EOD-%)
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), crash-safe position recovery, warmup-boundary duplicate/gap bug fully fixed, and data-loss-on-restart fixed — all tested and confirmed working on real market data (2026-07-23/24)
5. All 6 strategies/ variants locked + deployed into monthly_reconciliation.py on the live
   bot VM (2026-09-05) — replaces the old debunked raw-ZPF variant list with rigorously
   validated SL/TP combos, correct raw-₹ alpha methodology, and dual NIFTY/basket benchmarks
