# fv2 Signal Review — POWERGRID

Parent: [[fv2_index]]

## Signal Log

| #   | Stock     | Date       | Touch | Bounce | Entry | Outcome | G1      | G2              | G3  | Notes |
| --- | --------- | ---------- | ----- | ------ | ----- | ------- | ------- | --------------- | --- | ----- |
| 1   | POWERGRID | 2025-12-22 | 14:20 | 14:35  | 14:40 | EOD-    | ❌❌❌    | ❌✅✅❌✅✅N/A    | ❌❌  | signal rejected as per review. |
| 2   | POWERGRID | 2025-12-22 | 14:45 | 14:45  | 14:50 | SL      | ❌❌❌    | N/AN/AN/A✅N/A✅  | ❌❌  | Triple G1 fail. G2 vol noise. k=0. |
| 3   | POWERGRID | 2025-12-22 | 14:55 | 15:05  | 15:10 | SL      | ❌❌❌    | N/AN/AN/A✅✅N/A  | ❌❌  | G2 vol double pass, still rejected. |
| 4   | POWERGRID | 2025-12-22 | 15:15 | 15:15  | 15:20 | EOD     | ❌❌❌    | N/AN/AN/A✅N/A✅  | ❌✅  | Post-15:00 signal. Split G3. k=0. |
| 5   | POWERGRID | 2024-04-01 | 09:15 | 09:15  | 09:20 | EOD+    | ❌N/AN/A | N/AN/AN/A✅N/A✅  | ✅❌  | Opening bar. #02 N/A (no T-3). #03 N/A (no prior candles). Split G3. |
| 6   | POWERGRID | 2024-04-01 | 11:45 | 12:00  | 12:05 | EOD+    | ❌❌❌    | N/AN/AN/A✅✅N/A  | ✅❌  | Win after 14:50 → EOD+. Split G3. |
| 7   | POWERGRID | 2024-04-01 | 12:10 | 12:25  | 12:30 | EOD+    | ❌❌❌    | N/AN/AN/A✅✅N/A  | ✅✅  | First full G3 pass on rejected signal. EOD+. |
| 8   | POWERGRID | 2024-04-01 | 13:05 | 13:15  | 13:20 | EOD+    | ❌❌✅    | ❌✅❌❌✅✅N/A     | ✅❌  | ⭐ FIRST G1 #03 pass. G2 touch quality still mostly fails. Target hit after 14:50 → EOD+. |
| 9   | POWERGRID | 2024-04-01 | 14:55 | 14:55  | 15:00 | EOD     | ✅✅✅✅   | ⚠️❌✅✅N/A✅     | ✅✅  | Post-1450. 9 params clear. touch_body_pct fails. Worth logging but skip deep analysis. |

---

## Outcome Key
- **SL** = stop hit before 14:50
- **Win** = target hit before 14:50
- **EOD+** = open at 14:50, in profit (forced exit)
- **EOD-** = open at 14:50, at loss (forced exit)
- **EOD** = post-15:00 signal, skipped in review
- **LATE** = entry ≥ 14:45 — structurally disadvantaged, EOD exit almost certain, flag separately

---

## Emerging Patterns

### G1 regime failure → consistent rejection
Signals #1–#8: G1 slope fails across the board. G1 #03 (candles_above) first passes at signal #8.
Next threshold to watch: G1 fully pass (all 4 params) = full regime + approach confirmation.

### G2 vol as noise indicator
G2 vol params (bounce_vr_abs, bounce_vr_rel) passing on a broken regime does not rescue the trade.
Seen across signals #2–#7. Volume is present but context is wrong.

### G3 quality vs outcome
| Signal | G3a | G3b | Outcome |
|--------|-----|-----|---------|
| #2 | fail | fail | SL |
| #3 | fail | fail | SL |
| #4 | fail | pass | EOD (skip) |
| #5 | pass | fail | EOD+ |
| #6 | pass | fail | EOD+ |
| #7 | pass | pass | EOD+ |
| #8 | pass | fail | EOD+ |

