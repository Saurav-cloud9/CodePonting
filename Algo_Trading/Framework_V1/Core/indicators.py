"""
INDICATORS MODULE

Responsibility:
- Compute reusable features from raw price/volume data.
- Examples: MA, ATR, volatility, regime labels.

Rules:
- Deterministic and vectorizable.
- No strategy logic.
- No execution or portfolio awareness.
- Outputs are cached to disk (Parquet).

Used by:
- Backtests
- Paper trading
- Live trading
"""
