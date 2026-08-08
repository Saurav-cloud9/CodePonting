# Session Log — 2026-08-06

## Data infrastructure — DS3 gap-fill + NIFTY50 restructure
- Delegated (CCG, new standing pattern established this session) the Jan-July 2026 DS3 gap-fill
  to Grok: all 30 stocks + NIFTY50 daily, 5-min OHLCV, ma20/atr14 recomputed on append. Validated
  the result directly: row counts match exactly, indicator continuity clean across the append
  boundary, zero duplicate timestamps. One flagged anomaly (VEDL, 3 fewer bars) confirmed
  legitimate — Vedanta's real 1:5 demerger, ex-date 2026-04-30, special pre-session that day.
- CLAUDE.md updated: DS3 primary location repointed to Framework_V2's copy (has ma20/atr14
  precomputed, verified byte-identical to fv1's on shared columns); fv1's copy renamed to
  `intraday_5min_archived/` and marked superseded. NIFTY50.parquet moved from fv1 to fv2's daily
  folder, extended from Kite MCP fetch (2016-2025) + prior Yahoo Finance gap-fill for 2015,
  now 2015-02-02 -> 2026-07-31 (2845 rows) after the Grok append.
- New standing convention: `CCG_ORCHESTRATION.md` (project root) as the Claude Code <-> Grok
  task-delegation log, timestamped entries, most-recent-first. `CCG` is now a CLAUDE.md shorthand
  trigger for "write this task there instead of doing it in-session."

## MemLabs regime-signal work — NIFTY50-as-shared-gate hypothesis, tested and largely debunked
- Built notebook 31 (NIFTY50 Model A/B replication) and steps 25-29/32 (fv2 SHORT/LONG trade
  logs, regime-gating scripts) testing whether NIFTY50's own daily Model A/B signal could gate
  fv2's real SHORT strategy trades across all 30 stocks.
- Initial single-split result looked promising (mean ZPF=1.008, 10/30 stocks >=1.0) but did not
  survive scrutiny: (1) outlier-dependency check showed most "winners" were carried by one single
  historical event (2024-06-04, India election-result market crash) appearing across multiple
  stocks' best trades; (2) after the DS3 refresh shifted the Train/Test boundary, most top
  performers collapsed (NATIONALUM 2.82->0.79 ZPF, VEDL 1.82->0.99, etc.); (3) full WFA (two
  rolling-window configs, 9 and 4 folds, delegated to Grok, verified) showed EVERY single fold
  net-negative in real pooled money terms across both configs — no robust, repeatable edge.
- Established (and corrected) methodology along the way: pooled vs mean-of-ratios ZPF/PF
  (pooled = sum-of-wins/sum-of-losses across combined trades, the more honest metric; mean/
  median only meaningful when explicitly comparing across independent buckets like WFA folds);
  rolling fixed-size Train/Test windows (not expanding) for genuine walk-forward robustness
  testing; confirmed live paper-trading bot's PF is already computed the pooled way.
- Verdict documented in `34_updated_validation_summary.md`: NIFTY50-Model-B-as-gate does not
  show a genuine repeatable edge on fv2's SHORT strategy. Also built the exact same regime-
  gating pipeline for TATAMOTORS' own signal (steps 25-29) with the same negative outcome.

## Pearson's r feature screening — new thread started, in progress
- Established methodology: candidate features must be lagged (no lookahead), screened via
  Train-only Pearson's r/p-value against the fixed target (`close_log_return`), benchmarked
  against Model A's own `close_log_return_lag_1` (r=-0.0087 to -0.0204, always non-significant).
- Built notebook 35: tested RSI(14, Wilder-smoothed, lag-1) on both NIFTY50 (r=0.0212, p=0.33,
  not significant) and TATAMOTORS (r=0.0548, p=0.012, IS statistically significant — beats the
  benchmark meaningfully) — but r^2~=0.3%, i.e. genuinely tiny in practical terms even though
  real. Added colored (actual up/down) scatter plots per user request; walked through why that
  coloring is trivial/tautological here (color = sign of the same value on the y-axis) vs. the
  earlier Model B decision-boundary chart's genuinely independent color check.
- Explicitly NOT yet building a full model around RSI — screening more candidates first (agreed
  plan: volume, gap-size, other indicators) before investing in the heavier build+WFA step,
  given RSI's edge is real but too weak on its own to justify it yet.

## Next session priorities (explicitly agreed)
1. PRIMARY: continue Pearson's r feature screening in notebook 35 — add more candidates
   (volume on TATAMOTORS specifically, since NIFTY50's own volume field is confirmed meaningless/
   mostly-zero; gap-size vs intraday-move as a cleaner target pairing; possibly a different RSI
   period) — looking for a candidate with a genuinely stronger r, not just statistically
   significant.
2. Only escalate to a full Model A/B-style build + WFA once a meaningfully stronger candidate
   (not just RSI's current weak-but-real signal) is found.
3. Separately: August 2026 DS3 gap-fill (once the month closes) — parked in CCG_ORCHESTRATION.md
   pattern for whenever it's next relevant.
