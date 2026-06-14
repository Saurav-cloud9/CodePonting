# Handoff Note — 2026-06-14

## Current State
- Kijun Bounce strategy built and backtested on 5 stocks (Python)
- Kijun-HL (traditional): 4/5 stocks PF>1 — ITC 55.2%, TATAMOTORS 50%, HDFCBANK 55.9%, INFY 48%
- Kijun-Close (Pine Script): 3/5 stocks PF>1 — HDFCBANK best at 61.8%
- RELIANCE fails both formulas — likely to exclude
- TV ADJ mode shows PF=0.759 for ITC — signal is fragile, TV/Python gap exists
- Key data issue: our Python CSV uses ITC Hotels demerger-adjusted prices (~11% lower than TV unadjusted)
- Script: Algo_Trading/Framework_V2/scripts/kijun_bounce_backtest.py

## Next Step
1. Run all 30 stocks on Python with Kijun-HL — get full universe picture
2. Investigate TV vs Python gap further (ATR method, entry price differences)
3. If Kijun-HL holds across 20+ stocks → port to full fv2 framework

## Known Issues
- TV and Python prices don't align due to demerger adjustment — use TV ADJ mode for visual review
- Trade count mismatch TV vs Python (TV Kijun-Close ITC=18, Python Kijun-Close ITC=18 ✅ but prices differ)
- H5 signals not yet regenerated after p11 fix (30 stocks x 4 years x 2 variants) — background item
