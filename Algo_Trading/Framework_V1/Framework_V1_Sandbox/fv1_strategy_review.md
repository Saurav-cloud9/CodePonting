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

## Section 7 — Limitations, Assumptions & Improvements

**1. Trend filter compiled but never activated**

*Limitation:* The daily MA50/MA100/MA200 columns are computed and merged for every stock on every run, adding compute time and memory overhead. However, `generate_signals` receives `filter_mas=None` in all runs, so this data is never used to filter any signal. The strategy takes trades regardless of whether the stock is in a strong downtrend.

*Improvement:* Pass `filter_mas=["ma50"]` or `filter_mas=["ma200"]` to activate the already-built infrastructure. Based on standard mean-reversion theory, MA bounce setups work materially better when the stock is above its longer-term trend. The columns are already computed — this is a single config change with no code required, and is the single highest-impact change that could improve the portfolio win rate.

*Verdict:* Remove compute_daily_mas() call from the runner entirely. Daily MA filter showed minimal improvement in prior testing (v1.4.3) and is unused in current config. A proper regime filter will be implemented via Optuna AFTER Sandbox baseline CAGR is established.
No code required now — this is a deletion, not an addition.

---

**2. Dead code — `max_hold_bars`**

*Limitation:* `Portfolio` accepts a `max_hold_bars` parameter (default 80) that is never referenced in the position update loop. It has no effect on any backtest or live run. A trade that is not stopped out and does not hit target will always close at EOD — the parameter implies multi-day holding was intended, which the current EOD logic already prevents anyway.

*Improvement:* Either delete the parameter entirely (since EOD exit already covers it), or implement it as a hard backstop that closes any position open for more than N bars regardless of intraday logic. As-is it creates a misleading contract between the code and its reader.

*Verdict:* Delete max_hold_bars parameter entirely. At 5-min bars, 80 bars = 400 minutes which exceeds the full trading session (375 mins) — this parameter can never fire before the EOD exit. It is dead code with no intraday purpose. If a multi-day/swing variant is built in future, reintroduce it then with appropriate logic. For fv1 intraday → remove.

---

**3. Multi-position per stock is unrestricted**

*Limitation:* If two signals fire for the same stock on the same day, both are opened independently with no check for an already-open position on the same instrument. On volatile days with high-frequency MA20 touches, this can create many simultaneous positions on one stock — unintended concentration that inflates trade counts and skews PnL.

*Improvement:* Before opening a new position, check whether a position on the same instrument is already open. A simple `if instrument in self.open_positions: skip` guard eliminates the stacking behaviour. Optionally extend this to: close the existing position first, then re-enter, if a fresher signal is stronger.

*Verdict:* Enforce maximum 1 open position per stock at any time. Current position sizing constraints (capital ceiling + risk per trade) do not prevent a second position from opening on the same stock while the first is active — this must be handled by an explicit check in the engine. For live trading, if a new signal fires on a stock already in an open trade, skip it entirely. Do not close-and-reenter — the added complexity is not justified for an intraday strategy. Add this guard to the engine before Sandbox testing begins.

---

**4. Slippage and transaction costs are absent**

*Limitation:* All entries use the exact open price of the entry bar. All stops and targets fill at exact levels. No brokerage, STT, exchange fees, or bid-ask spread is modelled. Given the strategy's tight per-trade expectancy on most stocks, even ₹20–50 of friction per trade could meaningfully change profitability. At scale across 76,000 portfolio trades, conservative estimates suggest ₹23,00,000+ in unmodelled frictional costs — several times larger than the total profit on the top 5 stocks. Stop-loss fills at the exact stop price further overstate returns, as real fills on stops occur below the stop level.

*Improvement (costs):* Apply a flat per-trade friction charge (₹30–50 as a conservative NSE estimate) deducted from PnL at trade close. Run the full backtest with costs enabled and compare equity curves to establish a break-even frequency threshold. This is the single most important sanity check before live deployment.

