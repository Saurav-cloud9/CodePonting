# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  MemLabs feature screening -> model pipeline — new plan doc: memlabs/53_feature_screening_
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

P2  Kite bot (market hours only) — running live daily, resume next market session
        2026-07-28 progress: 3 real mid-session restarts (09:51/10:14/10:35) with open
        positions live - all successful, fully validates the weekend's catch-up/discard fix.
        Saurav validating live trades + weekly recon with VM CC directly (not this session).
        Older items still open: MA20/ATR14+touch-eval logging not yet added; ATR14 divergence
        question.

P3  Test weak Pearson-r signal(s) through actual RR/SL-TP exits (not yet started)
        Raised 2026-08-16: everything tested so far (Model C, naive baseline) captures the full
        day's raw return with no exit structure. A sub-50% hit rate can still be profitable with
        the right ATR-based SL/TP (this project's actual convention) — genuinely untested axis,
        separate from model/feature choice.

P4  Exit-management trials (Framework_V2/scripts/trials/exit_management/) — ongoing
        2026-09-02/03: August 2026 DS3 gap-fill DONE (30 stocks + NIFTY50 daily, verified
        pre-Aug data byte-identical). Built memory-safe baseline (01) + SL6/TP6 variant (02)
        offline engines — fixed a real OOM bug (pd.concat+to_dict('records') on 6.25M bars
        crashed the VM for 40min); rewrote using per-stock numpy arrays (known-good pattern
        from baseline_reserve_lock/sl_tp_sweep_baseline_short.py), process_bar()/core.py
        logic untouched. Ran a 4-way August comparison (live/reconcile/baseline/SL6-TP6) —
        found RECONCILE vs BASELINE diverge due to a real DIVISLAB split-adjustment data
        mismatch (~1.5% of bars), not a logic bug — confirmed by replaying reconcile's exact
        structure sourced from DS3 (exact match to baseline). Added volume/oi to reconcile's
        official_bars fetch (matches DS3 schema). Built two new cron jobs on the live bot VM:
        daily settled-reconcile (18:00 IST, `--settled` flag, lets same-day data settle) and
        monthly 3-way reconciliation (09:30 IST 1st-of-month, LIVE/RECONCILE/fresh-Kite-pull,
        catches retroactive corporate-action adjustments) — both validated against August.
        Next: dig into WHY the exit-management numbers themselves (ZPF<1) need improving —
        trailing stop / partial profit-taking, per the earlier diagnostic plan.

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
