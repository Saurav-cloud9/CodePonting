# Session Log — 2026-09-07/08 (fv2 VM session)

## Recovered prior SMC work from a bookmarked claude.ai session
- WebFetch couldn't render the share link (JS-based page, only an empty pre-render
  shell came through) — Saurav copy-pasted the actual content instead: detailed
  concepts (with locked entry logic + diagrams), a 9-strategy backtest results log,
  and a zip with 9 reference SVGs + an illustrative (non-production) Python script.
- Placed into `strategies/smc/`: `02_concepts_summary.md` replaced with the detailed
  version, `03_backtest_results.md` new (flagged: covers more than SMC — 6BCE variant
  exploration too — and uses a different SL/TP grid than this project's locked
  strategies/, not directly comparable number-for-number), `diagrams/`, reference script.
- Renamed to the zero-padded convention: `plan.md`→`01_plan.md`,
  `smc_concepts_summary.md`→`02_concepts_summary.md`.
- Caught and fixed a real gap: of "5 SMC concepts," Inducement is mechanically the same
  liquidity-grab mechanic as concept #1 — noted explicitly in the file now (4 distinct
  mechanisms, not 5), kept as its own section since it applies across all 3 zone-based
  setups, not just Liquidity.

## Built and drew a fresh Liquidity sweep diagram (04_liquidity_sweep_diagram.svg)
- First attempt had real layout bugs (callout boxes overlapping candles, title
  colliding with markers) — caught via actually rendering to PNG and looking at it
  (cairosvg), not just trusting the SVG source. Redesigned with numbered badges + one
  compact legend instead of five floating paragraph boxes. Clean on the second render.

## Full Liquidity 4-variant matrix — all 4 ruled out
- Two independent axes: which swing extreme triggers the setup (low/high) × entry
  direction (long/short) = 4 variants. Confirmed this maps exactly onto the flagship
  ma_short/ma_long family's own touch/flip structure — predicted V1 (contrarian short
  on swing low) would be strongest (mirrors ma_long_flip, the one flagship variant
  that got locked) and V3 weakest (mirrors ma_short_flip, decisively ruled out) BEFORE
  running V2/V3. V1-strongest held exactly (0.823, best of 4); V3-weakest was close but
  not exact (V0 edged it out at 0.661 vs V3's 0.691) — reported honestly either way.
- Raw 90-combo sweep results (ZPF): V0=0.661, V1=0.823, V2=0.798, V3=0.691 — all below
  real viability (1.0). Cross-checked V1 against the recovered session's own "LSS"
  result (0.808) — close match, validates the fresh engine.
- V1/V2 cleared the soft-triage gate, got full SL-sweep+alpha rigor at TP=3.0 fixed:
  genuine interior peaks (V1: SL=4.5, V2: SL=5.0). CAPM alpha overwhelmingly negative
  at EVERY SL value tested (p from e-29 to e-107) — locked-combo alpha V1=-12.24₹/day,
  V2=-13.45₹/day, both NIFTY+basket cross-validated, CIs entirely clear of zero.
- All 4 logged to `smc/nifty.csv`/`basket.csv` (new standard format, backtesting_rules.md
  §14) — V0/V3 explicitly marked `RULED_OUT` in the alpha columns, not silently dropped.
- Full write-up: `strategies/smc/04_liquidity_findings.md`.

## Recalibrated the viability "ruled out" gate (Saurav's own idea)
- Question raised: was the documented `ZPF<0.85→ruled out` rule ever actually enforced
  for the 6 already-locked flagship variants? Checked their raw-round scores directly:
  3 of 6 (`ma_short_v1`=0.815, `ma_short_v2vwap`=0.834, `ma_long_flip_v0`=0.841) sat
  BELOW 0.85 and got locked anyway after the full Table 2/3 rigor — the real gate has
  always been that rigor, never this raw number.
- Verified the raw→healthy-subset ZPF gap is remarkably consistent (0.083-0.102, mean
  ~0.09) across all 6 locked variants — used this to calibrate the new gate to 0.75
  (implies ~0.66 healthy-subset floor, and no filter tested anywhere in this project's
  history has closed a gap anywhere near the 0.34 needed to reach viability from there).
- `backtesting_rules.md` §12 reworded: 0.75 is now an explicit soft pre-triage check
  ("skip the expensive rigor"), not a final "ruled out" verdict like 0.85 was worded.

## Other infrastructure additions
- `backtesting_rules.md` new §2 warning: flagship's 14:45/14:50 cutoffs are calibrated
  for its 1-bar signal-to-entry chain specifically — any different-length chain (e.g.
  Liquidity's 2-bar sweep→confirm→entry) derives its OWN signal cutoff backward from
  the universal `ENTRY_CUTOFF_TIME=14:50` anchor, never reuses 14:45 verbatim.
- New `backtesting_rules.md` §14: standard cross-strategy comparison row format (all 20
  columns defined) — the format `smc/nifty.csv`/`basket.csv` now use, reusable for any
  future strategy comparison.
- Created `strategies/smc/nifty.csv`/`basket.csv` (no index prefix — running comparison
  logs referenced every time a new concept is tested).

## Extensive CAPM/stats Q&A continued from yesterday (brief, not repeated in full)
Covered: what "§" means, difference between t_alpha (data-derived test statistic) and
t_critical (sample-size-derived threshold), why the CI derivation follows directly from
inverting the t-statistic inequality, and confirmed "confidently zero" requires BOTH a
non-significant p-value AND a narrow CI — a wide CI crossing zero is "inconclusive," not
"confidently zero," regardless of the p-value.

## Known issue: background-task flakiness
Multiple `run_in_background` launches for the V2/V3 full sweeps were killed with zero
system-level evidence (checked dmesg, journalctl, free -h — nothing). Not caused by the
user, not caused by running two in parallel (a solo background launch also got killed).
Worked around by running in the foreground with a long timeout instead (auto-moves to
background on timeout, didn't hit the same issue). Not root-caused — worth retesting
background launches next session to see if it was transient.

Full detail: `PROGRESS_HISTORY.md` 2026-09-07/08 entry. Next-step priorities:
`.remember/handoff.md`.
