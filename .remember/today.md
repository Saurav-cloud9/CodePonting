# Session Log — 2026-08-16

## Model C (MemLabs online/Passive-Aggressive learning) — deep exploration, now paused

### BTC replication + eta0/reference mystery, fully resolved
- Notebook `50_model_c_dummy_then_real.ipynb` built fresh: Part 1 toy walkthrough (8 hand-picked
  ticks, full per-tick trace, 2D fitted-line plot with tab10 colors + tick labels, 3D swept-line
  ruled surface + separate interactive Plotly HTML version), Part 2 real BTC replication, Part 3
  eta0=1 vs eta0=0.01 stability comparison.
- Resolved the long-standing eta0 mystery via exact reverse-engineering of tau from the author's
  own real screenshot values at 9 ticks spanning the sequence: TRUE value is eta0=1.0 (not the
  reference code's stated 0.01), with epsilon=0.0002 confirmed simultaneously. Root cause: almost
  certainly a stale-Jupyter-output artifact in the author's own notebook (supported by a
  systematic comment-misalignment bug found directly in the reference code file).
- Also discovered a SEPARATE reference-document error: the assumed target hit rate 50.82% was
  itself wrong — author's real screenshot shows 50.02%.
- Verified sklearn source directly (`_sgd_fast.pyx.tp`) for the tick-0 special case: PA1 has a
  hard-coded `if sqnorm(x)==0: continue` guard (skips update entirely), NOT the naively-assumed
  `min(eta0, loss/0)=eta0` result — explains why tick 0 always gives w=b=0 under PA1 but not PA2.
- Fixed real bugs along the way: row-count mismatch (added date filter `>=2020-09-29` matching
  author's true Train start), a mislabeled second plot, a KeyError from a wrong dataframe
  reference, and (later) mislabeled "Warmup" vs "Zero-return" ticks in the Excel export (tick
  1088 has a genuine zero-return day, not a warmup case) plus a blank `cum_trade_log_return` gap
  and a VS-Code-unfriendly date format — all fixed in `50_model_c_real_replication_full.xlsx`.

### POWERGRID replication — the key finding
- Built `50c_model_c_powergrid.ipynb`: same Model C config applied to POWERGRID, 11.5 years
  (2015-02-04 to 2026-07-31), daily-resampled from DS3 5-min bars per CLAUDE.md's DS3-only rule.
- **Both eta0=1 (-0.947) and eta0=0.01 (-0.727) lose money over the full history**, vs raw
  POWERGRID buy-and-hold (+1.277, max drawdown only -0.440). eta0=1 never recovers into sustained
  profitability on POWERGRID — no repeat of BTC's "3yr underwater then breakeven" pattern, which
  directly answers a credibility concern raised mid-session (that pattern was only ever observed
  once, on one non-independent stretch of BTC data).
- eta0 sweep on both assets (0.001 to 5.0): POWERGRID's best is eta0=2.0 (+0.692, still loses to
  buy-and-hold); BTC's best is eta0=0.005 (+3.320, beats its own buy-and-hold). Zero overlap
  between the two assets' best eta0 — strong evidence Model C isn't finding a transferable edge,
  just fitting each asset's idiosyncratic noise pattern.
- Built `50b_model_c_eta_comparison.ipynb` (3-way stacked equity/drawdown: eta0=1 / eta0=0.01 /
  raw asset, for both BTC and POWERGRID) — visually confirms eta0=0.01 essentially rides the
  underlying asset's own trend (near-identical curve shape to buy-and-hold) rather than
  demonstrating independent signal.

### Root cause: weak underlying feature, not model capacity
- Pearson r, `close_log_return_lag_1` vs `close_log_return`: POWERGRID r=-0.0567 (p=0.0027,
  significant, r²<1%), BTC r=-0.0369 (p=0.09, NOT significant). Both negative (mean-reverting,
  not momentum). Naive "follow yesterday's sign" baseline loses money on both assets outright
  (POWERGRID -1.57, BTC -0.51 cumulative), confirming this isn't a model-tuning problem.
