# Handoff Note — 2026-06-15

## Current State
- HMA20 bounce backtest built and run: hma_bounce_backtest.py (30 stocks, raw PF=0.944)
- fv2 baseline confirmed: no volume filter (PF=0.918, N=51,803). BHARTIARTL = reference stock.
- Trading ABC (TV community script) fully dissected — 5-step logic understood, not yet backtested
- TGT-WR / PFT-WR terminology locked. BE = 35.7% theoretical.

## Next Step
1. **P2 — Trading ABC backtest**: Port 5-step logic to Python, test on BHARTIARTL first
   - Step 4 (lbounced) can be tested standalone vs full 5-step for comparison
   - Use fv2 CSV (BHARTIARTL_5min.csv), same SL=2.5×ATR / TGT=4.5×ATR as baseline
2. P1 HMA — per-stock comparison vs SMA baseline still pending (hma_bounce_backtest.py exists but no side-by-side table yet)
3. P3 — Kijun filter on MA20 Bounce (after P2)

## Known Issues / Context
- index.md still marks Top 5 as sweet spot — needs update to Top 6 (minor housekeeping)
- _temp_fv2_baseline.py has "Eco-WR" label in code — should be renamed PFT-WR if reused
- All temp scripts (_temp_*) in Framework_V2/scripts/ — working files, not cleaned up
- Trading ABC: abc_bar_count window is 6 bars; multiple C signals can fire from one ABC setup
- Scripts created this session: hma_bounce_backtest.py, _temp_hma_gated_compare.py, _temp_fv2_baseline.py, _temp_per_stock_baseline.py, _temp_ashokley_drill.py
