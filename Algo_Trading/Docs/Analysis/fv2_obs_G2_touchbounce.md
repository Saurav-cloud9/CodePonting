# G2 — Touch & Bounce Observations

Parent: [[fv2_index]]
Params: #05 shoot_depth · #06 touch_body_pct · #07 wick_defence_ratio · #08 bounce_vr_abs · #09 bounce_vr_rel · #10 same_candle_tb

**What G2 checks:** How does price INTERACT with the MA during the touch and bounce?
shoot_depth: how far it pierces. touch_body_pct: candle aggression at touch (≤40% = clean deceleration). wick_defence_ratio: buyer response quality at the MA. bounce_vr_abs/rel: volume spike confirming the bounce. same_candle_tb: whether touch and bounce are on the same bar.

---

## Signals where G2 passed but trade lost
<!-- -->

## Signals where G2 failed (correctly filtered)
<!-- -->

## Signals where G2 partially passed (mixed verdicts)
<!-- -->

## Param Roles (from signal #11 analysis, 2026-04-19)

| Param | Role | Type |
|---|---|---|
| `wick_defence_ratio` | Hard gate — flags close/open < MA (body pierced into MA) | Pass/fail |
| `shoot_depth` | Primary depth measure for wick-touch (body above MA, only wick dips below) | Quality gradient |
| `touch_body_pct` | Uniformity proxy — small body = no sudden price spike at touch. Relevant in both wick-touch and body-pierce scenarios | Quality gradient |

**Rule of thumb:**
- `wick_defence_ratio` = pass/fail boundary
- `shoot_depth` + `touch_body_pct` = quality gradient (subjective threshold, not hard gate)
- When body above MA: `shoot_depth` is primary, `touch_body_pct` secondary
- When body pierces MA: `wick_defence_ratio` calls it out; `touch_body_pct` still adds uniformity signal

**"Wanna be pullback" spike pattern** — spike green candle → crash through MA → no real pullback structure. G1 territory. Candidate filter if it repeats on failures.

## Pattern
<!-- -->
