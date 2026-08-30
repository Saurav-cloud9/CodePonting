# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  MemLabs Pearson's r feature screening — resume from here (notebook 35)
        2026-08-16: RSI period sweep (7/9/14/21/28) done — no period beats 14 meaningfully.
        Volume (TATAMOTORS) screened — weakest candidate yet, log transform didn't help. Two
        real DS3 data bugs found+fixed along the way (INFY frozen-tick day, DIVISLAB un-split-
        adjusted day). Model C (separate deep-dive, notebooks 50/50b/50c) concluded no
        transferable edge exists on raw signals either — reinforces this stays the priority.
        Next: screen gap-size (log(open_today/close_yesterday)) vs intraday-move as target.
        Only escalate to a full Model A/B build + WFA once something meaningfully stronger than
        RSI's current weak signal (r~=0.08, r^2<1%) turns up.

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

P4  August 2026 DS3 gap-fill — once the month closes, same CCG pattern as the July fill just
        completed (all 30 stocks + NIFTY50 daily).

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
