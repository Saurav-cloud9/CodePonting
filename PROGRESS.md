# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. WSL/Ubuntu installed on laptop; SSH connection to Oracle Cloud VM established (161.118.164.160) using found key; VM rebooted to clear pending updates
2. VM environment set up: python3-pip, python3-venv, kite_bot_env virtual env with kiteconnect/pandas/numpy/python-dotenv installed
3. Live bot deployed to VM (scp of live.py + core.py + .env + kite_auth.py); found + fixed a real rate-limit bug (30 sequential kite.ltp() calls with no delay — batched into 1 call; added delay to warm-up's historical_data loop)
4. Bot ran successfully on VM and produced real bars/logs, but found a significant new bug: VM's system clock causes Kite tick timestamps to resolve in UTC not IST (bar times off by 5:30, and EOD_HOUR check would fire at the wrong real-world time) — fix identified (set VM timezone via timedatectl) but not yet applied
5. Bot process silently exited on the VM after ~2 bar cycles with no visible crash reason yet — needs investigation (check original terminal for a traceback) before trusting unattended VM runs

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Live bot now has a confirmed-working full daily lifecycle on local PC: connect → warm-up → trade → EOD tick-exit → auto-stop (2026-07-21, verified at real market close)
4. Bot successfully deployed and run on the actual Oracle Cloud VM for the first time (2026-07-22) — the real eventual deployment target, not just local PC
5. Kite paper-trading bot architecture established: shared core logic + offline engine + live engine + reconciliation script (Algo_Trading/kite_oracle_papertrading/)
