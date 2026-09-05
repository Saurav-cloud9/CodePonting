# Handoff Note — 2026-09-04 (fv2 VM session)

## Current State — Strategy raw-edge search, mid-flight (PRIMARY, resume here)

Working through `Algo_Trading/Framework_V2/strategies/` — consolidated all MA-short/6BCE
variants into one folder today, found and fixed a systematic EOD-riding artifact in the
sweep methodology, confirmed via CAPM alpha testing that the current signal family has a
real, significant NEGATIVE edge (not just insufficient edge), and built a new SL/TP
"sweet-spot" methodology (hold TP fixed, sweep SL, find genuine plateau via ZPF+NetZPnL+
Alpha together — not just where the grid ends).

**Locked today** (SL=4.5x/TP=3.0x, clean interior peak on ZPF+NetZPnL+Alpha all 3):
- `ma_short/v1` (strategies/ma_short/v1/)
- `ma_short/v2_vwap` (strategies/ma_short/v2_vwap/)
- `6bce/v1_vwap` (strategies/6bce/v1_vwap/)

**NOT locked, needs a decision next session**:
- `6bce/v0` — genuine plateau found at SL=7.5-8.0x/TP=3.0x (extended grid to 10.0 to confirm
  it's real saturation, not just grid-edge), but EOD%=56-57% there vs ~47-50% for the other
  3 families' SL=4.5x picks. Open question: accept the higher EOD% since it's a genuine
  saturation point, or hold to SL=4.5x for cross-family consistency? Full numbers in
  PROGRESS_HISTORY.md 2026-09-03/04 entry.
- `ma_long_flip/v0` — same edge-of-grid issue as `6bce_v0` was (all metrics still climbing at
  SL=6.0), but its grid was NOT yet extended past 6.0 — do that first, mirroring what was
  done for `6bce_v0`, before deciding its SL/TP pick.

## Immediate next steps (in order)

1. Extend `ma_long_flip`'s SL grid (script: `strategies/ma_long_flip/v0/sweep_v0.py` — reuse
   the pattern from `6bce_v0_extend.py` in scratchpad, values 6.5-10.0, TP=3.0 fixed) to find
   its genuine plateau, same as was just done for `6bce_v0`.
2. Decide the `6bce_v0` SL/TP question above (needs Saurav's input, not a technical call).
3. Build `ma_long_flip`'s VWAP filter variant — above vs below comparison (mirror the
   `ma_short v2_vwap` decision process: 3-combo comparison, pick the clear winner, then full
   90-combo sweep on the locked signal). Not started at all yet.
4. DS3 data bug (ICICIBANK/ITC/SBIN zero-filled OHLC, 2015) — delegation to cpgeneric via
   cross-session message expired without approval. Either resend it, or fix directly using
   the direct Kite Connect API path (confirmed working — `kiteconnect` library + the live
   bot's own cached `.env` credentials at `/home/ubuntu/kite_oracle_papertrading/.env`). Do
   NOT use Kite MCP's `get_historical_data` — confirmed broken at the app level (generic
   failure even on recent dates; `search_instruments`/`login` work fine on the same MCP
   connection, so it's not a connection issue, just that one endpoint).
5. Once the 5 families' SL/TP picks are all settled, this whole thread's actual end goal is
   updating `monthly_reconciliation.py` on the live bot VM (~/kite_oracle_papertrading/
   scripts/) to include all locked variants for side-by-side comparison — not started yet,
   was the original ask that led into all of today's work.
6. SMC rebuild (Liquidity/FVG/OB standalone, then as filters on MA-short/6BCE) — explicitly
   on hold per Saurav's instruction until the above settles. When resumed: rebuild fresh
   from the locked spec in `strategies/smc/smc_concepts_summary.md` (the original backtest
   results live on a bookmarked claude.ai session Saurav has, not recovered here).

## Key methodology established today (apply going forward)

- **Exit-mix diagnostic is now mandatory** (backtesting_rules.md): any combo considered for
  deployment needs SL%/TP%/EOD+%/EOD-% reported, healthy threshold EOD%<=30%. A raw-ZPF-
  ranked #1 pick sitting at the edge of the swept grid is a red flag — check its exit mix
  before trusting it.
- **SL/TP sweet-spot method**: hold TP fixed (3.0x worked well as the reference), sweep SL,
  and require ZPF, NetZPnL, AND alpha to all show a genuine interior peak (not just "the
  metric flattened because we ran out of grid") before locking a value. Widening SL shifts
  losing trades from SL-hit into EOD- (not EOD+) via the position-guard "blocking" mechanism
  — an EOD-bound trade occupies its stock's slot till 15:00, silently losing any later
  same-day touch signal, while an SL-hit frees the slot for a possible re-entry. This is
  directly visible in falling N counts as SL widens.
- **Multiple-testing discipline still applies**: don't pick a time-window or SL/TP value by
  eyeballing which one looks best on the same data used to select it — validate any such
  choice against a held-out slice (see backtesting_rules.md's out-of-sample guard, added
  today after the earlier eta0/monthly-variant-cherry-picking lessons).
- **Kite MCP vs direct Kite Connect**: two separate access paths into Zerodha, not the same
  app — permissions can differ per-endpoint. Use direct `kiteconnect` (live bot's cached
  credentials) for historical data; Kite MCP is fine for quick interactive lookups.

## Housekeeping done today

- CLAUDE.md corrected: DS3/NIFTY50 date range was stale ("2015-2025"), actually extends live
  to 2026-08-31 and keeps growing — verify actual max date before assuming staleness.
- CLAUDE.md new rule: GIT SYNC BEFORE CROSS-AGENT HANDOFF — commit+push immediately before
  telling another agent/AI (Grok via CCG_ORCHESTRATION.md, or any similar handoff) to read a
  file; a local uncommitted edit is invisible to anything reading via a separate clone/remote.
- 2 commits pushed: `0f954a7` (CCG delegation instructions), `4ac0e9f` (main strategies/
  consolidation + all of today's findings).

## Known issues / open threads

- RS peer check-ins (cplearning, cpfable, mathmode, cpgeneric) sent at end-of-session — no
  replies received before this write. Check `.remember/today.md` or ask them directly next
  session if their status matters.
- Everything in `TODO.md` P2 (MemLabs #53 decision point) is untouched today — still pending
  from before, not addressed in this session.
