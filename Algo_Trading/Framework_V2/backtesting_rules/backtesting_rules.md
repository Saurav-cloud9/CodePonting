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
ZPF > 1.0 but only achieved with N < 500 trades (statistically thin)
```

### No automated pre-filter — removed 2026-09-08 (was 0.85, briefly 0.75)

A numeric pre-triage gate was tried at both 0.85 and 0.75 and removed entirely — during
this project's current exploratory phase (building intuition for the range of ZPF/alpha
outcomes across many untested signal shapes, not yet locking anything for paper trading),
a human eyeball on the raw numbers is enough to judge "not worth locking in" without an
automated rule skipping the full rigor. Compute Table 2/3 (and alpha) for every combo/
variant regardless of its raw-round ZPF — never substitute a `RULED_OUT` placeholder for
an actual computed value, since seeing the genuine number (however weak) is exactly the
data this phase exists to build intuition from. This may be reinstated later once the
project moves from exploration to actually selecting candidates for paper trading, but
should be recalibrated fresh against whatever's locked at that time, not reused from this
entry — the 0.85→0.75 history above already showed a fixed number silently drifts out of
sync with the actual population of variants being tested.

### Screening Tiers — not every variant gets full treatment (added 2026-09-09)

"Compute Table 2/3 for every combo" above means: no *automated* gate silently skips a
variant. It does NOT mean every variant that ever appears in a comparison CSV has
actually been through Table 2/3 — in practice, the full workup is only worth doing for a
variant whose raw round already looks good enough to plausibly survive it. A variant with
a decisively bad raw ZPF gets a lighter pass: it's already a clear no, and no amount of
SL-sweep interior-peak-hunting on precedent (§12 above shows grid extension buys ~0.006
ZPF at best) is going to flip that. Two distinct tiers exist across this project's master
CSVs today — recorded per-row via the `screen_tier` column (§14):

```
FULL_RIGOR   Table 1 (raw 90-combo sweep) → Table 2 (healthy-subset filter, EOD%<=30)
             → Table 3 (SL-sweep at fixed TP, confirming a genuine interior/plateau peak
             — not a grid-edge artifact, per each variant's own sl_sweet_spot.md) → CAPM
             alpha computed AT THE CONFIRMED COMBO. Required before a variant can be
             locked/deployed. Applied to: all 6 currently-locked flagship variants, and
             Liquidity V1/V2 (the 2 that cleared soft-triage — see
             smc/04_liquidity_findings.md).

RAW_SCREEN   Table 1 only (Table 2 may be computed/printed but isn't used to pick a
             combo) → a single CAPM alpha computed at the raw-best-ZPF combo, which is
             often edge-of-grid and explicitly reported as such. Sufficient to rule a
             variant OUT with confidence when the result is decisively bad (CI clear of
             zero) — NOT a sufficient basis to lock/deploy a variant that looks
             promising, since no interior-peak has been confirmed. Applied to: Liquidity
             V0/V3, and flagship 08/09/10 (all four ruled out at this tier).

REFERENCE    Not evaluated via this framework at all — a long-standing fixed comparison
             point that predates it. Applied to: FRESH_FULLDS3_BASELINE only.
```

**Caveat — tiers measure SL/TP-grid rigor only, not filter potential.** A `RAW_SCREEN`
(or even `FULL_RIGOR`) verdict rules out a signal at its best raw SL/TP combo — it says
nothing about that signal + a filter (VWAP/RSI/EMA/daily-bias — historically a much
bigger lever than grid-tuning, e.g. `6BCE+VWAP+RSI>54` jumped ZPF by +0.2-0.25 vs
grid-tuning's ~0.01). Don't read a `RAW_SCREEN` row as permanently dead on that axis —
this applies especially to a variant whose raw ZPF is decent (not one already struggling
to clear ~0.8 after the full 90-combo sweep), which is a more plausible filter candidate.

Known documentation gap: `ma_long_flip/v1_vwap` (locked SL=4.0/TP=3.0, live in
monthly_reconciliation.py) has no `sl_sweet_spot.md` of its own, unlike its 5 sibling
locked variants — its VWAP-direction decision was justified by reuse of
`ma_short/v2_vwap/vwap_decision.md` (a different strategy's 3-combo check), not a
dedicated Table 3 pass. The raw data for this variant, at TP=3.0 fixed, does show a real
plateau (ZPF 0.817-0.821 across SL=4.0-6.0, not still climbing) consistent with a genuine
locked pick — tagged `FULL_RIGOR` on that basis — but the formal write-up should be
backfilled to match its siblings.

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
screen_tier         FULL_RIGOR / RAW_SCREEN / REFERENCE — which of §12's Screening
                     Tiers this row's combo and alpha were computed under. Read this
                     before trusting a row as a candidate: RAW_SCREEN is only strong
                     enough to rule a variant OUT, not to lock it.
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

## 15. NaN-Safe Aggregation — Mandatory (added 2026-09-08)

DS3 has known, real per-stock/per-day data gaps (e.g. ICICIBANK/ITC/SBIN zero-filled
OHLC in 2015, DIVISLAB un-split-adjusted, and INFY — 2015-04-24, only the 09:15 bar is
valid, the remaining 74 bars that day are entirely NaN across OHLCV). A signal can
legitimately form on the last valid bar before a gap, then land its ENTRY on the first
NaN bar of the gap — giving `entry_px = NaN` for that one trade, discovered 2026-09-08
via `6bce_v0`/`6bce_v1vwap` on this exact INFY date.

**The danger is silent, not loud**: a single NaN trade doesn't crash anything — it
silently poisons any aggregate computed with a NaN-propagating operation. Confirmed
which stats are vulnerable and which aren't:
- **Not vulnerable** (skip NaN by construction, already safe): ZPF/PF — computed via
  sign-filtered sums (`pnl[pnl>0].sum()`, `pnl[pnl<0].sum()`; NaN fails both comparisons
  so is naturally excluded). Daily-aggregated Sh(D)/ZSh(D)/alpha/beta — `pandas`
  `.groupby().sum()` defaults to `skipna=True`, silently drops NaN within a group.
- **Vulnerable** (raw numpy `.sum()`/`.mean()` on the full trade array, no sign filter,
  no groupby): `net_zpnl` specifically — a single NaN trade among 100,000+ silently
  makes the whole total `NaN`. Caught this way in `smc/master_nifty.csv` /
  `master_basket.csv` — `net_zpnl` came back blank for exactly the 2 variants that
  happened to touch the INFY gap.

**Rule**: any NEW aggregate stat computed directly over a raw trade-level pnl/zpnl
array (not sign-filtered, not through a pandas groupby) MUST use `np.nansum`/
`np.nanmean` etc., never bare `.sum()`/`.mean()`. Additionally, log the NaN count
whenever computing metrics (`np.isnan(pnl_arr).sum()`) — a nonzero count is real
signal that a new DS3 gap was just hit, not noise to suppress silently.

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
