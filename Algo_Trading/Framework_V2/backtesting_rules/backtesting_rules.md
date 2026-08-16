# Backtesting Rules — Framework V2
*Reference file for consistent backtesting across all AI agents (Claude, Grok, CC) and environments.*

---

## 1. Data & Environment

- **Bars:** 5-minute OHLCV
- **Session:** 09:15 to 15:00 IST
- **EOD hour:** 15 (no new entries or exits at or after this hour)
- **Indicators pre-computed in parquet:** ma20 (20-period SMA of close), atr14 (14-period rolling mean of TR)
- **ATR14 formula:**
```
TR  = max(high - low, abs(high - prev_close), abs(low - prev_close))
ATR = rolling 14-period mean of TR
```

---

## 2. Entry Rules

- Entry signal bar must have `hour < 15`
- Entry is always at the **open of the next bar** (i+1), same trading day as the signal bar
- If `hour[i+1] >= 15` or date changes → signal is skipped entirely

### Touch / Entry cutoff (matches live bot, `ma_rejection_v1_core.py`)

- **LAST_TOUCH_TIME = 14:45** — the touch/signal bar's time must be `<= 14:45`. A touch
  registering at 14:50 or later is not recognized at all, since the resulting entry
  would fire with too little runway before the 15:00 hard EOD square-off. This is
  stricter than the plain `hour < 15` check above, which treats all of 14:00–14:55 as
  equally "not yet EOD" — 14:45 closes that gap.
- **ENTRY_CUTOFF_TIME = 14:50** — the entry bar (i+1, or the rejection-bar+1 for
  multi-bar rejection signals) must have time `<= 14:50`, else the signal is cancelled
  outright — no trade logged, no charges applied (distinct from the EOD_HOUR>=15 exit
  branch, which still logs a wash trade). Normally unreachable given the 14:45 touch
  cap (the very next bar is always 14:50), but guards multi-bar rejection windows
  (`MAX_TR_GAP`/`MAX_TB_GAP`) where the entry bar can land later than the touch bar.

---

## 3. SL / TP Sizing

SL and TP are ATR-based and computed at the entry bar:
```
SHORT:
  sl  = entry + SL_MULT  × ATR14
  tp = entry - TP_MULT × ATR14

LONG:
  sl  = entry - SL_MULT  × ATR14
  tp = entry + TP_MULT × ATR14
```

---

## 4. Exit Logic

Checked in strict priority order on each bar after entry:

| Priority | Condition | Exit Price | Outcome |
|---|---|---|---|
| 1 | Date change (next bar is a new day) | Previous bar's close `C[k-1]` | EOD+ / EOD- |
| 2 | `hour[k] >= 15` | Current bar's open `O[k]` | EOD+ / EOD- |
| 3 | SL hit — SHORT: `high[k] >= sl` / LONG: `low[k] <= sl` | SL price | L |
| 4 | TP hit — SHORT: `low[k] <= tp` / LONG: `high[k] >= tp` | TP price | W |

**SL is always checked before TP on the same bar.**
No overnight carry. Same-day exits only enforced via date change check.

---

## 5. Position Guard (Single-Pass)

- Only one trade open at a time per stock
- Scanner resumes from the bar after the trade closes — no overlap
- Candidates are collected in a single forward pass
- Per-combo position guard applied during the 90-combo sweep

---

## 6. Parameter Sweep Grid (90 combos)

```
SL_MULT  : 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0  (10 values, step 0.5)
TP_MULT : 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0        (9 values,  step 0.5)
Total    : 90 combinations
```

Run across all 30 stocks and aggregate results before selecting the best combo.

---

## 7. Charge Formula — Zerodha (ZPF / ZSh)

Applied per trade (qty = 1 share, intraday SHORT):

```python
brok  = min(0.0003 × entry, 20) + min(0.0003 × exit, 20)   # ₹20 cap per side
stt   = entry × 0.00025                                       # STT on sell (entry) side
txn   = (entry + exit) × 0.0000307                           # exchange transaction charges
sebi  = (entry + exit) × 0.000001                            # SEBI fee
stamp = exit  × 0.000003                                      # stamp duty on buy (exit) side
gst   = 0.18 × (brok + txn + sebi)                          # GST on brokerage + txn + sebi
total = brok + stt + txn + sebi + stamp + gst
```

