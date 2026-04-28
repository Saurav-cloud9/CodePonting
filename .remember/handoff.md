# Handoff Note — 2026-04-22

## State
POWERGRID signal review — 16 signals logged. #15 and #16 are first winners (June 23 2025).
Signal #16 detail block not yet added in Obsidian (only log row logged so far).
Pine ATR mismatch identified: `ta.atr(14)` = RMA (Wilder's), Python = SMA rolling mean → SL/TGT diverge.
Purple triangle for k=0 compiled but needs chart reload on TV to take effect.

## Next
1. Fix Pine ATR: change Python `tr.rolling(14).mean()` → Wilder's RMA in `build_html1.py` line ~77, rebuild H1
2. Reload POWERGRID chart on TV to pick up purple k=0 triangle
3. Log signal #16 detail block in Obsidian (via H1.1 review form)
4. Continue signal review — target 5 clean winners total, then H5 build

## Context
- Stop hook disabled (`"Stop": []` in `.claude/settings.json`) — re-enable when returning to Python dev
- H1.1 submit button fixed: serial regex now matches date in col2, no stock column, diff calculated
- G3a/G3b fixed in H1.1 param names (was G5a/G5b)
- Signal review pacing: 3-5 signals/day, 70% signal review / 30% Codedex
- Key hypothesis: G1 slope both pass = load-bearing condition for winners (2 data points only — not conclusive)
- Failed prior touch → clears weak hands → stronger second setup (observed on June 23 POWERGRID)
- Pine SL scan: TV shows SL hit on #16 but price never reaches 289.7 — investigate alongside ATR fix
- H1 launch config: `.claude/launch.json`, port 7701

## Key conventions (locked)
- Forced exit at 14:50 — wins after = EOD+
- 3-gate system (NO cascade — all 12 params always evaluated):
  - G1: pre-touch (#01–#04) | G2: touch & bounce (#05–#10) | G3: post-bounce (#11–#12)
- Signal review target revised: 5 clean winners → then H5 build (not 50-200)

## Files
- POWERGRID log: Algo_Trading/Docs/Analysis/fv2_signals_POWERGRID.md
- TATAMOTORS log: Algo_Trading/Docs/Analysis/fv2_signals_TATAMOTORS.md
- H1: Framework_V2/outputs/reports/fv2_h1_signal_viewer.html
- H1.1: Framework_V2/outputs/reports/fv2_h1_1_signal_review.html
- build_html1.py: Framework_V2/scripts/build_html1.py (ATR fix here)
- Pine Script: fv2_bounce_v1 on TV (POWERGRID 5-min)
