"""
SIMULATED BROKER ADAPTER

Responsibility:
- Simulate order execution.
- Apply slippage, latency, and fill rules.
- Return fills to the engine.

Rules:
- No strategy decisions.
- No market data access.
- Deterministic behavior when configured.

Used in:
- Backtesting
- Paper trading
"""
