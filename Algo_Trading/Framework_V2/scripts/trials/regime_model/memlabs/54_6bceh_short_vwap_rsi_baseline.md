# Step 54 — Regime filter for 6BCEH-Short + VWAP + RSI (target = the variant's own trade outcomes)

> New series. Distinct from #53 (which stays FROZEN at its Step-0 state — its raw-price-
> prediction target doesn't serve the priority). #54 borrows #53's *methodology* (Pearson
> screening + null-intuition / 5k-t-stat noise ruler) but points it at the right target:
> **a strategy's own per-trade win/loss (or PnL) outcomes**, to build a regime filter that
> lifts a breakeven signal into positive alpha. First subject: `FLAGSHIP_6BCEH_SHORT_VWAP_RSI60`.
> The whole experiment lives in this `54_*` series (flat files, letter-suffixed sub-iterations
> like #50b/#52b) — no subfolder.

---

## 1. The variant — full picture (consolidated here as #54's starting reference)

**Identity:** `FLAGSHIP_6BCEH_SHORT_VWAP_RSI60`
**Script:** `strategies/flagship/11_6bceh_short_vwap_rsi.py`
**Logged in:** all 4 master CSVs — `strategies/smc/master_{nifty,basket}.csv` and
`strategies/flagship/master_{nifty,basket}.csv` — `screen_tier = RAW_SCREEN`.

### Signal + filters (entry logic)
```
Base signal : close[i] == max(close[i-5 .. i])         # fresh 6-bar closing HIGH (6BCEH)
Direction   : SHORT   (fade the high — reversal, not continuation)
Filter 1    : close[i] < VWAP[i]                        # strict; ties excluded. VWAP resets daily.
Filter 2    : RSI(14, Wilder) on close, at bar i, > 60  # continuous series, no daily reset
Entry       : SHORT at open[i+1], same day
Cutoff      : LAST_TOUCH_TIME = 14:45, ENTRY_CUTOFF_TIME = 14:50 (live-matching, backtesting_rules.md)
Exit prio   : date change -> hour >= 15 -> SL -> TP
Charges     : Zerodha SHORT (entry = sell leg, exit = buy leg)
NaN guard   : skip any trade whose entry bar open is NaN (0 dropped here)
```

### Provenance
The recovered claude.ai session (`strategies/smc/03_backtest_results.md` §3) flagged
"6BCE+VWAP+RSI>54" as the only strategy there that ever crossed ZPF>1.0 with a real trade
count — but **only on an 8-stock curated universe (ZPF 1.1232)**; the full 30-stock universe
there reached just **0.9975**. That result also predated this project's NaN-guard / cutoff-
formula / charge-formula fixes and used a narrower/coarser SL/TP grid. `11_...py` reproduces
it properly: full 30-stock DS3, this project's 10x9 grid, correct charges/cutoffs/guard.

### Two-step build (2026-09-10)
- **Step A** — RSI-threshold sweep (50-80 step 2) at the locked VWAP-only combo SL=4.5/TP=3.0.
  Best on our data/infra is **RSI>60** (ZPF 0.872), *not* RSI>54 (which gives 0.816).
- **Step B** — full 90-combo SL/TP re-sweep at RSI>60:
  - Raw-best ZPF **0.927** at SL=4.5 / TP=6.0 — but edge-of-grid AND EOD% = 66.2 (**suspect**).
  - Healthy-subset best (EOD% <= 30) ZPF **0.899** at SL=1.5 / TP≈4.5-5.0 — but SL sat at the
    grid floor.
- **Table 3 (`54b`, 2026-09-10)** — SL-sweep [1.0 … 4.0] × fixed TP {3.0, 4.5, 5.0}, tracking
  ZPF + net_zpnl + basket alpha + EOD% together. **SL=1.5 confirmed as a genuine interior
  peak**: tighter (1.25, 1.0) degrades net_zpnl, alpha *and* ZPF across every TP. net_zpnl and
  basket alpha both peak at SL=1.5. ZPF's nominal max is SL=2.0 (0.902 vs 0.899 — a rounding-
  error gap) but that combo fails the EOD gate (33.8%). **Locked combo: SL=1.5 / TP=4.5**
  (best net_zpnl of the whole grid, EOD% 26.7 healthy, the SL<TP "cut-losers" geometry). Row
  re-tagged `FULL_RIGOR` in all 4 master CSVs.

