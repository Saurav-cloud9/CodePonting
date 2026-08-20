# ─────────────────────────────────────────────────────────────────
# REGIME PREDICTOR — CANDIDATE FEATURES (prev day only)
# ─────────────────────────────────────────────────────────────────

# PRICE-BASED:
# ─────────────────────────────────────────────────────────────────
#   1. prev_close > prev_ma50        ← already tested (weak alone)
#   2. prev_close > prev_ma100
#   3. prev_close > prev_ma200
#   4. prev_close > prev_open        ← was yesterday bullish candle?
#   5. prev_week_return              ← (close - close_5d_ago) / close_5d_ago
#   6. prev_2week_return             ← 10-day momentum
#   7. prev_month_return             ← 22-day momentum
#   8. prev_close vs 52w_high        ← % below recent high
#   9. prev_close vs 52w_low         ← % above recent low

# VOLATILITY-BASED:
# ─────────────────────────────────────────────────────────────────
#   10. prev_atr_ratio               ← prev ATR / prev_close (normalized vol)
#   11. prev_range_ratio             ← (high-low)/close yesterday
#   12. prev_candle_body_ratio       ← |close-open| / (high-low)
#       → small body = indecision, large body = conviction

# TREND STRENGTH:
# ─────────────────────────────────────────────────────────────────
#   13. ma50_slope                   ← ma50_today - ma50_5d_ago (trending up?)
#   14. ma50_vs_ma100                ← ma50 > ma100 (golden cross zone)
#   15. ma50_vs_ma200                ← ma50 > ma200
#   16. price_distance_from_ma50     ← (close - ma50) / ma50 in %
#       → too far above = stretched, near = bounce zone

# VOLUME-BASED:
# ─────────────────────────────────────────────────────────────────
#   17. prev_volume_ratio            ← prev_vol / avg_vol_20d
#       → high volume up day = strong trend confirmation
#   18. prev_vol_direction           ← was high volume day up or down?

# MARKET-WIDE (Nifty50):
# ─────────────────────────────────────────────────────────────────
#   19. nifty_prev_close > nifty_ma50   ← broad market regime
#   20. nifty_prev_week_return          ← market momentum
#   21. nifty_prev_atr_ratio            ← market volatility regime
#       → high VIX-like days = avoid bounce trades

# SECTOR-LEVEL (addresses Oct 2024 problem):
# ─────────────────────────────────────────────────────────────────
#   22. sector_index > sector_ma50   ← e.g. Nifty Metal, Nifty IT
#   23. sector_prev_week_return      ← sector momentum

# ─────────────────────────────────────────────────────────────────
# 📌 CLASSIFICATION TARGET (ground truth label):
#    same_day_close > same_day_ma50 → GOOD day (1) or BAD day (0)
#
# APPROACH:
#    Start simple → test features 1-9 individually for accuracy
#    Then combine best 2-3 → aim for >65% match accuracy per stock
#    Optuna tunes thresholds once best features identified
# ─────────────────────────────────────────────────────────────────