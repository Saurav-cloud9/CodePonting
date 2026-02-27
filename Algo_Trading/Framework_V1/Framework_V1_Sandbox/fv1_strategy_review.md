# FV1 MA Bounce Strategy — Comprehensive Code Review

**Review date:** 2026-02-23
**Reviewed files:** `core/strategy.py`, `core/engine.py`, `core/portfolio.py`, `core/indicators.py`, `scripts/run_backtest.py`
**Backtest data:** 30 NSE stocks, 5-min OHLCV, January 2022 – December 2025

---

## Section 1 — Strategy Overview

This is a momentum-bounce long-only intraday strategy built for Indian NSE equities. It is designed to catch short-term mean-reversion bounces off the 20-period intraday moving average. The core hypothesis is that when price briefly dips to touch the MA20 on a 5-minute chart and then closes back above it with volume at least 1.2× the 20-bar average, there is a short-term upward momentum burst worth trading.

The strategy operates purely within a single trading session — all positions are closed by 15:00 IST at the latest. It does not trade short positions. It has no overnight exposure.

The codebase is structured in three clean, separated modules: a `Strategy` module that generates signals, an `Engine` that drives the event loop, and a `Portfolio` that manages positions and state. This separation is deliberate — the same strategy and portfolio code is intended to run unchanged across backtesting, paper trading, and live trading modes.

The strategy is described internally as a framework port of "v1.4.5 detect_bounce()," meaning it is a refactored version of an earlier monolithic script, preserved to match its exact signal logic.

---

## Section 2 — Logic Flow (Step by Step)

1. A 5-minute OHLCV parquet file is loaded for a single stock and sorted chronologically.
2. Candles outside regular market hours are dropped, keeping only bars between 09:15 and 15:30 IST.
3. Intraday indicators are computed: the 20-period rolling moving average of close prices (MA20), and the 20-period rolling average of volume.
4. Daily trend filters are computed: the MA50, MA100, and MA200 are calculated on daily close prices (using the last close of each trading day) and merged back onto every 5-minute bar for that day.
5. ATR-14 is computed on the 5-minute bars using the standard True Range formula (maximum of: high minus low, high minus previous close, previous close minus low), rolling 14 periods.
6. All signals for the entire dataset are generated in one pass before the event loop begins. This is a vectorised pre-computation (not bar-by-bar streaming).
7. In the signal generation pass, for each bar from the beginning to three bars before the end, the following checks are applied in sequence:
   - Skip if MA20 is not yet available (NaN).
   - If average volume is available, skip if the current bar's volume is below 1.2 times the 20-period average volume.
   - Check if the bar's low touched or penetrated the MA20 (low ≤ MA20). This is the "touch" condition.
   - If touched, look ahead up to 3 subsequent candles to find the first one where the close is back above the MA20 — the "reclaim" candle.
   - The entry is scheduled for the open of the candle immediately after the reclaim candle.
   - Skip the entry if the entry candle crosses into a different calendar month from the touch candle.
   - Skip the entry if the entry candle's time is at or after 14:30 IST.
   - If all checks pass, a signal is recorded with the entry datetime, entry price (next candle's open), and the MA20 value at the time of touch.
8. After the full signal scan, duplicate signals targeting the same entry datetime are removed, keeping only the first occurrence.
9. The event loop then iterates through every bar in order. At each bar, it checks if any signal is scheduled for that datetime. If yes, it opens a new position. Then it updates all open positions.
10. Position update checks each open position for three possible exits: stop loss hit, target hit, or EOD forced close.
11. After all bars are processed, completed trades and the equity curve are exported.

---

## Section 3 — Entry Conditions

A trade is entered only when all of the following are simultaneously true:

- The bar's low price is less than or equal to the current MA20 value (the price touched the moving average).
- The bar's volume is at least 1.2 times the 20-period average volume. If average volume is not yet available (the first 19 bars of the dataset), this filter is skipped entirely.
- MA20 is not NaN (at least 20 bars of price history are available).
- Within the next 1 to 3 candles after the touch, at least one candle closes above the MA20 value at the time of touch.
- The entry candle (open of the bar after the reclaim) must occur before 14:30 IST.
- The touch candle and the entry candle must fall within the same calendar month.
- No trend filter is applied in the current default backtest configuration — the daily MA50/MA100/MA200 columns are computed but `filter_mas` is passed as `None`, meaning price can be in any trend direction.

---

## Section 4 — Exit Conditions

There are three possible exit paths. They are checked in the order described below for each bar, starting from the bar after the entry bar (positions cannot exit on the same bar they were entered).

**End-of-Day Forced Exit (Time Exit)**
If the current bar's date matches the entry date and the bar's time is at or after 15:00 IST, the position is closed at the open price of that bar. This is the highest-priority exit and fires first.

**Stop Loss**
If the bar's low is at or below the stop price, the position is closed at the exact stop price (not the bar's low). This implies the stop is modelled as a guaranteed-fill at the stop level — no slippage below the stop.