### CAPM — locked `FULL_RIGOR` combo SL=1.5 / TP=4.5, n_trades = 14,270

| | NIFTY-regressed | Basket-regressed (primary) |
|---|---|---|
| alpha (₹/day) | **-0.461** | **-0.674** |
| 95% CI | [-1.089, +0.167] | [-1.314, -0.035] |
| p-value | 0.150 | 0.039 |
| beta | -4.988 | -1.843 |
| net_zpnl (₹) | -2,436.26 | -2,436.26 |
| alpha_cumulative (₹) | -1,177 | -1,723 |
| ZPF / ZSh(D) | 0.899 / -0.904 | (same) |

**Verdict: borderline.** The two benchmarks straddle the significance line — basket p=0.039
(CI just clears zero, "barely significant-negative"), NIFTY p=0.150 (CI crosses zero, "not
significant"). Per §14 that disagreement makes this a *borderline* read, not a clean one: α is
small and negative-ish, and whether it's genuinely sub-zero or just at zero can't be pinned
down. **Still by far the mildest alpha of any variant tested** (every other row: -6 to -33).

Note the earlier RAW_SCREEN combo (4.5×6.0) showed a cleaner near-zero (NIFTY +0.031, basket
-0.397, both CIs crossing zero) — but that was partly an artifact of its EOD%=66 (trades
riding to close dampen daily variance and shrink |α|). The healthy combo is the honest test.

**Benchmark to lead on for #54: basket** (it *is* the traded universe, equal-weighted to
match the strategy's own sizing); NIFTY stays as the §14 cross-check. (Betas aren't comparable
across the two regressions — the basket is more volatile, bigger denominator.)

---

## 2. Loss decomposition — alpha vs beta drag (at the locked combo)

The CAPM identity, summed over all `n` trading days (OLS residuals sum to exactly zero):
```
net_zpnl = alpha_cumulative + beta × Σ(daily market returns)
```

At the locked `FULL_RIGOR` combo (SL=1.5/TP=4.5), the split depends on the benchmark:

| | alpha_cumulative | beta × Σx | net_zpnl | alpha's share |
|---|---|---|---|---|
| NIFTY  | -1,177 | -4.988 × 252.5 ≈ -1,259 | -2,436 | ~48% |
| **Basket** (primary) | -1,723 | -1.843 × 387 ≈ -713 | -2,436 | **~71%** |

So — **NOT "the loss is entirely beta drag"** (that read came from the RAW_SCREEN edge-of-grid
combo, where alpha happened to sit at ≈ 0 because EOD-riding dampened the daily variance). At
the honest combo:
- **Under basket (the primary benchmark), negative alpha is the *larger* driver (~71%)** — the
  signal does carry a genuine, if mild and borderline, skill deficit.
- Beta drag is real but secondary here (~29% under basket, ~52% under NIFTY).
- `Σx` (the cumulative market drift, sum of ~2,700 daily % returns, ≈ 0.09%/day) is what
  accumulates on the beta side; `beta` itself is a plain slope, not cumulative. Per *typical*
  day the beta term contributes only a rupee or two — it's the multi-year accumulation that
  builds it.

**Implication for #54:** unlike the decisively-negative variants (alpha -6 to -33, mispredict
direction, lose in any regime), this one's alpha is *marginal* — small and borderline. But the
RAW_SCREEN "already breakeven, just fix beta" picture was too rosy. The regime filter has to
close a genuine (if small) negative-alpha gap of ~-0.67/day under basket, **plus** trim the
secondary beta-drag component. Still the best starting line of anything tested; just not a
free ride. Two levers, addressed separately:
- **alpha** → optimize the signal (entries / filters / exits). Decided every trade. This is
  where a regime filter can *add* skill by concentrating trades into conditions where the
  signal works.
