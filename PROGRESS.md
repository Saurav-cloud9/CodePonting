# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. RSI/MACD 4-panel analysis: RSI<30 zone PF=1.31 (n=53 tiny); MACD flat — no discriminating power
2. fv2_baseline_formula.md updated: BHARTIARTL #1 (PF=1.092) > ASHOKLEY #2 (PF=1.054)
3. Kite MCP fixed in CC (.mcp.json: npx mcp-remote + NODE_OPTIONS=--use-system-ca)
4. BAJFINANCE DS3 parquet built: 127,843 candles 2015-02-02→2021-12-31 via Kite MCP (26 chunks)
5. RSI/MACD re-run: N=49,039 NaN=0 confirmed — BAJFINANCE warmup fix complete

── MILESTONES (5 most important) ────────────────────────────
1. fv2 direction locked — 3-gate system (G1/G2/G3) addressing structural gaps vs true MA bounce
2. fv2 baseline locked — ma_bounce.py: N=49,039 | PF=0.922 | 30 stocks 2022-2025 | no slippage
3. MFE/MAE confirmed — losers never move in your favour (median MFE 0.67 ATR vs 4.85 winners)
4. SL×TGT heatmap exhausted — entire 5×9 grid 0.90-0.94; exit tuning cannot fix the strategy
5. RSI<30 at bounce bar = only PF>1 zone (1.31, n=53) — RSI×MACD combo filter is next step
