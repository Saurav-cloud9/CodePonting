# fv2 Signal Review — TATAMOTORS

Parent: [[fv2_index]]

## Signal Log

| #   | Stock      | Date       | Touch | Bounce | Entry | Outcome | G1        | G2           | G3  | Notes |
| --- | ---------- | ---------- | ----- | ------ | ----- | ------- | --------- | ------------ | --- | ----- |
| 1   | TATAMOTORS | 2025-05-15 | 09:15 | 09:15  | 09:20 | Win     | ✅N/AN/A  | N/A⚠️❌❌✅N/A✅ | ❌❌  | whats interesting is that even if we fail this one as per review there is another signal right after this one that hits the target. and the next one looks like a text book bounce as well. this one is SL hit so good call to reject it |
| 2   | TATAMOTORS | 2025-05-15 | 09:45 | 09:45  | 09:50 | Win     | ✅✅✅✅    | ✅✅❌❌✅N/A✅  | ✅✅  | interesting one coz it hits target, looks like a textbook bounce from pull back pov. just that #6 and #7 fail. |
| 3   | TATAMOTORS | 2025-05-15 | 14:45 | 15:00  | 15:05 | EOD+    | ✅✅❌      | N/AN/AN/A✅✅N/A | ✅✅  | fail as per review. right call. G1 candles_above fails → G2 touch params not applicable. |
| 4   | TATAMOTORS | 2023-11-30 | 12:30 | 12:45  | 12:50 | Win     | ❌❌❌      | N/AN/AN/A✅✅N/A | ✅❌  | signal fails review but hits target, so G2 vol and partial G3 got it thru. |
| 5   | TATAMOTORS | 2023-11-30 | 14:10 | 14:10  | 14:15 | EOD+    | ✅✅✅✅    | ⚠️✅✅❌✅N/A✅  | ❌❌  | another EOD+ -> how do pros differentiate positive EOD that is the ones that end up with profit after charges from the ones that end up with loss after charges. Should we not worry about this during signal review and revisit later? advise |
| 6   | TATAMOTORS | 2023-11-30 | 14:40 | 14:40  | 14:45 | LATE    | ✅✅✅✅    | ✅✅✅✅✅N/A✅  | ✅❌  | the touch happens at 1440 → possible reason why it ends up as EOD- since hardly any time to hit target. LATE flag applied. |
| 7 | TATAMOTORS | 2025-02-14 | 09:25 | 09:35 | 09:40 | SL | ❌N/A✅⚠️ | ✅❌❌✅❌N/A | ❌❌ | fail. so even though it has 3 and 4, since 1 & 2 arent there plus body pct and negative wick defence means low buyers conviction at touch resulting in a weak bounce setup followed by weak entry. |
| 8 | TATAMOTORS | 2025-02-14 | 14:00 | 14:15 | 14:20 | Win | ❌❌❌❌ | ❌❌❌✅❌N/A | ❌❌ | interesting case. the bounce vr alone carried it to target. but that is what we are able to conclude based on the 12 params. perhaps there is a param that we haven't configured for our review. the most obvious thing that i notice on the bounce candle is the upward surge, can this be a param altogether? advise |

---

## Outcome Key
- **SL** = stop hit before 14:50
- **Win** = target hit before 14:50
- **EOD+** = open at 14:50, in profit (forced exit)
- **EOD-** = open at 14:50, at loss (forced exit)
- **EOD** = post-15:00 signal, skipped in review
- **LATE** = entry ≥ 14:45 — structurally disadvantaged, EOD exit almost certain, flag separately

---

## Signal Detail

### Signal #1 — 2025-05-15 09:15 (T) 09:15 (B) 09:20 (E)
**Stock:** TATAMOTORS | **Outcome:** Win

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | pass | — |
| 02 | slope_offset | G1 | N/A | Opening bar — T-3 pre-market |
| 03 | candles_above | G1 | N/A | Opening bar — no prior session candles |
| 04 | pullback_bars | G1 | — | — |
| 05 | shoot_depth | G2 | weak | weak coz you have marked it grey and it does seem to pierce the ma line a bit too much |
| 06 | touch_body_pct | G2 | fail | — |
| 07 | wick_defence_ratio | G2 | fail | long enuf to fail the signal |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | N/A | Same candle |
| 10 | same_candle_tb | G2 | pass | — |
| 11 | G5a | G3 | fail | — |
| 12 | G5b | G3 | fail | — |

**Final comment:** whats interesting is that even if we fail this one as per review there is another signal right after this one that hits the target. and the next one looks like a text book bounce as well. this one is SL hit so good call to reject it.

---

### Signal #2 — 2025-05-15 09:45 (T) 09:45 (B) 09:50 (E)
**Stock:** TATAMOTORS | **Outcome:** Win

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | pass | — |
| 02 | slope_offset | G1 | pass | — |
| 03 | candles_above | G1 | pass | — |
| 04 | pullback_bars | G1 | pass | — |
| 05 | shoot_depth | G2 | pass | — |
| 06 | touch_body_pct | G2 | fail | — |
| 07 | wick_defence_ratio | G2 | fail | we need to define this better. right now you have failed it based on the fact that most of the lower wick is below ma line right? if yes, then we need to define this |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | N/A | Same candle |
| 10 | same_candle_tb | G2 | pass | — |
| 11 | G5a | G3 | pass | — |
| 12 | G5b | G3 | pass | — |

**Final comment:** interesting one coz it hits target, looks like a textbook bounce from pull back pov. just that #6 and #7 fail.

---

