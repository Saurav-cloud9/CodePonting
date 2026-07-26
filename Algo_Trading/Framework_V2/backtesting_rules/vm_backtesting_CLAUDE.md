# CLAUDE.md — VM Backtesting Environment

> Scoped to ~/backtesting/ on the Oracle Cloud VM only.
> This is a separate, standalone environment — unrelated to the desktop project's CLAUDE.md.

## Session start
- Read `PROGRESS.md` (in this same folder) at the start of every session before doing anything else.

## Hard rule — always follow backtesting_rules.md
- Before writing, editing, or running ANY backtest script, read `backtesting_rules/backtesting_rules.md` in full and follow it exactly (EOD exit logic, ATR14 SL/TGT convention, NPF formula, etc.).
- If a script or request conflicts with what's in `backtesting_rules.md`, flag it and confirm with Saurav before proceeding — never silently deviate.

## Session end
- Update `PROGRESS.md` with what was done — short, one-liner entries, newest at top or bottom (pick one and stay consistent).

## Hard rule — live trading folder is off-limits
- Do NOT touch, read into working context unnecessarily, modify, or run anything inside `~/kite_oracle_papertrading/` unless Saurav explicitly asks for it in this session.
- This backtesting folder (`~/backtesting/`) is fully separate from the live paper trading bot. Never assume backtesting work should extend into or reference the live folder.

## Shorthand
- `vsa` = "very short answer" — reply in 1–2 lines max, no elaboration.
- `SS` = "save state" — update `PROGRESS.md` with what was completed this session (short entries, no ceremony beyond that single file).
- `CCP` = "Context Catch-Up / Peek" — read `PROGRESS.md` only (read-only, no writes), then reply with a 3-part summary: (1) where we are, (2) what's next, (3) any blockers.

## Data
- Local processing only, no live Kite API calls from this environment.
- venv: `backtest_env` (activate via `source ~/backtesting/backtest_env/bin/activate`)
- Packages: pandas, numpy, numba, scikit-learn, pyarrow

## Reference
- `project_instructions.md` (`backtesting_rules/` folder) — additional project context.
