# TODO.md — CodePonting fv2
# Max 5 items at any time. Tier structure (fixed 2026-09-20, not just raw urgency):
#   P1 = fv2 VM's own direct, active work
#   P2 = work tied to fv2 but happening in another session (math mode side-quest)
#   P3 = project-related work delegated to a peer session (cpgeneric)
#   P4/P5 = everything else, less important but still project-related
# ─────────────────────────────────────────────────────────────

# STANDING NOTE (2026-09-07): Saurav wants loop engineering applied to the max
# across CodePonting — wherever a task genuinely fits the 4-condition test
# (repeats regularly, mechanically verifiable, token budget absorbs it, agent
# has repro tools), default to proposing/building a loop rather than leaving
# it manual. Don't force-fit judgment-call work (research, signal design) —
# that stays manual per the same framework. The DS3 gap-fill/integrity monitor
# (now under P3) is the first concrete instance; keep watching for other
# qualifying candidates as they come up.

P1  Strategy raw-edge search (Algo_Trading/Framework_V2/strategies/) — ACTIVE
        2026-09-13: memlabs #54 roadmap fully detailed sub-step-by-sub-step in
        `54_...baseline.md` §3 (54c.1/54c.2 marked DONE with exact outputs, 54c.3/54c.4/54d
        laid out). India VIX fetch delegated to codeponting-2d — DONE same day
        (INDIA_VIX.parquet, 2015-02-02 to 2026-09-11, kept separate from NIFTY50.parquet
        per one-file-per-instrument convention; not needed for the current screen, just a
        filled Tier-2 gap for later). PAUSED before 54c.3 (the null-calibration+screen
        notebook, chosen pair: NIFTY trend 10d + basket dispersion) — Saurav wants to
        discuss the per-trade-vs-per-day unit-of-analysis question FIRST thing next
        session before any notebook code gets written. Proposed default (not yet agreed):
        aggregate to daily zpnl/win-rate before correlating against the daily regime
        features, matching how every CAPM alpha regression this project has ever run —
        avoids pseudo-replication from same-day trades sharing one feature value.
        2026-09-12: found+fixed a session-wide bug — basket market-factor construction
        (pd.concat of 30 stocks' daily closes) never sorted its index; 97.7% of rows were
        out of chronological order, silently corrupting pct_change() for EVERY basket-
        regressed alpha this session. Recomputed all 14 basket-regressed rows (both master
        CSVs): 13/14 verdicts unchanged, FLAGSHIP_6BCEH_SHORT_VWAP_RSI60 corrected from
        "borderline negative" (p=0.039) to "confidently near-zero" (alpha -0.41, p=0.201) —
        now agreeing with its own NIFTY read (-0.46, p=0.150) instead of contradicting it.
        NIFTY-regressed numbers unaffected (always sorted). Added backtesting_rules.md §16
        (mandatory .sort_index() rule). FRESH_FULLDS3_BASELINE also recomputed (the offline
        DS3-replay driver already existed — kite_oracle_papertrading_archive/scripts/
        ma_30_rejection_v1_offline.py, reads the same fv2 DS3 as everything else, just
        needed its Windows paths adjusted): basket alpha -16.269→-15.174, same decisive
        verdict. All 15 basket-regressed rows now fixed, nothing deferred.
        2026-09-10: built flagship/11 (6BCEH-Short + VWAP + RSI>60) fresh on full 30-stock
        DS3 — reproduces the one lead from the recovered claude.ai session. Still fails
        viability (raw-best ZPF 0.927 edge/suspect, healthy 0.899) BUT it's the first
        variant this session with alpha ≈ 0 (basket -0.40, NIFTY +0.03, CIs cross zero) —
        residual loss is beta drag (short-biased vs NIFTY's +253% cumulative drift), not
        negative skill. Logged as FLAGSHIP_6BCEH_SHORT_VWAP_RSI60 (RAW_SCREEN) in all 4
        master CSVs. Long beta-drag intuition thread — see PROGRESS_HISTORY 2026-09-10.
        2026-09-09: strategies/flagship/ created (01-07 = plan + 6 locked copies). Built+ran
        6-Bar-Close-Extreme siblings 08-10 (6BCEL-Short, 6BCEH-Long, 6BCEL-Long) — ALL 3
        RULED OUT. Formalized Screening Tiers (FULL_RIGOR/RAW_SCREEN/REFERENCE,
        backtesting_rules.md §12) + `screen_tier` column on all 4 master CSVs. 6BCE family
        closed out. Full detail: flagship/01_plan.md, PROGRESS_HISTORY 2026-09-09.
        2026-09-07/08: SMC Liquidity 4-variant matrix on DS3 — ALL 4 RULED OUT. Removed
        backtesting_rules.md §12's "ruled out" gate entirely (0.85->0.75->removed).
        2026-09-16/17: memlabs #54's dispersion lead RULED OUT (OOS test on
        `54c_oos_dispersion_gate.py` shows the Q5 threshold gate doesn't generalize).
        All 12 built candidate features screened (individual + widened max-of-12,
        circular-shift primary) — none survive. Added `volume_surge`, `india_vix_level`
        (`54c_add_volume_vix.py`), `us_overnight_return` (`54e_fetch_us_overnight.py`,
        S&P 500 close-to-close, correctly timezone-aligned to next India trading day) —
        all screened, all fail. Top-4 pairwise AND-rule interaction (24 combos,
        max-of-24 corrected) found ONE survivor (dispersion-low x volume_surge-high,
        r=-0.0709) — OOS-tested (`54d_oos_disp_volsurge.py`): decayed from 3.7x-worse
        (full sample) to 1.32x (test) to ~0x (test's own second half) — RULED OUT, not
        stable. True XOR-shaped test (6 pairs, `54d_xor_flags_top4.py`) also found
        nothing. `#54`'s market-wide daily-regime-filter search is now exhausted for
        this variant on every feature/combination tried.
        2026-09-19/20: NEXT STEP AGREED — escalate from manual Pearson-r/threshold
        screening to a fitted multi-feature regression (features -> predict daily_zpnl),
        the "last resort" per the design spec's complexity cap. Ridge/lasso become
        directly relevant here (correcting for overfitting risk across many correlated
        features, unlike the 1-2-feature threshold approach where they didn't apply).
        Saurav building intuition via math mode (see P2) + video-based learning before
        writing any regression code — do not start this until he brings the concepts
        back here to test on real data.
        Lower priority, parked behind the above: FVG (smc/ index 05), then OB (index 06);
        fold "SL>TP = weak edge" pattern into backtesting_rules.md.
        Full detail: PROGRESS_HISTORY.md 2026-09-07 through 2026-09-19/20 entries.

P2  Math mode — regression escalation theory (side-quest, tied to P1)
        2026-09-19/20: Saurav discussing multi-feature regression + ridge/lasso concepts
        with `math mode`, informed by video-based learning (no working YouTube-transcript
        tool available on this VM — cloud-provider IPs are blocked by YouTube's transcript
        API; Saurav pastes transcript text/timestamps manually instead). Goal: build enough
        intuition on ridge/lasso (regularization, bias-variance tradeoff) to decide whether
        and how to escalate #54's screening from manual Pearson-r/threshold rules to a
        fitted multi-feature regression predicting daily_zpnl. Bring concepts back to fv2
        to test on the actual `54c_trade_log_with_features.csv` data once solid — nothing
        to build here yet.

P3  CP Generic — project-related delegated work
        1. Beta-drag hedge simulation for FLAGSHIP_6BCEH_SHORT_VWAP_RSI60 (delegated
           2026-09-19, deliberately lower priority than alpha search — hedging can't
           create alpha, only remove a structural cost). Theoretical ceiling: net_zpnl
           -2436.26 -> ~-1042.49 (alpha-only) with a perfect hedge. First pass (daily-
           resolution, `memlabs/hedge_01_daily_combined_capm.py`) recovered 79.4% of the
           drag: net_zpnl -> -1329.59, beta -4.355 -> -1.185 (vs basket). Also caught a
           real bug: `memlabs/54b_table3_sl_sweep.py` still runs the pre-§16-fix
           (unsorted pd.concat) basket_daily construction — doesn't affect the SL=1.5
           lock (ZPF-based), but needs patching before reuse for anything alpha-related.
           PAUSED 2026-09-20 — cpgeneric told to hold, no further action, until Saurav
           reviews directly (his own desktop session). Next step when resumed: intraday-
           NIFTY fetch (KiteConnect) to isolate the ₹287 shortfall's cause (daily-
           resolution timing mismatch vs NIFTY/basket instrument mismatch). Full detail:
           memory/project_long_hedge_leg_parked.md.
        2. DS3 monthly gap-fill automation + data-integrity monitor — delegated
           2026-09-12: algorithmic split-ratio heuristic (KiteConnect has no corp-actions
           API), scheduled 2 AM IST. Original gap-fill plan (2026-09-06, sparked by a
           loop-engineering discussion) drafted but not yet built: new script (not the
           old append_ds3_2026_gap.py) fetching directly via KiteConnect SDK, auto-detect
           last date per symbol, append + recompute ma20/atr14/atr14_wilder for new rows
           only; objective gate (coverage, NaN, row-count sanity vs NSE calendar, fail
           loudly); crontab ~07:00 IST on the 1st (before monthly_reconciliation.py's
           09:30 run). Saurav had follow-up questions on how monthly_reconciliation.py
           itself works before proceeding — resume there. Check status via `cpdc`
           (reads ds3_integrity/known_issues.json's pending lists).

P4  Kite bot (market hours only) — running live daily, resume next market session
        2026-07-28 progress: 3 real mid-session restarts (09:51/10:14/10:35) with open
        positions live - all successful, fully validates the weekend's catch-up/discard fix.
        Saurav validating live trades + weekly recon with VM CC directly (not this session).
        Older items still open: MA20/ATR14+touch-eval logging not yet added; ATR14 divergence
        question.

P5  Test weak Pearson-r signal(s) through actual RR/SL-TP exits (not yet started)
        Raised 2026-08-16: everything tested so far (Model C, naive baseline) captures the full
        day's raw return with no exit structure. A sub-50% hit rate can still be profitable with
        the right ATR-based SL/TP (this project's actual convention) — genuinely untested axis,
        separate from model/feature choice.

# ── PARKED / FUTURE ───────────────────────────────────────────
# Segregated 2026-09-23: pre-live items (must be tested/deployed before real money) vs
# generic/conceptual items (not mandatory for the live bot). IDs unchanged from before
# the split — F9 is cross-referenced in PROGRESS_HISTORY.md, kept stable.

# ── Pre-live required (paper-bot testable, gates before real-money deployment) ──
F14 Drawdown circuit breaker (added 2026-09-23) — halt new entries when running daily
        zpnl crosses a threshold; let already-open positions ride to their existing
        SL/TP, don't force-exit; reset the flag at next day's start. Control-flow can be
        validated on the paper bot NOW at qty=1 scale (threshold ~-₹100 to -₹150/day,
        matching current per-trade economics) — logic is identical regardless of ₹
        magnitude, so no need to pull position sizing forward just to test this. When
        real position sizing (F9) eventually lands, just rescale the threshold number.
        Sparked by reviewing a trading-math-fundamentals doc's risk-management section
        against ma_30_rejection_v1_live.py — confirmed no drawdown/loss-streak halt
        logic exists in the live bot today.
F5  Portfolio construction — capital allocation across stocks
F9  Prediction-interval position sizing — once a model is validated/live, use OLS prediction
        intervals (wider than SE, includes individual-point scatter) for position sizing/risk
        bounding. Detail: memory/parked_prediction_interval_position_sizing.md

# ── Generic / conceptual (revisit when relevant, not a live-deployment gate) ──
F1  Single-stock trade dump (TATAMOTORS) — verify SHORT calculations
F2  Nifty Futures — Beluga signal on Nifty (post HMA Bounce investigation)
F3  Volume Spike Exhaustion — hypothesis parked
F4  Stock diversity analysis — check if 5 stocks fire on same days
F6  Insurance review
F7  51_least_squares_3d.md (memlabs) — Least Squares 2D->3D plane fit writeup, parked mid-2026-08
F8  Full 90-combo SL/TP sweep x 6 ATR variants via Grok — nice-to-have, not priority
F10 Model C 3D time-evolution visualization (parked 2026-08-31) — lag_1 vs tick(day) vs actual
        return, colored by correct/incorrect, to watch the online-learning boundary (w, b) drift
        over POWERGRID's 11-year history. Conceptually interesting (Model C's coefficients
        change every tick, unlike Model B's fixed fit) but not decision-driving — POWERGRID
        already concluded no significant edge (alpha p=0.39). Revisit only if curiosity-driven,
        not blocking #35 priority.
F11 StatQuest (Josh Starmer, YouTube) — standing reference source, explore over time. Covers
        most core ML/stats topics this project touches (regression, classification, trees,
        feature selection). First video logged: regime_model/statquest/roc_auc.md.
F12 Recon trade log persistence gap (found 2026-09-10) — the daily reconciliation
        (ma_rejection_v1_reconcile.py) only ever computes ZPnL from live_trades — the
        official-replay side (e.g. 2026-09-09: 47 trades vs live's 31, 17 official-only
        entries live never took) is used purely for bar-comparison/matched-trade price
        diffing, never persisted as its own full trade log with per-trade PnL/ZPF/ZPnL —
        unlike live trades, which do get a full CSV log. Fix: store the official-replay's
        own trade-level results (same columns as live trade logs) so official-side
        PnL/ZPF/ZPnL can be queried directly instead of only diffed against live.
F13 MemLabs #53 feature-screening -> model pipeline (FROZEN 2026-09-10) — decided not to
        retrofit; kept as a methodology reference (Pearson screening + null-intuition /
        5k-t-stat noise ruler), not the raw-price-prediction target. Superseded by #54
        (P1). Full detail: PROGRESS_HISTORY 2026-08-16 through 2026-09-10 entries.
F15 $100 Claude Code cloud session credit (claimed 2026-09-24) — Pro plan promo, separate
        from general account credits, not eligible for Projects/Routines. Cloud sessions
        run on Anthropic-hosted infra (clone of GitHub CodePonting@main), not the Oracle
        VM — can't see uncommitted VM changes or anything outside the repo. Good fit:
        running extended sweep/backtest scripts unattended once code/data is committed.
        Deliberately parked unused for now. EXPIRES 11:59 PM PT, Nov 5, 2026 — flag to
        Saurav by ~Oct 22, 2026 if still unused. Detail: memory/project_cloud_session_credits.md

# ── GLOSSARY ───────────────────────────────────────────────────
6BCEH    = 6-Bar Close Extreme HIGH (close[i] == max of last 6 closes). 6BCEH-Short
           (reversal-from-high fade) is the originally-tested/locked variant, formerly
           just called "6bce" — relabeled 2026-09-09 once its untested LOW-triggered
           sibling (6BCEL) surfaced, to avoid ambiguity. 6BCEH-Long untested, ruled out
           2026-09-09 (flagship/09).
6BCEL    = 6-Bar Close Extreme LOW (close[i] == min of last 6 closes) — the other half
           of the 6BCE family. Both 6BCEL-Short (breakdown continuation) and 6BCEL-Long
           (reversal/bounce) ruled out 2026-09-09 (flagship/08, /10).
beta drag = the `beta_capm × Σ(daily market returns)` term in the CAPM decomposition
           `net_zpnl = alpha_cumulative + beta × Σx`. For a short-biased strategy (beta<0)
           over an up-trending backtest period (Σx>0) this term is negative and can be the
           entire net loss even at alpha ≈ 0. Not a signal-quality problem — a structural
           market-exposure cost. Addressed via regime filter or hedge leg, not via better
           entries. Full worked example: PROGRESS_HISTORY 2026-09-10.

n        = number of trading days feeding a CAPM/alpha regression (daily-aggregated zpnl
           vs daily market return) — matches the clean "df = n-2" derivation notation.
           capm()'s own n variable already meant this correctly; no code change needed there.
n_trades = trade count (matches every report's own column, e.g. monthly_recon_*.csv —
           metrics()'s n_trades=len(trades_df)). A completely different count from n above
           (e.g. 1014 trades roll up into n=21 days for FRESH_6BCE_V0's August 2026
           regression). Flipped 2026-09-06 (was n=trades/n_days=days) after the original
           pairing caused real confusion mid-derivation-walkthrough; metrics()'s dict key
           renamed n -> n_trades to match.
HMM      = Hidden Markov Model — latent persistent regime state + transition matrix;
           purpose-built formalization of "regimes". Discussed 2026-09-15 as a later
           escalation for #54 (more params than a threshold gate, same scarce sample).
GARCH    = Generalized Autoregressive Conditional Heteroskedasticity — models volatility
           persistence (second moment), not direction. Trailing realized vol captures most
           of its information at zero fitted parameters.
SNR      = signal-to-noise ratio — for #54's screen, r=0.0565 -> R^2 ~ 0.3%: the binding
           constraint on any model family, not the functional form.
ACF1     = Autocorrelation Function at lag 1 — Pearson r between a series and its own
           value one step (one day, here) earlier. Not a new tool: literally the same r
           used throughout #54, applied to a series against a shifted copy of itself.
           dispersion acf1=0.42 (persists day to day -> circular-shift null needed);
           daily_zpnl acf1=0.018 (~iid, plain shuffle null is fine for it).