### Signal #3 — 2025-05-15 14:45 (T) 15:00 (B) 15:05 (E)
**Stock:** TATAMOTORS | **Outcome:** EOD+

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | pass | — |
| 02 | slope_offset | G1 | pass | — |
| 03 | candles_above | G1 | fail | — |
| 04 | pullback_bars | G1 | N/A | — |
| 05 | shoot_depth | G2 | N/A | — |
| 06 | touch_body_pct | G2 | N/A | — |
| 07 | wick_defence_ratio | G2 | N/A | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | pass | — |
| 10 | same_candle_tb | G2 | N/A | — |
| 11 | G5a | G3 | pass | — |
| 12 | G5b | G3 | pass | — |

**Final comment:** fail as per review. right call. G1 #03 candles_above fails — price not approaching from above. G2 touch/depth params not applicable (no proper pullback structure). EOD+ but structurally weak entry.

---

### Signal #4 — 2023-11-30 12:30 (T) 12:45 (B) 12:50 (E)
**Stock:** TATAMOTORS | **Outcome:** Win

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | fail | — |
| 03 | candles_above | G1 | fail | — |
| 04 | pullback_bars | G1 | N/A | — |
| 05 | shoot_depth | G2 | N/A | — |
| 06 | touch_body_pct | G2 | N/A | — |
| 07 | wick_defence_ratio | G2 | N/A | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | pass | — |
| 10 | same_candle_tb | G2 | N/A | — |
| 11 | G5a | G3 | pass | — |
| 12 | G5b | G3 | fail | — |

**Final comment:** signal fails review but hits target, so G2 vol (bounce_vr_abs + bounce_vr_rel) and partial G3 got it thru. Note: #05-#07 not applicable since no pullback structure confirmed — volume alone was driving this move.

---

### Signal #5 — 2023-11-30 14:10 (T) 14:10 (B) 14:15 (E)
**Stock:** TATAMOTORS | **Outcome:** EOD+

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | pass | — |
| 02 | slope_offset | G1 | pass | — |
| 03 | candles_above | G1 | pass | — |
| 04 | pullback_bars | G1 | weak | 12 bars — slow drift, momentum fading |
| 05 | shoot_depth | G2 | pass | — |
| 06 | touch_body_pct | G2 | pass | — |
| 07 | wick_defence_ratio | G2 | fail | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | N/A | — |
| 10 | same_candle_tb | G2 | pass | — |
| 11 | G5a | G3 | fail | — |
| 12 | G5b | G3 | fail | — |

**Final comment:** another EOD+ -> how do pros differentiate positive EOD that is the ones that end up with profit after charges from the ones that end up with loss after charges. Should we not worry about this during signal review and revisit later? advise. also 9/12 -> mostly pass if EOD profit stays truly positive.

---

### Signal #6 — 2023-11-30 14:40 (T) 14:40 (B) 14:45 (E)
**Stock:** TATAMOTORS | **Outcome:** LATE

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | pass | — |
| 02 | slope_offset | G1 | pass | — |
| 03 | candles_above | G1 | pass | — |
| 04 | pullback_bars | G1 | pass | — |
| 05 | shoot_depth | G2 | pass | — |
| 06 | touch_body_pct | G2 | pass | — |
| 07 | wick_defence_ratio | G2 | pass | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | N/A | — |
| 10 | same_candle_tb | G2 | pass | — |
| 11 | G5a | G3 | pass | — |
| 12 | G5b | G3 | fail | — |

**Final comment:** the touch happens at 1440 → possible reason why it ends up as EOD- since hardly any time to hit target. LATE flag applied — entry at 14:45 means only 1 candle before forced exit at 14:50.

---

### Signal — 2025-02-14 09:25 (T) 09:35 (B) 09:40 (E)
**Stock:** TATAMOTORS | **Outcome:** SL

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | N/A | — |
| 03 | candles_above | G1 | pass | — |
| 04 | pullback_bars | G1 | weak | debatable since only 2 candles available before T0. advise |
| 05 | shoot_depth | G2 | pass | passes but the close touches ma which means buyers consolidation is not upto the mark. advise |
| 06 | touch_body_pct | G2 | fail | — |
| 07 | wick_defence_ratio | G2 | fail | this param catches the close touching the ma. so my doubt at #5 is answered. pls confirm |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | fail | — |
| 10 | same_candle_tb | G2 | N/A | — |
| 11 | G5a | G3 | fail | — |
| 12 | G5b | G3 | fail | — |

**Final comment:** fail. so even though it has 3 and 4, since 1 & 2 arent there plus body pct and negative wick defence means low buyers conviction at touch resulting in a weak bounce setup followed by weak entry.

---

### Signal — 2025-02-14 14:00 (T) 14:15 (B) 14:20 (E)
**Stock:** TATAMOTORS | **Outcome:** Win

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | fail | — |
| 03 | candles_above | G1 | fail | — |
| 04 | pullback_bars | G1 | fail | — |
| 05 | shoot_depth | G2 | fail | — |
| 06 | touch_body_pct | G2 | fail | — |
| 07 | wick_defence_ratio | G2 | fail | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | fail | — |
| 10 | same_candle_tb | G2 | N/A | — |
| 11 | G5a | G3 | fail | — |
| 12 | G5b | G3 | fail | — |

**Final comment:** interesting case. the bounce vr alone carried it to target. but that is what we are able to conclude based on the 12 params. perhaps there is a param that we haven't configured for our review. the most obvious thing that i notice on the bounce candle is the upward surge, can this be a param altogether? advise

---
