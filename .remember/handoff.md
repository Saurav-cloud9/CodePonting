# Handoff Note — 2026-08-16

## Current State — Model C exploration (CLOSED OUT / PAUSED this session)

- Full investigation across `Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/`:
  notebooks `50` (toy walkthrough + BTC replication), `50b` (eta0=1 vs 0.01 vs raw-asset 3-way
  comparison), `50c` (same applied to POWERGRID, 11.5yr DS3). Formulas-only reference: `52`.
- **Conclusion**: Model C (online/Passive-Aggressive linear regression) shows no transferable edge
  across assets — BTC's best eta0 (0.005) and POWERGRID's best eta0 (2.0) share zero overlap, and
  BTC's "eta0=1 needs ~3yrs to become profitable" pattern does not repeat on POWERGRID even with
  2x the data (both eta0=1 and eta0=0.01 lose money outright over POWERGRID's full 11.5yr history,
  vs. buy-and-hold's +1.277). Root-caused to weak underlying signal (Pearson r on
  close_log_return_lag_1: POWERGRID r=-0.057/p=0.003 significant-but-r²<1%, BTC r=-0.037/p=0.09
  not significant), not model capacity — confirmed Models A/B/C are all strictly linear, making
  Pearson r the correctly-matched screening tool.
- **Full context recap saved**: `memlabs/50d_full_recap_seed.md` — a new session (or this one, if
  resumed later) should read that file for complete details rather than re-deriving anything.
- **Decision**: paused, not abandoned. Resume only once notebook 35 (separate thread, below) finds
  a candidate feature meaningfully stronger than what's been found so far.
- **Still open, not started**: testing the weak signal(s) through this project's actual RR/SL-TP
  exit framework (a sub-50% hit rate can be profitable with the right exits — this is a separate
  axis from model choice, raised explicitly but not yet built).

## Current State — MemLabs Pearson's r feature screening (PRIMARY, continues independently)

- Notebook 35 (`Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/
  35_pearson_r_feature_screening.ipynb`). Per the most recent tracked progress: RSI period sweep
  done (7/9/14/21/28 — no period beats period=14 meaningfully; POWERGRID/TATAMOTORS/DABUR stay
  significant across all periods but still weak, r²<1%), volume screened on TATAMOTORS (weakest
  candidate yet, only 2/30 stocks significant even before requiring NIFTY; log transform fixed
  skew/kurtosis but did not strengthen r). Two real DS3 data bugs found and fixed along the way:
  INFY frozen-tick day + gap (2015-04-24), DIVISLAB un-split-adjusted day (2015-09-22, real 1:1
  bonus issue) — both corrected in their respective parquet files.
- Standing memory saved: `|r|>0.1` in this daily-Pearson-r context is a trigger to verify against
  raw DS3/Kite data before trusting (`feedback_pearson_r_outlier_threshold.md`).
- **Next (explicitly agreed, PRIMARY)**: screen gap-size (`log(open_today/close_yesterday)`) vs
  intraday-move as target (not full close_log_return, to avoid gap-being-part-of-target overlap).
- Standing rule unchanged: only escalate to a full Model A/B build + WFA once a candidate is found
  meaningfully stronger than RSI's current best (r≈0.08, r²<1%), not just statistically
  significant.

## Current State — Math/stats teaching thread (alpha/beta CAPM regression, IN PROGRESS)

- Testing whether POWERGRID's eta0=2.0 Model C equity curve represents genuine skill vs.
  asset-trend-tracking, via `strategy_return_t = alpha + beta × market_return_t + error_t`.
- Explicit teaching preference (saved to memory, `feedback_math_before_domain_mapping.md`): teach
  math standalone/neutral-variables first, map onto trading terms second; go one small step at a
  time, wait for confirmation before adding the next piece.