- **beta drag** → structural, not a signal problem. A regime filter helps here too — not by
  changing the beta coefficient, but by keeping the strategy *flat* during strong uptrends so
  the summed `beta × market_return` over its trading days shrinks (or flips positive if it
  trades weak-market regimes). Alternative: a matched long hedge leg / short NIFTY futures
  (**parked**, TODO F13 — drags in the long leg's own negative alpha on this universe, not the
  first move).

A regime filter changes the trade stream, so **both alpha and beta get re-measured** after
adding it — nothing is locked.

---

## 3. #54 series roadmap

```
54  (this file)  variant baseline — signal, filters, sweep results, CAPM, loss decomposition
54b   [DONE]     Table 3 SL-sweep — locked SL=1.5/TP=4.5, re-tagged FULL_RIGOR in all 4 master
                 CSVs. SL=1.5 confirmed a genuine interior peak. Alpha at the honest combo
                 (post 2026-09-12 basket-sort fix, §16): basket -0.408 (p=0.201), NIFTY
                 -0.461 (p=0.150) — BOTH agree, confidently near-zero (the earlier
                 "borderline, benchmarks straddle the line" read was itself the sort-bug
                 artifact, corrected 2026-09-12). Script: 54b_table3_sl_sweep.py; results:
                 54b_table3_sl_sweep_results.csv.
54c.1 [DONE]     54c_build_trade_log.py — full per-trade log at the locked combo, 14,270
                 trades, signal-bar datetime + symbol + win/loss(zpnl>0) flag. Net_zpnl
                 verified exact match to the master CSV row (-2,436.26).
54c.2 [DONE]     54c_regime_features.py — 10 candidate market-wide features (NIFTY/basket
                 trend 5d/10d, dispersion, breadth, realized vol 10d, dist-from-MA50,
                 gap_pct, day-of-week, time-of-day-bucket, basket 5-min intraday pseudo-
                 index) built as-of prior-day-close (no lookahead) and joined onto the trade
                 log. Outputs: 54c_daily_regime_features.csv (2,869-day reference table),
                 54c_trade_log_with_features.csv (14,270-trade joined table). Re-run clean
                 2026-09-12 after the §16 basket-sort fix (this script is literally what
                 surfaced that bug). No India VIX in the data dir — noted gap, not filled.
                 Chosen starting pair for screening (deliberately 2 different KINDS of
                 signal, not near-duplicates): NIFTY trend (10-day) + basket dispersion.
54c.3 [DONE, notebook needs a correction pass — see "RESUME HERE" below]
                 54c_screen.ipynb — combines null-calibration + the real screen.
                 Built + run 2026-09-15: NIFTY trend 10d = null everywhere (r=0.032,
                 fails every ceiling; also dead on weak-form-efficiency theory — it's a
                 directional/first-moment feature). Dispersion vs daily_zpnl = the one
                 real-but-weak signal (r=0.0565) — but see the OOS result below, which
                 supersedes the notebook's current (too-optimistic) verdict text.
                 2026-09-16 additions (peer-verified + independently reproduced, NOT
                 yet written into the notebook):
                   - iid shuffle null was too lenient (dispersion acf1=0.417, a
                     persistent feature spuriously correlates more easily with an
                     iid-shuffled target). Circular-shift null (preserves the target's
                     own structure, only breaks alignment): dispersion clears 95th, NOT
                     99th, empirical p~0.02 (not 0.006). Still borderline-real, honestly
                     weaker. Circular-shift should become the PRIMARY null (§2), with
                     iid kept as the looser secondary comparison, not the reverse.
                   - `54c_10feature_screen.py` (new): max-of-2 (§3's current scope) was
                     under-sized — never confirmed only 2 of the 10 built candidates
                     were actually "looked at." Ran the full 10-feature r comparison:
                     gap_pct (r=-0.0625) is marginally the single STRONGEST of all 10 —
                     bigger than dispersion (0.0573), previously unscreened. Under an
                     iid max-of-10 null (ceil95=0.0555, ceil99=0.0676), both gap_pct and
                     dispersion individually still clear 95th, neither clears 99th — the
                     under-correction concern did NOT end up flipping the verdict, but
                     this hasn't been combined with the circular-shift fix yet (stacking
                     both corrections would be stricter still, and hasn't been run).
                   - `54c_oos_dispersion_gate.py` (new): out-of-sample test of the
                     lagged-dispersion Q5 threshold gate (Fable's "first ZPF>1.0 slice"
                     finding), chronological 70/30 split (train 2015-02-04—2023-04-11,
                     test 2023-04-12—2026-08-31), cutoff chosen on TRAIN only. RESULT:
                     FAILS. Own-period quintile tables show TRAIN's actual best bucket is
                     Q4 (ZPF 1.157), not Q5 (0.994, flat) — the "Q5 is special" story was
                     partly cutoff-specific even in-sample. TEST period: every single
                     quintile is under 1.0, and Q5 (highest dispersion) is one of the
                     WORST buckets (0.813), not the best — a full reversal. VERDICT: the
                     dispersion threshold-gate does not hold up out of sample. Ruled out.

                 [ALL DONE, 2026-09-17]:
                   1. 54c_screen.ipynb corrected in place: circular-shift now primary/
                      plotted in §2/§3 (iid kept as numeric comparison only, per
                      Saurav's "one-time exception, additive only" call for this
                      notebook specifically — the leaner circular-only convention
                      starts with 54d instead); §3c widened to max-of-N (dynamic, not
                      hardcoded — currently 12); §6 verdict rewritten to the final
                      read: dispersion clears the pair-only circular-shift 95th but
                      NOT max-of-12 circular-shift — fails the single most rigorous
                      test available. RULED OUT, confirmed independently of the OOS
                      gate failure (belt and suspenders — both point the same way).
                   2. 54c.4 (interaction/XOR check, trend x dispersion) — built as new
                      §7 in 54c_screen.ipynb, both iid and circular-shift (one-time
                      exception). Combined AND-rule doesn't clear either ceiling and
                      doesn't beat dispersion alone — confirms the escalation rule
                      working as designed, no rescue found.
                   3. volume_surge built (54c_add_volume_vix.py) — today's daily
                      volume ÷ that stock's own trailing 20-day average, basket-
                      averaged, shifted 1 day. india_vix_level also built in the same
                      pass (india_vix_level not originally planned, added since the
                      data already existed via codeponting-2d's earlier fetch and has
                      strong a priori grounding — implied-vol "fear gauge"). Found+
                      fixed a real INDIA_VIX.parquet bug along the way: 3 duplicate-
                      dated rows (2015-06-29/07-02/08-10, two intraday snapshots each
                      instead of one clean daily close) silently multiplied output
                      rows on first merge — caught, fixed via last-timestamp-of-day
                      dedup (matches DS3's own close_wide convention), verified back
                      to exact original row counts (14,270 trades / 2,869 days).
                   4. gap_pct, india_vix_level, volume_surge all individually screened
                      in 54d_screen_round2.ipynb (new notebook, leaner convention —
                      circular-shift only, no iid duplication). Individual circular-
                      shift result: volume_surge is the STRONGEST individual showing
                      of any candidate all session (clears both 95th AND 99th on both
                      targets — dispersion never cleared 99th). But under the max-of-12
                      widened check, all three fail — same fate as dispersion. 0 of 6
                      (feature, target) pairs survive both checks. No OOS gate test
                      run for any (not warranted — none cleared the full screen).
                 RESULT: all 12 built candidate features now screened (some via the
                 full individual+theory+OOS pipeline, all via the max-of-12 combined
                 check). None survive. #54's regime-filter search for THIS variant
                 (FLAGSHIP_6BCEH_SHORT_VWAP_RSI60) is exhausted on market-wide daily
                 features as currently constructed — no viable gate found.
Entry-logic build (future, not yet numbered — reached only if a future candidate
                 survives)
                 Fold a winning regime condition into the entry logic as a new
                 strategies/flagship/ script (next index), re-run the full 90-combo
                 sweep, re-measure alpha/beta on the filtered trade stream. Not
                 reached — no candidate has survived the full screen yet.
Success test   : does the regime filter move basket alpha from -0.41 (confidently near-
                 zero) to clearly positive, CI clear of zero on the positive side, AND
                 ZPF > 1.0 with ZSh(D) > 0? If yes → a real candidate for the first time.
                 If no → a clean negative result about both the signal and the process,
                 and the pipeline is built + reusable for the next candidate.
```

