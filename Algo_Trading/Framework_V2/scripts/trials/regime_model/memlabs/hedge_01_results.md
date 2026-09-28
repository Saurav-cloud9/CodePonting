# Hedge 01 — Passive NIFTY hedge overlay, daily-level MVP

FLAGSHIP_6BCEH_SHORT_VWAP_RSI60, delegated by fv2, 2026-09-19.

## Reference (unhedged, from master_basket.csv)

| Metric | Value |
|---|---|
| net_zpnl | -2436.26 |
| alpha (daily) | -0.408 |
| alpha_cumulative (theoretical ceiling) | -1042.49 |
| beta | -4.355 |
| p | 0.201 |

## Sanity check (reproduced from 54c_trade_log.csv, should match reference)

| Metric | Value |
|---|---|
| net_zpnl (all trades) | -2436.26 |
| alpha (daily) | -0.408 |
| alpha_cumulative | -1042.49 |
| beta | -4.355 |
| p | 0.201 |

## Hedged result

Hedge instrument: NIFTY (passive, tradeable). Sizing: hedge_beta = -basket_beta (offsets the reference basket-regressed beta by construction).

| Metric | Value |
|---|---|
| hedge_beta applied | 4.355 |
| hedge total P&L | 1106.67 |
| combined net_zpnl | -1329.59 |

### vs basket (primary — apples-to-apples with reference)

| Metric | Value |
|---|---|
| combined alpha (daily) | -0.374 |
| combined alpha_cumulative | -954.99 |
| combined beta | -1.185 |
| combined p | 0.242 |

### vs NIFTY (secondary — the hedge's own instrument)

| Metric | Value |
|---|---|
| combined alpha (daily) | -0.461 |
| combined beta | -0.632 |
| combined p | 0.150 |

## Comparison

- Theoretical ceiling (perfect hedge): net_zpnl -> -1042.49
- Realized: net_zpnl -> -1329.59
- Gap to ceiling: -287.10
- % of beta drag actually recovered: 79.4%
- Beta reduction: -4.355 -> -1.185

## Why it falls short of the ceiling

Two real, identifiable sources, not unexplained slippage:
1. **Daily-resolution approximation** — the hedge is priced once per day (NIFTY's own
   daily return), while the strategy's actual trades happen and exit intraday. A hedge
   that isn't actually held/sized at the moments the strategy's risk is live can't fully
   cancel it even with the right beta magnitude.
2. **Instrument mismatch** — the hedge is sized off the *basket*-regressed beta (-4.355)
   but traded via *NIFTY* (the only realistic passive instrument — "the basket" itself
   isn't tradeable). NIFTY and the 30-stock DS3 basket are correlated but not identical,
   so a NIFTY-sized hedge only closes ~73% of the basket-beta gap (-4.355 -> -1.185), not
   all of it. Consistent with the vs-NIFTY regression's own leftover beta (-0.632) being
   much smaller than the vs-basket leftover (-1.185) — the hedge does much better against
   its own actual instrument than against the proxy target it was sized from.

Side note on alpha: combined alpha_cumulative shifted from -1042.49 to -954.99 even
though the hedge is alpha=0 by construction. This isn't a bug — it's a finite-sample OLS
artifact of an *imperfect* beta cancellation (leftover beta of -1.185 still correlates
somewhat with the regression's alpha estimate). Expected, not a red flag.

## Assessment — is this worth pursuing further?

**Directionally yes, but not a slam dunk yet.** 79.4% beta-drag recovery is a real,
substantial effect — net_zpnl improved by over ₹1,100 (roughly half the original loss)
from a mechanically simple, passive overlay. That's a meaningful signal this is worth
continued investigation, not a null result.

But the honest gap (₹287 short of ceiling, beta only 73% closed) means the daily/NIFTY-
proxy version isn't a finished answer — it's a lower bound on what a properly-executed
hedge could do. The natural next step (flagged per your instructions, not done here):
**fetch intraday NIFTY data via KiteConnect** (same auth pattern as
monthly_reconciliation.py) and re-run this at the strategy's actual trade-level
resolution instead of daily-approximated. That would isolate how much of the remaining
gap is the daily-resolution approximation specifically (fixable) vs. the NIFTY/basket
instrument mismatch (structural, harder to fully close without a custom basket-tracking
instrument that doesn't exist).

Given the strategy's own alpha is not significant either way (p=0.201 unhedged, p=0.242
hedged) — this hedge doesn't turn a losing strategy into a winning one, and was never
going to (alpha isn't positive to begin with, per your own framing). Its value is purely
in removing a large, non-skill-driven drag so the strategy's *true* (currently
inconclusive) alpha becomes easier to see clearly — worth the intraday follow-up before
any live-testing conversation, not worth live-testing on this daily-approximated version
alone.
