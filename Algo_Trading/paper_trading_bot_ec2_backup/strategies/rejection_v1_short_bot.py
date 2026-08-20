"""
rejection_v1_short_bot.py — PAPER TRADING (SHORT side)

Live paper-trading version of:
  Framework_V2/scripts/trials/baseline_explorations/ma_30_rejection_v1.py

Same variable names, same touch/entry/exit formulas as the original backtest script.
Only the driver changes: instead of looping over a full historical DataFrame
(`while i < len(df)`), each symbol keeps a running buffer of candles and this
script processes ONE new candle at a time as it arrives live from Kotak Neo.

v1 touch: clean wick-only touch from below MA20
  high >= ma20 AND open < ma20 AND close < ma20  → body stays below MA20, only wick reaches up.
SL/TP locked from v1 sweep (geomean pick): SL=2.0x · TP=4.5x → PF=1.135 · Sharpe=2.358 (DS3, 11yr)

This script only READS market data from Kotak Neo (via auth_kotak_neo.py). It never
places a real order — trades are simulated and logged to CSV as if filled.

STATUS: cannot run end-to-end yet — auth_kotak_neo.get_latest_candle() and
get_warmup_candles() are stubs pending Kotak Neo developer API access.
"""

import os
import sys
import time
import csv
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auth_kotak_neo as neo

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
TRADES_CSV = os.path.join(DATA_DIR, "trades", "rejection_v1_short_trades.csv")

SL_MULT = 2.0
TP_MULT = 4.5
EOD_HOUR = 15
MA_PERIOD = 20
ATR_PERIOD = 14
POLL_SECONDS = 300  # one 5-min candle

UNIVERSE = [
    "ADANIPORTS", "ASHOKLEY", "AXISBANK", "BAJFINANCE", "BANDHANBNK",
    "BHARTIARTL", "CIPLA", "COALINDIA", "DABUR", "DIVISLAB",
    "HDFCBANK", "HINDALCO", "ICICIBANK", "INDUSINDBK", "INFY",
    "ITC", "JSWSTEEL", "NATIONALUM", "NTPC", "ONGC",
    "PNB", "POWERGRID", "RELIANCE", "SBIN", "SUNPHARMA",
    "TATAMOTORS", "TATASTEEL", "TECHM", "VEDL", "WIPRO",
]

CAPITAL = 1_000_000
RISK_PER_TRADE = 0.01  # 1% of current equity — sizing only, not part of the original signal
equity = CAPITAL

TRADE_FIELDS = ["symbol", "touch_dt", "entry_dt", "entry", "sl", "tp", "exit_dt", "qty", "pnl", "outcome"]


# ---------- Indicators (same formulas as core/indicators.py, computed on a rolling buffer) ----------
def update_ma20_atr14(buf):
    row = buf[-1]

    closes = [b["close"] for b in buf[-MA_PERIOD:]]
    row["ma20"] = sum(closes) / len(closes) if len(closes) == MA_PERIOD else None

    if len(buf) >= ATR_PERIOD + 1:
        trs = []
        for k in range(len(buf) - ATR_PERIOD, len(buf)):
            high_low = buf[k]["high"] - buf[k]["low"]
            high_prev_close = abs(buf[k]["high"] - buf[k - 1]["close"])
            low_prev_close = abs(buf[k]["low"] - buf[k - 1]["close"])
            trs.append(max(high_low, high_prev_close, low_prev_close))
        row["atr14"] = sum(trs) / len(trs)
    else:
        row["atr14"] = None


def log_trade(trade):
    os.makedirs(os.path.dirname(TRADES_CSV), exist_ok=True)
    write_header = not os.path.exists(TRADES_CSV)
    with open(TRADES_CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TRADE_FIELDS)
        if write_header:
            w.writeheader()
        w.writerow(trade)


# ---------- Per-symbol state: buf (candle history), touch_row (pending entry), trade (open position) ----------
symbol_state = {sym: {"buf": [], "touch_row": None, "trade": None} for sym in UNIVERSE}


