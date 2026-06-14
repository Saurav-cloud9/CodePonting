# Session Log — 2026-06-14

## Key Work Done

### Volume Observation (ITC on TV)
- Observed ITC Jan 2026 5-min chart: volume spikes = temporary corrections, NOT reversals
- Real direction set by low-volume gradual drift (smart money)
- Multi-timeframe insight: daily chart sets bias, 5-min times the entry
- ITC daily chart = lateral/ranging → not ideal for trend-following strategy

### Kijun Bounce Strategy
- Found "Daily Kijun with Bounce Alerts" (Pine Wizard, 663 boosts) on TV community
- Understood signal logic: 2-bar bounce off daily Kijun (50-period midpoint of range)
- Bar 1 (touch): low dips below Kijun, open above → Bar 2 (confirm): low back above, close>low
- Entry: open of bar 3. SL=2.5x ATR. TGT=3.0x ATR. EOD=15:15

### Python Backtest Results (5 stocks, 2022-2025)
- Kijun-HL (traditional HIGH/LOW): ITC 55.2%/PF1.75, TATA 50%/PF1.15, HDFC 55.9%/PF1.16, INFY 48%/PF1.41, RELIANCE 37.9%/PF0.57
- Kijun-Close (Pine Script CLOSE/CLOSE): HDFC best at 61.8%/PF1.97, TATA collapses to 33.3%
- Kijun-HL is stronger overall: 4/5 PF>1

### Data Issue Discovered
- TV unadjusted vs Python demerger-adjusted: ~11% price gap for ITC
- ITC Hotels demerger Jan 2025 caused retroactive price adjustment in our CSV
- TV with ADJ mode: PF drops to 0.759 → signal fragility confirmed
- Python backtest on consistent adjusted data is more trustworthy

## Decisions Made
- Kijun-HL is preferred formula for Python
- RELIANCE likely excluded (fails both formulas)
- TV = visual intuition only; Python = quantitative decisions
- Next: run all 30 stocks on Kijun-HL
