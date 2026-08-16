# Step 50d — Full recap / seed context for a new CC session

> Purpose: this file is a complete, self-contained summary of everything done across the 50-series
> (50, 50b, 50c, 51, 52) in this memlabs folder. A fresh Claude Code session (e.g. running under
> WSL) should read this file first to pick up full context without needing the original chat
> history. Written 2026-08-16.

## Background: Models A/B/C

Exploratory ML research (NOT production fv2 strategy code) replicating and stress-testing "Model
C" from a YouTube tutorial (MemLabs — "How to handle Regime Changes"), then testing its viability
on the actual project asset (POWERGRID). Three models were replicated from the tutorial in earlier
notebooks (`18`-`21`, not part of the 50-series but referenced): Model A (simple linear
regression), Model B (multi-feature linear regression), Model C (online/incremental
Passive-Aggressive learning).

**All three are strictly linear models** (`ŷ = w·x + b`) — only the *fitting procedure* differs.
A/B use one-shot closed-form OLS (Normal Equation) fit on the whole dataset at once. Model C fits
online, one data point ("tick") at a time. Models A/B were verified to match the tutorial author's
numbers exactly (~14 decimal places) via independent hand-derivation.

## Model C's full mechanics (fully derived, verified against sklearn source code)

Uses `sklearn.linear_model.SGDRegressor(loss="epsilon_insensitive", penalty=None,
learning_rate="pa1"|"pa2", eta0=..., random_state=69)`.

Per tick:
1. Scaling: `x_scaled = (x - running_mean) / running_std` (incremental via `StandardScaler.partial_fit`)
2. Prediction (using PRE-update weights): `ŷ = w·x_scaled + b`
3. Error: `error = y - ŷ`
4. Loss (epsilon-insensitive): `loss = max(0, |error| - epsilon)`. loss=0 → "passive" (no update). loss>0 → "aggressive".
5. Step size — **PA1** (hard cap): `τ = min(eta0, loss/‖x_scaled‖²)`
5b. Step size — **PA2** (no hard cap, soft denominator): `τ = loss / (‖x_scaled‖² + 1/(2·eta0))`
6. Weight update: `w_new = w_old + τ·sign(error)·x_scaled`
7. Bias update: `b_new = b_old + τ·sign(error)·1`

Full formulas-only reference: **`52_model_c_formulas.md`**.

Key mechanical findings:
- **Tick 0 special case (PA1 only)**: `x_scaled=0` always at tick 0 (single point, zero deviation
  from its own mean). sklearn's actual source (`_sgd_fast.pyx.tp`) has a hard-coded guard:
  `if sqnorm(x)==0: continue` — skips the update ENTIRELY, both w and b stay exactly 0. This is
  NOT "min(eta0, loss/0)=eta0" as one might naively assume — verified via reading sklearn source
  directly. PA2 has no such guard (denominator never hits zero), so PA2's tick 0 produces a small
  nonzero bias update.
- `random_state` is a proven no-op for single-sample streaming `partial_fit` calls (verified via
  sklearn source + empirical multi-seed test) — it only affects internal batch-shuffling,
  irrelevant when each call gets exactly one row.
- `eta0` is literally the "C" (aggressiveness cap) parameter per sklearn's own docstring.

## `eta0` mystery resolved (BTC replication)

The reference tutorial code stated `eta0=0.01`, but this did NOT reproduce the author's real
output. Extensive reverse-engineering (solving for τ algebraically from the author's own real
screenshot values at 9 independent ticks spanning early and late in the sequence) proved the TRUE
value used was **`eta0=1.0`**, with `epsilon=0.0002` confirmed simultaneously (capped ticks pin
`eta0`, uncapped ticks independently pin `epsilon` — proven unique solution). Most likely
explanation: a "stale Jupyter output" — the author edited the eta0 value after generating the
shown output without re-running that cell (supported by a systematic comment-misalignment bug
found in the reference code file, itself evidence of a transcription-process artifact).

