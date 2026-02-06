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

# core/indicators.py
# Extracted + framework-aligned indicator functions

import numpy as np
import pandas as pd


# ---------- Intraday indicators ----------
def add_intraday_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # MA20 used for bounce touch detection
    df["ma20"] = df["close"].rolling(20).mean()

    # Volume baseline
    df["avg_volume"] = df["volume"].rolling(20).mean()

    return df


# ---------- Daily trend MAs ----------
def compute_daily_mas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["ma50"] = df["close"].rolling(50).mean()
    df["ma100"] = df["close"].rolling(100).mean()
    df["ma200"] = df["close"].rolling(200).mean()

    return df[["date", "ma50", "ma100", "ma200"]]


# ---------- ATR ----------
def add_atr(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    df = df.copy()

    prev_close = df["close"].shift(1)

    df["high_low"] = df["high"] - df["low"]
    df["high_prev_close"] = (df["high"] - prev_close).abs()
    df["low_prev_close"] = (df["low"] - prev_close).abs()

    df["true_range"] = df[
        ["high_low", "high_prev_close", "low_prev_close"]
    ].max(axis=1)

    df[f"atr_{window}"] = df["true_range"].rolling(window).mean()

    # Clean temp cols
    df.drop(
        columns=["high_low", "high_prev_close", "low_prev_close"],
        inplace=True
    )

    return df

"""
# TODO: Regime filter to be introduced along with GSS in the future
# ---------- Regime helper (used later in metrics/portfolio) ----------
def categorize_price_vs_mas(df: pd.DataFrame) -> str:
    valid = df.dropna(subset=["ma50", "ma100", "ma200"])
    if valid.empty:
        return "UNKNOWN"

    last = valid.iloc[-1]
    p = last["close"]

    if p > last["ma50"] and p > last["ma100"] and p > last["ma200"]:
        return "STRONG_UP"
    if p < last["ma50"] and p < last["ma100"] and p < last["ma200"]:
        return "STRONG_DOWN"
    if p > last["ma50"]:
        return "UP"
    if p > last["ma200"]:
        return "SIDEWAYS"

    return "DOWN"
"""