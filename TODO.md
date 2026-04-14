# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# Update: replace completed items, add new ones at bottom.
# When done → move to PROGRESS.md as one line, delete from here.
# ─────────────────────────────────────────────────────────────

P1  Signal review — TATAMOTORS in progress (4 done); target 30-50 total across stocks/regimes
        Gate ordering locked: G1→G2→G3→G4→G5 (G2=approach direction, G3=pullback quality)
        Next session: discuss G3 sub-gate split with Claude.ai Opus
          → #04 pullback_bars depends on pullback (G2 gates it)
          → #05 shoot_depth, #06 touch_body_pct, #07 wick_defence_ratio = touch candle quality
          → may need to split G3 into two sub-gates or rename
        Also discuss: EOD+ charge-adjusted outcome tracking

P2  TradingView revisit — paid subscription (₹5800) must be utilised actively
        Explore: replay mode for signal review, Pine Script for fv2 param visualisation
        Integrate TV MCP tools into signal review workflow where possible
        Do not let subscription sit idle — schedule dedicated TV session

P3  Build H5 — master combined tuner (all G1-G5 params)
        Approach: coarse Python grid search → filter by 4 conditions:
          best test PF + train PF + good signal count + stability
        Display: top combos satisfying ALL 4 conditions (not just PF rank)
        Get Sonnet/Opus spec before building

P4  Optuna joint sweep (.py script, CC terminal)
        Search space = all 12 params from master list
        Objective = maximise PF_test, enforce min signals both periods
        Includes simple position guarding (cooldown per stock)

# ── PARKED / FUTURE ───────────────────────────────────────────
# F1  CC source code exploration
# F2  GCP OAuth → SSD Google Drive sync
# F3  H2: per-stock comparison table
# F4  Signal replacement / position upgrade logic (post-WFA)
# F5  Oct 2022 per-stock WR% → contrast stock (CC script pending)
# F6  YouTube Strategy Scanner → Gemini extracts + Claude audits via API (parked, post paper-trading)
