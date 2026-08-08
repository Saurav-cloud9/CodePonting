# Handoff Note — 2026-08-06

## Current State — MemLabs Pearson's r feature screening (PRIMARY focus going forward)
- Notebook 35 (`Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/
  35_pearson_r_feature_screening.ipynb`) is the active file. Scope is deliberately narrow:
  Train-only Pearson r/p-value screening of candidate features against the fixed target
  `close_log_return`, benchmarked against Model A's own `lag_1` (always non-significant,
  r=-0.01 to -0.02). NOT building a full regression model yet — that's a later, separate step.
- Only candidate tested so far: RSI(14, Wilder-smoothed, lagged 1 day). Result: NIFTY50
  r=0.0212/p=0.33 (not significant); TATAMOTORS r=0.0548/p=0.012 (significant, beats benchmark,
  but r^2~=0.3% — real but very weak in practical terms).
- Agreed next candidates to screen (not yet built): volume (TATAMOTORS only — NIFTY50's own
  volume field is confirmed mostly-zero/meaningless, verified directly against the data), gap-
  size (`log(open_today/close_yesterday)`) paired against intraday-move as target (not the full
  close_log_return, to avoid the gap-is-part-of-target overlap issue), possibly other RSI
  periods or a medium-term momentum feature.
- Rule going forward: only escalate to a full Model A/B-style build + WFA once a candidate shows
  a meaningfully STRONGER r than RSI's current weak signal, not just statistical significance.

## Current State — NIFTY50-as-shared-gate hypothesis (CLOSED OUT, debunked)
- Full pipeline built (notebook 31, scripts 25-29/32-33) testing whether NIFTY50's own Model B
  signal could gate fv2's real 30-stock SHORT trades. Initial single-split result looked
  promising (mean ZPF=1.008) but did not survive: outlier-dependency check (most "winners"
  carried by the 2024-06-04 election-crash day), Train/Test-boundary sensitivity (top performers
  collapsed after a data refresh shifted the split), and full WFA (delegated to Grok, 9-fold +
  4-fold rolling configs) — every single fold net-negative in real pooled money terms.
- Full writeup: `34_updated_validation_summary.md`. Established/corrected methodology along the
  way (pooled vs mean-of-ratios ZPF, rolling not expanding WFA windows) — reusable for any future
  multi-bucket validation work, not just this thread.

## Current State — Data infrastructure (DONE, validated)
- DS3 (30 stocks) + NIFTY50 daily both extended through 2026-07-31 via Grok (CCG delegation).
  Validated directly: row counts, indicator continuity, zero duplicates. One flagged anomaly
  (VEDL) confirmed as a real corporate action (Vedanta demerger), not a data issue.
- CLAUDE.md updated: DS3 primary = Framework_V2's copy (has ma20/atr14 precomputed); fv1's copy
  renamed `intraday_5min_archived/`, marked superseded. NIFTY50.parquet now lives in fv2's daily
  folder.
- New standing pattern: `CCG_ORCHESTRATION.md` (project root) for Claude Code -> Grok task
  delegation. `CCG` = CLAUDE.md shorthand trigger for this.

## Next Step (START HERE) - explicitly agreed with the user

### Primary (this session/thread)
1. Continue Pearson's r screening in notebook 35 — add volume (TATAMOTORS), gap-size (vs
   intraday-move target), and any other quick candidates. Compare all r/p values side by side.
2. Once a genuinely stronger candidate is found (not just RSI's weak-but-real signal), build a
   proper Model A/B-style regression + full Train/Test/WFA validation around it.

### Parked / lower priority
1. August 2026 DS3 gap-fill — once the month closes, same CCG pattern as the July fill.
2. Full 90-combo SL/TP sweep x 6 ATR variants via Grok — still not priority, carried over from
   before this session (unrelated to the current MemLabs thread).
3. Separate (Saurav + VM CC, kite bot thread, not this session): live trade validation/recon —
   status unchanged from before this session.

## Known Issues
- None new this session beyond what's already resolved/documented above. Prior known issues
  (TODO.md glossary SL/TP note, ma_30_rejection_v1.py's missing EOD entry-skip) still carried
  over, unchanged, from before this session — not touched tonight.
