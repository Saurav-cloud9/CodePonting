# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

# STANDING NOTE (2026-09-07): Saurav wants loop engineering applied to the max
# across CodePonting — wherever a task genuinely fits the 4-condition test
# (repeats regularly, mechanically verifiable, token budget absorbs it, agent
# has repro tools), default to proposing/building a loop rather than leaving
# it manual. Don't force-fit judgment-call work (research, signal design) —
# that stays manual per the same framework. P5 (DS3 gap-fill) is the first
# concrete instance; keep watching for other qualifying candidates as they
# come up (e.g. recurring data checks, sweep re-runs with an objective gate).

P1  Strategy raw-edge search (Algo_Trading/Framework_V2/strategies/) — ACTIVE
        2026-09-09: strategies/flagship/ created (SMC-style numbered files, 01-07 = plan +
        6 locked copies, originals untouched). Built+ran the 3 untested 6-Bar-Close-Extreme
        siblings (08 6BCEL-Short, 09 6BCEH-Long, 10 6BCEL-Long) — ALL 3 RULED OUT, decisive
        negative alpha (CIs clear of zero), same pattern as Liquidity. Fixed 6bce naming to
        6BCEH across master CSVs (disambiguates from the new 6BCEL family). Also formalized
        Screening Tiers (FULL_RIGOR/RAW_SCREEN/REFERENCE, backtesting_rules.md §12) + added
        `screen_tier` column to all 4 master CSVs — makes explicit that only raw-promising
        variants get the deep Table 3 treatment. Decided against a Table 3 follow-up on
        6BCEL-Short (its RAW_SCREEN ZPF already sits below the locked 6BCEH-Short's FULL_RIGOR
        ZPF) — 6BCE family closed out. Full detail: flagship/01_plan.md, master_nifty.csv/
        master_basket.csv (both smc/ and flagship/).
        2026-09-07/08: SMC Liquidity concept fully tested — recovered claude.ai session's
        prior concepts/backtest results into smc/, then built+ran the full 4-variant matrix
        ({swing low,swing high} x {long,short}) fresh against DS3. ALL 4 RULED OUT, same
        decisive-negative-alpha pattern. Full detail: smc/04_liquidity_findings.md. Also:
        removed backtesting_rules.md §12's "ruled out" gate entirely (0.85->0.75->removed) —
        compute Table 2/3 + alpha for every combo now, no RULED_OUT placeholders.
        Immediate next steps, in order:
        1. FVG (index 05 in smc/) — same 4-variant-matrix discipline as Liquidity, next per
           smc/01_plan.md's ordering.
        2. Then OB (index 06).
        3. Resend/manually fix the DS3 data bug (ICICIBANK/ITC/SBIN zero-filled OHLC, 2015) —
           direct Kite Connect API confirmed working (not Kite MCP's historical_data).
        4. Full diff-review of strategies/_archive_pre_strategies_consolidation/ — not urgent.
        5. Live bot core file renaming for naming consistency — deferred "to another day."
        Full detail: PROGRESS_HISTORY.md 2026-09-07/08/09 entries.

P2  MemLabs feature screening -> model pipeline — new plan doc: memlabs/53_feature_screening_
        to_model_pipeline.md. Continuation of notebook 35, not a restart.
        2026-08-16: RSI period sweep (7/9/14/21/28) done — no period beats 14 meaningfully.
        Volume (TATAMOTORS) screened — weakest candidate yet, log transform didn't help. Two
        real DS3 data bugs found+fixed along the way (INFY frozen-tick day, DIVISLAB un-split-
        adjusted day). Model C (separate deep-dive, notebooks 50/50b/50c, now also eta0=5.0
        confirmatory run) concluded no transferable edge exists on raw signals either.
        2026-08-30 methodology note: don't limit screening to single-feature Pearson r — always
        cross-check any 2-feature combination with a 2D scatter (XOR/interaction-effect lesson).
        2026-09-01/02: #53 Step 0 done — recapped as `53_step0_recap_pearson_r_screening.ipynb`,
        confirmed Aug-10 DS3 update doesn't affect #35's results (raw close byte-identical).
        DECISION NEEDED before Step 1: #53 as currently scoped (target=close_log_return, feeds
        Models A/B/C raw-price-prediction) does NOT directly serve the actual priority — the
        MA-bounce strategy needs a REGIME FILTER (target = strategy's own trade win/loss
        outcomes) to push ZPF above 1.0 BEFORE alpha/beta testing is meaningful. Decide next
        session: redirect #53's target to the strategy's own outcomes, or run both as separate
        parallel threads.

P3  Kite bot (market hours only) — running live daily, resume next market session
        2026-07-28 progress: 3 real mid-session restarts (09:51/10:14/10:35) with open
        positions live - all successful, fully validates the weekend's catch-up/discard fix.
        Saurav validating live trades + weekly recon with VM CC directly (not this session).
        Older items still open: MA20/ATR14+touch-eval logging not yet added; ATR14 divergence
        question.

