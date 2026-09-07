# Smart Money Concepts (SMC) — Session Summary

---

## 1. Liquidity

**Definition:** Clusters of resting stop-loss and pending orders sitting just above swing highs or below swing lows. Price is drawn to these zones to trigger those orders, then reverses.

**What we covered:**
- N-bar fractal logic for swing low identification (N=2, 5 candles total)
- Sweep candle mechanics (wick below swing low, close above)
- 3-candle entry sequence: sweep → confirmation → entry
- Why shallow sweeps are stronger than deep ones
- Buy-side vs sell-side liquidity (mirror logic for shorts)

**Entry Logic Locked:**
- Swing low: N=2 fractal (middle candle lowest of 5)
- Distance: sweep within 50 candles of swing low
- Sweep candle: low < swing_low_level AND close > swing_low_level
- Confirmation: next candle close > swing_low_level
- Entry: open of candle after confirmation

---

## 2. Fair Value Gap (FVG)

**Definition:** A 3-candle imbalance zone where C2 moves so fast that C1's high does not overlap C3's low, leaving an untouched price zone that price often returns to fill.

**What we covered:**
- Strict 3 consecutive candle formation (C1 → C2 → C3)
- FVG zone = C1 high (bottom) to C3 low (top)
- C2 has no specific condition — gap is confirmed by C3.low > C1.high
- Rally condition: at least one candle after C3 must have high > C3.high
- Retest candle: wick touches zone top, body stays above
- Penetration depth concept (shallow touch = stronger signal)
- Retest candle can simultaneously satisfy rally condition

**Entry Logic Locked:**
- FVG zone: C3.low > C1.high across 3 consecutive candles
- Rally: at least one candle after C3 with high > C3.high
- Retest: low <= C3.low AND close > C3.low (within 50 candles of C3)
- Confirmation: next candle close > C3.low
- Entry: open of candle after confirmation

---

## 3. Order Block (OB)

**Definition:** The last opposite-direction candle just before a strong impulsive displacement move. That candle's full range (high to low) becomes the OB zone — where institutions placed large orders before driving price away.

**What we covered:**
- 2-candle formation (OB candle + displacement candle)
- OB zone = full range of OB candle (high to low, including wicks)
- Displacement candle must close above OB candle's high
- Rally condition same as FVG — at least one candle above displacement high
- Retest candle: wick touches OB zone top, body stays above
- Penetration depth as a future optimization parameter
- Retest candle can satisfy rally condition simultaneously

**Entry Logic Locked:**
- OB candle: bearish, immediately before bullish displacement
- Displacement: close > OB candle high
- OB zone top = OB candle high, bottom = OB candle low
- Rally: at least one candle after displacement with high > displacement high
- Retest: low <= OB zone top AND close > OB zone top (within 50 candles)
- Confirmation: next candle close > OB zone top
- Entry: open of candle after confirmation

---

## 4. Break of Structure (BOS)

**Definition:** A candle that closes beyond the last higher low (uptrend) or lower high (downtrend), confirming the current trend structure has broken and a new direction is forming.

**What we covered:**
- Uptrend = higher highs + higher lows
- BOS = one candle closes below the last higher low → trend flipped
- Used as a REGIME FILTER, not a standalone entry signal
- Only take long setups when uptrend structure is intact (no BOS to downside)
- Simple to code: find last local low, check if current candle closes below it

**Entry Logic:** Not a standalone entry — used as G1 regime gate for fv2.

---

## 5. Inducement

**Definition:** A small deliberate liquidity grab just before the real move, designed to trap early entries before smart money commits to the direction.

**What we covered:**
- Conceptual explanation — fake move before real move
- Helps avoid premature entries and SL hits from early long entries
- Indirectly reduces some EOD minus hits by improving entry timing
- Hardest of the 5 to define precisely in code
- Entry logic NOT yet finalized — pending future session

---

## Key Principles Discussed

- These 5 concepts are FILTERS layered on top of MA20 bounce, not standalone strategies
- Build filters INTO entry signal generation upfront — not applied to backtest results after the fact
- Liquidity, FVG, OB = WHERE to trade (zone-based)
- BOS = WHEN conditions are right (regime-based)
- Inducement = timing filter to avoid traps
- Triple confluence (liquidity + FVG + OB in same zone) = highest quality signal
- Penetration depth is a future optimization parameter for both FVG and OB
- All three long setups have mirror short versions (flip direction)

---

## Backtesting Status

| Concept    | Entry Logic | Backtest Status     |
|------------|-------------|---------------------|
| Liquidity  | Locked      | Sent to backtest    |
| FVG        | Locked      | Sent to backtest    |
| OB         | Locked      | Sent to backtest    |
| BOS        | Conceptual  | Not yet             |
| Inducement | Conceptual  | Not yet             |

**⚠️ TODO — revisit:** Liquidity/FVG/OB backtests were run on a bookmarked claude.ai
session (Saurav has the link), not in this repo — no entry code or results exist here
yet. Before building further on SMC, check that session for the actual backtest
results and code, then carry them forward into this folder.
