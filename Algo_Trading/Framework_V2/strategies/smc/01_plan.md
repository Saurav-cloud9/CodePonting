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
Recovered 2026-09-07 from the bookmarked claude.ai session (see `02_concepts_summary.md`'s
old TODO, now resolved): full concept detail + entry logic + diagrams in
`02_concepts_summary.md`, all backtest results in `03_backtest_results.md`, reference
diagrams in `diagrams/`, and an early illustrative (not production) Python sketch of the
Liquidity Sweep signal in `reference_liquidity_sweep_signal_illustrative.py`.

Per `03_backtest_results.md`: Liquidity (as "LSS"), FVG, and OB were all already backtested
on DS3's full 11-year history and **failed the project's ZPF>1.0 viability bar** as
standalone SHORT signals (best: LSS+VWAP+RSI>54 at ZPF=1.01 but only 411 trades — too thin
to trust). The one strategy that passed cleanly was unrelated to these three SMC concepts
(6BCE+VWAP+RSI>54 on a curated 8-stock universe, ZPF=1.12) — not covered by this repo's
current locked strategies/ variants, worth a look on its own.

Next real decision before more work here: these 3 SMC concepts were tested standalone and
already look weak (matches this project's own repeated finding that most single filters
don't clear the bar alone) — the plan's own "Key Principles" section already flags that
**triple confluence** (Liquidity + FVG + OB in the same zone) is where the real edge is
expected to concentrate, not any one of them alone. Decide: pursue confluence testing next,
or treat all 3 standalone results as sufficient evidence to deprioritize this whole
direction in favor of something else.