P4  Test weak Pearson-r signal(s) through actual RR/SL-TP exits (not yet started)
        Raised 2026-08-16: everything tested so far (Model C, naive baseline) captures the full
        day's raw return with no exit structure. A sub-50% hit rate can still be profitable with
        the right ATR-based SL/TP (this project's actual convention) — genuinely untested axis,
        separate from model/feature choice.

P5  DS3 monthly gap-fill automation — new, not yet started (2026-09-06)
        Sparked by a "loop engineering" discussion (X/LinkedIn post) — good-fit candidate per
        the 4-condition test (repeats monthly, mechanically verifiable, no judgment call).
        No prior recurring process exists — CCG/Grok did July+Aug fills as one-off manual
        delegations (Grok subscription now paused). Plan drafted, not yet built:
        1. New script (not the old append_ds3_2026_gap.py, which only appends pre-staged JSON
           from manual Kite MCP calls) — fetch directly via KiteConnect SDK using the bot's
           existing auto-refreshing token (same auth as monthly_reconciliation.py), auto-
           detect last date per symbol, append (never overwrite), recompute ma20/atr14/
           atr14_wilder for new rows only. Same for NIFTY50.parquet.
        2. Objective gate: per-symbol continuous coverage to month-end, no NaN gaps outside
           warmup, row count sanity vs NSE holiday calendar. Fail loudly, not silently.
        3. Schedule via plain crontab (~07:00 IST on the 1st) — well before
           monthly_reconciliation.py's 09:30 IST run. Note: recon does NOT read DS3 files
           directly (independent KiteConnect fetch) — running DS3 first is good discipline
           for consistency, not a hard blocking dependency.
        4. Log each run (rows added, date range, gate pass/fail) to a dedicated file; reuse
           the bot's existing ntfy alert channel on gate failure.
        Saurav has follow-up questions on how monthly_reconciliation.py itself works before
        proceeding — resume there next session.

# ── PARKED / FUTURE ───────────────────────────────────────────
F1  Single-stock trade dump (TATAMOTORS) — verify SHORT calculations
F2  Nifty Futures — Beluga signal on Nifty (post HMA Bounce investigation)
F3  Volume Spike Exhaustion — hypothesis parked
F4  Stock diversity analysis — check if 5 stocks fire on same days
F5  Portfolio construction — capital allocation across stocks
F6  Insurance review
F7  51_least_squares_3d.md (memlabs) — Least Squares 2D->3D plane fit writeup, parked mid-2026-08
F8  Full 90-combo SL/TP sweep x 6 ATR variants via Grok — nice-to-have, not priority
F9  Prediction-interval position sizing — once a model is validated/live, use OLS prediction
        intervals (wider than SE, includes individual-point scatter) for position sizing/risk
        bounding. Detail: memory/parked_prediction_interval_position_sizing.md
F10 Model C 3D time-evolution visualization (parked 2026-08-31) — lag_1 vs tick(day) vs actual
        return, colored by correct/incorrect, to watch the online-learning boundary (w, b) drift
        over POWERGRID's 11-year history. Conceptually interesting (Model C's coefficients
        change every tick, unlike Model B's fixed fit) but not decision-driving — POWERGRID
        already concluded no significant edge (alpha p=0.39). Revisit only if curiosity-driven,
        not blocking #35 priority.
F11 StatQuest (Josh Starmer, YouTube) — standing reference source, explore over time. Covers
        most core ML/stats topics this project touches (regression, classification, trees,
        feature selection). First video logged: regime_model/statquest/roc_auc.md.

# ── GLOSSARY ───────────────────────────────────────────────────
6BCEH    = 6-Bar Close Extreme HIGH (close[i] == max of last 6 closes). 6BCEH-Short
           (reversal-from-high fade) is the originally-tested/locked variant, formerly
           just called "6bce" — relabeled 2026-09-09 once its untested LOW-triggered
           sibling (6BCEL) surfaced, to avoid ambiguity. 6BCEH-Long untested, ruled out
           2026-09-09 (flagship/09).
6BCEL    = 6-Bar Close Extreme LOW (close[i] == min of last 6 closes) — the other half
           of the 6BCE family. Both 6BCEL-Short (breakdown continuation) and 6BCEL-Long
           (reversal/bounce) ruled out 2026-09-09 (flagship/08, /10).

n        = number of trading days feeding a CAPM/alpha regression (daily-aggregated zpnl
           vs daily market return) — matches the clean "df = n-2" derivation notation.
           capm()'s own n variable already meant this correctly; no code change needed there.
n_trades = trade count (matches every report's own column, e.g. monthly_recon_*.csv —
           metrics()'s n_trades=len(trades_df)). A completely different count from n above
           (e.g. 1014 trades roll up into n=21 days for FRESH_6BCE_V0's August 2026
           regression). Flipped 2026-09-06 (was n=trades/n_days=days) after the original
           pairing caused real confusion mid-derivation-walkthrough; metrics()'s dict key
           renamed n -> n_trades to match.