*Improvement (exit slippage):* Fill stop-loss exits at `stop_price - 1 tick` (or `- small fraction of ATR`) rather than at the exact stop level to simulate realistic negative slippage. Target fills are less affected as they are limit-like and tend to fill near the target on a bullish move.

*Verdict:* Model transaction costs dynamically using the actual broker formula, not a flat estimate. For each trade, compute charges as: brokerage (0.05% per side for Upstox, 0.03% per side for Kite) + STT (0.025% on sell side only) + exchange fees (0.00345% per side) + SEBI (0.0001% per side) + GST (18% on brokerage + exchange + SEBI) + stamp duty (0.003% on buy side). Deduct from PnL at trade close. Report three output columns: raw_pnl (no charges), net_pnl_upstox, net_pnl_kite — and corresponding CAGR for each. Entry slippage: fill at open + 0.1×ATR (conservative, scales with volatility). SL exit slippage: fill at stop_price - 1 tick. Target fills: exact (no slippage). This gives a realistic view of strategy profitability across both brokers before committing to live deployment.


---

**5. Cross-month filter is a v1.4.5 compatibility artifact**

*Limitation:* Any signal where the touch candle and the entry candle fall in different calendar months is silently dropped. This was a compatibility artifact from when the strategy processed data month-by-month. In the current continuous-data framework it serves no purpose and discards valid signals at month-ends with no economic justification.

*Improvement:* Remove the cross-month boundary check from `generate_signals` entirely.

*Verdict:* Remove the cross-month boundary check from generate_signals entirely. With a 14:30 entry cutoff and 15:00 EOD exit, the touch candle and entry candle always fall on the same day — making cross-month signals mathematically impossible. No logging or measurement needed before removal. Straightforward deletion.

---

**6. Risk amount is fixed to initial capital**

*Limitation:* The 1% risk per trade is always calculated on the original ₹10,00,000, not the current portfolio value. If the portfolio grows to ₹12,00,000, the strategy under-risks. If it shrinks to ₹7,00,000, the strategy over-risks. Position sizes do not compound in either direction.

*Improvement:* Replace `initial_capital` with `current_equity` (or `self.cash + open_position_value`) in the risk calculation so position sizes scale with portfolio performance. This is the standard approach in systematic trading and materially changes long-run equity curve shape.

*Verdict:* Replace initial_capital with current_equity in both the risk constraint and capital-per-stock ceiling calculations so position sizes compound with portfolio performance. This is a more realistic simulation of live trading behaviour — sizes grow after winning streaks and shrink after losing streaks. Results will differ from the current flat baseline, but that difference is the point. Implement before Sandbox runs so all 16 combination results reflect compounding from the start.

---

**7. ATR is computed on 5-minute bars, not daily**

*Limitation:* ATR-14 is derived from 14 consecutive 5-minute candles, not 14 trading days. This makes stop and target distances extremely narrow in absolute terms (often a fraction of a rupee), resulting in large share quantities and high sensitivity to minor intrabar moves. It is unclear whether this was intentional or a carry-over from an earlier version.

*Improvement:* Test a parallel config where position sizing uses daily ATR-14 (14 trading days) while stop/target placement retains 5-minute ATR. Daily ATR better represents the stock's realistic daily risk range and would produce more conservative, realistic position sizes. Compare trade counts, average loss, and equity curves between both approaches in Sandbox before committing.

*Verdict:* Keep ATR-14 computed on 5-minute bars for both position sizing and exit logic. This is correct and intentional for an intraday strategy — 5-min ATR produces stop distances proportional to intraday noise, meaningful position sizes, and exits that resolve within the trading session. Daily ATR would produce oversized stops (₹20-50+), tiny quantities, and negligible PnL — effectively breaking the strategy. CC raises a valid question but 5-min ATR is the right choice. No change required.

---

**8. Entry price is the next bar's open**

