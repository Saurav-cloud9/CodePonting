# Session Log — 2026-07-25/26 (weekend session, spanned midnight)

## Kite bot: EOD_HOUR revert + warmup fix completion
- Reverted EOD_HOUR from the temporary 16 (Friday's testing value) back to 15 - both
  locally (ma_rejection_v1_core.py) and pushed to the VM. Confirmed via `date` that this
  was Saturday, so no live-trading-day risk either way, but cleaned up regardless.
- Continued the stale-first-tick discussion from Friday (deferred implementation until
  today, per explicit request to discuss first) - walked through the exact chronological
  sequence (script start -> historical_data loop -> KiteTicker object creation -> connect()
  -> first tick arrival) to pin down precisely where the "which bucket to exclude" decision
  gets made, and confirmed it currently happens too early (right after the historical_data
  loop, before connect()).
- Landed on a MORE COMPLETE fix than originally scoped, through back-and-forth: instead of
  just discarding stale ticks, the bot now (a) discards ALL ticks belonging to the
  connect-time "current bucket" or older, (b) schedules a one-shot catch-up fetch
  (`catchup_current_bucket()`, via `threading.Timer`) to fire exactly 5 minutes later - by
  which point that bucket has genuinely closed - fetching it and running it through the
  FULL `process_bar()` (not just indicator-seeding), so it gets a real touch-check too, not
  just a silent MA20 contribution. This closes both problems: no duplicate, no permanently
  skipped bar, no missed signal opportunity on the transition bucket.
- Implemented in ma_30_rejection_v1_live.py: new module-level `current_bucket` (set by
  warmup()), new `catchup_current_bucket()` function, `on_ticks()` now discards ticks with
  `bucket <= current_bucket`, and the catch-up timer is scheduled in `__main__` right after
  warmup/position-recovery. Verified via `ast.parse` syntax check. NOT yet tested live -
  market was closed all weekend, so this needs its first real test Monday.
- Also fixed the separately-flagged live_trades.csv/live_bars.csv data-loss bug: added
  `load_existing_logs()`, called at the very start of `__main__`, which reads any existing
  CSV data into the in-memory `trades`/`bar_log_rows` lists before the periodic save loop
  begins - so a restart no longer silently drops whatever was already recorded. Verified via
  a standalone simulation (old + new trade both survived a resave). Pushed to VM.
- Both fixes pushed to the VM while the bot was confirmed inactive (safe, no live process
  disrupted).

## MemLabs: online-learning year-wise check (closing out the online-learning thread)
- Built 13_online_learning_yearwise.py - checked whether the earlier promising-looking
  online-learning filtered result (N=479, ZPF=1.01 overall) holds up year by year.
- It doesn't: 6 years pass (ZPF>=1.0), 4 fail (<0.9), 1 borderline - same instability pattern
  as the static bucketing found the day before. Also noticed the filtered N per year grows
  from single digits (2015-2017) to 100+ (2024-2025) - the model isn't staying selectively
  adaptive, it's drifting toward "take almost everything" as more data accumulates.
- This closes out all three approaches tried so far (static bucketing, single-feature OLS,
  online-learning) with the same honest negative conclusion - no persistent ATR%-based
  regime effect found on TATAMOTORS alone, regardless of method.
- Confirmed all memlabs work (scripts 01-13 + output CSVs/PNGs) is committed and pushed to
  git (verified via `git log`/`git status` - clean, up to date with origin/main).

## VM backtesting environment (side quest, via a separate mobile CC session on the VM)
- User set up ~/backtesting/ on the VM themselves (via phone SSH + a separate Claude Code
  instance running directly on the VM, not this session) - folder structure
  (data/scripts/outputs), backtest_env venv (pandas, numpy, numba, scikit-learn, pyarrow).
- From this session: copied Framework_V2/backtesting_rules/ (backtesting_rules.md,
  project_instructions.md) into ~/backtesting/backtesting_rules/; created and pushed a
  VM-scoped CLAUDE.md + PROGRESS.md (session-start/end rules, hard rule to never touch
  ~/kite_oracle_papertrading/ unless explicitly asked, vsa/SS/CCP shorthand, and a hard rule
  to always read+follow backtesting_rules.md before any backtest work); copied two reference
  scripts (ma_30_rejection.py, sl_tgt_sweep_baseline_short.py) into ~/backtesting/scripts/;
  copied the full DS3 dataset (160MB, 30 parquet files) into ~/backtesting/data/DS3/.
- Deliberately did NOT set up a `.remember/`-style deep memory system for this VM
  environment - agreed a single PROGRESS.md is enough for a smaller, single-purpose project;
  the richer split only earns its keep on the main desktop project's multiple concurrent
  threads.
- Deliberately decided NOT to turn the VM folders into a git repo - `CodePonting` (desktop)
  remains the single source of truth, both local and on GitHub; VM stays plain folders synced
  via scp/manual pulls, avoiding the complexity of keeping secrets (.env) and constantly-
  changing data files out of a VM-side git history.

## VS Code Remote-SSH setup (for direct VM file access from desktop)
- Installed the official Microsoft "Remote - SSH" extension (ms-vscode.remote-ssh).
- Set up a Windows-side SSH config (previously only existed inside WSL, not natively
  accessible to Windows' own OpenSSH client that VS Code's extension uses): copied the
  private key to C:\Users\Saurav\.ssh\oracle_key, restricted its permissions via `icacls`
  (Windows equivalent of chmod 400), and created C:\Users\Saurav\.ssh\config with a
  `Host oracle-vm` entry. Verified the connection works via native Windows ssh before
  handing off to VS Code. Confirmed working end-to-end.
- Also set `remote.SSH.remotePlatform: {"oracle-vm": "linux"}` in settings.json (VS Code
  asked once, now remembered).

## CSV viewer preference
- Compared Data Wrangler (already used for .parquet) vs a simpler grid viewer for .csv.
  Landed on the already-installed "Spreadsheet Viewer" (GrapeCity.gc-excelviewer, formerly
  "Excel Viewer") for plain CSV viewing - Data Wrangler is better suited to genuine deep-dive
  cleaning/transformation work, not quick reads. Set via
  workbench.editorAssociations: "*.csv": "gc-excelviewer-csv-editor" (auto-written by VS
  Code's own "Configure default editor" picker, not guessed).

## Side note (informational, no action taken)
- Clarified "headless" (no GUI installed at all, vs. Windows always having a GUI regardless
  of monitor state) - and in the process discovered/confirmed a genuinely different past
  setup: an old EC2 instance (Algo_Trading/paper_trading_bot_ec2_backup/) had a
  `~/start_desktop.sh` script referenced from a local .bat file, meaning a desktop
  environment WAS deliberately installed there for RustDesk-style remote viewing - unlike
  the current Oracle VM, which was built headless from the start on purpose. That old EC2
  instance is presumably no longer active; no follow-up planned, just a clarified memory.

## Next session priorities (explicitly agreed with the user)
1. Kite bot: watch Monday's first live restart under the new catch-up/discard logic
2. Review 24th July's PnL logs + validate against recon, specifically:
   (a) quantify how many of that day's trades were actually affected by the stale-tick bug
   (b) consolidate the day's fragmented iteration snapshots into one clean picture
   (c) remember today's 2 new fixes can only be tested against Monday's fresh data, not
       retroactively against the 24th
3. Resume MemLabs work after the above - likely multi-stock test or a different feature,
   possibly bring in Grok CLI for independent validation first
