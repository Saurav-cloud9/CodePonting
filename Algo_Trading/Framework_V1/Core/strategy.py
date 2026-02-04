"""
STRATEGY MODULE

Responsibility:
- Define pure signal logic.
- Input: data up to current time + parameters.
- Output: trading signals (buy/sell/hold).

Rules:
- NO data loading.
- NO indicator computation.
- NO execution, PnL, or portfolio state.
- NO environment awareness (backtest/paper/live).

This code must run identically in all environments.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class StrategyParams:
    lookback: int
    atr_mult: float
    min_volume: Optional[float] = None


@dataclass
class Signal:
    action: str          # "BUY", "SELL", "HOLD"
    reason: str = ""


def generate_signal(row, history, params: StrategyParams) -> Signal:
    """
    Pure strategy logic.

    Inputs:
    - row: current candle (pd.Series-like)
    - history: past candles up to now (pd.DataFrame-like)
    - params: strategy parameters

    Output:
    - Signal(action, reason)

    Rules:
    - No future access
    - No execution logic
    - No portfolio state
    """

    if len(history) < params.lookback:
        return Signal("HOLD", "insufficient_history")

    # Example placeholder logic (to be replaced with your bounce logic)
    if row["close"] < history["close"].tail(params.lookback).min():
        return Signal("BUY", "mean_reversion_break")

    return Signal("HOLD", "no_edge")
