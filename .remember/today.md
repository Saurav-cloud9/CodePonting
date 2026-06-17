# Session Log — 2026-06-15 (updated)

## Key Work Done

### EOD Fix (15:15 → 15:00) [earlier in session]
- Corrected EOD from 15:15 to 15:00 in kijun_bounce_backtest.py, _kijun_subset_analysis.py, and Pine Script
- Re-ran 30-stock backtest: 790 trades, PF 0.848. Top 11 results updated in index.md
- Top 6 sweet spot identified: VEDL+SBIN+NTPC+BHARTIARTL+ICICIBANK+ADANIPORTS → PF 1.489, N=157

### Kijun Period Sweep [earlier in session]
- New script: _kijun_period_sweep.py — tests 10/20/30/40/50-day on Top 11 stocks
- 50-day is only profitable period (PF 1.378). All shorter periods fail.

### HMA Bounce (this session)
- Created hma_bounce_backtest.py — HMA20 replacing SMA20 in fv2 bounce logic
- HMA formula: WMA(2×WMA(n/2) - WMA(n), √n), period=20, warmup=24 bars
- Raw HMA20 30-stock result: N=352k, PF=0.944 (vs SMA20 raw PF=0.918)
- Additional temp scripts: _temp_hma_gated_compare.py, _temp_fv2_baseline.py, _temp_per_stock_baseline.py
- voltrend_touch < 4 tested as filter: SMA20+open>MA+vt<4 → PF=0.941

### fv2 Baseline Clarification
- Confirmed source of truth: fv2_batch_build.py (has 1.2× volume condition on bounce)
- No volume filter is better baseline: PF 0.918, N=51,803 (vs PF 0.906, N=44,823 with vol)
- Per-stock top 4: BHARTIARTL(1.053), DABUR(1.049), ASHOKLEY(1.030), SUNPHARMA(1.013)
- BHARTIARTL chosen as reference stock going forward

### Terminology Locked
- TGT-WR = target hit rate only; PFT-WR = pnl>0 win rate. Never use plain WR.
- Theoretical BE = SL/(SL+TGT) = 2.5/7.0 = 35.7%

### Trading ABC (TV community script)
- Full Pine Script read (219 lines). 5-step logic dissected:
  1. Trend Cloud: 6 MAs (SMA50/100/150/200 + EMA20/40), trend=+1 if all below candle 2 bars
  2. ZigZag (period=8): pivot detection, keeps last 5 points
  3. ABC pattern: Fib retracement 38.2-61.8% of A→B swing (±5% error rate)
  4. Bounce check: min(low,low[1]) <= MA AND close > MA AND close > open (lbounced)
  5. Final long: trend+1 AND abc_bar_count<=6 AND lbounced AND no new low since C
- lstoch (stochastic) is dead code — computed but never used in signal
- Screenshot taken: tradingview-mcp/screenshots/bhartiartl_trading_abc.png
- Multiple C labels = abc_bar_count<=6 fires on each bar independently within window
