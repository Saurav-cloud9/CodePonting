# Session Log — 2026-07-22

## Kite Paper Trading Bot — first VM deployment (Algo_Trading/kite_oracle_papertrading/)

### WSL/Ubuntu installed on laptop
- Confirmed WSL wasn't installed (matches yesterday's finding); installed via `wsl --install`
  (needed elevation/UAC, and a restart which we'd deferred yesterday specifically to avoid
  interrupting live testing — no longer a concern once bot was stopped)
- Set up default Ubuntu user, declined telemetry opt-in
- Clarified along the way: WSL is local-only (unrelated to Oracle account, which is
  cloud/browser-based and not device-specific); WSLg (GUI Apps) is for running Linux GUI
  programs locally, unrelated to remote VM access, which needs actual remote-desktop
  software (RustDesk/VNC/RDP) if ever wanted — deferred as unnecessary for this headless
  server use case

### SSH connection to Oracle Cloud VM established
- Found and validated SSH key (Framework_V2/oracle key/ssh-key-2026-07-11.key)
- VM: 161.118.164.160, user `ubuntu`, instance-20260712-0412
- Copied key into WSL's native filesystem (~/.ssh/oracle_key, chmod 400) — avoids the
  Windows-mounted-file permission issue that would make SSH refuse the key
- First connection showed "System restart required" — rebooted via `sudo reboot`,
  reconnected successfully after ~30s. Kernel confirmed up-to-date post-reboot

### VM environment set up
- Found already present: Python 3.12.3, git 2.43.0. Missing: pip3
- Installed: python3-pip, python3-venv
- Created virtual environment (~/kite_bot_env) — needed since Ubuntu 24.04 blocks direct
  system-wide pip installs (externally-managed-environment restriction)
- Installed inside venv: kiteconnect, pandas, numpy, python-dotenv (explicitly skipped
  matplotlib/plotly — those are backtest-engine-side needs, VM only executes+logs trades)

### Live bot deployed to VM
- Only the 2 files actually needed for the live bot were copied (not the whole scripts/
  folder — offline engine, reconcile script, reference backtest, sweep script all stay
  local per the division of labor agreed this session): ma_30_rejection_v1_live.py,
  ma_rejection_v1_core.py, plus .env and kite_auth.py at the papertrading root
- First scp attempt failed silently (folders created but empty) — root cause: commands
  were run in PowerShell using WSL-style paths (`/mnt/c/...`, `~/.ssh/oracle_key`), which
  don't resolve in Windows' own shell. Fixed by re-running from an actual WSL Ubuntu
  terminal (Windows Terminal → dropdown → Ubuntu), where the paths correctly matched
- Second attempt succeeded, verified all 4 files present via `ls -la` on the VM

### Real bug found and fixed: Kite API rate limiting on the VM
- First VM run failed immediately: `kiteconnect.exceptions.NetworkException: Too many requests`
- Root cause: instrument-resolution loop made 30 sequential `kite.ltp()` calls with zero
  delay; warm-up loop made 30 sequential `kite.historical_data()` calls with zero delay.
  This worked "by accident" on the laptop because natural network latency there happened
  to keep us under Kite's ~3 req/sec limit — the VM's lower latency to Kite's servers
  blasted through the limit fast enough to actually trigger it
- Fixed: batched the 30 `kite.ltp()` calls into a single request (Kite's `ltp()` accepts a
  list natively — `kite.ltp([f'NSE:{sym}' for sym in UNIVERSE])`); added `time.sleep(0.34)`
  between each `historical_data()` call in warm-up (that endpoint can't be batched, it's
  inherently per-instrument)

### Bot ran successfully on VM — with a significant new bug found
- After the rate-limit fix, bot connected, warmed up, and started producing real bars
- Temporarily bypassed EOD_HOUR to 16 (since first successful connection happened after
  real 15:00 IST) to observe the remaining minutes before actual market close; reverted to
  15 afterward (both locally and re-synced to VM) once testing was done for the day
- **Timezone bug found**: bars showed timestamps like "09:35" instead of the expected
  "15:05" IST. Root cause: Kite's tick `exchange_timestamp` gets parsed via
  `datetime.fromtimestamp()` (both inside pykiteconnect's own code and our fallback),
  which converts using the RUNNING MACHINE's system timezone. The laptop happened to be
  set to IST already, masking this entirely during local testing — the VM defaults to UTC
  (standard for cloud servers), so every bar timestamp came out 5:30 behind. This isn't
  just cosmetic — the EOD_HOUR check (`bar['hour'] >= 15`) would fire at the wrong real
  moment on the VM as it currently stands (3pm UTC = 8:30pm IST, not 3pm IST)
  - Fix identified (set VM's system timezone via `timedatectl set-timezone Asia/Kolkata`)
    but NOT YET APPLIED — first priority next session
- **Bot silently exited**: after saving bars through 09:40 UTC (two full cycles across all
  30 stocks), the live console stopped printing, and separately `ps aux | grep python3`
  confirmed the bot process had fully exited — no crash/traceback captured yet. The CSV
  data itself is intact through that point (proves it wasn't frozen mid-cycle, it fully
  finished processing then stopped existing as a process). Needs checking the original
  launch terminal for whatever error/exit reason is sitting there — deferred to next session

### Concepts clarified along the way (useful reference)
- scp vs sftp vs ftp: scp/sftp both SSH-based (encrypted), FTP is a separate older
  protocol; scp is direct point-to-point transfer, not a "temp staging" copy
- scp must run from whichever side has a reachable public IP + listening SSH server (the
  VM), not the other way around — laptop has neither, so transfers always originate locally
- python venv purpose: isolates this project's package versions from system Python and
  other projects, required practically on Ubuntu 24.04 due to its system-package protection
- WSL (Windows Subsystem for Linux) vs cloud CLI tools (oci/az/aws): WSL is an OS-level
  compatibility layer for running an actual Linux kernel; cloud CLIs are just normal
  programs making API calls — no "Windows Subsystem for Oracle/Azure/AWS" concept exists,
  cloud services aren't operating systems needing that kind of integration

## Key numbers
- VM: 161.118.164.160, ubuntu@instance-20260712-0412, Ubuntu 24.04 (noble), Python 3.12.3
- Rate-limit fix: instrument resolution 30 calls → 1 batched call; warm-up gets 0.34s delay/symbol
- Bot produced 2 full bar cycles (09:35, 09:40 UTC / 15:05, 15:10 IST) across all 30 stocks
  before silently exiting — CSV confirms data integrity up to that point

## Next session priorities
1. Investigate the silent VM process exit — check original launch terminal for traceback
2. Fix VM timezone: `sudo timedatectl set-timezone Asia/Kolkata`, re-verify bar timestamps show IST
3. Re-run full-day test on VM once both above are resolved
4. Run recon script (locally) against the VM's live_bars.csv/live_trades.csv once a clean
   run exists, same workflow as local-PC reconciliation
5. Older open items still carried forward: reconcile script's fetch-window bug (misses EOD
   trades), MA20/ATR14+touch-eval logging, SUNPHARMA reconstruction mismatch unresolved