**Target (Take Profit)**
If the bar's high is at or above the target price, the position is closed at the exact target price.

**Intra-bar Priority Logic**
When both the stop and target could have been triggered within the same bar (i.e., the bar spans both levels), the strategy uses the candle direction as a tiebreaker:
- If the bar is bullish (close greater than open), it is assumed the price dipped first before rallying, so the stop loss is checked first. If the stop is hit, the position closes at stop. Only if the stop is not hit is the target checked.
- If the bar is bearish (close less than or equal to open), it is assumed the price rallied first before dropping, so the target is checked first.

**What Does Not Exist**
There is no trailing stop. There is no breakeven stop. There is no max holding period in practice despite the `max_hold_bars=80` parameter being defined — this parameter is never checked anywhere in the update loop.

---

## Section 5 — Position Sizing Logic

Position sizing is computed at the moment a trade is opened, using two separate constraints, and the smaller quantity wins.

**Capital constraint:**
Each stock is allocated an equal slice of the total portfolio. With default settings of ₹10,00,000 total capital split across 30 stocks, each stock gets ₹33,333. The maximum quantity allowed by this constraint is: floor(33,333 / entry_price). On a low-priced stock like ASHOKLEY (~₹170), this allows roughly 196 shares. On an expensive stock like HDFCBANK (~₹1,600), this allows roughly 20 shares.

**Risk constraint:**
The strategy risks 1% of the initial total capital per trade, which is ₹10,000 regardless of current portfolio value. The stop distance is: ATR-14 multiplied by the ATR stop multiplier. The maximum quantity by risk is: floor(10,000 / stop_distance).

**Final quantity:**
The final quantity is the minimum of the two constraints above, with a hard floor of 1 share even if both constraints compute zero.

**Fallback:**
If ATR-14 is zero or negative (data corruption), the stop distance defaults to 1% of the entry price.

**Key implication:**
Position sizing does not compound. The risk amount (₹10,000) and the capital-per-stock ceiling (₹33,333) are computed from the initial capital and never updated as the portfolio grows or shrinks. This means a stock that loses 50% of its allocation does not receive reduced sizing on the next trade.

---

## Section 6 — ATR Configs

Four configurations are tested, referred to collectively as "Extreme" configs. The naming reflects that these use wide stops and wide targets compared to typical mean-reversion settings.

All configs set the stop as a multiple of ATR-14 below entry, and the target as a separate multiple of ATR-14 above entry. The risk-reward ratio is the implied ratio between the two distances.

| Config | Stop Distance | Target Distance | Implied RR |
|--------|--------------|-----------------|-----------|
| Extreme-1 | 2.5 × ATR | 4.0 × ATR | 1 : 1.6 |
| Extreme-2 | 2.5 × ATR | 4.5 × ATR | 1 : 1.8 |
| Extreme-3 | 3.0 × ATR | 4.5 × ATR | 1 : 1.5 |
| Extreme-4 | 3.0 × ATR | 5.0 × ATR | 1 : 1.67 |

Wider stops reduce the probability of getting stopped out by noise but increase the loss per stopped-out trade. Wider targets increase the reward when the trade works but reduce the probability of the target being hit. Extreme-4 is the most commonly selected best config across the 29-stock universe.

---

## Section 7 — Known Limitations and Assumptions

**Dead code — max hold bars:**
The `Portfolio` accepts a `max_hold_bars` parameter (default 80) but it is never referenced in the position update loop. It has no effect on any backtest or live run. A trade that is not stopped out, does not hit its target, and is entered intraday will always close at EOD — but the parameter implies it was intended to also handle multi-day holding, which the current EOD logic would prevent anyway.

**Trend filter is compiled but never activated:**
The daily MA50/MA100/MA200 columns are computed and merged for every stock, adding computation time and memory overhead. However, `generate_signals` receives `filter_mas=None` in all runs, so this data is never used to filter any signal. The strategy takes trades regardless of whether the stock is in a strong downtrend.

**Multi-position per stock is unrestricted:**
If two signals fire for the same stock on the same day, both are opened independently. There is no check for an already-open position on the same instrument. In extreme conditions (high-frequency touches of MA20), this can create many simultaneous positions on one stock.

