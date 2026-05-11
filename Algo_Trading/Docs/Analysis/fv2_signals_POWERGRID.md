# fv2 Signal Review — POWERGRID

Parent: [[fv2_index]]

## Signal Log

| #   | Date       | Touch | Bounce | Entry | diff | Outcome | G1 (4)     | G2 (5)         | G3 (2) | Verdict                                                                                                                                                                                                    |
| --- | ---------- | ----- | ------ | ----- | ---- | ------- | ---------- | -------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 2025-12-22 | 14:20 | 14:35  | 14:40 | 3    | EOD-    | ❌❌❌        | ❌✅✅❌✅✅N/A      | ❌❌     | G1 broken, vol noise, rejected                                                                                                                                                                             |
| 2   | 2025-12-22 | 14:45 | 14:45  | 14:50 | 0    | SL      | ❌❌❌        | N/AN/AN/A✅N/A✅ | ❌❌     | diff=0, G1 fail, vol noise                                                                                                                                                                                 |
| 3   | 2025-12-22 | 14:55 | 15:05  | 15:10 | 2    | SL      | ❌❌❌        | N/AN/AN/A✅✅N/A | ❌❌     | G1 fail, vol passes, G3 fail                                                                                                                                                                               |
| 4   | 2025-12-22 | 15:15 | 15:15  | 15:20 | 0    | EOD     | ❌❌❌        | N/AN/AN/A✅N/A✅ | ❌✅     | post-15:00, skip                                                                                                                                                                                           |
| 5   | 2024-04-01 | 09:15 | 09:15  | 09:20 | 0    | EOD+    | ❌N/AN/A    | N/AN/AN/A✅N/A✅ | ✅❌     | opening bar, split G3                                                                                                                                                                                      |
| 6   | 2024-04-01 | 11:45 | 12:00  | 12:05 | 3    | EOD+    | ❌❌❌        | N/AN/AN/A✅✅N/A | ✅❌     | G1 fail, G3a pass, price followed                                                                                                                                                                          |
| 7   | 2024-04-01 | 12:10 | 12:25  | 12:30 | 3    | EOD+    | ❌❌❌        | N/AN/AN/A✅✅N/A | ✅✅     | first full G3 pass, price followed                                                                                                                                                                         |
| 8   | 2024-04-01 | 13:05 | 13:15  | 13:20 | 2    | EOD+    | ❌❌✅        | ❌✅❌❌✅✅N/A      | ✅❌     | ⭐ first G1 #03 pass, price followed                                                                                                                                                                        |
| 9   | 2024-04-01 | 14:55 | 14:55  | 15:00 | 0    | EOD     | ✅✅✅✅       | ⚠️❌✅✅N/A✅      | ✅✅     | post-14:50, 9/12 pass, skip                                                                                                                                                                                |
| 10  | 2025-03-17 | 09:20 | 09:20  | 09:25 | 0    | SL      | ❌N/A✅N/A   | ⚠️✅❌✅N/A✅      | ✅❌     | opening rush, T-1 first candle of day                                                                                                                                                                      |
| 11  | 2025-06-04 | 10:25 | 10:40  | 10:45 | 3    | SL      | ❌❌❌❌       | ✅❌✅✅✅N/A       | ❌❌     | diff=3 stale touch, entry reversed immediately                                                                                                                                                             |
| 12  | 2025-06-04 | 10:50 | 10:55  | 11:00 | 1    | EOD+    | ❌❌❌❌       | ❌✅❌✅✅N/A       | ❌❌     | diff=1, no pullback, poor touch, rejected                                                                                                                                                                  |
| 13  | 2025-06-04 | 12:45 | 13:00  | 13:05 | 3    | EOD-    | ✅✅❌❌       | ⚠️✅❌✅✅N/A      | ❌❌     | delayed touch — vol lag pushed T0 past pullback structure; T+3 bounce, poor follow-through                                                                                                                 |
| 14  | 2025-06-04 | 13:45 | 14:00  | 14:05 | 3    | SL      | ❌❌❌❌       | ⚠️❌❌✅✅N/A      | ✅❌     | bad setup at G1; bounce/entry show good surge but sudden downward movement in subsequent candles                                                                                                           |
| 15  | 2025-06-23 | 12:05 | 12:20  | 12:25 | 3    | Win     | ✅✅❌✅       | ✅❌❌✅✅N/A       | ❌✅     | not a perfect setup still wins. need to be discussed as to what pushed it to the finish line.                                                                                                              |
| 16  | 2025-06-23 | 12:35 | 12:35  | 12:40 | 0    | Win     | ✅✅✅✅       | ⚠️✅✅✅N/A✅      | ✅❌     | strongest signal we have come across imo. passes!                                                                                                                                                          |
| 17  | 2025-06-26 | 12:20 | 12:35  | 12:40 | 3    | Win     | ❌❌❌❌       | ❌✅❌✅✅N/A       | ❌❌     | fails almost everything yet wins — exception, not a pattern                                                                                                                                                |
| 18  | 2025-06-26 | 12:45 | 12:45  | 12:50 | 0    | Win     | ❌❌✅✅       | ✅✅❌✅N/A✅       | ✅❌     | 4 failures still pulls off a win. need to investigate the cause. most likely the volume surge on multiple candles pushes the price towards the target in this case.                                        |
| 19  | 2025-06-26 | 13:05 | 13:15  | 13:20 | 2    | Win     | ❌❌✅⚠️      | ⚠️❌❌✅✅N/A      | ✅❌     | another possible anomaly since it hits target despite the poor performance over the Gates                                                                                                                  |
| 20  | 2025-06-26 | 13:30 | 13:35  | 13:40 | 1    | EOD+    | ❌❌✅⚠️      | ✅❌✅✅✅N/A       | ✅❌     | another similar signal in terms of how it reaches the target, although its EOD+ and not a win. Signals 17 to 20 are pretty much the same in terms of how they move from start to end with few differences. |
| 21  | 2025-06-26 | 09:15 | 09:15  | 09:20 | 0    | Win     | ❌N/AN/AN/A | ✅✅✅✅N/A✅       | ✅❌     | G1 fails, rest still looks fine. could be an acceptable one since it has 2,3,4 params N/A. need to discuss this.                                                                                           |
| 22  | 2025-07-22 | 11:15 | 11:30  | 11:35 | 3    | Win     | ❌❌❌❌       | ❌❌❌✅✅N/A       | ❌❌     | anomaly since it mostly fails every param but still wins on the trade                                                                                                                                      |
| 23  | 2025-07-22 | 11:50 | 11:50  | 11:55 | 0    | Win     | ❌❌✅❌       | ✅✅✅✅N/A✅       | ✅❌     | G2 strong, G1 slope absent, #04 fail (lows rising to T0 — wick touch only). Not counted as winner.                                                                                                         |