*Limitation:* The strategy assumes it can enter at the exact open of the candle after the reclaim. In live markets this requires either a pre-market limit order or a very fast market order at candle open. Any delay produces a mid-candle fill at an unknown worse price — especially problematic in the first 30 minutes of the session when spreads are wide.

*Improvement:* Add a configurable entry slippage offset: `entry_price = next_bar_open + (entry_slip_fraction × ATR)`. Default to a small positive fraction (e.g., 0.1 × ATR) to simulate realistic mid-candle fills. This is distinct from transaction costs — it models execution timing risk, not fee drag.

*Verdict:*: No separate action required. The concern about mid-candle fills is overstated for liquid NSE F&O stocks where order books are deep and 50-500ms latency produces negligible price movement. Entry slippage modelled as open + 0.1×ATR (agreed under point #4) already handles this conservatively. Covered.

---

**9. Equity curve uses a single mark-to-market price**

*Limitation:* Unrealised PnL for open positions is computed using the last close price seen across all positions — a single shared value — rather than each position's own instrument price. In the current per-stock isolated backtest this produces no error. In a future multi-stock simultaneous simulation it would silently produce incorrect unrealised PnL.

*Improvement:* Refactor mark-to-market to look up each position's own instrument's last close independently. This is a low-effort correctness fix that future-proofs the portfolio module before multi-stock simulation is enabled.

*Verdict:* Defer to full DS3 backtest phase (Step 5 of master plan). Mark-to-market equity curve has zero impact on CAGR, PnL, win rate, or any Sandbox combination results. Relevant only for drawdown accuracy and risk-adjusted metrics (Sharpe, Calmar). Implement then, not now. Added to deferred improvements tracker.

---

**10. No short side**

*Limitation:* The strategy is long-only. On bearish stocks or during market downturns, the MA bounce pattern generates repeated short-side setups that the strategy cannot exploit. This limits opportunity and leaves the portfolio fully exposed to downtrend periods with no offsetting positions.

*Improvement:* This is a design boundary, not a bug. A short-side mirror (price touches MA from below, reclaims below MA, stock in downtrend via MA50 filter) could be designed as a separate strategy module and tested independently in Sandbox before integration. Not recommended until the long-only version is stable and the trend filter is activated.

*Verdict:* Long-only is correct and intentional for FV1. MA Bounce mean-reversion works best with the structural bullish bias of Indian large-cap equities. Short side requires a completely different signal generator (MA rejection from above), separate SEBI/circuit-breaker risk management, and independent validation before merging with long signals. Defer to FV2 or a dedicated short module. No action required in FV1.

---

**11. No filter for the open auction window**

*Limitation:* The strategy permits entries from 09:15 IST onward, including the first 30 minutes of the session (09:15–09:45). This window is characterised by wide spreads, low liquidity, high volatility, and unreliable price discovery on NSE. Signals generated here are structurally noisier than mid-session signals, but no filter exists to exclude them.

*Improvement:* Add a session open filter: block all entries before 09:45 IST. This is a one-line addition to the entry time check already present in `generate_signals`. Measure its impact on trade count, win rate, and average entry slippage before and after.

*Verdict:* Add a 09:15–09:45 open auction filter as variant E in the Sandbox test matrix. Keep it as a direct comparison against variant A (fixed ATR baseline) with everything else identical. This answers cleanly whether skipping the noisy open window improves CAGR. Updated Sandbox plan: 5 exit variants (A/B/C/D/E) × 4 ATR configs = 20 combinations total. Still fast, ~2.5 mins in Sandbox.

---

**12. No intra-trade risk management (breakeven / trailing stop)**

*Limitation:* Once a position is open, the stop and target levels are fixed for the life of the trade. A trade that moves 80% of the way to target and then reverses will close at the full stop loss — there is no mechanism to protect captured profit mid-session. For the 5 profitable stocks in the universe, a meaningful share of winning trades likely give back significant gains before the final exit.

*Improvement:* Test four variants in Sandbox against all four Extreme ATR configs:
- **A — Fixed ATR** (current baseline): static SL + static target as per Extreme configs, no adjustment after entry
- **B — Breakeven-1.5ATR**: move SL to breakeven once price is 1.5 ATR above entry; target unchanged
- **C — Breakeven-2.5ATR**: move SL to breakeven once price is 2.5 ATR above entry; target unchanged
- **D — Trailing SL 1.5ATR**: trailing stop that follows price at 1.5 ATR distance once in profit; no fixed target (EOD exit)

All four variants to be tested against all four Extreme ATR configs in `Framework_V1_Sandbox`. Evaluate impact on: win rate, average loss, expectancy, and trade count. A serves as the control. B and C are pure breakeven triggers with no trailing. D is the only variant with a dynamic stop that continues moving after the initial trigger.

*Verdict:* Just follow the above improvement details and implement the required SL using the four variants as described above.

---

**13. Signal deduplication is silent and unmonitored**

*Limitation:* The deduplication step that removes duplicate signals targeting the same entry datetime keeps only the first occurrence and silently discards the rest. There is no logging of how frequently this fires, which stocks it affects most, or whether the discarded signal was systematically different (e.g., from a later, stronger touch). The extent of information loss is unknown.

*Improvement:* Add a debug log or counter that records the number of signals dropped per stock per run. If deduplication fires frequently on certain stocks, investigate whether the two signals represent independent setups or are artefacts of the lookahead logic. This is a diagnostic step — no change to strategy logic required.

*Verdict:* Add a deduplication counter as Phase 1 — log the count of duplicate signals (same entry datetime) per stock per run. After running on DS3, if duplicates are below 1% of total signals → no further action needed. If frequent → Phase 2: compare default behaviour (keep first occurrence) against quality filter (keep highest volume touch candle) and evaluate PnL/CAGR impact. No code change to strategy logic until Phase 1 data justifies it.

---

## Section 8 — Open Questions

**Why 14:30 as the entry cutoff?**
NSE closes at 15:30 IST. With an entry cutoff at 14:30 and ATR-based wide stops, a trade entered at 14:30 has at most 30 minutes to hit its target before EOD closes it. No rationale is documented for choosing 14:30 specifically over 14:00 or 15:00.

*Resolution — Why 14:30 as entry cutoff:* 14:30 is a reasonable default but untested. Add variant F (entry cutoff extended to 14:45) to the Sandbox test matrix. Compare directly against variant A (14:30 baseline) — same everything else. Let data decide whether the extra 15 minutes of signals improves or hurts CAGR. Updated Sandbox plan: 6 variants (A/B/C/D/E/F) × 4 ATR configs = 24 combinations.

**Why lookahead up to 3 candles?**
The reclaim can be detected 1, 2, or 3 bars after the touch. There is no documented reason for 3 as the upper bound. A 1-bar reclaim (close above MA on the very next candle) would be a stronger, more decisive signal. Allowing 3 bars increases trade count but may introduce weaker setups.

*Resolution — Why lookahead up to 3 candles:* No fixed verdict on the optimal value yet. Lookahead window {1, 2, 3} added to Optuna parameter space as OP-1 (suggest_int(1, 3)). Let Optuna find the optimal value on DS3 data during the optimization phase. No Sandbox variant created for this — too many combinations if added manually. Defer to Optuna. 🎯

**Why a volume multiplier of exactly 1.2?**
The 20% above average threshold for volume has no documented rationale. Most momentum literature uses 1.5x–2x. A lower threshold like 1.2x may be generating marginal volume spikes that do not represent genuine institutional interest.

*Resolution — Why volume multiplier of exactly 1.2:* No fixed verdict. Volume multiplier added to Optuna parameter space as OP-3 (suggest_float(1.0, 3.0)). Let Optuna find the optimal value on DS3 data. No Sandbox variant needed. Defer to Optuna.

**What does "Extreme" mean in the config names?**
The four configs are all labelled "Extreme" without an opposing baseline (e.g., "Conservative" or "Normal"). It is unclear whether these configs were selected from a broader optimisation or hand-picked, and what the eliminated alternatives looked like.

*Resolution — What does "Extreme" mean in config names:* The four configs were named "Extreme" during iterative development as wider-than-typical ATR multiples were tested and found to outperform tighter configs. The naming was not formally documented at the time. No action required on the code. Note for CC context: Extreme-1 through Extreme-4 represent four hand-picked ATR multiplier combinations (stop: 2.5-3.0×, target: 4.0-5.0×) that emerged as the best performers from earlier v1.4.x testing. The full ATR range will be explored systematically via Optuna (OP-4).

**Why is daily MA data computed but never used?**
The `compute_daily_mas` function runs for every stock on every backtest, adding meaningful compute time for 30 stocks. If the trend filter is never going to be activated, this function call could be removed from the runner to reduce backtest time.

*Resolution — Why is daily MA data computed but never used:* Already resolved under Verdict #1. compute_daily_mas() deleted from the runner entirely. Regime filter (JSWSTEEL-based Optuna classification) is the proper replacement and lives in OP-5 — applied post-Sandbox as Step 3 of the master plan. No further action here.

**Why is risk_per_trade fixed at 1% of initial capital and not configurable per stock?**
The current configuration gives the same rupee risk per trade (₹10,000) to every stock in the universe, regardless of price level, liquidity, or historical volatility. A low-priced stock like ASHOKLEY (~₹170) ends up with a very different share quantity and capital exposure than a high-priced stock like HDFCBANK (~₹1,600), yet both risk the same ₹10,000. This is true across all 29 stocks — the flat 1% rule takes no account of individual stock characteristics. Is this intentional, or is it a default left in from earlier development?

*Resolution — Why is risk_per_trade fixed at 1% of initial capital:* Two separate issues addressed. First, compounding: resolved under Verdict #6 — replace initial_capital with current_equity. Second, capital cap vs risk constraint conflict: the ₹33,333 capital ceiling dominates the risk constraint, causing actual losses to vary wildly per stock — hiding weak stocks. Fix introduced as SB-G (Fixed Fractional sizing): remove capital ceiling, let risk constraint alone determine qty with ₹1,00,000 emergency guard. Risk per trade revised to ₹2,000-3,000 range (not ₹10,000) to avoid capital concentration on low-ATR stocks. Compare SB-A (current model) vs SB-G (Fixed Fractional) in Sandbox. Risk % range added to Optuna as OP-6 (suggest_float(0.2, 1.0) as % of portfolio). Updated Sandbox: 7 variants (A/B/C/D/E/F/G) × 4 ATR configs = 28 combinations. Updated Optuna: OP-1 through OP-6.

**Why does max_hold_bars exist?**
The parameter suggests the strategy was at some point intended to handle multi-day or multi-session holding. If all positions are guaranteed to close at EOD, why is this parameter present at all? This raises the question of whether there is a planned multi-day version of the strategy.

*Resolution — Why does max_hold_bars exist:* Already resolved under Verdict #2. Parameter deleted entirely — dead code with no intraday purpose. Not applicable to SB or OP runs.


**Why is ATR computed on 5-minute bars rather than daily bars?**
Using 5-minute ATR for position sizing means the stop distance is extremely small in absolute terms (a few rupees on most stocks). Is this intentional — i.e., was the strategy explicitly designed for tight intraday ATR-based risk? Or is this a carry-over from a different version where daily ATR was intended?

*Resolution — Why is ATR computed on 5-minute bars rather than daily bars:* Already resolved under Verdict #7. 5-min ATR is correct and intentional for both position sizing and exit logic in an intraday strategy. Daily ATR would break the strategy. Not applicable to SB or OP runs.

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