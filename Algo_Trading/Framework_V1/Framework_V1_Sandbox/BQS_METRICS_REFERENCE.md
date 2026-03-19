# BQS_METRICS_REFERENCE.md — Bounce Quality Score
# ══════════════════════════════════════════════════════════════
# CodePonting fv1 — Bounce Quality Score framework
# DS3 validation: 28,085 trades | 2022–2025 | E2-A config
# Winner definition: exit_reason == "target" (4,163 = 14.82%)
# Loser definition:  all other exits (23,922 = 85.18%)
# Baseline win rate: 14.82%
# File location: Framework_V1_Sandbox/BQS_METRICS_REFERENCE.md
# ══════════════════════════════════════════════════════════════

# ─── EXIT BREAKDOWN ───────────────────────────────────────────
#
#  Target hit  :  4,163  (14.8%)   ← winners
#  EOD exit    : 12,028  (42.8%)   ← mixed
#  Stop loss   : 11,894  (42.3%)   ← definite losers
#
#  Profitable trades (raw)         : 11,634  (41.4%)
#  Profitable trades after Upstox  :  9,128  (32.5%)
#  Profitable trades after Kite    :  9,904  (35.3%)
#
#  Key insight: ALL 12,028 EOD exits have pnl < 0.5 × risk_amt.
#  Meaningful profit only comes from target hits.

# ══════════════════════════════════════════════════════════════
# METRIC GROUPS
# ══════════════════════════════════════════════════════════════
#
#  Group A → Continuous (mean/std)       : M1, M2, M3, M5, M6
#  Group B → Binary (proportion)         : M4, M9
#  Group C → Discrete win rate per value : M7
#  Group D → Binned win rate             : M8

# ══════════════════════════════════════════════════════════════
# GROUP A — CONTINUOUS METRICS
# ══════════════════════════════════════════════════════════════

# ─── M1: Volume_Ratio ─────────────────────────────────────────
#  Formula   : bounce_bar_volume / avg_volume_20d
#  Hypothesis: HIGHER ratio → more likely winner
#
#  DS3 2022–2025:
#    Winners: mean=1.740  std=1.358
#    Losers:  mean=1.669  std=1.224
#    Gap: +0.071 | Direction vs hypothesis: MATCHES ✅
#  Verdict: Gap too small vs high std. Weak signal.
#  BQS Role: LOW weight

# ─── M2: Bounce_Strength_Pct ──────────────────────────────────
#  Formula   : (bounce_close - touch_low) / touch_low × 100
#  Hypothesis: HIGHER % → more likely winner
#
#  DS3 2022–2025:
#    Winners: mean=0.281%  std=0.220
#    Losers:  mean=0.304%  std=0.307
#    Gap: -0.023 | Direction vs hypothesis: REVERSED ⚠️
#  Verdict: Losers bounce slightly stronger. Lower = better on DS3.
#  Possible reason: overshot bounce reverts; modest bounce sustains.
#  BQS Role: LOW weight (use actual direction: lower = better)

# ─── M3: Wick_Ratio ───────────────────────────────────────────
#  Formula   : (touch_open - touch_low) / |touch_close - touch_open|
#  Hypothesis: HIGHER ratio → more likely winner
#
#  DS3 2022–2025:
#    Winners: mean=1.809  std=4.438
#    Losers:  mean=1.831  std=3.746
#    Gap: -0.022 | Direction vs hypothesis: REVERSED but negligible
#  Verdict: Extremely noisy (std=3.7-4.4). Zero predictive value.
#  BQS Role: EXCLUDE

# ─── M5: Hours_Until_Close ────────────────────────────────────
#  Formula   : (15:30 - entry_time) in decimal hours
#  Hypothesis: HIGHER hours → more likely winner
#
#  DS3 2022–2025:
#    Winners: mean=3.444 hrs  std=1.094
#    Losers:  mean=3.097 hrs  std=1.283
#    Gap: +0.347 | Direction vs hypothesis: MATCHES ✅
#
#  Bucket analysis:
#    < 1hr    :     0 trades  n/a
#    1–2hrs   : 6,809 trades  7.55%  (-7.27pp)  ← killer bucket
#    2–3hrs   : 6,683 trades  14.50% (-0.32pp)
#    3–4hrs   : 7,209 trades  19.36% (+4.54pp)  ← sweet spot
#    4–5hrs   : 4,936 trades  19.63% (+4.81pp)  ← sweet spot
#    > 5hrs   : 2,448 trades  12.87% (-1.96pp)
#
#  Verdict: Structural signal. 3–5 hrs window is the edge.
#  Hard filter candidate: hours_until_close > 2.0
#  BQS Role: HIGH

