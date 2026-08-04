# MA Window Sweep — MA-alone & Model B (2026-08-04)

## Question
Author's 40-day rolling window for `close_log_return_ma_lag_1` was never explicitly justified
as tuned in the video. Is 40 an arbitrary/poor choice, or does the Train/Test generalization
gap we found persist regardless of window size?

*(Correction, 2026-08-04: the author's "we haven't done any hyperparameter optimization"
remarks (transcript timestamps 16:30, 18:04, 19:43, 22:54 in `19_memlab_regime_transcript.md`)
are specifically about Model C — the Online Learning / Passive-Aggressive regressor — not
MA-alone or Model B. No transcript quote confirms he deliberately left the 40-day window
untuned; it's simply a manual feature-engineering choice with no hyperparameter search shown
either way. The window is still "picked, not learned" structurally, since plain
`LinearRegression` has no window parameter to optimize — but that's our own inference, not
something the author states.)*

## Method
Same `backtest_model()` logic as notebook 22, but predicting separately on Train-only and
Test-only slices (not the author's full-combined-df approach) — same fix applied earlier for
Model A/MA-alone/Model B. `test_size=0.25`, `shuffle=False`, same BTCUSDT data
(`BTCUSDT_1d_author_original.csv`). Swept window lengths: 10, 20, 30, 40, 50, 60, 90, 120.

## Results

| Window | MA-alone Train cum | MA-alone Test cum | Model B Train cum | Model B Test cum |
|---|---|---|---|---|
| 10  | 1.1454 | -0.1024 | 3.2400 | -0.2516 |
| 20  | 2.0598 | -0.5619 | 3.1296 | -0.0553 |
| 30  | 2.3826 | -0.7184 | 2.5862 |  0.1608 |
| **40 (author's default)** | 2.5967 | -0.3852 | 2.9164 |  0.0104 |
| 50  | 3.0480 | -0.8805 | 2.3601 | -0.1482 |
| 60  | 2.6756 | -0.2658 | 2.9233 | -0.1910 |
| 90  | 1.8429 | -0.4976 | 1.5941 |  0.0174 |
| 120 | 1.4254 | -0.0301 | 1.8351 |  0.0902 |

## Conclusion

- **MA-alone: negative on Test at every single window tested** (10 through 120). Train cum is
  always strongly positive (1.1 to 3.0), Test cum is always negative (-0.03 to -0.88). This is
  not a "40 was a bad pick" problem — the MA-alone approach itself does not generalize to
  unseen data at any window length tried.
- **Model B: mixed, mostly weak-to-flat on Test**, ranging -0.25 to +0.16 across windows, with
  no window producing a strong positive Test result. 40 (0.0104) is unremarkable — not the best
  (120 gives 0.0902, 30 gives 0.1608) nor the worst (10 gives -0.2516). No clear monotonic
  relationship between window size and Test performance — looks like noise, not a real signal
  the model is picking up.
- **Author's 40-day choice is not an outlier** in either direction — the Train/Test gap found
  earlier (notebook 22) is a structural property of both approaches on this dataset, not an
  artifact of window-length choice. Widening or narrowing the window does not fix it.

## Files
- Raw sweep data (all 8 windows × 2 models, coef_/intercept_ included): `23_ma_window_sweep_raw.json`