Also discovered: the assumed target hit-rate of 50.82% (from a secondary reference doc) was
ITSELF wrong — the author's real screenshot shows **50.02%**, not 50.82%. This was a second,
independent reference-document error, unrelated to the eta0 question.

Full run of `eta0=1.0` on BTC still diverges from the author's exact numbers somewhere in the
middle of the 2053-tick sequence (floating-point/sklearn-version drift, inherent to long
sequential online learning) — agreed to stop chasing this further; not a real algorithmic gap,
diminishing returns.

## Notebook `50_model_c_dummy_then_real.ipynb`

**Part 1 — Toy walkthrough**: 8 hand-picked (x,y) pairs, full per-tick trace (scaled x, w/b
before/after, loss, passive/aggressive). Visualizations: w/b evolution 2-panel plot,
predicted-vs-actual plot, 2D "fitted line y=wx+b evolving tick by tick" (tab10 qualitative
colormap — switched from `plasma` after poor contrast between adjacent ticks was flagged; each
dot/line pair color-matched, ticks labeled), 3D "fitted line swept across time" ruled-surface plot
(matplotlib + a separate interactive Plotly HTML version:
`50_toy_line_evolution_3d_interactive.py`/`.html`).

**Part 2 — Real BTC replication**: `eta0=1`, `epsilon=0.0002`, `pa1`, `random_state=69`. Data:
`BTCUSDT_1d_author_original.csv`, date-filtered to `>= 2020-09-29` (matches author's actual Train
start, where his 40-day MA warmup column would have finished — NOT a hardcoded row-count slice,
deliberately date-based to survive future data refreshes). Result: n=2056 rows in stream, 3
excluded as unscoreable (tick 0, tick 1 = true warmup; tick 1088 = genuine zero-return day,
`close_price` unchanged 26582.0→26582.0 on 2023-09-22/23), 2053 scored rows. **Hit Rate: 49.63%**
(vs corrected reference 50.02%).

**Part 3 — Stability comparison** (eta0=1 vs eta0=0.01, same BTC data): stability metrics table
(w/b std dev, mean |Δw|/|Δb|, % extreme jumps, hit rate, final cum return) + overlaid w/b plots.
- eta0=1: w std 0.508, b std 0.539, 22.7%/75.6% of ticks have |Δw|/|Δb|>0.5, hit rate 49.63%,
  final cum return 0.612.
- eta0=0.01: w std 0.0096, b std 0.0137, 0%/0% extreme jumps, hit rate 48.61%, final cum
  return 0.489.

