# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. VM timezone fixed (Asia/Kolkata applied); systemd service (kitebot.service) built with OnFailure crash-alert hook pushing to ntfy.sh (codeponting-kitebot-x7j2m9) — tested via deliberate kill -9, confirmed desktop + phone push both fire correctly
2. Built + validated event-driven position-recovery (open_positions.json, saved on every open/close) + reconcile_gap_positions() (replays historical_data since entry to check SL/TP hit during downtime) — full end-to-end test on real market data: 6 restored positions, 1 (SUNPHARMA) correctly gap-closed via SL hit, 5 carried forward correctly, independently verified against official Kite data
3. EOD tick-exit validated live (bot auto-stopped correctly at 15:00, all positions closed, open_positions.json empty) + separately via synthetic simulation
4. Ran 4 iterations of VM live testing today (11:00ish, 13:00-13:39, 14:00-15:00) archived to data/trades/daily data/23rdJuly/; original recon script run + new ma_rejection_v1_trade_check.py built (custom start/end window, full-universe replay) to check 3 known bot-uptime windows separately
5. Recon findings: most "mismatches" explained (pre-restart scope, position-guard blocking, connection-gap on bot startup) but one real structural finding — ATR14 (unlike MA20) is sensitive to live-tick-built bar highs/lows vs official bars, causing official-replay SL/TP to diverge from live's actual SL/TP even on correct data; only 2/17 trades checked matched exactly across all 3 windows

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Live bot now has a confirmed-working full daily lifecycle on local PC AND on the VM: connect → warm-up → trade → EOD tick-exit → auto-stop
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), plus crash-safe position recovery with historical gap-check — all tested and confirmed working on real market data (2026-07-23)
5. Kite paper-trading bot architecture established: shared core logic + offline engine + live engine + 2 reconciliation scripts (full recon + custom-window trade_check) (Algo_Trading/kite_oracle_papertrading/)