Pattern emerging: G3a pass correlates with EOD+ (price followed through at entry).
Full G3 pass (#7) = strongest entry confirmation seen so far — still EOD+ not win.

### Opening bar edge case (#5)
T0 = 09:15 → #02 N/A (T-3 pre-market), #03 N/A (no prior session candles).

### EOD+ cluster on 2024-04-01
Signals #5, #6, #7 all on same day, all EOD+.
Possible: stock was in a slow grind-up on that day — weak regime by our definition but directionally positive intraday.

---

## Signal Detail

### Signal #1 — 2025-12-22 14:20 (T) 14:35 (B) 14:40 (E)
**Stock:** POWERGRID | **Outcome:** EOD-

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | fail | — |
| 03 | candles_above | G1 | fail | not approaching from above |
| 04 | pullback_bars | G1 | fail | no pullback structure |
| 05 | shoot_depth | G2 | fail | barely touching MA → pass (original note), but G1 regime broken |
| 06 | touch_body_pct | G2 | pass | its still huge right? shouldn't it be less than 50%? |
| 07 | wick_defence_ratio | G2 | pass | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | pass | — |
| 10 | same_candle_tb | G2 | N/A | Different candles |
| 11 | G5a | G3 | fail | — |
| 12 | G5b | G3 | fail | — |

**Final comment:** signal rejected as per review. G1 triple fail kills it.

---

### Signal #2 — 2025-12-22 14:45 (k=0)
**Touch:** 14:45 | **Bounce:** 14:45 | **Entry:** 14:50 | **Outcome:** SL

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | MA slope negative at touch |
| 02 | slope_offset | G1 | fail | MA slope at T-3 also negative |
| 03 | candles_above | G1 | fail | Not approaching from above |
| 04 | pullback_bars | G1 | N/A | No pullback structure |
| 05 | shoot_depth | G2 | N/A | G1 regime broken |
| 06 | touch_body_pct | G2 | N/A | G1 regime broken |
| 07 | wick_defence_ratio | G2 | N/A | G1 regime broken |
| 08 | bounce_vr_abs | G2 | pass | VR > 1.2× floor |
| 09 | bounce_vr_rel | G2 | N/A | Same candle — N/A convention |
| 10 | same_candle_tb | G2 | pass | k=0 confirmed |
| 11 | G5a | G3 | fail | Entry close < bounce close |
| 12 | G5b | G3 | fail | Entry VR drops |

**Final comment:** Triple G1 fail. G2 vol noise (passes but regime broken). k=0.

---

### Signal #3 — 2025-12-22 14:55
**Touch:** 14:55 | **Bounce:** 15:05 | **Entry:** 15:10 | **Outcome:** SL

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | |
| 02 | slope_offset | G1 | fail | |
| 03 | candles_above | G1 | fail | |
| 04 | pullback_bars | G1 | N/A | |
| 05 | shoot_depth | G2 | N/A | G1 regime broken |
| 06 | touch_body_pct | G2 | N/A | G1 regime broken |
| 07 | wick_defence_ratio | G2 | N/A | G1 regime broken |
| 08 | bounce_vr_abs | G2 | pass | |
| 09 | bounce_vr_rel | G2 | pass | Bounce VR > touch VR |
| 10 | same_candle_tb | G2 | N/A | Different candles |
| 11 | G5a | G3 | fail | |
| 12 | G5b | G3 | fail | |

**Final comment:** G2 vol double pass, still rejected. G1 broken throughout.

---

### Signal #4 — 2025-12-22 15:15 (k=0, post-15:00 — skipped)
**Touch:** 15:15 | **Bounce:** 15:15 | **Entry:** 15:20 | **Outcome:** EOD (skip)

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | |
| 02 | slope_offset | G1 | fail | |
| 03 | candles_above | G1 | fail | |
| 04 | pullback_bars | G1 | N/A | |
| 05 | shoot_depth | G2 | N/A | |
| 06 | touch_body_pct | G2 | N/A | |
| 07 | wick_defence_ratio | G2 | N/A | |
| 08 | bounce_vr_abs | G2 | pass | |
| 09 | bounce_vr_rel | G2 | N/A | Same candle |
| 10 | same_candle_tb | G2 | pass | k=0 |
| 11 | G5a | G3 | fail | |
| 12 | G5b | G3 | pass | First split G3 observed |

**Final comment:** Post-15:00 signal. Split G3 — G3a fail, G3b pass. k=0.

---

### Signal #5 — 2024-04-01 09:15 (opening bar, k=0)
**Touch:** 09:15 | **Bounce:** 09:15 | **Entry:** 09:20 | **Outcome:** EOD+

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | |
| 02 | slope_offset | G1 | N/A | Opening bar — T-3 pre-market |
| 03 | candles_above | G1 | N/A | Opening bar — no prior session candles |
| 04 | pullback_bars | G1 | N/A | |
| 05 | shoot_depth | G2 | N/A | |
| 06 | touch_body_pct | G2 | N/A | |
| 07 | wick_defence_ratio | G2 | N/A | |
| 08 | bounce_vr_abs | G2 | pass | |
| 09 | bounce_vr_rel | G2 | N/A | Same candle |
| 10 | same_candle_tb | G2 | pass | k=0 |
| 11 | G5a | G3 | pass | Entry close > bounce close |
| 12 | G5b | G3 | fail | Entry VR drops |

**Final comment:** Opening bar. #02 N/A (T-3 pre-market), #03 N/A (no prior session candles). Split G3.

---

### Signal #6 — 2024-04-01 11:45
**Touch:** 11:45 | **Bounce:** 12:00 | **Entry:** 12:05 | **Outcome:** EOD+

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | |
| 02 | slope_offset | G1 | fail | |
| 03 | candles_above | G1 | fail | |
| 04 | pullback_bars | G1 | N/A | |
| 05 | shoot_depth | G2 | N/A | G1 regime broken |
| 06 | touch_body_pct | G2 | N/A | G1 regime broken |
| 07 | wick_defence_ratio | G2 | N/A | G1 regime broken |
| 08 | bounce_vr_abs | G2 | pass | |
| 09 | bounce_vr_rel | G2 | pass | |
| 10 | same_candle_tb | G2 | N/A | Different candles |
| 11 | G5a | G3 | pass | |
| 12 | G5b | G3 | fail | Entry VR drops |

**Final comment:** Win after 14:50 → EOD+. Split G3.

---

### Signal #7 — 2024-04-01 12:10
**Touch:** 12:10 | **Bounce:** 12:25 | **Entry:** 12:30 | **Outcome:** EOD+

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | |
| 02 | slope_offset | G1 | fail | |
| 03 | candles_above | G1 | fail | |
| 04 | pullback_bars | G1 | N/A | |
| 05 | shoot_depth | G2 | N/A | G1 regime broken |
| 06 | touch_body_pct | G2 | N/A | G1 regime broken |
| 07 | wick_defence_ratio | G2 | N/A | G1 regime broken |
| 08 | bounce_vr_abs | G2 | pass | |
| 09 | bounce_vr_rel | G2 | pass | |
| 10 | same_candle_tb | G2 | N/A | Different candles |
| 11 | G5a | G3 | pass | |
| 12 | G5b | G3 | pass | First full G3 pass on rejected signal |

**Final comment:** First full G3 pass on rejected signal. EOD+.

---

### Signal #8 — 2024-04-01 13:05 ⭐ First G1 #03 pass
**Touch:** 13:05 | **Bounce:** 13:15 | **Entry:** 13:20 | **Outcome:** EOD+

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | MA slope not rising |
| 02 | slope_offset | G1 | fail | T-3 also negative |
| 03 | candles_above | G1 | pass | ⭐ First G1 #03 pass — price approached from above |
| 04 | pullback_bars | G1 | fail | Only 1 bar — too rushed |
| 05 | shoot_depth | G2 | fail | — |
| 06 | touch_body_pct | G2 | pass | Precision kiss, tiny overshoot |
| 07 | wick_defence_ratio | G2 | fail | Huge body = aggressive move through MA |
| 08 | bounce_vr_abs | G2 | fail | Weak buyer defence at MA |
| 09 | bounce_vr_rel | G2 | pass | Vol spike confirmed |
| 10 | same_candle_tb | G2 | pass | Bounce VR > touch VR |
| 11 | G5a | G3 | pass | Entry close > bounce close |
| 12 | G5b | G3 | fail | Entry VR drops |

**Final comment:** G1 #03 passes for the first time — approach direction correct. G1 slope (#01 #02) still fails. G2 touch quality mostly fails (3/4). Target hit after 14:50 → EOD+.

---

### Signal #9 — 2024-04-01 14:55 (T) 14:55 (B) 15:00 (E)
**Stock:** POWERGRID | **Outcome:** EOD

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | pass | — |
| 02 | slope_offset | G1 | pass | — |
| 03 | candles_above | G1 | pass | — |
| 04 | pullback_bars | G1 | weak | > 8 bars so its not a clear pass so its either weak or fail. its confusing coz its still a pull back visually right? advise |
| 05 | shoot_depth | G2 | weak | shoot_depth is .302, visually support at ma20 is available but candle body is huge and its a red candle. for now we just log this analysis. |
| 06 | touch_body_pct | G2 | fail | i want to know what is the threshold you have kept here since the value is already in red zone |
| 07 | wick_defence_ratio | G2 | pass | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | N/A | — |
| 10 | same_candle_tb | G2 | pass | — |
| 11 | G5a | G3 | pass | — |
| 12 | G5b | G3 | pass | — |

**Final comment:** in my opinion its got 9 params clear. this table view with all the columns is making me look at the data differently. like what should be the cutoff to rule out a signal? should it get all 12 params ticked or even 1 param failing means the signal fails? normally we would fail this one coz it has weak pullback and fails at #6. plus its a signal post 1450. perhaps worth skipping discussing it too much. for now you can clarify the points i have mentioned here and in the one line comments.

---