**Excel export** (`50_model_c_real_replication_full.xlsx`): all 2056 rows including warmup, with
`close_price`, `date` (fixed to clean `YYYY-MM-DD` format — VS Code's Excel viewer doesn't
reliably render openpyxl's default datetime format), and a fixed labeling scheme: `"Warmup"`
(tick 0/1 only, no prior model state) vs `"Zero-return"` (tick 1088 — model IS trained, real
prediction exists, but `true_y=0` exactly so sign-matching is undefined — a DIFFERENT situation
from warmup, was originally mislabeled the same). `cum_trade_log_return` fixed to always
accumulate (no blank gaps) since `trade_log_return` is structurally 0 on both excluded-tick types
anyway.

**pa2 exploration**: swept eta0 with `learning_rate="pa2"` trying to match reference numbers —
none matched better than pa1/eta0=1 (closest hit-rate 50.19% at eta0=0.1, but wrong signal-count
shape and wrong sign on `y_hat[2055]`). Confirmed pa1/eta0=1 remains the best-justified config;
pa2 not pursued further. Also discovered structurally: pa2's tick-0 bias comes out nonzero
(`b≈0.000266`, verified via direct calc: `τ = loss/(0+1/(2·0.01)) = loss/50`), unlike pa1's
exact-zero — this changes which ticks get excluded as unscoreable between the two modes (pa2 has
one fewer "Warmup" tick than pa1, since its tick 1 prediction is already nonzero).

## Notebook `50b_model_c_eta_comparison.ipynb`

Extension of #50, focused only on eta0=1 vs eta0=0.01 vs raw BTC buy-and-hold, real BTC data.

- **Equity curves** (3 stacked panels, own y-axis each): eta0=0.01's curve is nearly a carbon copy
  of raw BTC buy-and-hold — same rally into ~tick 1400, same steady bleed afterward. Makes sense:
  with such a tiny step cap, `w` stays near 0, so `pred_y_hat ≈ b`, which tends to hold one
  consistent sign for long stretches — functionally closer to "stay long/short and ride it" than
  genuine signal-following. eta0=1 looks structurally different (choppier, doesn't track BTC's
  own shape).
- **Drawdowns**: eta0=1's max drawdown (-0.880) is meaningfully shallower than both eta0=0.01
  (-2.122) and even raw BTC itself (-1.455). eta0=0.01 is actually WORSE than just holding BTC on
  this metric — it tracks BTC's upside closely but doesn't cushion the late collapse at all.
- **Segment analysis** (splitting BTC's eta0=1 curve at the LAST time its cum return dips below
  zero, tick 1147 = date 2023-11-20):
  - Segment 1 (tick 0–1147, 2020-09-29 to 2023-11-20, "learning/underwater"): eta0=1 total_return
    -0.004 (flat/breakeven), hit_rate 49.30%. eta0=0.01 total_return +2.129, hit_rate 50.78%
    (beats raw BTC's own +1.254 return in this window).
  - Segment 2 (tick 1148–2055, 2023-11-21 to 2026-05-16, "post-breakeven"): eta0=1 total_return
    **+0.616**, hit_rate 49.89%. eta0=0.01 total_return **-1.640**, hit_rate drops to 45.70%
    (worse than coin-flip).
  - This is a genuine reversal: eta0=1 needs ~3 years to become profitable on BTC, then holds;
    eta0=0.01 dominates early (riding the trend) then collapses when the trend reverses.
  - **Caveat explicitly raised and agreed**: Segment 2 is only ~2.5 years / 908 ticks, a single
    non-independent stretch (one specific BTC path), and its hit rate is barely above coin-flip
    (49.89%) — NOT strong evidence of a repeatable "learning mechanism". `random_state` is a
    proven no-op for this streaming setup, so no cheap variance estimate is available via
    re-seeding. Agreed next test: apply the same comparison to POWERGRID (11+ years of data) to
    see if the same "slow learn then edge" pattern is asset-specific (BTC-only) or general.

## Notebook `50c_model_c_powergrid.ipynb`

Same eta0=1 vs eta0=0.01 vs raw-asset comparison, applied to POWERGRID (the actual fv2 target
asset). **Tick = 1 trading day**, resampled from DS3's 5-min POWERGRID bars (last close of each
session) — per CLAUDE.md, DS3 is the only permitted historical source (no CSV fallback). n=2808
trading days, 2015-02-04 to 2026-07-31 (~11.5 years).

**Results — THE KEY FINDING**:
| | eta0=1 | eta0=0.01 | Raw POWERGRID buy-and-hold |
|---|---|---|---|
| final cum return | **-0.947** | **-0.727** | **+1.277** |
| max drawdown | -1.653 | -1.433 | -0.440 |

**Both Model C configs lose money over the full 11.5-year POWERGRID history**, while simple
buy-and-hold gains +1.277 with a far shallower drawdown. Critically: **eta0=1 never recovers into
sustained profitability on POWERGRID** — no repeat of BTC's "long learning phase then breakeven"
pattern; it trends down almost the whole 11.5 years with only a small late partial recovery
(-1.65 → -0.95, never crossing zero). This directly answers the earlier credibility concern: the
BTC "3 years to learn, then profit" story does NOT generalize to POWERGRID, even with ~2x the
data — strong evidence it was a property of that one BTC path, not a real learning mechanism.

**eta0 sweep on POWERGRID** (eta0 ∈ {0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0}):
| eta0 | 0.001 | 0.005 | 0.01 | 0.05 | 0.1 | 0.5 | 1.0 | **2.0** | 5.0 |
|---|---|---|---|---|---|---|---|---|---|
| final cum return | -0.439 | -0.622 | -0.727 | -1.354 | -0.032 | -0.455 | -0.947 | **+0.692** | +0.201 |
| max drawdown | -0.853 | -1.516 | -1.433 | -2.068 | -1.047 | -1.407 | -1.653 | **-0.635** | -0.833 |
| hit_rate% | 48.35 | 48.75 | 48.21 | 48.28 | 49.04 | 50.09 | 49.26 | 50.56 | 49.98 |

No `eta0` beats buy-and-hold (+1.277) on POWERGRID. Best is eta0=2.0 (+0.692, added to the
notebook's stacked comparison as a 4th curve/panel between eta0=0.01 and raw POWERGRID). Its
equity curve is flat/choppy near zero for the first ~1600 ticks (2015–~2021), then a real climb
from ~tick 1700 onward — timing that lines up closely with when raw POWERGRID's own uptrend
accelerates too. Looks like another case of a specific eta0 happening to align with one asset's
realized trend, not an independent learned edge.

**Same eta0 sweep repeated on BTC for direct comparison**:
| eta0 | 0.001 | **0.005** | 0.01 | 0.05 | 0.1 | 0.5 | 1.0 | 2.0 | 5.0 |
|---|---|---|---|---|---|---|---|---|---|
| final cum return | +0.886 | **+3.320** | +0.489 | -0.993 | +0.778 | +0.719 | +0.612 | +0.360 | -1.019 |
| max drawdown | -1.622 | -1.044 | -2.122 | -2.081 | -1.455 | -0.815 | -0.880 | -1.234 | -2.329 |
| hit_rate% | 50.22 | 50.37 | 48.61 | 48.42 | 50.85 | 49.39 | 49.39 | 49.98 | 48.56 |

BTC's best is eta0=0.005 (+3.320, actually beats BTC's own buy-and-hold of +1.988). **No overlap
whatsoever between BTC's best eta0 (0.005) and POWERGRID's best eta0 (2.0)** — opposite ends of
the range. If Model C had a real, transferable edge, you'd expect the well-performing eta0 region
to at least roughly overlap between assets. It doesn't. 6/9 BTC configs are net positive vs only
2/9 for POWERGRID — BTC's sweep is generally more favorable across the board too.

## Pearson r / naive-baseline diagnostics (root-cause investigation)

Tested WHY Model C underperforms — is the underlying feature (`close_log_return_lag_1` predicting
`close_log_return`) even worth modeling?

| | n | Pearson r | p-value | naive "follow yesterday's sign" hit rate |
|---|---|---|---|---|
| **POWERGRID** | 2808 | -0.0567 | **0.0027** (significant) | 46.08% |
| **BTC** | 2095 | -0.0369 | 0.0909 (NOT significant) | 47.64% |

Key findings:
- Both assets show **negative (mean-reverting) autocorrelation, not momentum** — yesterday's
  return direction is a weak CONTRARIAN signal. Naive "follow yesterday" loses on both.
- **POWERGRID's correlation IS statistically significant; BTC's is NOT.** This is a genuine twist:
  POWERGRID has the statistically sounder (if still very weak, r²≈0.3%) signal, yet Model C loses
  money on it; BTC has the weaker/insignificant signal, yet Model C appeared to "work" there
  (best-case +3.320 at eta0=0.005). Consistent with BTC's apparent success being noise/overfitting
  rather than a real exploited relationship.
- Naive "follow yesterday's sign" baseline (no model at all): POWERGRID hit_rate=46.08%, final
  cum return **-1.5700**, max drawdown -1.8176. BTC hit_rate=47.64%, final cum return **-0.5054**,
  max drawdown -1.9017. Both lose money outright, worse than Model C on both assets — confirms the
  naive rule is a genuinely losing baseline, and Model C (whatever its flaws) is doing somewhat
  better than blind trend-following, just not well enough to beat holding the asset.
- Consistent with the earlier notebook-35 Pearson-r feature-screening work (separate MemLabs
  thread — see project memory `project_strategy_foundation_concern.md` /
  `feedback_pearson_r_outlier_threshold.md`): POWERGRID shows weak-but-persistent statistical
  significance across multiple features (RSI too, r≈0.08, r²<1%) — this is a second, independent
  confirmation of the same "real but very thin edge" story for POWERGRID specifically.

**Important caveat raised**: all of the above evaluates `trade_log_return = signal × true_y`,
i.e. capturing the ENTIRE day's return in the predicted direction with NO stop-loss/target/exit
rule at all. A sub-50% hit rate strategy CAN still be profitable under the right RR-based exit
structure (this project's actual ATR-based SL/TP convention, per `backtesting_rules.md`) — this
has NOT yet been tested. What's been shown is "no raw directional edge worth exploiting without
risk management," not "definitely unprofitable under any exit structure."

## Notebook `51_least_squares_3d.md` (PARKED, unrelated side-thread)

User-provided text + 5 images about Least Squares extending from 2D lines to 3D planes (R² from
-10.819 up to 0.980). Explicitly parked, not part of the active Model C investigation. Revisit
later if wanted — not urgent.

## `52_model_c_formulas.md`

Pure math-mode reference, formulas only (steps 1–7 + tick-0 boundary condition + step 5b for pa2),
no prose — see file directly.

## Conclusion / current status (as of 2026-08-16)

**Decision made**: pause Model A/B/C exploration. Root cause of Model C's underperformance
identified as data (weak/thin real signal, r²<1% on the lag-1-return feature for both assets), not
model capacity — jumping to more complex models (e.g. neural networks) would likely just increase
overfitting risk on a near-noise feature, not close a real gap. Confirmed via explicit discussion
that Models A/B/C are ALL linear (`ŷ=w·x+b`); Pearson r (linear-relationship-specific) is
therefore the correctly-matched screening tool for this model family — non-linear-detecting
methods (mutual information, tree importance) would be misleading since a linear model can't
exploit non-linear relationships anyway even if found.

**Agreed next step**: resume the SEPARATE, PARALLEL notebook-35 Pearson r feature-screening thread
(different exploration, same project) — pending: gap-size (`log(open_today/close_yesterday)`) vs
intraday-move screening. Standing rule: only escalate back to a full Model A/B/C rebuild once a
feature is found meaningfully stronger than the current best (RSI r≈0.08, lag-1 return r≈-0.057,
both r²<1%). See project memory `project_model_c_regime_learning.md` for the canonical version of
this conclusion.

**Also still open, not yet done**: testing the existing weak signal(s) through this project's
actual RR/SL-TP exit framework (separate axis from model choice, per the caveat above) — not
started.

## In-progress, NOT finished: Alpha/Beta CAPM-style regression derivation

Separate thread: testing whether POWERGRID's eta0=2.0 equity curve (the sweep's best performer)
represents genuine skill or just asset-trend-tracking, via:

**strategy_return_t = alpha + beta × market_return_t + error_t**

(market_return = POWERGRID's own daily return, strategy_return = Model C's daily
signal×actual-return). This derivation was being taught slowly, step by step, as a **math-mode**
exercise (Saurav's explicit stated preference: teach pure math standalone, using neutral variables,
BEFORE mapping onto trading terms — combining new math + new domain vocabulary simultaneously is
harder to absorb; see project memory `feedback_math_before_domain_mapping.md`).

**Steps covered so far** (go slow, one step at a time, wait for confirmation before continuing —
do NOT dump multiple new formulas in one reply):
1. `beta = Cov(market_return, strategy_return) / Var(market_return)`
2. `alpha = mean(strategy_return) - beta × mean(market_return)` (forces the line through the
   "point of averages")
3. `error_t = strategy_return_t - (alpha + beta × market_return_t)` — the residual per day,
   computed AFTER fitting (unlike Model C, where error drives the fit LIVE, tick by tick — this
   distinction was explicitly taught: "for prediction it's better to have the online-ness
   involved (Model C); for evaluating a model itself it's better to go with OLS-style residuals
   (fair, hindsight-based, since one single line is fit using ALL data at once, no point gets
   privileged)").
4. Covariance/Variance refresher: `Var(X) = (1/n)Σ(xᵢ-mean(X))²`, `Cov(X,Y) = (1/n)Σ(xᵢ-mean(X))(yᵢ-mean(Y))`.
   Variance is the special case Cov(X,X). For beta specifically (a RATIO), n vs n-1 cancels out
   and doesn't matter; it only matters for a STANDALONE variance/covariance number.
5. Residual variance: `Var(error) = (1/(n-2)) × Σ(error_t)²`. Fully explained WHY n-2 (not n or
   n-1): OLS's alpha AND beta fits force TWO exact constraints on the residuals —
   `Σerror_t = 0` (from `dS/dalpha=0`, where `S=Σerror²`) and `Σ(error_t × market_return_t) = 0`
   (from `dS/dbeta=0` via calculus chain rule). Two constraints → only n-2 residuals are truly
   free; the last 2 are mathematically forced. Taught via a concrete numeric analogy: "5 numbers
   whose mean must be exactly 10 — freely pick 4, the 5th is forced" (extends the same idea to n-2
   for two simultaneous constraints). Also explicitly clarified: this n-2 correction is COMPLETELY
   UNRELATED to Model C's "Warmup tick" exclusions (that's a data-availability issue, not a
   degrees-of-freedom/statistics issue) — these came up in the same conversation but are
   independent concepts. Also clarified: `mean(error_t)` across the WHOLE series is EXACTLY zero
   (not "ideally" — mathematically guaranteed for any OLS fit), which is why the variance formula
   has no visible "- mean" term (it's there, just simplifies to subtracting zero).

**NEXT STEP TO CONTINUE FROM (not yet taught)**: Standard error of alpha —
`SE(alpha) = √[ Var(error) × ( 1/n + mean(market_return)² / Σ(market_returnₜ - mean(market_return))² ) ]`
— just introduced as one line, not yet broken down. Continue from here, same slow style, then:
t-statistic (`t = alpha / SE(alpha)`), p-value (t-distribution, n-2 degrees of freedom), and
finally (only once the pure math is solid, per Saurav's stated preference) actually computing this
for POWERGRID's eta0=2.0 strategy to answer "is this equity curve's outperformance statistically
real, or noise."

## Session/workflow notes

- A background subagent named "math-mode" was already spawned from the ORIGINAL (native Windows)
  Claude Code session to serve as a dedicated math-tutoring companion, seeded with this same
  alpha/beta context — but `SendMessage`/cross-session-messaging to keep it in sync doesn't work
  well since the original session runs on native Windows (cross-session messaging isn't available
  there per Claude Code's own docs: macOS/Linux only, WSL2 counts as Linux). This WSL session is
  being set up specifically so genuine two-way cross-session messaging (real peer sessions, not
  parent-child subagent) becomes available — e.g. this WSL session + a second independent WSL
  session for "math mode," orchestrated between themselves, with the original native-Windows
  session acting as more of a "master backup" thread.
- Project-level standing conventions (from CLAUDE.md, apply here too): DS3 is the only permitted
  historical data source (never `intraday_5min`, never CSV fallback); ATR-based SL/TP only, never
  fixed % stop; dark-mode matplotlib (`plt.style.use('dark_background')`) on every chart; numbered
  scripts in a folder use zero-padded prefixes for ordering.
