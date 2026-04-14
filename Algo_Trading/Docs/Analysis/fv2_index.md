# fv2 Signal Analysis — Index

## What this is
Manual signal review of fv2 MA bounce signals against all 12 master params.
Each signal gets its own note. This index links them all.

## Gate Structure (3-gate temporal)
| Gate | When | Params | Purpose |
|------|------|--------|---------|
| G1 | Pre-touch | #01–#04 | Regime context + approach direction |
| G2 | Touch & bounce | #05–#10 | MA interaction quality + volume |
| G3 | Post-bounce | #11–#12 | Entry follow-through confirmation |

## Master Params Reference
| # | Param | Gate | Description |
|---|-------|------|-------------|
| 01 | slope_threshold | G1 | MA slope % minimum at touch |
| 02 | slope_offset | G1 | MA slope % minimum at T-3 |
| 03 | candles_above | G1 | consecutive lows > MA20 before touch — price approached from above |
| 04 | pullback_bars | G1 | bars from swing high to touch |
| 05 | shoot_depth | G2 | (MA - low) / ATR14 at touch |
| 06 | touch_body_pct | G2 | body size % of total candle range (≤40% ideal) |
| 07 | wick_defence_ratio | G2 | (min(O,C)−MA) / (MA−low) — >1 = buyers recovered more than they overshot |
| 08 | bounce_vr_abs | G2 | bounce VR > 1.2x absolute floor |
| 09 | bounce_vr_rel | G2 | bounce VR > touch VR relative spike |
| 10 | same_candle_tb | G2 | touch + bounce same candle (bool) |
| 11 | G5a | G3 | entry close > bounce close |
| 12 | G5b | G3 | entry VR > bounce VR |

## Signal Reviews
- [[fv2_signals_POWERGRID]] — POWERGRID — #1–9 logged
- [[fv2_signals_TATAMOTORS]] — TATAMOTORS — #1–6 logged
- [[fv2_signals_HDFCBANK]] — HDFCBANK — #1–4 logged

## Observations by Gate
- [[fv2_obs_G1_pretouch]] — G1: regime + approach (#01–#04)
- [[fv2_obs_G2_touchbounce]] — G2: touch & bounce quality (#05–#10)
- [[fv2_obs_G3_followthrough]] — G3: post-bounce follow-through (#11–#12)

## Summary
- [[fv2_signal_patterns]] — Cross-signal patterns + filter candidates