**After #54:** redefine #53 with the lessons learned; then work through the remaining SMC
concepts (FVG index 05, OB index 06) to establish which are viable for our use case.

---

## 4. Design spec for the regime filter (`54c`+) — locked before building

Pinned down explicitly so `54c` doesn't scope-creep into a bigger model than intended.
"Scope"/"form" etc. are axes for characterizing any ML model in general — most below were
already implied by the conversation, written down here as the actual spec:

| Axis | `#54`'s choice |
|---|---|
| Scope | Market-wide (NIFTY / basket) — never per-instrument. A stock-specific "regime" (that stock's own trend/vol state) is a real, separate concept but out of scope here — it would reopen the many-independent-draws overfitting surface this is deliberately avoiding. |
| Learning paradigm | Supervised, **offline/batch** — one-shot historical screen against fixed thresholds, frozen and applied going forward. Not adaptive/online (Model C style) — parked as a possible *later* iteration only if the one-shot version works and then decays; not a parallel track. |
| Horizon | Feature known as of **prior-day close**; applied as a gate to **that day's** signals only. No multi-day-ahead prediction. |
| Target/task | **Both**, not equal weight — trade **zpnl (continuous, ₹) leads**, since it maps to the real objective (ZPF/alpha/net_zpnl are all magnitude-based, and this variant's edge specifically comes from `SL<TP` letting winners run in *size*, not just hit-rate). Binary **win/loss is the fast first-pass screen** (simpler null-calibration mechanics, less outlier-sensitive) to cheaply cut weak candidates before the continuous check — not the deciding vote if the two disagree. **This is also what the XOR/interaction check (Complexity cap row) colors its 2D scatter by** — zpnl as a colour gradient, win/loss as two colours — so whichever target is being screened at that moment is the one the interaction plot uses. |
| Output usage | Hard binary gate (in/out that day) — not a continuous weight/sizing signal. Matches how VWAP/RSI already work. |
| Complexity cap | **1-2 combined threshold conditions max, by design.** Default: a single simple threshold. Escalate to 2 (e.g. NIFTY trend AND basket dispersion) only if the interaction/XOR check on a promising pair shows a genuine joint pattern a single condition can't capture — and even then, try a plain AND of two thresholds before anything fancier (no fitted regression/logistic combination). The escalation call itself goes through the **same null-calibration test** as any single feature — a combined rule must clear the noise ceiling by more than either feature does alone, or it's just an extra parameter for noise to hide behind. |

Log returns: not used anywhere in this pipeline (target is raw ₹ zpnl, not a return figure;
market factors use plain % change, standard for this kind of daily CAPM regression) — not a
gap, just the applicable convention. `close_log_return` was `#53`'s old target, dropped in
the `#53→#54` redirect.

---

## 5. Pointers

- Engine / sweep: `strategies/flagship/11_6bceh_short_vwap_rsi.py`
- Run log: `strategies/flagship/11_run.log`; exit breakdown:
  `strategies/flagship/11_6bceh_short_vwap_rsi60_exit_breakdown.csv` (the `60` = the winning
  RSI threshold, baked into the filename). No grid-cache `.npz` is written by `11_...py`
  (unlike the 08-10 scripts) — the run log + exit-breakdown CSV are the full record.
- Screening Tiers definition: `backtesting_rules.md` §12
- Beta-drag worked example + the full Q&A thread: `PROGRESS_HISTORY.md` 2026-09-10
- Locked 6BCEH-Short (no RSI): `strategies/6bce/v0/` (SL=8.0/TP=3.0) and
  `strategies/6bce/v1_vwap/` (SL=4.5/TP=3.0, +VWAP) — the FULL_RIGOR siblings
