# Backtesting Rules — Framework V2

Reference file for consistent backtesting across Claude.ai and Claude Code sessions.
Attach this to any Claude.ai backtesting project to ensure rules match the CC-side runs.

---

## EOD Exit Logic

**EOD_HOUR = 15** (3:00 PM IST — no new entries or exits at or after this hour)

### Exit priority (in order, checked each bar):

1. **Date change** — if the current bar's date differs from the trade entry date:
   - Exit at the **previous bar's close** (not next bar's open — avoids overnight bleed)
   - Outcome: `EOD+` if profitable, `EOD-` if loss

2. **Hour >= 15** — if the current bar's hour is 15 or later:
   - Exit at the **current bar's open**
   - Outcome: `EOD+` if profitable, `EOD-` if loss

3. **SL hit** — checked **before** TGT (conservative: same-bar ambiguity resolved to loss)
   - SHORT: `k_bar['high'] >= sl` → pnl = entry - sl, outcome = `L`
   - LONG:  `k_bar['low']  <= sl` → pnl = sl - entry, outcome = `L`

4. **TGT hit** — only checked if SL not hit on same bar
   - SHORT: `k_bar['low']  <= tgt` → pnl = entry - tgt, outcome = `W`
   - LONG:  `k_bar['high'] >= tgt` → pnl = tgt - entry, outcome = `W`

### Entry filter:
- No entries at or after EOD_HOUR on the touch bar
- Entry is always on the **next bar's open** (i+1), same day as touch

### No new signals during open trade:
- Scanner resumes from `k+1` after each trade closes — no overlap

---

## ATR14 — Stop Loss / Target Calculation

ATR14 = 14-period Average True Range. Used to size SL and TGT dynamically per bar.

```
TR  = max(high - low, abs(high - prev_close), abs(low - prev_close))
ATR = rolling 14-period mean of TR
sl  = entry ± SL_MULT  × ATR14   (+ for SHORT, − for LONG)
tgt = entry ∓ TGT_MULT × ATR14   (− for SHORT, + for LONG)
```

---

## NPF — Neo Profit Factor (Kotak Neo, Intraday, Qty=1)

NPF = real-world profit factor after full Kotak Neo intraday statutory charges.
Use this to validate whether a backtest PF survives real costs before paper/live.

### Per-trade cost formula (at ~900 INR avg price ≈ ₹1.38 total per trade):

```
brok  = (entry + exit) × 0.0005      # 0.05%/side brokerage
stt   = exit  × 0.00025              # STT on sell side only
txn   = (entry + exit) × 0.0000297   # transaction charges on turnover
sebi  = (entry + exit) × 0.000001    # SEBI fee on turnover
stamp = entry × 0.00003              # stamp duty on buy side only
gst   = 0.18 × (brok + txn)         # GST on brokerage + transaction
total = brok + stt + txn + sebi + stamp + gst
```

### PF hierarchy:

| Metric | What it measures |
|---|---|
| PF  | Raw profit factor — zero charges (Python backtest output) |
| TPF | TradingView PF — brokerage only (0.05%/side), understates real cost |
| NPF | Neo Profit Factor — full Kotak Neo charges including all statutory |

### Target:
- Compute NPF precisely per iteration using the formula above
- Minimum viable: **NPF > 1.0** after all charges