**Slippage and transaction costs are absent:**
All entries use the exact open price of the entry bar. All stops and targets fill at exact levels. No brokerage, STT, exchange fees, or bid-ask spread is modelled. Given the strategy's tight per-trade expectancy on most stocks, even ₹20–50 of friction per trade could meaningfully change profitability.

**ATR is on 5-minute bars, not daily:**
The ATR-14 used for stop and target sizing is computed from 14 consecutive 5-minute candles, not 14 trading days. This makes the stop and target distances very narrow (typically a fraction of a rupee on many stocks), which is why qty values can be large.

**Entry price is the next bar's open:**
The strategy assumes it can enter at the exact open of the candle after the reclaim. In live markets, this would require a pre-market order or a fast execution at the candle open. Any delay converts this to a mid-candle fill with unknown slippage.

**Cross-month filter is a v1.4.5 compatibility artifact:**
Any signal where the touch candle and the entry candle fall in different calendar months is silently dropped. In practice this discards setups that occur in the last few candles of a trading month. There is no economic justification for this filter.

**Equity curve uses single mark-to-market price:**
The unrealised P&L for open positions is computed using the last close price seen across all positions, not each position's own instrument price. In a single-stock backtest this is irrelevant. In a multi-stock portfolio simulation it would be incorrect, but the current backtest is run per-stock in isolation, so this does not create errors.

**No short side:**
The strategy only goes long. On bearish stocks or in market downturns, the MA bounce pattern may signal repeated short-side setups that the strategy cannot exploit.

**Risk amount is fixed to initial capital:**
The 1% risk per trade is always calculated on the original ₹10,00,000, not the current portfolio value. If the portfolio grows to ₹12,00,000, the risk per trade stays ₹10,000, meaning the strategy under-risks relative to portfolio size. If it shrinks to ₹7,00,000, the strategy over-risks.

---

## Section 8 — CC Suggestions for Improvement

**1. Activate the trend filter**
The infrastructure to apply daily MA filters already exists — `filter_mas` just needs to be passed as `["ma50"]` or `["ma200"]`. Based on standard mean-reversion theory, MA bounce setups work far better when the stock is in an uptrend (price above MA50 or MA200). The daily MA columns are already computed; activating the filter costs nothing and is the single highest-impact change that could improve the portfolio win rate.

**2. Remove or implement max_hold_bars**
Either delete `max_hold_bars` from the Portfolio constructor (since EOD exit already prevents overnight holds), or implement it as a hard backstop that closes any position that has been open for more than N bars regardless of intraday logic. As-is it creates a misleading contract between the code and its reader.

**3. Add a concurrent-position guard**
Before opening a new position, check whether a position on the same stock is already open. On volatile days, a single stock can generate 5–10 bounce signals. Stacking all of them creates unintended concentration and inflates trade counts.

**4. Model transaction costs**
Even a flat ₹30 per trade (brokerage + STT + exchange fees, conservative estimate for NSE) applied across all 76,000 portfolio trades would amount to roughly ₹23,00,000 in frictional costs over the backtest period — several times larger than the total profit on the top 5 stocks. This is the single most important sanity check before live deployment.

**5. Avoid the first 30 minutes**
The 09:15–09:45 window on NSE is characterised by wide spreads, high volatility, and unreliable price discovery. Adding a time filter that blocks entries before 09:45 would reduce noise trades and improve signal quality.

**6. Compounding position sizing**
Replace `initial_capital` with `self.cash` (or `current_equity`) in the risk calculation so that position sizes scale with portfolio performance. Currently the strategy behaves as if it has exactly ₹10,00,000 forever.

**7. Breakeven stop management**
For the 5 profitable stocks, a significant share of winning trades likely see a favourable move before reversing to hit the wide stop. Implementing a rule to move the stop to breakeven once the trade is, say, 50% of the way to target would materially reduce average loss size and improve expectancy on the marginal stocks (HDFCBANK, ICICIBANK).

**8. Drop the cross-month boundary filter**
The filter discarding setups that span a month boundary is a legacy artifact from when the strategy processed data month-by-month. In the current continuous-data framework it serves no purpose and silently discards valid signals at month-ends.

**9. Add slippage to the intra-bar exit model**
Currently, stop-loss fills happen at the exact stop price. A conservative improvement would fill at stop minus one tick (or stop minus a small fixed fraction of ATR) to simulate realistic negative slippage on stop fills. Target fills are less affected since they are limit-like and tend to fill near the target on a bullish move.

**10. Validate signal deduplication logic**
The deduplication step keeps only the first signal for a given entry datetime. If two different touch candles from different points in the day converge on the same entry bar, one is silently discarded. Log the number of deduplicated signals per stock to understand how often this fires.

---

## Section 9 — Open Questions

