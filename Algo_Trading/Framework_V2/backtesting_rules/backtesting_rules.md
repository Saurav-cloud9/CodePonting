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

> ⚠️ **Only ENTRY_CUTOFF_TIME is universal — the signal-time cutoff is strategy-specific**
> (clarified 2026-09-07, sharpened same day). `ENTRY_CUTOFF_TIME = 14:50` is a property
> of the ENTRY bar alone — how much runway a freshly-opened position needs before the
> 15:00 hard EOD — and that reasoning doesn't depend on how many bars led up to it, so
> **this stays 14:50 for every strategy, always.**
>
> What changes per strategy is the signal-time cutoff (`LAST_TOUCH_TIME` for the
> flagship, or whatever the analogous "last signal bar" concept is called elsewhere),
> derived BACKWARD from the fixed entry cutoff:
> ```
> signal_cutoff = ENTRY_CUTOFF_TIME - (bars_from_signal_to_entry × 5min)
> ```
> Flagship family (ma_short/6bce/ma_long_flip): signal → entry is 1 bar apart →
> `14:50 - 5min = 14:45`, exactly the locked `LAST_TOUCH_TIME` below. A structurally
> different strategy (e.g. Liquidity: sweep → confirmation → entry, 2 bars apart) needs
> its OWN signal cutoff from the same formula — e.g. `14:50 - 10min = 14:40` for the
> sweep candle — never 14:45 reused verbatim, since that would leave the wrong amount of
> runway for a chain of a different length. Sections 3-5, 7, 8, and 12 below (SL/TP
> sizing, exit logic, position guard, charges, metrics, viability) are fully universal/
> project-wide and apply to any strategy unchanged — only this section's specific times
> are flagship-calibrated.

- Entry signal bar must have `hour < 15`
- Entry is always at the **open of the next bar** (i+1), same trading day as the signal bar
- If `hour[i+1] >= 15` or date changes → signal is skipped entirely

### Touch / Entry cutoff (flagship MA-bounce family only — see warning above; matches
### live bot, `ma_rejection_v1_core.py`)

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

**Exit-mix / touch-hour breakdown (mandatory, added 2026-09-04):**
- For any combo being seriously considered (not every one of the 90 — at minimum
  the best-by-ZPF combo, and any combo proposed for live/paper deployment),
  bucket trades by touch-bar hour (09-10, 10-11, ..., 14-15) and report per
  bucket: N, EOD%, SL%, TP%, PF, ZPF, Net ZPnL.
- Why: raw overall ZPF alone can hide a combo that only "works" by riding most
  trades to EOD close (SL/TP too wide to bind intraday, changing the exit-type
  mix rather than reflecting genuine directional edge) — found 2026-09-04 when
  every family's raw-ZPF-ranked #1 combo landed at the edge of the swept SL/TP
  grid. A combo whose top-line ZPF looks fine but whose per-hour breakdown
  shows EOD% climbing sharply late in the day (e.g. >60-70% in the 14-15
  bucket) is suspect even if its blended number looks acceptable.
- This diagnostic does not replace the SL/TP health check in §11/§12 — it
  supplements ZPF-based ranking with a second, orthogonal lens (when in the
  day the edge actually shows up, not just whether it exists in aggregate).
- Any newly proposed time-of-day-restricted variant (e.g. trading only the
  best-looking hour window) must be validated out-of-sample (derive the
  window on one time split, confirm it holds on a held-out split) before
  being treated as a real candidate — picking the best-looking window from
  the same data used to evaluate it is the same selection-bias trap as
  cherry-picking a single significant variant from a multi-variant sweep.

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

## 14. Standard Cross-Strategy Comparison Row Format

*Added 2026-09-07. Distinct from §9's format — §9 is exhaustive detail for evaluating*
*ONE strategy's own 90-combo sweep; this is a compact ONE-ROW summary per strategy,*
*for comparing MULTIPLE strategies side by side (e.g. across all 5 SMC concepts as*
*each gets tested). Column set matches `monthly_reconciliation.py`'s report output*
*on the live bot VM exactly — reuse that shape, don't invent a new one per strategy.*

```
source              strategy/variant name (e.g. "LIQUIDITY_V0")
sl_tp               locked SL/TP combo, "x"-separated (e.g. "4.5x3.0") — never "/"
                     (a "/"-joined number pair is exactly what Excel/Sheets
                     auto-reinterprets as a date on open)
n_trades            total trade count
pf                  raw profit factor (pre-charge)
sh_d                raw daily Sharpe, annualised (pre-charge)
zpf                 Zerodha profit factor (post-charge) — primary viability metric
zsh_d               Zerodha daily Sharpe, annualised (post-charge)
net_zpnl            total net zpnl, ₹
sl_pct / tp_pct     % of trades exiting via SL / TP
eod_plus_pct        % of trades exiting via EOD, profitable
eod_minus_pct       % of trades exiting via EOD, unprofitable
eod_pct             eod_plus_pct + eod_minus_pct combined (mandatory exit-mix check, §9)
alpha_capm          CAPM alpha, ₹/day — raw daily zpnl regressed against a market
                     factor's daily % return (NEVER normalize by pcap — see CLAUDE.md's
                     PCAP/TCAP section). n in this regression = trading DAYS, not
                     n_trades (see TODO.md's GLOSSARY) — e.g. thousands of trades can
                     roll up into a much smaller n_days for an 11-year DS3 backtest.
p_alpha_capm        two-tailed p-value on alpha (H0: alpha=0)
alpha_capm_cumulative  alpha × n_days — exact by OLS construction (residuals sum to
                     exactly zero), the true total ₹ attributable to skill over the
                     period
ci_low_capm / ci_high_capm  95% confidence interval on alpha (alpha ± t_critical×SE).
                     Read alongside p_alpha_capm, not instead of it — distinguishes
                     "confidently near-zero" (narrow CI hugging zero) from
                     "inconclusive" (wide CI that happens to cross zero) from
                     "confidently not-zero" (CI entirely clear of zero) — same
                     p<0.05 threshold, very different practical read (added 2026-09-06
                     after this exact ambiguity mattered for a real result)
beta_capm           CAPM beta — the strategy's ₹/day sensitivity to the market
                     factor's 1% move (NOT a normalized/dimensionless stock-style beta)
se_alpha_capm       standard error of alpha — feeds both p_alpha_capm and the CI
t_alpha_capm        alpha / se_alpha_capm
```

3-decimal fixed-width string formatting on `zpf` and every `*_capm` column
(`round()` alone drops trailing zeros — format as `f'{x:.3f}'` explicitly).

Run against BOTH NIFTY50 and the 30-stock equal-weighted basket as separate market
factors (two output files) — cross-validates that a finding isn't a market-factor
artifact, not two independent claims. For SMC/new-strategy backtests, log results into
`strategies/smc/basket.csv` and `strategies/smc/nifty.csv` (no numeric index — these
are running comparison logs referenced every time a new concept is tested, not a
single strategy's own numbered pipeline output).

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
