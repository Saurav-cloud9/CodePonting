# MA-short "flip" hypothesis — ruled out (2026-09-04)

## Motivation

CAPM-style alpha/p-value check (daily aggregate zpnl vs NIFTY50 daily return,
manual OLS, all 30 stocks pooled) run on 8 shortlisted combos — raw #1-by-ZPF
and healthy-subset #1 (EOD%≤30), for each of ma_short v1, ma_short v2_vwap,
6bce v0, 6bce v1_vwap:

| Combo | Alpha (₹/day) | p-value | Verdict |
|---|---|---|---|
| ma_short_v1 raw (6.0/6.0) | -10.31 | <0.0001 | SIG NEG |
| ma_short_v1 healthy (2.0/3.0) | -18.70 | <0.0001 | SIG NEG |
| ma_short_v2vwap raw (4.5/6.0) | -7.02 | <0.0001 | SIG NEG |
| ma_short_v2vwap healthy (2.0/3.0) | -12.68 | <0.0001 | SIG NEG |
| 6bce_v0 raw (6.0/6.0) | -9.73 | <0.0001 | SIG NEG |
| 6bce_v0 healthy (2.0/3.0) | -32.23 | <0.0001 | SIG NEG |
| 6bce_v1vwap raw (4.0/6.0) | -5.39 | <0.0001 | SIG NEG |
| 6bce_v1vwap healthy (2.0/3.0) | -11.61 | <0.0001 | SIG NEG |

All 8 showed **statistically significant negative alpha** — not noise/zero,
a real and consistent negative edge beyond market-beta exposure. This raised
the hypothesis: if the SHORT direction has confident negative alpha, does
flipping to LONG on the exact same touch condition produce positive alpha?

## Why it's not the same as ma_bounce

ma_short's touch condition (`high>=MA20, open<MA20, close<MA20` — body fully
below MA, bearish-looking rejection) and ma_bounce's touch condition
(`low<=MA20, open>MA20, close>MA20` — body fully above MA, bullish-looking
bounce) are **structurally disjoint** — a candle's open can't be both above
and below the MA at once. The flip tests going LONG specifically on the
bearish-looking candles (a contrarian/fakeout bet, SMC "inducement"-adjacent),
not the already-tested bullish-looking bounce candles.

## Result — hypothesis NOT supported

Single-combo sanity check (`entry_flip.py`), SL=2.0/TP=4.5 (same as the
live-deployed SHORT combo, for direct comparison), full 30 stocks, full DS3
range:

| | SHORT (live combo) | LONG-flip |
|---|---|---|
| N | 114,516 | 120,943 |
| PF | 1.123 | **0.923** |
| ZPF | 0.762 | **0.622** |
| SL% / EOD% / TP% | 45.1 / 38.6 / 16.3 | 49.3 / 36.7 / 14.0 |

LONG-flip is worse on every metric, not better — PF drops below 1.0 even
before charges. Full 90-combo sweep was not run; this single-combo result
was decisive enough to close out the hypothesis.

## Why the naive flip didn't work (reasoning correction)

A significant negative alpha for the SHORT direction does not imply a
significant positive alpha for a naive LONG flip, because flipping direction
changes the entire exit structure (SL/TP price levels swap sides), not just
the sign of the same PnL series — trades resolve on different triggers and
timing entirely. More likely explanation: the entries may carry some genuine
downside-predictive information, but the ATR-multiple SL/TP sizing doesn't
cleanly capture it in either direction — a different, harder problem than
"we had the direction backwards."

## Verdict

**Ruled out.** Not pursuing further. Back to SMC rebuild as the next raw-edge
direction (per the 2026-09-04 discussion).