> Note: For SHORT entry = sell, exit = buy. STT applies on the sell side (entry). Stamp duty on buy side (exit).
> For LONG trades, flip the legs: `stt = exit × 0.00025` (sell side) and `stamp = entry × 0.000003` (buy side).

---

## 8. Primary Metrics

### ZPF — Zerodha Profit Factor
```
ZPF = sum(winning zpnl) / abs(sum(losing zpnl))
where zpnl = raw_pnl - zerodha_charge_per_trade

Target: ZPF > 1.0
```

### ZSh(D) — Zerodha Daily Sharpe (annualised)
```
daily_zpnl[date] = sum of all trade zpnl on that date (across all stocks)
ZSh(D) = (mean(daily_zpnl) / std(daily_zpnl)) × √252

Target: ZSh(D) > 0
```

### Raw PF (pre-charge)
```
PF = sum(winning pnl) / abs(sum(losing pnl))
Used as a reference — does not determine viability
```

### Raw Sh(D) (pre-charge)
```
Sh(D) = (mean(daily_pnl) / std(daily_pnl)) × √252
Used as a reference alongside ZSh(D)
```

---

## 9. Required Output Format

Every backtest result must include:

**Overall (all stocks, all years combined):**
- N trades, N trading days
- PF, ZPF
- Sh(D), ZSh(D)
- % profitable days (after charges)

**Year-wise (2015 to 2025):**
- Same metrics per year
- Flag each year: ✅ ZPF≥1.0 / 🟡 ZPF 0.90–0.99 / ❌ ZPF<0.90

**90-combo sweep table:**
- All 90 SL/TP combos with N, PF, ZPF, Sh(D), ZSh(D)
- Highlight best ZPF and best ZSh(D) combo

---

## 10. Iteration Methodology

```
Step 1: Run baseline strategy → 90-combo sweep → identify best SL/TP by ZPF
Step 2: Add filter or structural modification → re-run 90-combo sweep
Step 3: Compare ZPF and ZSh(D) vs baseline → accept if improvement is meaningful
Step 4: Further refine (e.g. secondary filter sweep at locked SL/TP)
Step 5: Repeat until ZPF > 1.0 AND ZSh(D) > 0, or rule out the strategy
```

Filters tested so far (for reference):
- VWAP (intraday, resets daily)
- RSI threshold sweep (Wilder 14-period, threshold 50→80 step 2)
- EMA100 (continuous, 5-min bars)
- Daily bias (close vs previous day close)
- Pierce depth (for FVG-type strategies)

---

## 11. Combo Selection — Consistency Score (preferred over raw ZPF)

Rather than selecting the combo with best overall ZPF, prefer the combo that is most **consistent across all 11 years**:

```
Consistency Score = mean(yearly ZSh) - λ × std(yearly ZSh)
where λ = 1.0 (equal weight on mean and variance penalty)
```

This rewards combos with stable year-on-year performance and penalises those carried by a few exceptional years.

---

## 12. Viability Criteria

A strategy is considered viable for paper trading when:
```
ZPF  > 1.0   (after Zerodha charges, across all years combined)
ZSh(D) > 0   (positive daily Sharpe after charges)
Both must be met simultaneously
```

A strategy is ruled out when:
```
Best ZPF across all 90 combos < 0.85  (no meaningful edge)
OR  ZPF > 1.0 but only achieved with N < 500 trades (statistically thin)
```

---

## 13. Position Guard — Implementation Standard

- Use inline single-pass per combo (no candidate pre-storage)
- Position guard: i = k + 1 (resume from exit bar + 1)
- Exit loop starts at entry bar (k = ei, not ei + 1)

---

## ARCHIVED — Kotak Neo Charges (NPF)

*Kept for reference. Not currently in use — broker is Zerodha.*

```python
brok  = (entry + exit) × 0.0005
stt   = exit  × 0.00025
txn   = (entry + exit) × 0.0000297
sebi  = (entry + exit) × 0.000001
stamp = entry × 0.00003
gst   = 0.18 × (brok + txn)
total = brok + stt + txn + sebi + stamp + gst

NPF = sum(winning npnl) / abs(sum(losing npnl))
Minimum viable: NPF > 1.0
```
