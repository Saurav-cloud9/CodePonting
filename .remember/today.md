# Session Log — 2026-07-24

## baseline_reserve_lock terminology cleanup
- Renamed TGT→TP across all 4 files in the locked folder (ma_30_rejection.py, ma_30_bounce.py,
  sl_tgt_sweep_baseline_short.py, sl_tgt_sweep_baseline_long.py, iteration_log_new.md) for
  consistency with the project's SL/TP naming standard - variables, print labels, table
  headers/docstrings only. Case-sensitive replace (TGT uppercase = metric label, tgt
  lowercase = filenames) meant the two script filenames and two output PNG filenames were
  left untouched automatically/deliberately, since renaming those would require updating
  cross-references in other folders (archive/, scripts/trials/baseline_explorations/) that
  weren't in scope. All 4 .py files verified to still parse cleanly (ast.parse check) after
  the rename - confirmed it's purely cosmetic, no behavior change (standalone scripts, no
  external imports of these variable names).
- Also fixed the markdown table alignment in iteration_log_new.md (center-aligned all
  columns via `:---:` - right-align alone still looked off given header/value length
  mismatches).

## MemLabs regime-model work (first real implementation, not just concept)
- New folder: Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/ (separate
  "memlabs" subfolder under regime_model, since more regime-based video ideas may come later)
- **01_build_trade_log.py**: generates a trade log for a chosen symbol/year-range using the
  exact same signal logic as the live Kite bot (imports StockState/process_bar directly from
  ma_rejection_v1_core.py, not a reimplementation), reading from the correct DS3 parquet
  source (Framework_V2/data/historical/intraday_5min_DS3/ - NOT the fv2 CSV folder, caught
  and corrected this early). For each trade, reconstructs the touch bar (positionally, one
  row before entry_dt - not a blind 5-min subtract, to be safe against gaps) and attaches two
  features: atr_pct_at_touch (raw, instantaneous ATR% reading) and hidden_atr_pct_rollmean40
  (rolling-40-mean of that ATR% series - the actual MemLabs "memory encoding" technique,
  computed with no lookahead). Also added ZPF/ZSh(D) metrics (borrowed the exact Zerodha
  charge formula from baseline_reserve_lock/ma_30_rejection.py, adapted field names).
  TATAMOTORS 2023: N=316, PF=1.415, ZPF=0.894, ZSh(D)=-0.835, win rate 44.6%.
- **02_bucket_by_memory_feature.py**: splits trades into tertiles (Low/Mid/High) by the
  memory-encoded feature value, reports PF/ZPF/ZSh(D)/win-rate per bucket - same idea as an
  SL/TGT sweep table, just sweeping across the feature's value range instead of strategy
  params. On 2023 alone: Low-vol bucket showed ZPF≈0.997 vs ~0.86 for Mid/High - looked like a
  real regime effect at first.
- **03_compare_raw_vs_memory_encoded.py**: direct raw-vs-memory-encoded comparison (same
  bucketing, but on atr_pct_at_touch instead of the rolled version) to test whether the
  40-bar smoothing actually adds value over the raw instantaneous reading. Surprising 2023
  result: raw ATR% showed a MUCH stronger split (ZPF spread 0.943 vs memory-encoded's 0.142),
  with the High-vol bucket hitting ZPF=1.442, PF=2.004, win rate 54.7% - stronger and in the
  OPPOSITE direction (high vol wins, not low vol) from what memory encoding suggested.
- **04_build_trade_log_full_range.py**: same pipeline, widened to the full DS3 range
  (2015-2025) to test whether either 2023 pattern was real or a single-year fluke.
  N=3,697 trades, PF=1.324, win rate 45.7%.
- Reran 03's comparison on the full range: BOTH patterns weakened dramatically. Raw ATR%'s
  best bucket became Mid (ZPF=1.042), not High (which dropped to 0.944). Memory-encoded
  spread shrank to 0.066 (basically flat, no bucket meaningfully different).
- **05_bucket_yearwise.py**: year-by-year breakdown per bucket, fixed cutoffs from the
  full-sample tertiles. This was the real verdict - every single bucket (raw and
  memory-encoded) swings wildly between good (ZPF>1.5) and bad (ZPF<0.6) years with no
  consistent winner. The full-sample averages were just smoothing over high year-to-year
  variance, not reflecting a real persistent effect. One artifact caught and flagged:
  memory-encoded Low bucket, 2020, showed ZPF=6.446 but only N=5 trades - pure noise, not
  a real result, explicitly called out as such.
- **Conclusion so far**: neither raw ATR% nor its 40-bar-smoothed version shows a robust,
  persistent single-stock regime effect on TATAMOTORS across 11 years. Honest negative
  result - the promising 2023-only numbers were overfitting to one year, not a real pattern.
- **06_ols_demo_small_sample.py**: built to explain the concept, not for research value - a
  10-trade OLS fit (X=hidden feature, y=pnl) with a plotted scatter+fitted-line chart
  (dark_background per convention), to walk through w/b/y_hat mechanics concretely. Used to
  clarify that memory encoding (the feature) and the actual prediction model (fitting
  w/b via regression, generating y_hat, taking sign() as a signal) are two separate steps -
  we've only done the first (feature engineering); bucketing was a descriptive stand-in for
  the second (the model), not the model itself.
- Clarified along the way: "regime prediction" is a loose phrase - the memory-encoding step
  measures the regime directly (a computed indicator), it doesn't predict it; what actually
  gets predicted (via the regression) is the future outcome/return, using the regime as
  context, not the regime itself.

## Grok CLI note (deferred, not yet used)
- Confirmed grok CLI is installed (~/.grok/bin/grok) and can be invoked via Bash directly in
  the same terminal (not a separate environment) - it's actually an agentic coding tool
  ("Grok Build TUI"), not a simple one-shot Q&A API, with a `-p`/`--single` flag for headless
  single-turn prompts if we want non-interactive output. Confirmed cost isn't a concern
  ($700/mo flat, already committed). Deferred actually using it for independent validation of
  the memlabs trade log - to be picked up next session.

## Key numbers
- TATAMOTORS 2023 baseline (v1 signal, DS3): N=316, PF=1.415, ZPF=0.894, ZSh(D)=-0.835
- TATAMOTORS full 2015-2025: N=3,697, PF=1.324, win rate=45.7%
- Bucket tertile cutoffs (full range) - raw ATR%: [0.052, 0.219, 0.322, 3.930]; memory-encoded:
  [0.075, 0.234, 0.329, 2.169]
- No bucket (either feature) sustained ZPF≥1.0 across most years - no persistent effect found

## Next session priorities
1. MemLabs thread: either fit the actual OLS regression (w/b/y_hat/sign - the step we
   skipped, only bucketed so far) as a more rigorous test, or test across multiple stocks
   (single-stock may just be too noisy), or try a different feature entirely
2. Grok CLI: use it to independently validate the memlabs trade log build (offline-vs-offline
   cross-check, same pattern as the earlier Kite bot grok_review.md)
3. Kite bot thread (carried from 2026-07-23, still P1): ATR14 divergence question, remaining
   unexplained trade mismatches, confirm VM's live.py version, fix live_trades.csv data loss
4. Older carried-forward items: reconcile script's fetch-window bug, MA20/ATR14+touch-eval
   logging not yet added to live_bars.csv
