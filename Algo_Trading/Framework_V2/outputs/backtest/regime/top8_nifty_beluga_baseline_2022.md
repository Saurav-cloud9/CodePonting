# Top 8 Nifty Stocks — Beluga Regime Baseline | 2022 | tb3

## Purpose
The fv2 MA Bounce strategy on raw signals has a thin edge (PF ~1.03 on POWERGRID).
Signal-quality filtering alone (Optuna, 11 gates) failed to produce generalizable OOS edge.

We are now testing the Big Beluga regime filter as a pre-condition — the hypothesis being
that the market regime at the moment a signal fires (captured by the Beluga oscillator's
trend + voltrend components) can separate high-probability bounces from low-probability ones.

This file is the **baseline reference** — raw strategy results for the top 8 Nifty 50
stocks (by index weightage) before any Beluga filter is applied. The goal is to build
filters one by one (time gate, voltrend threshold, trend delta, bounce speed) and measure
how each one moves W% and PF relative to this baseline. A filter is useful only if it
consistently improves both metrics across multiple stocks, not just one.

Stocks: Top 8 Nifty 50 constituents by weightage available in fv2 dataset
Year: 2022 | Bounce window: tb3 | No filters applied (raw baseline)

## Baseline Results

| Stock     | Total |   W |   L | EOD+ | EOD- |   W% |     PF |
|-----------|-------|-----|-----|------|------|------|--------|
| HDFCBANK  |  1508 | 282 | 611 |  450 |  165 | 18.7 | 1.1511 |
| ICICIBANK |  1498 | 254 | 658 |  433 |  153 | 17.0 | 0.9237 |
| RELIANCE  |  1519 | 290 | 660 |  376 |  193 | 19.1 | 0.9525 |
| BHARTIARTL|  1504 | 247 | 598 |  391 |  268 | 16.4 | 0.9851 |
| INFY      |  1435 | 237 | 619 |  383 |  196 | 16.5 | 1.0303 |
| SBIN      |  1508 | 269 | 665 |  352 |  222 | 17.8 | 0.8462 |
| AXISBANK  |  1489 | 246 | 653 |  360 |  230 | 16.5 | 0.8795 |
| ITC       |  1574 | 321 | 611 |  403 |  239 | 20.4 | 1.1739 |

## Beluga Regime Breakdown at Touch Bar

| Stock      | R_W/R_tot | R_W% | G_W/G_tot | G_W% | B_W/B_tot | B_W% | Y_W/Y_tot | Y_W% | vt5_W/vt5_tot | vt5_W% |
|------------|-----------|------|-----------|------|-----------|------|-----------|------|----------------|--------|
| HDFCBANK   |  37/280   | 13.2 |  66/373   | 17.7 |  95/416   | 22.8 |  84/439   | 19.1 |     53/340     |  15.6  |
| ICICIBANK  |  51/293   | 17.4 |  47/338   | 13.9 |  86/438   | 19.6 |  70/429   | 16.3 |     56/332     |  16.9  |
| RELIANCE   |  48/280   | 17.1 |  63/312   | 20.2 |  90/453   | 19.9 |  89/474   | 18.8 |     64/307     |  20.8  |
| BHARTIARTL |  47/270   | 17.4 |  61/348   | 17.5 |  77/439   | 17.5 |  62/447   | 13.9 |     67/333     |  20.1  |
| INFY       |  39/257   | 15.2 |  54/328   | 16.5 |  77/419   | 18.4 |  67/431   | 15.5 |     47/301     |  15.6  |
| SBIN       |  48/284   | 16.9 |  58/309   | 18.8 |  76/473   | 16.1 |  87/442   | 19.7 |     55/295     |  18.6  |
| AXISBANK   |  50/282   | 17.7 |  56/317   | 17.7 |  69/435   | 15.9 |  71/455   | 15.6 |     58/325     |  17.8  |
| ITC        |  49/297   | 16.5 |  85/334   | 25.4 |  98/488   | 20.1 |  89/455   | 19.6 |     61/349     |  17.5  |

## Quadrant Definitions (Big Beluga)
- R = trend < 0, voltrend > 0  — strong downtrend + high volume
- G = trend >= 0, voltrend > 0 — uptrend + high volume
- B = trend >= 0, voltrend <= 0 — uptrend + low volume
- Y = trend < 0, voltrend <= 0 — weak downtrend + low volume
- vt5 = voltrend > 5 filter only (no trend condition) — our best single filter on POWERGRID (24.3%)

## Key Observations
- No regime is consistently the best across all 8 stocks
- Red regime is actually the WORST for HDFCBANK (13.2%)
- Blue regime performs best for HDFCBANK (22.8%) and RELIANCE (19.9%)
- Green regime performs best for ITC (25.4%) — outlier
- voltrend > 5 helps RELIANCE (20.8%) and BHARTIARTL (20.1%) but hurts HDFCBANK (15.6%) and INFY (15.6%)
- SBIN and AXISBANK have the weakest PF (0.84, 0.87) — high EOD- counts dragging them down
- HDFCBANK and ITC have the strongest raw PF (1.15, 1.17)

## Next Steps
- Test time gate filter (entry 10:00–13:30) on all 8 stocks
- Test trend_delta > 0 (trend improving touch to entry)
- Test bounce_bar_index <= 1 (quick bounce)
- Build filters one by one, measure W% and PF lift per stock
