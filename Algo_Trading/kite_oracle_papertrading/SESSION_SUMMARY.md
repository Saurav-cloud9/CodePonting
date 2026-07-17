# Paper Trading Bot — Build Plan (Script 1)

1. **Config** — 30-stock universe (with `TATAMOTORS→TMPV` symbol mapping),
   instrument tokens, SL=2.5×ATR / TGT=4.0×ATR (provisional, revisit on desktop
   with latest sweep results), EOD hour 15:00, risk_per_trade=1%, starting
   capital=10L, compounding on, no portfolio-wide position cap (per-stock
   guard only — max 1 trade per stock at a time).

2. **Startup warm-up** — for each stock, pull `historical_data` (wide window,
   ~10 calendar days), take the last 20 candles, seed rolling MA20/ATR14.

3. **KiteTicker connection** — subscribe all 30 instrument tokens (full mode,
   need OHLC/volume for bar building).

4. **Bar builder** — per-stock, aggregate incoming ticks into the current
   forming 5-min bar by tracking timestamp boundaries; on close, update
   rolling MA20/ATR14, evaluate signal.

5. **Signal + entry** — touch-bar check (same wick-only condition as the
   backtest); before firing, check whether MIS/short is currently allowed for
   that stock (skip signal if restricted — ASM/GSM/trade-to-trade status can
   change over time, so this is checked live, not just once); on touch bar
   close, arm entry for next bar; fill at that bar's first live tick.

6. **Exit monitoring** — per open position, every incoming tick checked
   against SL/target (SL priority, matching backtest) and EOD cutoff; fill at
   live tick price.

7. **Position sizing** — quantity = (1% × current equity) ÷ SL distance,
   recalculated each trade (compounding).

8. **Reconnect handling** — on reconnect, ticks resume from "now" only (gap
   not auto-replayed); pull `historical_data` for the missed window to patch
   the rolling MA20/ATR14 calculation with correct official bars before
   resuming tick-building.

9. **Logging** — basic bar log + trade log CSVs to `data/trades/`, matching
   the backtest's existing trade-output columns for now (schema to expand
   once we see real output).

## Not discussed / gaps to close before building

**Not discussed at all:**
- **#3 KiteTicker connection** — talked about ticks conceptually (format,
  frequency, binary encoding) but never discussed the connection mechanics
  itself: which subscription mode to use (`ltp`/`quote`/`full` — "full mode"
  was written into the plan without an actual decision), or whether Kite's
  per-connection instrument subscription limits are a concern for 30 stocks
  (almost certainly fine, but never verified).
- **#9 Logging** — explicitly parked on purpose, until we see real output.

**Conceptually agreed, implementation detail never nailed down:**
- **#1 Config** — `EOD_HOUR=15` was never actually discussed for the live bot —
  it's carried over from the backtest script's constant, not explicitly
  confirmed to apply the same way live.
- **#4 Bar builder** — the idea (aggregate ticks ourselves, detect boundaries)
  is settled, but not the mechanics: exact boundary-detection algorithm, or
  what happens if a stock gets zero ticks in some 5-min window (illiquid
  moment, no trades at all).
- **#7 Position sizing** — the formula (1% risk ÷ SL distance) is settled, but
  not rounding rules (floor vs. round) or the edge case where risk amount
  doesn't even cover 1 share's SL-distance cost.
- **#8 Reconnect handling** — the strategy (patch gap via `historical_data`) is
  settled, but not the technical detail — which KiteTicker callback actually
  fires on reconnect, and how we determine the exact missed window.

**Fully covered:**
- #2 Warm-up, #5 Signal+entry (including shortability), #6 Exit monitoring.