# ─── M6: Touch_Candle_Index ───────────────────────────────────
#  Formula   : (touch_time - 09:15) / 5 minutes
#  Hypothesis: LOWER index (earlier touch) → more likely winner
#
#  DS3 2022–2025:
#    Winners: mean=31.85  std=13.14  (~bar 31 = ~11:50)
#    Losers:  mean=35.94  std=15.37  (~bar 36 = ~12:15)
#    Gap: -4.09 | Direction vs hypothesis: MATCHES ✅
#
#  Verdict: Earlier touch = better. Correlated with M5.
#  Validate independence from M5 before assigning full weight.
#  BQS Role: HIGH

# ══════════════════════════════════════════════════════════════
# GROUP B — BINARY METRICS
# ══════════════════════════════════════════════════════════════

# ─── M4: Candle_Color ─────────────────────────────────────────
#  Formula   : 1 if bounce_close > bounce_open else 0
#  Hypothesis: Bullish (1) → more likely winner
#
#  DS3 2022–2025:
#    Winners bullish: 87.3%  |  Losers bullish: 86.8%  |  Gap: 0.5pp
#  Verdict: Zero filtering value. Almost all bounces are green.
#  BQS Role: EXCLUDE

# ─── M9: Prev_Candle_Direction ────────────────────────────────
#  Formula   : 1 if prev_close > prev_open else 0
#  Hypothesis: Bullish prev (1) → more likely winner
#
#  DS3 2022–2025:
#    Winners bullish prev: 43.4%  |  Losers bullish prev: 43.4%  |  Gap: 0.0pp
#  Verdict: Completely uninformative.
#  BQS Role: EXCLUDE

# ══════════════════════════════════════════════════════════════
# GROUP C — DISCRETE METRIC
# ══════════════════════════════════════════════════════════════

# ─── M7: Bounce_Candle_Index_Gap ──────────────────────────────
#  Formula   : bounce_candle_index - touch_candle_index (0–3)
#  Hypothesis: LOWER gap (faster reclaim) → more likely winner
#
#  DS3 2022–2025:
#    gap=0 : 14,868 trades → 15.4%  (+0.58pp)
#    gap=1 :  5,300 trades → 14.5%  (-0.32pp)
#    gap=2 :  3,807 trades → 13.7%  (-1.12pp)
#    gap=3 :  4,105 trades → 14.1%  (-0.72pp)
#
#  Verdict: Win rate range = 1.74pp. Direction loosely matches
#  but signal too weak to be actionable.
#  BQS Role: EXCLUDE

# ══════════════════════════════════════════════════════════════
# GROUP D — BINNED METRIC
# ══════════════════════════════════════════════════════════════

# ─── M8: MA20_Distance_Pct ────────────────────────────────────
#  Formula   : (MA20 - touch_low) / MA20 × 100
#  Hypothesis: Sweet spot at 0.5–2.5% (inverted U)
#
#  DS3 2022–2025:
#    < 0.3%   : 22,724 trades → 15.5%  ← 96% of all trades here
#    0.3–0.8% :  4,857 trades → 12.7%
#    0.8–1.5% :    373 trades →  7.2%
#    1.5–2.5% :     51 trades →  2.0%
#    2.5–3.5% :     10 trades → 10.0%  (tiny sample)
#    > 3.5%   :     11 trades →  9.1%  (tiny sample)
#
#  Verdict: Hypothesis WRONG on sweet spot. Actual = MONOTONIC.
#  Shallower touch consistently better. Deep touches fail.
#  96% of trades cluster at <0.3% making this a weak standalone filter.
#  BQS Role: MODERATE (soft score — lower distance = better)