- Confirmed explicitly: Models A/B/C are ALL strictly linear (ŷ=w·x+b, only the fitting procedure
  differs) — established Pearson r as the correctly-matched screening tool for this model family
  specifically (a non-linear-detecting metric like mutual information would be misleading, since a
  linear model can't exploit a non-linear relationship even if one existed).
- Discussed but explicitly deferred: testing the weak signal through this project's actual
  RR/SL-TP exit framework (separate axis from model choice — a sub-50% hit rate can still be
  profitable with the right exit structure) — not yet built.

### Decision
Pause Model A/B/C exploration. Resume notebook 35's Pearson r feature screening (parallel,
separately-tracked thread) as primary. Only return to Model C once a feature meaningfully
stronger than current candidates (RSI r≈0.08, lag-1 return r≈-0.057, both r²<1%) is found.

## Math/stats teaching thread (alpha/beta CAPM regression) — in progress, paused mid-derivation

- Explicit standing preference established and saved to memory: teach underlying math (variance,
  OLS, calculus) as pure/standalone math first, then map onto trading terms second — combining
  new math + new domain vocabulary simultaneously was flagged as harder to absorb.
- Derivation covered so far (testing whether POWERGRID's eta0=2.0 equity curve is real skill or
  just trend-tracking): beta=Cov/Var, alpha=mean(y)-beta*mean(x), residual/error_t definition,
  covariance/variance refresher, residual variance formula (n-2) with full derivation of WHY n-2
  (OLS's alpha+beta fit forces two exact constraints: sum(error)=0 from dS/dalpha=0, and
  sum(error*x)=0 from dS/dbeta=0 via calculus) — taught via a concrete "5 numbers, mean must be
  10" analogy. Explicitly clarified this n-2 correction is unrelated to Model C's "Warmup tick"
  exclusions (different concepts that happened to come up in the same conversation).
- Paused right after introducing (not yet breaking down) the SE(alpha) formula. Next: SE(alpha)
  breakdown → t-statistic → p-value → apply to POWERGRID's real eta0=2.0 data.

## Session/tooling: WSL + cross-session messaging setup

- Explored Claude Code's cross-session messaging feature (SendMessage/ListAgents) to get a
  genuinely separate, addressable "math mode" chat session. Learned via official docs
  (code.claude.com/docs/en/cross-session-messaging) that this feature is NOT available on native
  Windows (macOS/Linux/WSL2 only) — confirmed empirically here too (`/list-agents` returned "not
  available in this environment").
- Initially spawned a background subagent ("math-mode") via the Agent tool as a workaround — this
  works (parent-child relationship, SendMessage-able by agentId) but is a different mechanism from
  true peer-to-peer cross-session messaging.
- Set up WSL (Ubuntu, already installed) + VS Code WSL extension to get a genuine second,
  independent Claude Code session with real cross-session messaging available. Confirmed Node
  v20.19.5 and Claude Code CLI 2.1.233 already present inside WSL, repo reachable at the same
  path via `/mnt/c/Users/Saurav/CodePonting` (same files, not a separate copy — no sync-drift risk
  like the kite_oracle_papertrading VM setup). Configured a global `python.analysis.exclude`
  (`data`, `outputs`) to fix a Pylance performance warning along the way.
- Plan going forward: this native-Windows session stays as the "master backup" thread; the WSL VS
  Code instance becomes the orchestration hub, spawning its own independent "math mode" WSL
  session for genuine two-way cross-session messaging between peers.
- Wrote a full recap/seed file (`memlabs/50d_full_recap_seed.md`) covering the entire Model C
  investigation end-to-end, for the new WSL session to read and continue from with zero context
  loss (including the exact alpha/beta derivation stopping point).

## Next session priorities (explicitly agreed)
1. PRIMARY: continue Pearson r feature screening in notebook 35 (separate thread — see its own
   handoff notes for exact next candidate: gap-size vs intraday-move).
2. When picking the math-mode/alpha-beta thread back up (new WSL session, seeded from
   `memlabs/50d_full_recap_seed.md`): continue from SE(alpha), same slow one-step-at-a-time style.
3. Not urgent: testing the weak Pearson-r signal(s) found so far through actual RR/SL-TP exits
   rather than raw full-day-return capture — a separate, not-yet-started axis of investigation.
