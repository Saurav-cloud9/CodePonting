# Handoff Note — 2026-06-27

## Current State
- fv2 baseline locked: ma_bounce.py | N=49,039 | PF=0.922 | Prof_WR=41.5% | 30 stocks 2022-2025
- RSI/MACD 4-panel chart built (rsi_macd_mfe.py) — RSI<30 only zone above PF=1 (n=53); MACD flat
- BAJFINANCE DS3 gap: 26 trades NaN (0.05%); fetch_bajfinance_ds3.py ready, run from Claude Desktop
- Codedex: ex13_The_Final_Scrub.ipynb open (pandas data cleaning, in progress)

## Next Step
1. **P2 — RSI×MACD combination filter**: find zone where both RSI<X AND MACD>Y together give PF>1.0
   - Script: rsi_macd_mfe.py already has both indicators computed on all 49,039 trades
   - Add 2D heatmap: RSI bucket × MACD zone → PF grid
2. **P1 — Trading ABC filter**: apply A/B/C stock classification on ma_bounce.py baseline
   - Top-9 subset was PF=1.197, N=911 — re-confirm on current locked baseline
3. **BAJFINANCE DS3**: run fetch_bajfinance_ds3.py from Claude Desktop to fix 26 NaN trades

## Known Issues / Context
- BAJFINANCE DS3 not available from CC (Kite OAuth = Claude Desktop only)
- rsi_macd_mfe.py uses `dropna(subset=['rsi','macd_hist'])` — excludes 26 BAJFINANCE warmup trades
- fv2_baseline_formula.md: BHARTIARTL now correctly ranked #1 (was listed alphabetically before)
- Codedex path: Learning/Codedex/pandas/exercise13_The_Final_Scrub.ipynb