---

## Outcome Key
- **SL** = stop hit before 14:50
- **Win** = target hit before 14:50
- **EOD+** = exit at 14:50, in profit (forced exit)
- **EOD-** = exit at 14:50, at loss (forced exit)
- **LATE** = entry ≥ 14:45 — covers all post-14:45 entries incl. post-15:00 signals

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
| #14 | pass | fail | SL |
| #15 | fail | pass | Win |
| #16 | pass | fail | Win |
| #17 | fail | fail | Win |

Pattern emerging: G3a pass correlates with EOD+ (price followed through at entry).
Full G3 pass (#7) = strongest entry confirmation seen so far — still EOD+ not win.
⚠️ #14 breaks the G3a→EOD+ pattern — first G3a pass ending in SL. G1 full fail context may be the differentiator.
⭐ #15 and #16 both Win with split G3 — G3 alone is not the deciding factor. G1 slope intact appears to be the load-bearing condition.
⚠️ #17 breaks the G1 slope hypothesis — full G1 fail, G3 both fail, only bounce vol passes. Win outcome. Exception: bounce VR combination may have been strong enough to force the outcome in a weak-regime setup. Do not generalise.

### Opening bar edge case (#5)
T0 = 09:15 → #02 N/A (T-3 pre-market), #03 N/A (no prior session candles).

### EOD+ cluster on 2024-04-01
Signals #5, #6, #7 all on same day, all EOD+.
Possible: stock was in a slow grind-up on that day — weak regime by our definition but directionally positive intraday.

### Winner candidates — 2025-06-23 ✅ reviewed
Signal #15 (12:05) and #16 (12:35) — both Win on same day. Both have G1 slope intact.

### First full G1 pass → Win (#16) ⭐
Signal #16: first signal with all 4 G1 params passing AND k=0 AND Win outcome.
- Orderly pullback to T0 — consistent bars drawing toward touch, near-perfect T0 attributes
- k=0: touch and bounce same candle, strong VR confirmation
- Swing high bar shows sudden surge (grey area) — but context explains it:
  A prior pullback+touch earlier in the day failed (two huge red candles post swing high, low VR at touch, no conviction) → weak hands cleared → late surge built the swing high for signal #16 → on the follow-up pullback, genuine buyer conviction at MA produced a proper bounce and entry follow-through
- Theory: failed prior touch → clears weak hands → sets up stronger second attempt

### June 26 momentum day anomaly (#17–#20) ⚠️
All 4 signals on 2025-06-26 share the same character: violent MA touches, immediate rejections, no clean pullback structure. POWERGRID was in a strongly trending/momentum day — price repeatedly tested and rejected MA without a genuine pullback setup. Gates evaluated structurally poor setups that occasionally won by accident (momentum carried price). Not reproducible edge.
Flag: candidate for a day-level filter (e.g. ADX threshold, daily candle range %). Do not generalise wins from this date.

### Fakeout pattern (#18, #19, #20 candidates)
Price briefly breaks below MA, gets rejected hard (large touch candle), snaps back immediately. Touch and bounce are a reaction to the touch candle's own downward momentum — not a genuine pullback to MA. Characteristics:
- k=0 or k=1 (no real pullback bar structure)
- Large touch candle body (aggressive move through MA)
- Extreme touch vr (>2.5x) — institutional spike not clean vol signature
- Shallow shoot_depth — price barely broke below MA
Gate implication: minimum pullback bar count (swing high → T0 ≥ 3 bars) would likely reject all fakeout candidates.

### Imperfect winner hypothesis (#15)
Signal #15 won with 7/11 params pass, 1 N/A. Key observations:
- G2 touch quality: 2/3 touch bar params failed (touch_body_pct, wick_defence_ratio) but both bounce bar params passed (bounce_vr_abs, bounce_vr_rel) — bounce confirmed buyers even though touch wasn't clean
- G1 slope both pass (#01 #02 ✅) may be the load-bearing condition — MA was genuinely rising
- Theory: when G1 slope is intact, G2 touch shape params matter less. Needs more winners to confirm.

---

## Signal Detail

### Signal #1 — 2025-12-22 14:20 (T) 14:35 (B) 14:40 (E)
**Stock:** POWERGRID | **Outcome:** EOD-

| #   | Param              | Gate | Verdict | Comment                                                         |
| --- | ------------------ | ---- | ------- | --------------------------------------------------------------- |
| 01  | slope_threshold    | G1   | fail    | —                                                               |
| 02  | slope_offset       | G1   | fail    | —                                                               |
| 03  | candles_above      | G1   | fail    | not approaching from above                                      |
| 04  | pullback_bars      | G1   | fail    | no pullback structure                                           |
| 05  | shoot_depth        | G2   | fail    | barely touching MA → pass (original note), but G1 regime broken |
| 06  | touch_body_pct     | G2   | pass    | its still huge right? shouldn't it be less than 50%?            |
| 07  | wick_defence_ratio | G2   | pass    | —                                                               |
| 08  | bounce_vr_abs      | G2   | pass    | —                                                               |
| 09  | bounce_vr_rel      | G2   | pass    | —                                                               |
| obs | same_candle_tb     | obs | N/A     | Different candles                                               |
| 10 | G3a                | G3   | fail    | —                                                               |
| 11 | G3b                | G3   | fail    | —                                                               |

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
| obs | same_candle_tb | obs | pass | k=0 confirmed |
| 10 | G3a | G3 | fail | Entry close < bounce close |
| 11 | G3b | G3 | fail | Entry VR drops |

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
| obs | same_candle_tb | obs | N/A | Different candles |
| 10 | G3a | G3 | fail | |
| 11 | G3b | G3 | fail | |

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
| obs | same_candle_tb | obs | pass | k=0 |
| 10 | G3a | G3 | fail | |
| 11 | G3b | G3 | pass | First split G3 observed |

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
| obs | same_candle_tb | obs | pass | k=0 |
| 10 | G3a | G3 | pass | Entry close > bounce close |
| 11 | G3b | G3 | fail | Entry VR drops |

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
| obs | same_candle_tb | obs | N/A | Different candles |
| 10 | G3a | G3 | pass | |
| 11 | G3b | G3 | fail | Entry VR drops |

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
| obs | same_candle_tb | obs | N/A | Different candles |
| 10 | G3a | G3 | pass | |
| 11 | G3b | G3 | pass | First full G3 pass on rejected signal |

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
| obs | same_candle_tb | obs | pass | Bounce VR > touch VR |
| 10 | G3a | G3 | pass | Entry close > bounce close |
| 11 | G3b | G3 | fail | Entry VR drops |

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
| obs | same_candle_tb | obs | pass | — |
| 10 | G3a | G3 | pass | — |
| 11 | G3b | G3 | pass | — |

**Final comment:** in my opinion its got 9 params clear. this table view with all the columns is making me look at the data differently. like what should be the cutoff to rule out a signal? should it get all 12 params ticked or even 1 param failing means the signal fails? normally we would fail this one coz it has weak pullback and fails at #6. plus its a signal post 1450. perhaps worth skipping discussing it too much. for now you can clarify the points i have mentioned here and in the one line comments.

---

### Signal #10 — 2025-03-17 09:20 (T) 09:20 (B) 09:25 (E)
**Stock:** POWERGRID | **Outcome:** SL

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | N/A | — |
| 03 | candles_above | G1 | pass | — |
| 04 | pullback_bars | G1 | N/A | only 1 candle before T0 |
| 05 | shoot_depth | G2 | weak | — |
| 06 | touch_body_pct | G2 | pass | — |
| 07 | wick_defence_ratio | G2 | fail | >1 = buyers recovered more than they overshot -> what does this part mean |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | N/A | — |
| obs | same_candle_tb | obs | pass | — |
| 10 | G3a | G3 | pass | — |
| 11 | G3b | G3 | fail | — |

**Final comment:** the T-1 candles is huge and has a sudden downward movement. T-1 is also the first candle of the day and so there is no prior candle to build a pattern. The touch candle looks decent visually but gets followed by a neutral entry candle and post that there is consistent downward movement. This suggests that at the start of the day if there is a sudden downward movement then perhaps its best not to trade for the first few minutes.

---

### Signal #11 — 2025-06-04 10:25 (T) 10:40 (B) 10:45 (E)
**Stock:** POWERGRID | **Outcome:** SL

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | fail | — |
| 03 | candles_above | G1 | fail | — |
| 04 | pullback_bars | G1 | fail | — |
| 05 | shoot_depth | G2 | pass | — |
| 06 | touch_body_pct | G2 | fail | — |
| 07 | wick_defence_ratio | G2 | pass | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | pass | — |
| obs | same_candle_tb | obs | N/A | — |
| 10 | G3a | G3 | fail | — |
| 11 | G3b | G3 | fail | — |

**Final comment:** most things went wrong from start to end. no pullback setup, the T0 candle itself looks fine but has a poor pullback preceeding it. There is a visible surge of price from T0 to T3(bounce), but the bounce candle despite showing huge volume has a weak follow thru or rather sudded downfall at the entry. rightly fails the setup

---

### Signal #12 — 2025-06-04 10:50 (T) 10:55 (B) 11:00 (E)
**Stock:** POWERGRID | **Outcome:** EOD+

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | fail | — |
| 03 | candles_above | G1 | fail | — |
| 04 | pullback_bars | G1 | fail | — |
| 05 | shoot_depth | G2 | fail | — |
| 06 | touch_body_pct | G2 | pass | — |
| 07 | wick_defence_ratio | G2 | fail | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | pass | — |
| obs | same_candle_tb | obs | N/A | — |
| 10 | G3a | G3 | fail | — |
| 11 | G3b | G3 | fail | — |

**Final comment:** its an EOD+ so it needs to be seen later if this one and signals like these actually profit us or end up as losers. For our signal review this one gets rejected. No pullback, no good touch, only bounce candle looks somewhat promising but gets followed up by a poor entry bar.

---

### Signal #13 — 2025-06-04 12:45 (T) 13:00 (B) 13:05 (E)
**Stock:** POWERGRID | **Outcome:** EOD-

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | pass | — |
| 02 | slope_offset | G1 | pass | — |
| 03 | candles_above | G1 | fail | — |
| 04 | pullback_bars | G1 | fail | — |
| 05 | shoot_depth | G2 | weak | — |
| 06 | touch_body_pct | G2 | pass | — |
| 07 | wick_defence_ratio | G2 | fail | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | pass | — |
| obs | same_candle_tb | obs | N/A | — |
| 10 | G3a | G3 | fail | — |
| 11 | G3b | G3 | fail | — |

**Final comment:** Delayed touch — T-2 was the structurally cleaner touch but its subsequent bounce didn't meet VR criteria, so Pine skipped it. T0 (12:45) was selected because its bounce (13:00) had sufficient VR. By then the pullback structure was consumed. T+3 bounce exists but follow-through is weak. Rejected.

---

### Signal #14 — 2025-06-04 13:45 (T) 14:00 (B) 14:05 (E)
**Stock:** POWERGRID | **Outcome:** SL

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | fail | — |
| 03 | candles_above | G1 | fail | — |
| 04 | pullback_bars | G1 | fail | — |
| 05 | shoot_depth | G2 | weak | — |
| 06 | touch_body_pct | G2 | fail | — |
| 07 | wick_defence_ratio | G2 | fail | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | pass | — |
| obs | same_candle_tb | obs | N/A | — |
| 10 | G3a | G3 | pass | — |
| 11 | G3b | G3 | fail | — |

**Final comment:** bad setup at G1. poor touch although bounce/entry show good surge but are followed by sudden downward movement in the subsequent candles.

---

### Signal #15 — 2025-06-23 12:05 (T) 12:20 (B) 12:25 (E)
**Stock:** POWERGRID | **Outcome:** Win

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | pass | — |
| 02 | slope_offset | G1 | pass | — |
| 03 | candles_above | G1 | fail | — |
| 04 | pullback_bars | G1 | pass | passes visual test but needs to be discussed since T-1 isnt above ma |
| 05 | shoot_depth | G2 | pass | — |
| 06 | touch_body_pct | G2 | fail | — |
| 07 | wick_defence_ratio | G2 | fail | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | pass | — |
| obs | same_candle_tb | obs | N/A | — |
| 10 | G3a | G3 | fail | — |
| 11 | G3b | G3 | pass | — |

**Final comment:** not a perfect setup still wins. need to be discussed as to what pushed it to the finish line.

---

### Signal #16 — 2025-06-23 12:35 (T) 12:35 (B) 12:40 (E)
**Stock:** POWERGRID | **Outcome:** Win

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | pass | — |
| 02 | slope_offset | G1 | pass | — |
| 03 | candles_above | G1 | pass | — |
| 04 | pullback_bars | G1 | pass | 3 bars = satifies the bare minimum |
| 05 | shoot_depth | G2 | weak | — |
| 06 | touch_body_pct | G2 | pass | — |
| 07 | wick_defence_ratio | G2 | pass | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | N/A | — |
| obs | same_candle_tb | obs | pass | — |
| 10 | G3a | G3 | pass | — |
| 11 | G3b | G3 | fail | — |

**Final comment:** strongest signal we have come across imo. passes!

---

### Signal #17 — 2025-06-26 12:20 (T) 12:35 (B) 12:40 (E)
**Stock:** POWERGRID | **Outcome:** Win | **k=3**

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | fail | — |
| 03 | candles_above | G1 | fail | — |
| 04 | pullback_bars | G1 | fail | — |
| 05 | shoot_depth | G2 | fail | — |
| 06 | touch_body_pct | G2 | pass | — |
| 07 | wick_defence_ratio | G2 | fail | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | pass | — |
| obs | same_candle_tb | obs | N/A | k=3, different candles |
| 10 | G3a | G3 | fail | — |
| 11 | G3b | G3 | fail | — |

**Final comment:** fails almost everything — G1 complete fail, G2 mostly fail, G3 both fail. Only bounce vol both pass. Treat as exception: bounce volume + price movement together pulled off the win despite no structural setup. Not a repeatable pattern.

---

### Signal #18 — 2025-06-26 12:45 (T) 12:45 (B) 12:50 (E)
**Stock:** POWERGRID | **Outcome:** Win

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | fail | — |
| 03 | candles_above | G1 | pass | — |
| 04 | pullback_bars | G1 | pass | — |
| 05 | shoot_depth | G2 | pass | — |
| 06 | touch_body_pct | G2 | pass | — |
| 07 | wick_defence_ratio | G2 | fail | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | N/A | — |
| obs | same_candle_tb | obs | pass | — |
| 10 | G3a | G3 | pass | — |
| 11 | G3b | G3 | fail | — |

**Final comment:** 4 failures still pulls off a win. need to investigate the cause. most likely the volume surge on multiple candles pushes the price towards the target in this case.

---

### Signal #19 — 2025-06-26 13:05 (T) 13:15 (B) 13:20 (E)
**Stock:** POWERGRID | **Outcome:** Win

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | fail | — |
| 03 | candles_above | G1 | pass | — |
| 04 | pullback_bars | G1 | weak | — |
| 05 | shoot_depth | G2 | weak | — |
| 06 | touch_body_pct | G2 | fail | — |
| 07 | wick_defence_ratio | G2 | fail | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | pass | — |
| obs | same_candle_tb | obs | N/A | — |
| 10 | G3a | G3 | pass | — |
| 11 | G3b | G3 | fail | — |

**Final comment:** another possible anomaly since it hits target despite the poor performance over the Gates

---

### Signal #20 — 2025-06-26 13:30 (T) 13:35 (B) 13:40 (E)
**Stock:** POWERGRID | **Outcome:** EOD+

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | fail | — |
| 03 | candles_above | G1 | pass | — |
| 04 | pullback_bars | G1 | weak | — |
| 05 | shoot_depth | G2 | pass | — |
| 06 | touch_body_pct | G2 | fail | — |
| 07 | wick_defence_ratio | G2 | pass | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | pass | — |
| obs | same_candle_tb | obs | N/A | — |
| 10 | G3a | G3 | pass | — |
| 11 | G3b | G3 | fail | — |

**Final comment:** another similar signal in terms of how it reaches the target, although its EOD+ and not a win. Signals 17 to 20 are pretty much the same in terms of how they move from start to end with few differences.

---

### Signal #21 — 2025-06-26 09:15 (T) 09:15 (B) 09:20 (E)
**Stock:** POWERGRID | **Outcome:** Win

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | N/A | — |
| 03 | candles_above | G1 | N/A | — |
| 04 | pullback_bars | G1 | N/A | — |
| 05 | shoot_depth | G2 | pass | — |
| 06 | touch_body_pct | G2 | pass | — |
| 07 | wick_defence_ratio | G2 | pass | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | N/A | — |
| obs | same_candle_tb | obs | pass | — |
| 10 | G3a | G3 | pass | — |
| 11 | G3b | G3 | fail | — |

**Final comment:** G1 fails, rest still looks fine. could be an acceptable one since it has 2,3,4 params N/A. need to discuss this.

---

### Signal #22 — 2025-07-22 11:15 (T) 11:30 (B) 11:35 (E)
**Stock:** POWERGRID | **Outcome:** Win

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
| 09 | bounce_vr_rel | G2 | pass | — |
| obs | same_candle_tb | obs | N/A | — |
| 10 | G3a | G3 | fail | — |
| 11 | G3b | G3 | fail | — |

**Final comment:** anomaly since it mostly fails every param but still wins on the trade

---

### Signal #23 — 2025-07-22 11:50 (T) 11:50 (B) 11:55 (E)
**Stock:** POWERGRID | **Outcome:** Win

| # | Param | Gate | Verdict | Comment |
|---|-------|------|---------|---------|
| 01 | slope_threshold | G1 | fail | — |
| 02 | slope_offset | G1 | fail | — |
| 03 | candles_above | G1 | pass | — |
| 04 | pullback_bars | G1 | fail | lows rising from swing high to T0 — no descent toward MA20; touch is a single wick spike, not a pullback conclusion |
| 05 | shoot_depth | G2 | pass | — |
| 06 | touch_body_pct | G2 | pass | — |
| 07 | wick_defence_ratio | G2 | pass | — |
| 08 | bounce_vr_abs | G2 | pass | — |
| 09 | bounce_vr_rel | G2 | N/A | — |
| obs | same_candle_tb | obs | pass | — |
| 10 | G3a | G3 | pass | — |
| 11 | G3b | G3 | fail | — |

**Final comment:** G2 strong (5/5 applicable). G1 slope absent (#01 #02 fail); #03 pass, #04 fail (lows rising from swing high to T0 — single wick touch, no structural descent). 3/4 G1 fail. Not counted as winner.

---
