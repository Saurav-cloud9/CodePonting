# Step 52 — math-mode session handoff (for a fresh session, e.g. on the Oracle VM)

**Purpose:** if this WSL math-mode session can't be carried over directly (confirmed: no session
teleport across machines exists), a brand new Claude Code session opened in this same repo should
be able to read this ONE file and resume teaching the alpha/beta CAPM thread with zero lost
context. Written 2026-08-18 (per the fv2 peer session's request, `codeponting-f9` at the time).

---

## Where the thread stands right now

The full OLS/CAPM alpha-beta derivation has been taught **end to end**, from first principles, in
this order:
1. Slope (basic "tilt of a line" concept) — the very first thing covered.
2. Disambiguated **t vs T** — three unrelated meanings that all share the letter "t" in the
   notebook: `t` as a row-index, `t` as the single t-statistic number, capital `T` as the
   t-distribution random variable (NOT total count — that's `n`).
3. Probability vs. **probability density** — density × width = probability (area under curve),
   density itself is not a probability and can exceed 1.
4. **Differentiation from scratch** — slope generalized to curves, why setting a derivative to 0
   finds a minimum (bowl-shape argument + a `f(x)=x²` worked numeric example).
5. **Full OLS derivation**, chronological, calculus-first: `S = Σerror_t²` → two normal equations
   (`dS/dalpha=0`, `dS/dbeta=0`) → closed-form `alpha`, `beta` → residuals → why `n-2` → rewriting
   `alpha`/`beta`/`y_bar` as weighted sums of `y_t` → `Cov(y_bar,beta)=0` proof → `Var(y_bar)` and
   `Var(beta)` individually derived → combined into the general `SE(y at x0)` formula → `SE(alpha)`
   as the `x0=0` special case → t-statistic → p-value.
6. Clarified what "regression" means as a math term (general best-fit-line-via-OLS concept, not
   inherently about time/past→future), that THIS application is inference-flavored (testing if
   alpha is real, not forecasting), and its finance-specific name: **factor regression** /
   **performance-attribution regression**.
7. Corrected a couple of natural misconceptions along the way (worth knowing if they resurface):
   - "OLS is applied to error_t" — no, OLS is applied to `(x,y)` in both a plain prediction model
     AND this CAPM regression; `error_t` is the byproduct being squared/summed, not the input.
   - "We minimize x,y" — no, x,y are always fixed data; only the residual (gap between actual y
     and the model's guess) is ever minimized, in both prediction and inference contexts.

## NOT yet done — the actual "resume from here" point

- **Part 2 of the notebook** (`52_alpha_beta_concept_and_powergrid.ipynb`, marked "pending" in its
  own last cell): running this exact pipeline on REAL POWERGRID eta0=2.0 Model C data (instead of
  the 5-15 point dummy datasets used for teaching) to actually answer "is POWERGRID's eta0=2.0
  equity-curve outperformance statistically real, or noise?" — not started.
- p-value has been derived as a FORMULA (`P(|T|>|t|)`) but its practical interpretation/decision
  rule (e.g. "what does a 44% vs a 4% p-value actually mean for deciding real-vs-noise here") has
  not yet been walked through as its own dedicated step — natural next thing to teach before or
  alongside Part 2.

## Teaching-style preferences (apply throughout, not just at the start)

- **Math-before-domain-mapping** (Saurav's explicit standing preference, see project memory
  `feedback_math_before_domain_mapping.md`): teach pure math with neutral variables FIRST, only
  map onto trading/CAPM vocabulary after the math itself is solid.
- **One step at a time** — do not dump multiple new formulas/concepts in one reply; explain one
  piece, then wait for explicit confirmation before continuing.
- When a pure-math sub-concept needs illustrating, build a **tiny standalone dummy example** (5 or
  fewer clean integer points, e.g. `x=[-2,-1,0,1,2]`) rather than reusing real trading numbers —
  Saurav has asked for this explicitly multiple times ("dont use trading data. just a very very
  simple example"). Verify derived formulas numerically against the dummy example's actual
  computed values wherever possible.
- Saurav frequently replies "ris" (reply in short) — when it appears, keep the answer to 1-3 tight
  lines, no elaboration, unless a correction is needed.
- Saurav often restates his own understanding as a check ("so X means Y, right?") — confirm
  precisely, and explicitly flag+correct the exact part that's off if only partially right; don't
  just say yes/no without pinpointing which piece was correct vs. which piece needs fixing.
- Plain-text notation preferred over LaTeX in conversational replies (LaTeX `$$` blocks are fine
  in the reference .md files themselves, matching the pre-existing `52_alpha_beta_formulas.md`
  style — but keep in-chat explanations in plain arithmetic/text form).
- When a concrete visual would help, build a real matplotlib graph (dark-mode, per project
  convention: `plt.style.use('dark_background')`) and save both the `.py` script and the `.png`
  into this memlabs folder — don't just describe a graph in words.

## Companion files in this folder (read these, don't re-derive)

| File | What it covers |
|---|---|
| `52_alpha_beta_formulas.md` | Pre-existing. Formulas only, in APPLICATION order (spreadsheet order), no derivation shown. |
| `52_alpha_beta_concept_and_powergrid.ipynb` | Pre-existing. Part 1 = toy dataset concept plots (done/confirmed). Part 2 = real POWERGRID eta0=2.0 (pending, see above). |
| `52_mathmode_full_derivation_chronological.md` | **The main derivation reference** — all 14 steps above, in the order they were actually derived, each with the calculation shown. Includes the general regression definition + finance-specific naming note at the top. |
| `52_t_and_T_explained.md` | Disambiguates the 3 meanings of t/T (index, t-statistic, t-distribution). Also has a `[MATH-MODE]` aside section on probability density via a population-density analogy. |
| `52_mathmode_population_density_example.py` / `.png` | Standalone "density × width = count" dummy example (10km road, 2-segment step function), no trading data. |
| `52_mathmode_confidence_band_example.py` / `.png` | Standalone 5-point dummy dataset showing the SE confidence band narrow at the pivot (`mean(x)`), wide at the edges. |
| `52_mathmode_confidence_band_explained.md` | Write-up for the above: SE formula broken into its two additive terms, the see-saw analogy for why uncertainty grows with distance from center, and how `SE(alpha)` is just that same formula evaluated at `x0=0`. |
| `52_mathmode_session_handoff.md` | This file. |

## Everything else a fresh session needs

- Project-level standing conventions (from CLAUDE.md, apply here too): DS3 is the only permitted
  historical data source (never `intraday_5min`, never CSV fallback) — relevant once Part 2 pulls
  real POWERGRID data; ATR-based SL/TP only, never fixed % stop; dark-mode matplotlib on every
  chart; numbered scripts in a folder use zero-padded prefixes for ordering (this whole thread
  stays under index `52`, no new numeric index was opened for it).
  - Note: this thread has NOT needed DS3/live data itself so far (everything taught used tiny hand-
    built dummy datasets) — DS3 only becomes relevant once Part 2 (POWERGRID eta0=2.0) starts.
- Broader background (Model A/B/C, why this alpha/beta thread exists at all — testing whether
  eta0=2.0's equity curve is genuine skill vs. asset-trend-tracking) is fully covered in
  `50d_full_recap_seed.md` in this same folder — read that first if the Model A/B/C context itself
  (not just the alpha/beta math) is unfamiliar.
- Cross-session naming: this session = "math mode" (scoped strictly to this alpha/beta CAPM
  thread). The other/main session = "fv2". See project memory `project_cross_session_naming.md`
  for how Saurav refers to each and how to resolve live peer names via `ListAgents`.
