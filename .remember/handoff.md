# Handoff Note — 2026-09-07/08 (fv2 VM session)

## Current State — SMC Liquidity concept fully tested, all 4 variants ruled out

Recovered the prior Liquidity/FVG/OB concept work and backtest results from a bookmarked
claude.ai session into `strategies/smc/` (`02_concepts_summary.md` replaced with the
detailed version, `03_backtest_results.md` new, `diagrams/`, a reference script). Then
built and ran a fresh 4-variant matrix for Liquidity against DS3 (full history, 2015-02-02
to last month-end): {swing low, swing high} × {long, short}.

**Result: all 4 ruled out.** V0 (swing low+long)=0.661 ZPF, V1 (swing low+short,
contrarian)=0.823, V2 (swing high+short, true mirror)=0.798, V3 (swing high+long,
contrarian)=0.691 — all below actual viability (1.0). V1 and V2 cleared the (newly
lowered) soft-triage gate of 0.75 and got the full SL-sweep+alpha rigor: both show
**confidently, decisively NEGATIVE alpha** (p<0.001, CIs entirely clear of zero, at
every single SL value tested, not just the locked combo) — a real negative edge, not
just "not there yet." Full tables: `strategies/smc/04_liquidity_findings.md`.

**Confirmed a real structural parallel** to the flagship ma_short/ma_long_flip family
(same touch-condition × entry-direction 2×2 shape): V1 (contrarian short on the
bullish-looking swing-low setup) is the strongest of Liquidity's 4 variants — exactly
mirroring why `ma_long_flip` was the one flagship variant that got locked.

**Also recalibrated `backtesting_rules.md` §12's viability gate**: lowered `ZPF<0.85 →
ruled out` to `ZPF<0.75 → skip the full rigor` (soft pre-triage, not a final verdict).
Found the old 0.85 would have wrongly killed 3 of the 6 currently-locked flagship
variants at their own raw-round stage (`ma_short_v1`=0.815, `ma_short_v2vwap`=0.834,
`ma_long_flip_v0`=0.841 — all below 0.85, all locked anyway).

All 4 Liquidity variants logged to `strategies/smc/nifty.csv`/`basket.csv` in the new
standard cross-strategy format (`backtesting_rules.md` §14) — V0/V3 recorded as
`RULED_OUT` in the alpha columns rather than silently dropped.

## Immediate next steps (in order)

1. **FVG (index 05)** — same 4-variant-matrix discipline as Liquidity (build the 4
   combinations, smoke test, full 90-combo sweep each, soft-triage at 0.75, full rigor
   for whichever qualify). Follow `01_plan.md`'s ordering.
2. Then **OB (index 06)**.
3. DS3 data bug (ICICIBANK/ITC/SBIN zero-filled OHLC, 2015) — still unresolved, use
   direct Kite Connect API, not Kite MCP's broken `get_historical_data`.
4. Diff-review `strategies/_archive_pre_strategies_consolidation/` — low priority.
5. Live bot core file renaming — deferred "to another day," not blocking anything.

## Key methodology locked this session (apply going forward)

- **Soft pre-triage gate is now 0.75, not 0.85** — a raw-round ZPF below this isn't
  worth the full SL-sweep+alpha rigor (extrapolated healthy-subset score would still be
  ~0.66, and no filter in this project's history has closed a gap that wide). This is a
  screen to save compute, NOT a final ruled-out verdict — the real decision has always
  been the Table 2/3 rigor.
- **Entry-cutoff formula, not fixed numbers**: `ENTRY_CUTOFF_TIME=14:50` is universal
  (property of the entry bar's own runway to EOD); the signal-time cutoff is derived
  backward per strategy: `signal_cutoff = 14:50 - (bars_from_signal_to_entry × 5min)`.
  Never reuse the flagship's 14:45 verbatim for a structurally different signal chain.
- **4-variant matrix discipline for any new SMC concept**: {which structural extreme
  triggers it} × {entry direction} — build and test all 4 combinations before declaring
  a concept dead or alive, following the same parallel-prediction-then-check approach
  used for Liquidity (predict from the flagship's own touch/flip pattern, then verify).
- **Standard cross-strategy comparison format is `backtesting_rules.md` §14** — reuse
  this exact column set (matches `monthly_reconciliation.py`'s report shape) for any
  future strategy comparison log, logging RULED_OUT variants explicitly rather than
  omitting them from the record.

## Known issues / open threads

- **Background-task flakiness this session**: multiple `run_in_background` launches
  were silently killed with zero system-level evidence (no OOM, no crash trace in
  dmesg/journalctl). Workaround used: run in the foreground with a long timeout — it
  auto-moves to background on timeout without hitting the same issue. Not root-caused;
  worth watching for again next session, and worth trying background launches again to
  see if it was transient.
- TODO.md P2 (MemLabs #53 feature-screening decision point) — still untouched.
- Kite token needs manual weekend refresh — not relevant this session (no monthly_recon
  work done), but will resurface whenever that thread picks back up on a weekend.
