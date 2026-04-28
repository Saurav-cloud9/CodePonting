# fv2 Signal Review — HDFCBANK

Parent: [[fv2_index]]

## Signal Log

| #  | Stock    | Date       | Touch | Bounce | Entry | Outcome | G1      | G2         | G3  | Notes |
|----|----------|------------|-------|--------|-------|---------|---------|------------|-----|-------|
| 1  | HDFCBANK | 2022-10-03 | 12:15 | 12:30  | 12:35 | EOD+    | ✅✅✅✅ | ✅✅⚠️✅✅✅ | ✅❌ | 10/11 pass. 1 N/A. overall looks like a pass but EOD+. |
| 2  | HDFCBANK | 2022-10-03 | 12:40 | 12:55  | 13:00 | EOD+    | ✅✅✅✅ | ⚠️❌❌✅✅N/A | ❌❌ | fail. EOD+. G2 touch/bounce quality fails, G3 also fails. |
| 3  | HDFCBANK | 2022-10-03 | 14:00 | —      | —     | SL      | ✅✅✅   | ❌❌❌       | ❌  | Rising regime. G2 correctly rejects touch quality. |
| 4  | HDFCBANK | 2022-10-03 | 14:45 | —      | —     | LATE    | ❌❌❌   | ❌❌❌       | ❌  | Flat signal. G1 alone kills it. Entry ≥ 14:45. |

---

## Outcome Key
- **SL** = stop hit before 14:50
- **Win** = target hit before 14:50
- **EOD+** = exit at 14:50, in profit (forced exit)
- **EOD-** = exit at 14:50, at loss (forced exit)
- **LATE** = entry ≥ 14:45 — covers all post-14:45 entries incl. post-15:00 signals

---

## Signal Detail

<!-- Each signal added below as review progresses -->

### Signal #1 — 2022-10-03 12:15 (T) 12:30 (B) 12:35 (E)
**Stock:** HDFCBANK | **Outcome:** EOD+

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | pass | — |
| 02 | slope_offset | G1 | pass | — |
| 03 | candles_above | G1 | pass | — |
| 04 | pullback_bars | G1 | pass | — |
| 05 | shoot_depth | G2 | pass | — |
| 06 | touch_body_pct | G2 | weak | 57.1% — above ideal 40% threshold, aggressive candle |
| 07 | wick_defence_ratio | G2 | pass | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | pass | — |
| 10 | same_candle_tb | G2 | N/A | — |
| 11 | G5a | G3 | pass | — |
| 12 | G5b | G3 | fail | — |

**Final comment:** 10/11 pass. 1 N/A. overall looks like a pass but EOD+.

---

### Signal #2 — 2022-10-03 12:40 (T) 12:55 (B) 13:00 (E)
**Stock:** HDFCBANK | **Outcome:** EOD+

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | pass | — |
| 02 | slope_offset | G1 | pass | — |
| 03 | candles_above | G1 | pass | — |
| 04 | pullback_bars | G1 | pass | — |
| 05 | shoot_depth | G2 | weak | shoot_depth looks too long to not fail. advise |
| 06 | touch_body_pct | G2 | fail | — |
| 07 | wick_defence_ratio | G2 | fail | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | pass | — |
| 10 | same_candle_tb | G2 | N/A | — |
| 11 | G5a | G3 | fail | — |
| 12 | G5b | G3 | fail | — |

**Final comment:** fail. EOD+. G1 passes, G2 touch quality fails (#5 weak, #6 fail, #7 fail), G3 also fails.

---

### Signal #3 — 2022-10-03 14:00 (T)
**Stock:** HDFCBANK | **Outcome:** SL

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | pass | — |
| 02 | slope_offset | G1 | pass | — |
| 03 | candles_above | G1 | pass | Rising regime — price approaching from above |
| 04 | pullback_bars | G1 | — | Needs full re-review via H1.1 |
| 05 | shoot_depth | G2 | fail | — |
| 06 | touch_body_pct | G2 | fail | — |
| 07 | wick_defence_ratio | G2 | fail | — |
| 08 | bounce_vr_abs | G2 | — | — |
| 09 | bounce_vr_rel | G2 | — | — |
| 10 | same_candle_tb | G2 | — | — |
| 11 | G5a | G3 | fail | — |
| 12 | G5b | G3 | — | — |

**Final comment:** Rising regime. G2 touch quality correctly rejects. Needs full re-review via H1.1.

---

### Signal #4 — 2022-10-03 14:45 (T)
**Stock:** HDFCBANK | **Outcome:** LATE

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | fail | — |
| 03 | candles_above | G1 | fail | — |
| 04 | pullback_bars | G1 | — | — |
| 05 | shoot_depth | G2 | fail | — |
| 06 | touch_body_pct | G2 | fail | — |
| 07 | wick_defence_ratio | G2 | fail | — |
| 08 | bounce_vr_abs | G2 | — | — |
| 09 | bounce_vr_rel | G2 | — | — |
| 10 | same_candle_tb | G2 | — | — |
| 11 | G5a | G3 | fail | — |
| 12 | G5b | G3 | — | — |

**Final comment:** Flat signal. G1 alone kills it. Entry ≥ 14:45 — LATE flag applied.

---