- **2026-08-23 update (math-mode VM session)**: built a new expanded companion file,
  `memlabs/52_mathmode_full_derivation_expanded.md` (every algebra line shown), alongside the
  existing compact `52_mathmode_full_derivation_chronological.md`. Fully re-derived Steps 0-6 in
  the expanded file (parabola-shape cross-check, full Cov(x,y)/Var(x) expansion proof, two
  understanding-checkpoint summaries), plus a standalone 10-residual worked example +
  matplotlib chart (`52_mathmode_variance_dof_example.py`/`.png`) illustrating the n-2
  degrees-of-freedom correction concretely (Var(n)=17.4 vs correct Var(n-2)=21.75).
- **Steps covered (chronological file has all 14 in compact form; expanded file has 0-6 in full
  detail)**: beta=Cov/Var formula; alpha=mean(y)-beta*mean(x); residual/error_t definition;
  covariance vs variance refresher; residual variance formula with FULL derivation of why n-2;
  weighted-sum rewrite of β/ȳ (Step 7); Cov(ȳ,β)=0 proof (Step 9); general SE(ŷ at x0) formula
  (Step 11); SE(α) as the x0=0 special case (Step 12); confidence-interval-vs-prediction-interval
  distinction (SE formula = uncertainty about the *line's location*, not a wider prediction
  interval for one new individual observation — that needs an extra +1 term, not derived here).
- **PAUSED right here — next step**: write Steps 7-12 into the expanded file (matching the full
  algebra-line detail already there for Steps 0-6) — covered conversationally but not yet
  transcribed. Then continue to Steps 13-14 (t-statistic, p-value), then finally apply the whole
  derivation to real POWERGRID eta0=2.0 data (Part 2 of `52_alpha_beta_concept_and_powergrid.ipynb`
  — still not started).
- Full context (including everything needed to continue with zero loss) is in
  `memlabs/50d_full_recap_seed.md` and `memlabs/52_mathmode_session_handoff.md`.

## Session/tooling note — WSL + cross-session messaging

- Set up WSL (Ubuntu) + VS Code WSL extension specifically to get genuine cross-session messaging
  (confirmed NOT available on native Windows — this main session cannot use `/list-agents` or
  `SendMessage` to peer sessions at all, confirmed empirically). Node/Claude CLI already present
  in WSL; repo reachable at the same path (`/mnt/c/Users/Saurav/CodePonting`, same files, no
  sync-drift risk). Plan: this native-Windows session = "master backup" thread; a WSL VS Code
  instance = orchestration hub, spawning its own independent "math mode" WSL peer session.
- A background subagent named "math-mode" was also spawned earlier from this session (via the
  Agent tool, parent-child relationship, not true peer messaging) — seeded with the same alpha/
  beta context. Superseded by the WSL plan for anything needing genuine two-way sync, but still
  reachable via SendMessage-by-agentId from this session if needed.

## Housekeeping — 2026-08-23 (math-mode VM session)

- Renamed "SS"/"save state" → "SIF"/"save information" across all 6 CLAUDE.md files on the VM
  (main + kite_oracle_live_trading x2 + kite_oracle_papertrading + backtesting), incl.
  `kbss`→`kbsif` and `SSD`→`SIFD` in the main file. Verified no leftover bare SS/ss matches.
- Fixed the PostToolUse `log_modified.py` hook (was relative-path, broke on cwd change) —
  switched to absolute path in `settings.local.json`.
- Added VM-hostname skip to `git_sync_check_stop.sh` — sync reminder no longer fires on the VM
  itself (primary workspace), still fires on desktop/laptop.
- Set up project memory for the first time (`~/.claude/projects/-home-ubuntu-CodePonting/memory/`)
  — `MEMORY.md` index + first entry (`parked_prediction_interval_position_sizing`, mirrored as
  TODO.md's F9).

## Known Issues

- None new beyond what's documented above. Prior known issues (TODO.md glossary SL/TP note,
  ma_30_rejection_v1.py's missing EOD entry-skip) still carried over, unchanged.
