# BQS_SESSION_SUMMARY.md — Step 4.3 Session Log
# ══════════════════════════════════════════════════════════════
# Sandbox: Framework_V1_Sandbox
# Session date: 2026-03-18
# Covers: BQS export → winner/loser analysis → hypothesis validation approach
# ══════════════════════════════════════════════════════════════


## STARTING POINT

- DS3 baseline confirmed: 28,085 trades | 2022–2025 | CAGR -8.62% | SL=A config
- BQS learning phase complete: 9 metrics defined (from Claude chat consultation)
- Task: attach all 9 raw BQS metrics to every trade, then run winner vs loser analysis


## WHAT WAS BUILT

### Script: bqs_export.py
- Runs the exact same backtest as run_winner.py (no config changes)
- Extended signal generation to capture touch_idx and bounce_idx per trade
- Computes all 9 BQS metrics at trade generation time using raw candle data
- Winner label: exit_reason == "target" (confirmed: all EOD exits have pnl < 0.5 × risk_amt)
- Output: outputs/bqs/bqs_trades.parquet + bqs_trades.csv + mobile copy


## KEY NUMBERS FROM bqs_export.py (2022–2025)

| Stat | Value |
|------|-------|
| Total trades | 28,085 |
| Target hits (winners) | 4,163 (14.82%) |
| Stop loss hits | 11,894 (42.4%) |
| EOD exits | 12,028 (42.8%) |
| EOD profitable (raw) | 7,471 (26.6%) |
| EOD profitable after Upstox charges | 4,967 (66.5% of 7,471) |
| EOD profitable after Kite charges | 5,741 (76.8% of 7,471) |
| **Total profitable after Upstox** | **9,128 (32.5%)** |
| **Total profitable after Kite** | **9,904 (35.3%)** |

Charge flip detail (raw-profitable EOD trades that turn negative after charges):
- Upstox: 2,504 trades flipped (median raw pnl Rs 25.30, charges ~Rs 50.65 avg)
- Kite: 1,730 trades flipped (median raw pnl Rs 18.60, charges ~Rs 35.17 avg)


## BQS LEADERBOARD — 2022–2025

