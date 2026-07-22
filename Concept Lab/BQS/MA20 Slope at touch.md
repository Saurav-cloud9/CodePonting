
BQS-R2 M1 — MA20 Slope at touch

Hypothesis:
MA20 should be RISING at the point of touch.
Price pulling back to a rising support = stronger bounce.
Flat or falling MA = no directional bias = weaker bounce.

Metric: slope = MA20[touch_idx] - MA20[touch_idx - 5] / 5
Categories: rising (>0.05%) | flat (-0.05% to 0.05%) | falling (<-0.05%)

Expected:
Winners → touch on rising MA more often
Losers  → touch on flat/falling MA more often

**MA20 Slope at Touch — Results from DS3 validation run**

| Category | Trades | W1 Win% | vs Base | W2 Win% | vs Base | W3 Win% | vs Base |
| -------- | ------ | ------- | ------- | ------- | ------- | ------- | ------- |
| rising   | 6,773  | 15.6%   | +0.8pp  | 34.0%   | +1.5pp  | 36.5%   | +1.2pp  |
| flat     | 8,892  | 16.0%   | +1.2pp  | 30.6%   | -1.9pp  | 33.4%   | -1.9pp  |
| falling  | 11,945 | 13.5%   | -1.3pp  | 32.8%   | +0.3pp  | 35.7%   | +0.4pp  |

BQS-R2 M1 — MA20 Slope at Touch — VERDICT: WEAK

Rising slope shows mild positive edge (+0.8pp on w1, +1.5pp on w2)
Falling slope shows mild negative signal (-1.3pp on w1)
Max spread across categories: ~2.5pp — not actionable
Rising bucket captures only 25.3% of all w1 winners
***No star bucket***. Cannot use as standalone filter.
Direction of hypothesis confirmed but signal too weak to deploy.
Parked alongside BQS-R1 metrics.


