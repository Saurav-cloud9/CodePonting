"""
INDICATOR PRECOMPUTATION SCRIPT

Responsibility:
- Read raw historical data.
- Compute all technical indicators.
- Save to indicator cache (Parquet).

Usage:
    python compute_indicators.py --source historical --output indicators

Output:
    data/indicators/{symbol}_indicators.parquet
"""