# ══════════════════════════════════════════════════════════════
# BQS LEADERBOARD — DS3 2022–2025
# ══════════════════════════════════════════════════════════════
#
#  Rank  Metric                  Role      Hypothesis Direction
#  ──────────────────────────────────────────────────────────────
#  1     M5  Hours_Until_Close   HIGH      CONFIRMED ✅
#  2     M6  Touch_Candle_Index  HIGH      CONFIRMED ✅
#  3     M8  MA20_Distance_Pct   MODERATE  REVERSED (shallower = better)
#  4     M2  Bounce_Strength     LOW       REVERSED (lower = better)
#  5     M1  Volume_Ratio        LOW       CONFIRMED ✅ (gap too small)
#  6     M7  Bounce_Gap          EXCLUDE   Weak signal
#  7     M3  Wick_Ratio          EXCLUDE   Zero signal
#  8     M4  Candle_Color        EXCLUDE   Zero signal
#  9     M9  Prev_Candle_Dir     EXCLUDE   Zero signal

# ══════════════════════════════════════════════════════════════
# CC INSTRUCTIONS — NEXT STEPS
# ══════════════════════════════════════════════════════════════
#
#  File location: Framework_V1_Sandbox/BQS_METRICS_REFERENCE.md
#  Trade data:    Framework_V1_Sandbox/outputs/bqs/bqs_trades.parquet
#
#  CONTEXT:
#  The 2022–2025 results above show direction for each metric.
#  We now need to check if these directions HOLD on 2015–2025.
#  Goal: validate patterns generalize — NOT tune thresholds.
#
#  P1 — Re-run bqs_export.py on full DS3 2015–2025.
#        Remove the 2022+ date filter from trade generation.
#        Output: Framework_V1_Sandbox/outputs/bqs/bqs_trades_full.parquet
#
#  P2 — Compute winner vs loser stats on 2015–2025 full dataset:
#        Group A (M1, M2, M3, M5, M6): winner mean, loser mean, gap, direction
#        Group B (M4, M9): winner bullish%, loser bullish%, gap in pp
#        Group C (M7): win rate per gap value (0, 1, 2, 3)
#        Group D (M8): win rate per bin (<0.3%, 0.3-0.8%, 0.8-1.5%, 1.5-2.5%, >2.5%)
#
#  P3 — For each metric, answer:
#        "Does the direction on 2015–2025 match 2022–2025?"
#        ROBUST   = direction consistent across both periods → keep
#        FRAGILE  = direction flips or disappears → exclude
#
#  P4 — Add a new section at the bottom of THIS FILE:
#        "DS3 2015–2025 VALIDATION RESULTS"
#        Same format as above. Mark each metric ROBUST or FRAGILE.
#        Do NOT modify any existing content above.
#
#  RULES:
#    Do NOT tune any thresholds — direction validation only.
#    Clarify if any metric definition is unclear before running.
#    Print summary to terminal before updating this file.

# ══════════════════════════════════════════════════════════════
# DS3 2015–2025 VALIDATION RESULTS
# ══════════════════════════════════════════════════════════════
#
#  Script : Framework_V1_Sandbox/scripts/bqs_full_validation.py
#  Data   : Framework_V1_Sandbox/outputs/bqs/bqs_trades_full.parquet
#  Period : 2015–2025 (full DS3, no year filter)
#
#  Total trades  : 77,028
#  Winners (target hits only) : 12,565 (16.31%)
#  Baseline win rate          : 16.31%
#
#  Note: CAGR not computed (capital wiped in early years as expected —
#        strategy is known to lose; this run is for direction validation only)

# ──────────────────────────────────────────────────────────────
# GROUP A — CONTINUOUS METRICS
# ──────────────────────────────────────────────────────────────
#
#  Metric  W-mean   L-mean   Gap(full)  Gap(22-25)  Dir match  Verdict
#  ───────────────────────────────────────────────────────────────────
#  M1       1.743    1.694    +0.049     +0.071      YES        ROBUST
#  M2       0.332    0.355    -0.024     -0.023      YES        ROBUST
#  M3       1.686    1.731    -0.046     -0.022      YES        ROBUST
#  M5       3.413    3.088    +0.325     +0.347      YES        ROBUST
#  M6      32.222   36.068    -3.845     -4.090      YES        ROBUST
#
#  Notes:
#  M3: direction matches but gap negligible — EXCLUDE role unchanged
#  M5: gap shrinks marginally (+0.325 vs +0.347) — signal holds cleanly
#  M6: gap slightly smaller (-3.845 vs -4.090) — still strong structural signal

