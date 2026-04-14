# Handoff Note — 2026-04-13

## Current task
Manual signal review — fv2 MA Bounce. POWERGRID complete (9 signals). TATAMOTORS in progress (2 of many).

## Status
- 9 POWERGRID + 2 HDFCBANK + 2 TATAMOTORS = 13 signals reviewed total
- H1.1 fully stable — folder persistence, row counter fixed, output clean
- Next signal: TATAMOTORS 2025-05-15 signal #3 onwards

## Key conventions (all locked)
- Forced exit at 14:50 — wins after = EOD+
- Outcome: Win / SL / EOD+ / EOD- / EOD skip (post 15:00)
- #02 N/A when opening bar; #03 N/A when opening bar (no prior candles)
- #09 N/A when k=0; #10 pass when k=0, N/A when different candles
- G2 fail → G3 all N/A cascade; G2 N/A → G3 also N/A

## Gate ordering (locked 2026-04-13)
- G1: Trend — slope_threshold (#01), slope_offset (#02)
- G2: Approach direction — candles_above (#03) — gates G3
- G3: Pullback quality — pullback_bars (#04), shoot_depth (#05), touch_body_pct (#06), wick_defence_ratio (#07)
- G4: Volume — bounce_vr_abs (#08), bounce_vr_rel (#09), same_candle_tb (#10)
- G5: Follow-through — G5a (#11), G5b (#12)

## Key patterns emerging (13 signals)
- POWERGRID: no G1+G2 double pass yet across 9 signals
- TATAMOTORS #2: G1+G2+G5 all pass, G3 weak — wins anyway. G3 quality may be less critical than G1+G2
- wick_defence_ratio needs threshold calibration — 1.0 is starting point only

## H1.1 workflow
- Select signal in H1 sidebar → "✎ Review Signal" activates
- Opens H1.1 in new tab, pre-filled
- Fill 12 dropdowns + comments + outcome → Submit
- Folder stored in IndexedDB — no picker after first use per browser session
- Writes to Docs/Analysis/fv2_signals_STOCK.md

## Files
- POWERGRID log: Algo_Trading/Docs/Analysis/fv2_signals_POWERGRID.md
- TATAMOTORS log: Algo_Trading/Docs/Analysis/fv2_signals_TATAMOTORS.md
- HDFCBANK log: Algo_Trading/Docs/Analysis/fv2_signals_HDFCBANK.md
- H1: Framework_V2/outputs/reports/fv2_h1_signal_viewer.html
- H1.1: Framework_V2/outputs/reports/fv2_h1_1_signal_review.html

## Next steps
1. Continue TATAMOTORS signal review via H1.1
2. Target 30–50 total signals before drawing conclusions
3. Watch for: first G1+G2 double pass on TATAMOTORS, wick_defence_ratio values across wins vs SL
