# SMC Exploration Plan

## Goal
Concept-check and eventually backtest 5 Smart Money Concepts (SMC) indicators,
one at a time. Visual validation happens on TradingView via native Pine Script
(not MCP-drawn shapes — that approach was tried and abandoned, see below).
Backtesting happens separately in Python once the Pine version confirms the
logic marks the right candles.

## Indicators to test (in order)
1. Liquidity (swing high/low sweep — the logic explored last session)
2. Fair Value Gap (FVG)
3. Order Block (OB)
4. Break of Structure (BOS)
5. Inducement

## Workflow per indicator
1. Write the indicator logic as a Pine Script (`plotshape`/`label.new`/`box.new`
   to mark it directly on the chart).
2. Load it on TV manually, visually confirm it fires where expected across a
   few different symbols/timeframes.
3. Once confirmed, port the same logic to Python for backtesting against real
   historical data (fv2 CSVs or DS3 parquet — TBD per indicator, not live MCP
   snapshots).
4. Record win rate / PF / trade count, same format as other fv2 baseline work.

## Claude.ai involvement
Checking/validating each indicator's logic and design happens with Claude.ai
(mobile strategy scratchpad), consistent with the existing CC/Claude.ai split:
Claude.ai for strategy discussion and logic sourcing, CC for execution
(writing the Pine Script, running the Python backtest, file/folder work).

## Why not MCP-drawn shapes (last session's approach, abandoned)
Tried pulling live OHLCV via MCP, running the Python signal logic, then calling
`draw_shape` to plot markers on the live chart. This required fixing multiple
layers of infrastructure just to get a visual check:
- TradingView's Store/MSIX package update broke direct launch entirely,
  requiring a custom `IApplicationActivationManager` COM activation helper
  (`tradingview-mcp/scripts/tv_activate_helper/`) to launch with the CDP
  debug port.
- Found and fixed real bugs in `tradingview-mcp/src/core/drawing.js` and
  `chart.js` (`draw_list`, `draw_clear`, `draw_remove_one`, `getVisibleRange`,
  `scrollToDate`, `symbolInfo` were all missing `_resolve(_deps)`, causing
  `getChartApi is not defined` / `evaluate is not defined` errors).
- Even after all that, `draw_shape` output (text labels, then rectangles) was
  a poor substitute for what a native Pine Script indicator gives for free.

Verdict: Pine Script is simpler, native, and doesn't depend on any of the
above. MCP/CDP control is worth it for dynamic/interactive tasks, not for
"does this indicator mark the right candles."

## Status
Not started. Files from the abandoned MCP-drawing attempt
(`liquidity_sweep_logic.py`, `run_analysis.py`, and the HDFC data snapshot)
were deleted from this folder on 2026-07-14.