**Why 14:30 as the entry cutoff?**
NSE closes at 15:30 IST. With an entry cutoff at 14:30 and ATR-based wide stops, a trade entered at 14:30 has at most 30 minutes to hit its target before EOD closes it. No rationale is documented for choosing 14:30 specifically over 14:00 or 15:00.

**Why lookahead up to 3 candles?**
The reclaim can be detected 1, 2, or 3 bars after the touch. There is no documented reason for 3 as the upper bound. A 1-bar reclaim (close above MA on the very next candle) would be a stronger, more decisive signal. Allowing 3 bars increases trade count but may introduce weaker setups.

**Why a volume multiplier of exactly 1.2?**
The 20% above average threshold for volume has no documented rationale. Most momentum literature uses 1.5x–2x. A lower threshold like 1.2x may be generating marginal volume spikes that do not represent genuine institutional interest.

**What does "Extreme" mean in the config names?**
The four configs are all labelled "Extreme" without an opposing baseline (e.g., "Conservative" or "Normal"). It is unclear whether these configs were selected from a broader optimisation or hand-picked, and what the eliminated alternatives looked like.

**Why is daily MA data computed but never used?**
The `compute_daily_mas` function runs for every stock on every backtest, adding meaningful compute time for 30 stocks. If the trend filter is never going to be activated, this function call could be removed from the runner to reduce backtest time.

**Why is risk_per_trade fixed at 1% of initial capital and not configurable per stock?**
The current configuration gives the same rupee risk per trade (₹10,000) to every stock in the universe, regardless of price level, liquidity, or historical volatility. A low-priced stock like ASHOKLEY (~₹170) ends up with a very different share quantity and capital exposure than a high-priced stock like HDFCBANK (~₹1,600), yet both risk the same ₹10,000. This is true across all 29 stocks — the flat 1% rule takes no account of individual stock characteristics. Is this intentional, or is it a default left in from earlier development?

**Why does max_hold_bars exist?**
The parameter suggests the strategy was at some point intended to handle multi-day or multi-session holding. If all positions are guaranteed to close at EOD, why is this parameter present at all? This raises the question of whether there is a planned multi-day version of the strategy.

**Why is ATR computed on 5-minute bars rather than daily bars?**
Using 5-minute ATR for position sizing means the stop distance is extremely small in absolute terms (a few rupees on most stocks). Is this intentional — i.e., was the strategy explicitly designed for tight intraday ATR-based risk? Or is this a carry-over from a different version where daily ATR was intended?

---

*Review generated by Claude Code (fv1_strategy_review.md). All observations are based solely on reading the source files above — no runtime assumptions beyond what is explicitly coded.*


**CLAUDE CHAT DISCUSSION**

Below is the OCT 2024 drawn down analysis discussion. We will later look at all the major drawdowns and use that information to apply fixes to our code to avoid these windows for trading via our bot.
# ─────────────────────────────────────────────────────────────────
# 💡 KEY INSIGHT FROM THIS ANALYSIS:
# ─────────────────────────────────────────────────────────────────

# TWO SEPARATE PROBLEMS in Oct 2024:
# ─────────────────────────────────────────────────────────────────

#   PROBLEM 1 → 10 stocks fell below MA50 → filter removed them
#               ✅ Filter worked as designed

#   PROBLEM 2 → Metals stayed ABOVE MA50 but still lost badly
#               NATIONALUM: 100% up-days → still -5,030 loss
#               WIPRO:      100% up-days → still -3,702 loss
#               ❌ Filter was blind to SECTOR-LEVEL corrections

# ─────────────────────────────────────────────────────────────────
# 🎯 THE REAL PROBLEM THIS REVEALS:
# ─────────────────────────────────────────────────────────────────

#   MA50 trend filter = individual stock filter only
#   It cannot detect: "metals sector is in a sharp correction"
#   even though each metal stock is still above its own MA50.
#   FII selling hit metals hard → every bounce attempt failed.

# ─────────────────────────────────────────────────────────────────
# 💡 WHAT THIS SUGGESTS FOR FV2:
# ─────────────────────────────────────────────────────────────────

#   A sector-level filter would have helped here:
#   → If NIFTY Metal index < MA50 → skip all metal stocks
#   → Nifty50 index filter as master on/off switch
#   Individual stock MA50 alone is insufficient during
#   sharp sector rotations driven by FII flows.

# ─────────────────────────────────────────────────────────────────
# ⚠️  BOTTOM LINE:
#   Oct 2024 proves the strategy has no defense against
#   coordinated sector selloffs. The bounce just doesn't work
#   when the whole sector is in distribution mode.
# ─────────────────────────────────────────────────────────────────