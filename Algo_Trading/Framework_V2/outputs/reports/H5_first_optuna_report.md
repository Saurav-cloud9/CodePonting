H5 Optuna — Full Context & Findings
1. What is H5 and what are we working with?
H5 Full is a signal viewer and backtest engine for the fv2 MA Bounce strategy. It works on pre-computed signal CSVs — one file per stock per year.

Universe: 30 NSE F&O stocks
Period: 2022–2025 (4 years)
Signal type: tb3 (touch-to-bounce gap ≤ 3 candles)
Total signals in dataset: 182,517 across 30 stocks × 4 years
Average per stock per year: ~1,500 signals
Each signal has 11 filter parameters (p01–p11) across 3 gates:

G1 — Pre-touch: trend context, approach direction (p01–p04)
G2 — Touch & bounce quality: pullback, volume (p05–p10)
G3 — Post-bounce follow-through (p11)
2. What were we trying to do?
Goal: Find one universal parameter set (values for p01–p11) that maximizes profit factor (PF) across all 30 stocks over all 4 years simultaneously.

This is different from what was done before (per-stock Optuna), where each stock got its own independently tuned parameter set.

3. What was done before — Per-Stock Optuna (2022)
h5_optuna_batch.py ran a separate Optuna study for each stock × tb variant for 2022 only.

500 trials per stock
Hard floors: N_pass ≥ 10% of signals, PF ≥ 1.3
Result: 9 out of 30 stocks cleared PF ≥ 1.3
5 stocks survived both tb3 and tb9 variants
This is the "locally optimal" approach — each stock gets params tuned to its own signal distribution. The downside: you end up with 30 different param sets, one per stock, which is impractical to use in live trading.

4. Walk-Forward Analysis (WFA) — The Key Finding
After per-stock Optuna on 2022, WFA was run on 5 stocks (POWERGRID, HDFCBANK, ITC, NATIONALUM, PNB):

Train: 2022 best params
Validate: Apply those exact params to 2023, 2024, 2025
Result: No param set trained on 2022 held up across all validation years. Specifically:

2024 broke all stocks — PF collapsed in 2024 for every stock tested
Manual WFA on PNB tb3 confirmed: no single param combo holds 2022–2025
Conclusion recorded: "Signal is regime-specific; regime problem confirmed"
This is the most important finding. It tells us the signal itself behaves differently in different market years — params that select good trades in 2022 do not select good trades in 2024.

5. The Universal Optuna Attempt — What Happened Today
Attempt: Run one Optuna study across all 30 stocks × 4 years combined (182,517 signals). Find ONE param set that maximizes PF across the full portfolio.

Problem 1 — Hard floor blocked everything:
Initial design used a hard per-stock floor: each stock must have ≥ 5% of its signals passing. If any stock fails → trial scores -1,000,000,000.

After 200+ trials: every single trial returned -1,000,000,000. Optuna had no signal to learn from.

Diagnostic revealed BAJFINANCE was the bottleneck — even the loosest reasonable params give it only 4.6% passing (285 signals vs 307 required). Every other stock easily clears 5%.

Problem 2 — Baseline PF is already below 1.0:
With zero filters applied (all 182,517 signals included):


Pooled PF  : 0.924
Win rate   : 42.2%
Net PnL    : -26,782
The raw signal has no edge at the portfolio level. This means the PF > 1.0 hard floor (second constraint) was also impossible — filters need to lift PF from 0.924 to above 1.0, which requires the optimizer to first explore before any valid trial appears.

Fix attempted: Replaced hard floors with soft penalty — score = pooled PF × coverage (fraction of stocks meeting 5% floor). This gives Optuna a gradient to learn from. Seed trial immediately returned 0.842 (vs -1e9 before).

Why 0.842 is still problematic:

Baseline no-filter PF = 0.924
Seed params (p05 + p08 + p11 filters) gave pooled PF ≈ 0.87 — actually lower than no filters
Meaning: the seed filters are cutting more winners than losers at the portfolio level
The 2024 regime drag is embedded in all 182,517 signals
6. Why the Universal Optuna Won't Serve the Purpose
The regime problem (confirmed by WFA) means:

The signal generates good trades in some years and bad trades in other years
This is not a parameter problem — it's a signal behavior problem
No combination of p01–p11 thresholds can distinguish "2022-style good trade" from "2024-style bad trade" because those params describe the trade's own characteristics, not the market regime
Example to illustrate:
Imagine p08 (volume ratio) threshold = 1.5x. In 2022, trades with volume ratio > 1.5x are mostly winners. In 2024, the same trades with the same volume characteristics are mostly losers — because the underlying market regime has changed (different volatility, different trend character, etc.). No matter what threshold you pick for p08, it can't solve this because the relationship between the signal and outcome has changed.

Running universal Optuna over 2022–2025 combined would find a "least-bad" compromise param set — one that's mediocre in all years rather than good in any specific year. The 2024 data actively drags down any param set that would otherwise work well for 2022/2023/2025.

7. Current State
Item	Status
Per-stock Optuna (2022, tb3+tb9)	Complete — 9/30 cleared PF ≥ 1.3
WFA (5 stocks)	Complete — regime problem confirmed, 2024 breaks all
Universal Optuna (4 years)	Attempted, stopped — structurally unsound given regime findings
Universal Optuna script	Written and saved at Framework_V2/scripts/h5_universal_optuna.py
8. Open Questions for Claude.ai Discussion
Is the regime problem solvable at the filter level? Or does it require a fundamentally different signal design?
Should we exclude 2024 from optimization? Run universal Optuna on 2022+2023+2025 only, treating 2024 as a known-bad regime year?
Is the signal fixable? The current G1-G3 criteria describe individual trade quality — but if the market regime determines outcome more than trade quality, the signal needs a regime gate on top.
What does "regime-specific" mean concretely for 2024? Was 2024 a trending year where MA bounces fail structurally? Understanding the why could point to the fix.
This document captures the full arc. Share with Claude.ai and come back with the direction.