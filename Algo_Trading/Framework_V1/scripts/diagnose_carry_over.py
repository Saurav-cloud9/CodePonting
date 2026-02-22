"""
DIAGNOSTIC SCRIPT: Overnight / Month-Boundary Carry-Over Analysis
==================================================================

Purpose:
    Verify whether Framework_V1's continuous processing generates signals
    whose ENTRY CANDLE falls on a different month than the RECLAIM CANDLE (j).
    These are "carry-over" signals that v1.4.5 would have silently dropped
    because it slices data month-by-month, and once next_candle_idx >= n
    (the month's last index), it breaks without appending the signal.

Steps executed (READ-ONLY -- no files modified):
    1. Load full TATASTEEL parquet + compute indicators (same pipeline as run_backtest.py)
    2. Run augmented signal detection that records:
         touch_idx   = candle i  (MA20 touch with volume filter)
         reclaim_idx = candle j  (first close > ma_touch)
         entry_idx   = j + 1    (the candle whose open is the entry price)
    3. For each signal, compare:
         a. DATE boundary: date(entry) != date(reclaim)  -- overnight carry-over
         b. MONTH boundary: month(entry) != month(reclaim) -- v1.4.5 would have DROPPED this
    4. Print count of month-boundary carries and their specific timestamps.
    5. Report whether eliminating month-boundary carries would close the ~19-trade gap.

Usage (from Framework_V1 root):
    python scripts/diagnose_carry_over.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from core.indicators import add_intraday_indicators, compute_daily_mas, add_atr

# ------------------------------------------------------------------
# CONFIG  (mirrors run_backtest.py)
# ------------------------------------------------------------------
SCRIPT_DIR        = Path(__file__).parent
BASE_DIR          = SCRIPT_DIR.parent
DATA_PATH         = BASE_DIR / "data/historical/intraday_5min/TATASTEEL.parquet"
VOLUME_MULTIPLIER = 1.2
LOOKAHEAD         = 3   # candles j can look ahead from i
ATR_CONFIGS_COUNT = 4   # run_backtest.py runs 4 ATR configs


# ------------------------------------------------------------------
# AUGMENTED SIGNAL DETECTOR
# Returns every signal with extra fields:
#   touch_idx, reclaim_idx, entry_idx,
#   touch_dt, reclaim_dt, entry_dt
# ------------------------------------------------------------------
def detect_signals_augmented(df):
    """
    Mirrors strategy.generate_signals() exactly, but also records the
    touch candle index and reclaim candle index so we can check date/month
    boundaries.
    """
    n         = len(df)
    ma20      = df["ma20"].to_numpy()
    avg_vol   = df["avg_volume"].to_numpy()
    vol       = df["volume"].to_numpy()
    low       = df["low"].to_numpy()
    close_arr = df["close"].to_numpy()
    open_arr  = df["open"].to_numpy()
    dt_arr    = df["datetime"].to_numpy()

    raw_signals = []

    for i in range(0, n - 3):
        if np.isnan(ma20[i]):
            continue

        # Volume filter
        if not np.isnan(avg_vol[i]):
            if vol[i] < avg_vol[i] * VOLUME_MULTIPLIER:
                continue

        # Touch MA20
        if low[i] <= ma20[i]:
            ma_touch = ma20[i]

            for j in range(i, min(i + LOOKAHEAD + 1, n)):
                if close_arr[j] > ma_touch:
                    next_idx = j + 1
                    if next_idx >= n:
                        break

                    raw_signals.append({
                        "touch_idx":   i,
                        "reclaim_idx": j,
                        "entry_idx":   next_idx,
                        "touch_dt":    pd.Timestamp(dt_arr[i]),
                        "reclaim_dt":  pd.Timestamp(dt_arr[j]),
                        "entry_dt":    pd.Timestamp(dt_arr[next_idx]),
                        "entry_price": open_arr[next_idx],
                        "ma20":        ma_touch,
                    })
                    break

    # Deduplicate by entry time (identical to strategy.py)
    seen   = set()
    unique = []
    for s in raw_signals:
        if s["entry_dt"] not in seen:
            unique.append(s)
            seen.add(s["entry_dt"])

    return unique


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
def main():
    sep = "=" * 70
    dash = "-" * 70

    print(sep)
    print("CARRY-OVER DIAGNOSTIC  --  Framework_V1 vs v1.4.5 (TATASTEEL)")
    print(sep)

    # 1. Load + compute indicators (same pipeline as run_backtest.py)
    print("\n[1/3] Loading data and computing indicators...")
    df = pd.read_parquet(DATA_PATH)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    df = add_intraday_indicators(df)
    df = compute_daily_mas(df)
    df = add_atr(df)
    print(f"      Rows: {len(df):,}  |  "
          f"{df['datetime'].min().date()} -> {df['datetime'].max().date()}")

    # 2. Detect all signals (augmented)
    print("\n[2/3] Running augmented signal detection...")
    signals = detect_signals_augmented(df)
    print(f"      Total unique signals: {len(signals)}")

    # 3. Classify each signal
    print("\n[3/3] Classifying signals by date/month boundary...")

    for s in signals:
        touch_d   = s["touch_dt"]
        reclaim_d = s["reclaim_dt"]
        entry_d   = s["entry_dt"]

        # Day boundary: entry is on a different calendar date than the touch
        s["touch_to_entry_day_cross"]   = touch_d.date()   != entry_d.date()
        s["reclaim_to_entry_day_cross"] = reclaim_d.date() != entry_d.date()

        # Month boundary: entry is in a different (year, month) than reclaim
        s["month_boundary_carry"] = (
            (reclaim_d.year, reclaim_d.month) != (entry_d.year, entry_d.month)
        )

    sig_df = pd.DataFrame(signals)

    # -- Summary counts
    total               = len(sig_df)
    day_carry           = int(sig_df["reclaim_to_entry_day_cross"].sum())
    month_carry         = int(sig_df["month_boundary_carry"].sum())
    same_day_same_month = total - day_carry

    print(f"\n{dash}")
    print(f"  Total signals (Framework_V1, no filter):   {total:>6}")
    print(f"  Entry same day as reclaim (intraday):      {same_day_same_month:>6}")
    print(f"  Entry on DIFFERENT day (any):              {day_carry:>6}  (overnight carry)")
    print(f"  Entry in DIFFERENT MONTH than reclaim:     {month_carry:>6}  <- v1.4.5 would DROP these")
    print(f"{dash}")

    # -- Month-boundary carry-over details
    mb_carries = sig_df[sig_df["month_boundary_carry"]].copy()
    if len(mb_carries) > 0:
        print(f"\nMONTH-BOUNDARY CARRY-OVER SIGNALS ({len(mb_carries)} total):")
        print("  These are entries where the reclaim candle was in month M")
        print("  but the entry candle is in month M+1.")
        print()
        hdr = f"  {'#':<5} {'Reclaim candle (j)':<32} {'Entry candle (j+1)':<32} {'Entry price':>12}"
        print(hdr)
        print("  " + "-" * (len(hdr) - 2))
        for row_num, (_, row) in enumerate(mb_carries.iterrows(), start=1):
            print(f"  {row_num:<5} "
                  f"{str(row['reclaim_dt']):<32} "
                  f"{str(row['entry_dt']):<32} "
                  f"{row['entry_price']:>12.2f}")
    else:
        print("\n  No month-boundary carry-over signals found.")

    # -- Gap analysis
    print(f"\n{dash}")
    print("GAP ANALYSIS")
    print(f"{dash}")
    print(f"  Observed trade gap (Framework_V1 - v1.4.5):   ~19 trades")
    print(f"  Month-boundary carry-over signals found:        {month_carry}")
    estimated_trade_impact = month_carry * ATR_CONFIGS_COUNT
    print(f"  x {ATR_CONFIGS_COUNT} ATR configs  =>  estimated trade delta:  {estimated_trade_impact}")

    if abs(estimated_trade_impact - 19) <= 3:
        verdict = "HYPOTHESIS CONFIRMED: removing month-boundary carry-overs\n" \
                  "    would account for the observed ~19-trade gap."
    elif estimated_trade_impact > 19:
        verdict = f"Impact ({estimated_trade_impact}) EXCEEDS gap (19).\n" \
                  "    Month-boundary carries are more than needed -- there may be\n" \
                  "    an offsetting factor (e.g. some carries replace other signals)."
    else:
        verdict = f"Impact ({estimated_trade_impact}) is LESS than gap (19).\n" \
                  "    Month-boundary carries alone don't explain the full gap.\n" \
                  "    Other sources of divergence may exist."

    print(f"\n  >> {verdict}")

    # -- Day-boundary breakdown (informational)
    print(f"\n{dash}")
    print("DAY-BOUNDARY BREAKDOWN (informational -- both systems allow these)")
    print(f"{dash}")
    day_only = sig_df[sig_df["reclaim_to_entry_day_cross"] & ~sig_df["month_boundary_carry"]]
    print(f"  Signals with overnight carry (same month, different day): {len(day_only)}")
    print("  NOTE: v1.4.5 also allows these within a month -- NOT the source of the gap.")

    # -- Save detailed CSV for further inspection
    out_path = BASE_DIR / "outputs/trades/carry_over_diagnostic.csv"
    sig_df.to_csv(out_path, index=False)
    print(f"\n  Detailed signal table saved -> {out_path}")
    print(f"{dash}\n")


if __name__ == "__main__":
    main()