def on_new_candle(symbol, row):
    """
    row: dict with datetime, date, hour, open, high, low, close (same shape as a DS3 df row).
    Mirrors ma_30_rejection_v1.py's run_backtest() body, one row at a time instead of df.iloc[i].
    """
    global equity
    state = symbol_state[symbol]
    buf = state["buf"]
    buf.append(row)
    update_ma20_atr14(buf)

    trade = state["trade"]

    # ===================== manage open trade (mirrors the k-loop in the original) =====================
    if trade is not None:
        touch_date = trade["touch_date"]
        k_bar = row

        if k_bar["date"] != touch_date:
            prev = buf[-2]
            pnl = trade["entry"] - prev["close"]
            outcome = "EOD+" if pnl > 0 else "EOD-"
            exit_dt = prev["datetime"]
        elif k_bar["hour"] >= EOD_HOUR:
            pnl = trade["entry"] - k_bar["open"]
            outcome = "EOD+" if pnl > 0 else "EOD-"
            exit_dt = k_bar["datetime"]
        elif k_bar["high"] >= trade["sl"]:
            pnl = trade["entry"] - trade["sl"]
            outcome = "L"
            exit_dt = k_bar["datetime"]
        elif k_bar["low"] <= trade["tp"]:
            pnl = trade["entry"] - trade["tp"]
            outcome = "W"
            exit_dt = k_bar["datetime"]
        else:
            return  # trade still open, nothing to do this bar

        pnl_rupees = pnl * trade["qty"]
        log_trade({
            "symbol": symbol,
            "touch_dt": trade["touch_dt"],
            "entry_dt": trade["entry_dt"],
            "entry": trade["entry"],
            "sl": trade["sl"],
            "tp": trade["tp"],
            "exit_dt": exit_dt,
            "qty": trade["qty"],
            "pnl": round(pnl_rupees, 2),
            "outcome": outcome,
        })
        state["trade"] = None
        equity += pnl_rupees
        return  # position guard — i = k+1: no touch scan on the bar a trade just closed on

    # ===================== entry: this bar is the one right after a touch =====================
    if state["touch_row"] is not None:
        touch_row = state["touch_row"]
        state["touch_row"] = None

        entry_bar = row
        if entry_bar["date"] != touch_row["date"]:
            pass  # entry voided (touch and next bar crossed a day boundary) — fall through, re-check this bar as a fresh touch
        else:
            touch_date = touch_row["date"]
            atr = touch_row["atr14"]
            entry = entry_bar["open"]
            sl = entry + SL_MULT * atr
            tp = entry - TP_MULT * atr

            risk_amount = RISK_PER_TRADE * equity
            qty = max(int(risk_amount // (sl - entry)), 0) if (sl - entry) > 0 else 0
            if qty > 0:
                state["trade"] = {
                    "touch_date": touch_date,
                    "touch_dt": touch_row["datetime"],
                    "entry_dt": entry_bar["datetime"],
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "qty": qty,
                }
            return

    # ===================== new touch detection =====================
    if row["ma20"] is None or row["atr14"] is None:
        return
    if row["high"] >= row["ma20"] and row["open"] < row["ma20"] and row["close"] < row["ma20"]:
        if row["hour"] >= EOD_HOUR:
            return
        state["touch_row"] = row


def build_row(candle_dict):
    """Adapts a raw candle from Kotak Neo into the same field shape as the DS3 df row."""
    dt = candle_dict["datetime"]
    return {
        "datetime": dt,
        "date": dt.date(),
        "hour": dt.hour,
        "open": candle_dict["open"],
        "high": candle_dict["high"],
        "low": candle_dict["low"],
        "close": candle_dict["close"],
    }


def run():
    print(f"[{datetime.now()}] rejection_v1_short_bot starting — {len(UNIVERSE)} symbols, PAPER MODE (no real orders).")

    print("Fetching warm-up history (needs Kotak Neo live access — not yet configured)...")
    for sym in UNIVERSE:
        warmup_candles = neo.get_warmup_candles(sym, count=max(MA_PERIOD, ATR_PERIOD) + 1)
        for c in warmup_candles:
            row = build_row(c)
            symbol_state[sym]["buf"].append(row)
            update_ma20_atr14(symbol_state[sym]["buf"])

    while True:
        now = datetime.now()
        if now.hour >= EOD_HOUR + 1 or now.hour < 9:
            print(f"[{now}] Outside trading window, stopping poll loop.")
            break

        for sym in UNIVERSE:
            candle = neo.get_latest_candle(sym)
            row = build_row(candle)
            on_new_candle(sym, row)

        time.sleep(POLL_SECONDS)

    print(f"[{datetime.now()}] Done. Trades logged to {TRADES_CSV}")


if __name__ == "__main__":
    run()
