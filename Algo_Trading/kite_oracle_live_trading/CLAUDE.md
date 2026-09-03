# CLAUDE.md — kite_oracle_live_trading

> Scoped to this folder only. Placeholder — real-money execution, not paper trading.

## Status: NOT STARTED

This folder is a deliberate anchor/reminder, not active infrastructure. Do NOT build
real order-placement logic, broker-adapter code, or `.env`/credentials here unless
Saurav explicitly asks — doing so would imply a readiness that doesn't exist yet.

## Blocked on (all must clear before real work starts here)
- Paper trading (`kite_oracle_papertrading/`) proving a stable, validated edge
- MemLabs / regime-filter work reaching a real conclusion
- An explicit go-ahead from Saurav to begin live-trading infrastructure

## Shared infrastructure
- Uses the same `~/kite_bot_env` venv as `kite_oracle_papertrading/` (VM) — no separate
  environment needed once real work starts.

## Shorthand
- `vsa` = "very short answer" — reply in 1–2 lines max, no elaboration.
- `RS` = "right save" — update `PROGRESS.md` with what was completed this session.
  On a Linux/VM session, first ListAgents/SendMessage any live peer sessions on this
  machine for a one-line update to fold in (skip if none respond promptly, or if on
  native Windows where cross-session messaging is unavailable).
- `CCP` = "Context Catch-Up / Peek" — read `PROGRESS.md` only (read-only), then reply
  with a 3-part summary: (1) where we are, (2) what's next, (3) any blockers.
