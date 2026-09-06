# Session Log — 2026-09-06 (fv2 VM session)

## Parity-checked monthly_reconciliation.py against DS3 — found + fixed 2 real bugs
- Saurav's own idea, following a question about "how confident are we these new replay
  engines actually match strategies/'s locked signals?" — ran each locked family's exact
  signal logic (read straight from `strategies/*/sweep_*.py`, unmodified) on DS3 through
  August, diffed trade-by-trade against `monthly_reconciliation.py`'s saved output.
- Step 1 first ruled out a data-source explanation: DS3 (synced 2026-09-03) and FRESH
  (Kite pull, 2026-09-05) agree on raw OHLCV exactly (45,360 bars, zero mismatches), and
  `update_indicators()`'s formula exactly reproduces DS3's own precomputed ma20/atr14
  across the full 11-year history.
- Step 2 found 5 of 6 locked variants had massive trade-set mismatches — only
  `ma_short_v1` (which reuses `v1_core.process_bar()` directly) matched near-perfectly.
- **Bug 1**: all 3 new standalone replay functions read ma20/atr14 BEFORE calling
  `update_indicators()` for the current bar, not after — a one-bar-stale indicator,
  opposite of `v1_core.process_bar()`'s own (confirmed-correct) ordering. Fixed in all 3.
  `6bce_v0`/`6bce_v1vwap` reached PERFECT parity immediately after this fix alone.
- **Bug 2** (ma_short_vwap + ma_long_flip only): the position-guard skip-ahead (`i=k+1`
  after a trade closes) also skipped calling `update_indicators()` for every bar between
  entry and exit, desyncing the deque from DS3's continuous (never-skips-a-bar)
  computation. Fixed by updating indicators for every bar in the exit-scan loop.
- All 6 variants now show 99.6-100% trade-level parity with DS3. **Pre-fix August numbers
  reported earlier the same day for 5 of 6 variants were wrong and are superseded.**

## Added 95% CI columns to the report
- `ci_low_capm`/`ci_high_capm` (= alpha ± t_critical×SE) added next to
  `alpha_capm_cumulative`. Directly distinguishes "confidently near-zero" (narrow CI
  hugging zero) from "inconclusive" (wide CI crossing zero) from "confidently not-zero"
  (CI clear of zero) — same p<0.05 threshold, very different practical conclusion.
- Concrete case this caught: `ma_long_flip_v0` (p=0.061, CI=(-62.55,+1.49)) is genuinely
  inconclusive, not "confidently zero" as it might otherwise read — same fragility class
  as `6bce_v0`.

## Cleanup + naming lock
- Removed dead `pcap_lookup` code (unused since yesterday's raw-₹ alpha fix).
- `sl_tp` separator changed `/` → `x` (avoids Excel's date auto-reinterpretation of
  slash-joined number pairs).
- Locked naming convention (TODO.md GLOSSARY): `n` = trading days in a CAPM regression,
  `n_trades` = trade count. `metrics()`'s dict key renamed accordingly.
- CLAUDE.md: new section — Pcap/Tcap are live-console-display-only, never for computation
  without Saurav's explicit direction.

## Extensive CAPM/statistics Q&A this session (not repeated in full here)
Covered: t-stat vs t-critical, SE vs raw std vs residual std, CI derivation from the
t-statistic inequality, "confidently zero" vs "inconclusive" vs "confidently not-zero"
framework (with worked real-number examples from August's actual 9 sources), leave-one-out
outlier sensitivity (found `6bce_v0`'s significance flips when its single worst day is
dropped — fragile result), and why alpha magnitude alone doesn't determine significance
(SE matters just as much). See session transcript for full derivations if needed again.

## RS peer check-ins sent (end of session)
cplearning, cpfable, mathmode, cpgeneric — all showed idle in ListAgents, messaged for a
one-line status update. Check for replies before assuming nothing happened elsewhere.

Full detail: `PROGRESS_HISTORY.md` 2026-09-06 entry. Next-step priorities: `.remember/handoff.md`.