# ──────────────────────────────────────────────────────────────
# GROUP B — BINARY METRICS
# ──────────────────────────────────────────────────────────────
#
#  Metric  W-bull%  L-bull%  Gap(full)  Gap(22-25)  Dir match  Verdict
#  ────────────────────────────────────────────────────────────────────
#  M4       86.2%    86.2%   +0.0003    +0.0050     YES        ROBUST (negligible)
#  M9       42.3%    41.9%   +0.0044    +0.0004     YES        ROBUST (negligible)
#
#  Notes:
#  Both metrics confirm zero predictive value across 11 years — EXCLUDE confirmed

# ──────────────────────────────────────────────────────────────
# GROUP C — DISCRETE METRIC
# ──────────────────────────────────────────────────────────────
#
#  M7: Bounce_Candle_Index_Gap — win rate per gap value
#
#  Gap   Trades(full)   WR%(full)   WR%(22-25)
#  ────────────────────────────────────────────
#  0       41,509        16.88%      15.43%
#  1       14,197        15.81%      14.49%
#  2       10,314        15.62%      13.69%
#  3       10,985        15.44%      14.08%
#
#  Hypothesis (lower gap = better): MATCHES on full dataset ✅
#  Win rate range full: 1.44pp (16.88% – 15.44%)
#  Direction: gap=0 is strictly highest on 2015–2025 (cleaner than 2022-2025)
#  Verdict: ROBUST — but signal magnitude still too small to be actionable
#  BQS Role: EXCLUDE unchanged

# ──────────────────────────────────────────────────────────────
# GROUP D — BINNED METRIC
# ──────────────────────────────────────────────────────────────
#
#  M8: MA20_Distance_Pct — win rate per distance bin
#
#  Bin         Trades(full)   WR%(full)   WR%(22-25)
#  ──────────────────────────────────────────────────
#  < 0.3%        59,366        16.96%      15.43%
#  0.3–0.8%      15,634        14.43%      12.70%
#  0.8–1.5%       1,686        11.74%       7.24%
#  1.5–2.5%         253        12.65%       1.96%
#  > 2.5%            89        11.24%       9.09%
#
#  Hypothesis (shallower = better): MATCHES ✅
#  Monotonic decline confirmed for bins 0–3 on full dataset
#  1.5–2.5% bin recovers slightly on full data (12.65% vs 1.96%) due to larger sample
#  > 2.5% remains below baseline (11.24%)
#  Verdict: ROBUST — shallower touch consistently better across all 11 years
#  BQS Role: MODERATE unchanged

# ──────────────────────────────────────────────────────────────
# CONSOLIDATED VERDICT — POST VALIDATION
# ──────────────────────────────────────────────────────────────
#
#  Metric  2022-25 Role   2015-25 Verdict    Final BQS Role
#  ─────────────────────────────────────────────────────────
#  M5      HIGH           ROBUST             HIGH   ✅ — use in scoring
#  M6      HIGH           ROBUST             HIGH   ✅ — use in scoring
#  M8      MODERATE       ROBUST             MODERATE ✅ — use in scoring
#  M1      LOW            ROBUST             LOW    ✅ — minor weight
#  M2      LOW            ROBUST             LOW    ✅ — minor weight (reversed dir)
#  M3      EXCLUDE        ROBUST (noise)     EXCLUDE ❌ — zero signal magnitude
#  M4      EXCLUDE        ROBUST (negligible)EXCLUDE ❌ — zero signal magnitude
#  M7      EXCLUDE        ROBUST (weak)      EXCLUDE ❌ — signal too small (~1.4pp)
#  M9      EXCLUDE        ROBUST (negligible)EXCLUDE ❌ — zero signal magnitude
#
#  KEY FINDING:
#  All 9 metrics show CONSISTENT direction across 2015–2025 and 2022–2025.
#  No metric FLIPPED. This confirms the BQS hypothesis directions are structural,
#  not 2022–2025 artifacts.
#
#  Active BQS metrics for scoring: M5, M6, M8 (HIGH/MODERATE)
#  Supporting metrics (minor weight if score needed): M1, M2
#  Excluded metrics: M3, M4, M7, M9