| Rank | Metric | Score (Cohen's d / prop gap) | Verdict |
|------|--------|------------------------------|---------|
| 1 | M5 Hours Until Close | 0.291 | HIGH |
| 2 | M6 Touch Candle Index | 0.286 | HIGH |
| 3 | M8 MA20 Distance % | 0.135 | MODERATE |
| 4 | M2 Bounce Strength % | 0.087 | LOW |
| 5 | M1 Volume Ratio | 0.055 | LOW |
| 6 | M7 Bounce Gap | 0.017 | EXCLUDE |
| 7 | M3 Wick Ratio | 0.005 | EXCLUDE |
| 8 | M4 Candle Color | 0.005 | EXCLUDE |
| 9 | M9 Prev Candle Dir | 0.000 | EXCLUDE |


## M5 HOURS UNTIL CLOSE — BUCKET BREAKDOWN (2022–2025)

| Bucket | Trades | Win Rate | vs Baseline |
|--------|--------|----------|-------------|
| < 1hr | 0 | n/a | — |
| 1–2hrs | 6,809 | 7.55% | -7.27pp |
| 2–3hrs | 6,683 | 14.50% | -0.32pp |
| 3–4hrs | 7,209 | 19.36% | +4.54pp |
| 4–5hrs | 4,936 | 19.63% | +4.81pp |
| > 5hrs | 2,448 | 12.87% | -1.96pp |

Sweet spot: 3–5hrs before close (entries ~10:30–12:30).
Killer bucket: 1–2hrs (6,809 trades at 7.55% — half the baseline).


## THE OVERFITTING DISCUSSION

**Saurav's question:** We want to use the 9 BQS params to get the 9,128/9,904
profitable trades in the output. But how do we avoid overfitting to 2022–2025?

**Key framing established:**
- Wrong goal: "find thresholds that recover the 9,128 trades" → that IS overfitting
- Right goal: "find BQS thresholds that consistently improve win rate on unseen data"
- The 9,128 trades are a consequence of a good filter, not the target itself

**Saurav's refinement:** Don't reverse-engineer the outcome. Instead:
> Find what is common between the 9,128 winners.
> Find what is common between the losers.
> Check how many BQS hypotheses map correctly onto winners vs losers.
> That way we depend on the hypothesis, not the answer key.

This is the right approach: **hypothesis validation, not outcome recovery.**


## THE PIVOT POINT — WHERE THE QUESTION WAS ASKED

At this point in the conversation, CC asked:

> "Before I run this — do you have the original hypothesis direction for each of the
> 9 metrics written down somewhere, or should I infer the 'expected winner direction'
> from the metric definitions and bounce logic?"

**Answer:** BQS_METRICS_REFERENCE.md already existed in the sandbox root with full
hypothesis directions pre-documented (from Claude chat consultation). No inference
needed — the reference file had:
- Hypothesis direction per metric (higher=better / lower=better / sweet spot)
- 2022–2025 observed directions already filled in
- CC instructions for the next steps (P1–P4)


## WHAT HAPPENED AFTER THAT QUESTION

### bqs_full_validation.py was created and run

P1: Re-ran full DS3 2015–2025 (removed 2022+ year filter)
P2: Computed winner vs loser stats on 77,028 trades
P3: Compared direction of each metric vs 2022–2025 reference

**Result: ALL 9 metrics ROBUST — zero reversals across 11 years**

| Metric | 2022–25 Gap | 2015–25 Gap | Direction Match |
|--------|-------------|-------------|-----------------|
| M1 | +0.071 | +0.049 | YES — ROBUST |
| M2 | -0.023 | -0.024 | YES — ROBUST |
| M3 | -0.022 | -0.046 | YES — ROBUST (noise) |
| M5 | +0.347 | +0.325 | YES — ROBUST |
| M6 | -4.090 | -3.845 | YES — ROBUST |
| M4 | +0.005 | +0.0003 | YES — ROBUST (negligible) |
| M9 | +0.0004 | +0.0044 | YES — ROBUST (negligible) |
| M7 | gap=0 highest | gap=0 highest | YES — ROBUST |
| M8 | shallower=better | shallower=better | YES — ROBUST |

M8 bucket detail (2015–2025):
- < 0.3%: 59,366 trades → 16.96%
- 0.3–0.8%: 15,634 trades → 14.43%
- 0.8–1.5%: 1,686 trades → 11.74%
- 1.5–2.5%: 253 trades → 12.65%
- > 2.5%: 89 trades → 11.24%

BQS_METRICS_REFERENCE.md updated with full validation section.


## FINAL BQS METRIC ROLES (POST VALIDATION)

| Metric | Final Role | Use in scoring |
|--------|-----------|----------------|
| M5 Hours Until Close | HIGH | Yes — primary |
| M6 Touch Candle Index | HIGH | Yes — primary |
| M8 MA20 Distance % | MODERATE | Yes — secondary |
| M1 Volume Ratio | LOW | Optional minor weight |
| M2 Bounce Strength % | LOW | Optional minor weight (reversed dir) |
| M3 Wick Ratio | EXCLUDE | No — zero magnitude |
| M4 Candle Color | EXCLUDE | No — zero magnitude |
| M7 Bounce Gap | EXCLUDE | No — 1.4pp range too small |
| M9 Prev Candle Dir | EXCLUDE | No — zero magnitude |


## NEXT STEPS (as of session end)

P1 — Design composite BQS score using M5, M6, M8 (+ optional M1, M2)
P2 — Train score threshold on 2015–2021 only
P3 — Validate CAGR lift on 2022–2025 blind (no threshold tuning on this period)

See: TODO.md P1–P2 for current priorities.
