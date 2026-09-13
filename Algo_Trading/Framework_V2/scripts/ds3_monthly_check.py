"""
DS3 monthly gap-fill + integrity check — cron entry point (2 AM IST, 1st of month).

Merges two things (TODO.md P5, delegated 2026-09-12 via fv2 -> cpgeneric session):
  1. Gap-fill: append the just-closed month's 5-min bars (30 DS3 stocks + NIFTY50
     daily) via direct KiteConnect SDK calls (NOT Kite MCP's historical_data,
     confirmed unreliable for this per TODO.md P1 item 4) using the bot's existing
     auto-refreshing access token.
  2. Integrity check, run over the FULL history every time (not just new rows):
       a. zero/negative OHLC
       b. missing-day gaps, via a consensus method across all 30 stocks (a day is
          a real market holiday if very few stocks traded; a gap is a day most
          stocks traded but one specific stock didn't) -- avoids needing to
          source/maintain an external NSE holiday calendar
       c. single-day price jumps beyond a threshold, split into three outcomes:
            - matches an allowlisted market-wide event date (known_events.json)
              -> real, expected, not a defect
            - matches a common split/bonus ratio (2:1, 5:1, 10:1, 3:2, ...)
              -> CATEGORY 2: proposed corporate-action adjustment, logged for
                 review, NEVER auto-applied (retroactive rescale across years
                 of history is too high-blast-radius to auto-apply unattended)
            - neither -> CATEGORY 1: bad/corrupted single day, auto-fixed by
              re-fetching that one day fresh from Kite and recomputing the
              indicator columns for the affected window

Known-issues tracking (ds3_integrity/known_issues.json) means already-fixed or
already-reviewed days are never re-flagged on subsequent runs -- only genuinely
new anomalies alert.

Fails loudly: any CATEGORY 1 fix applied, any new CATEGORY 2 proposal, or any
unexplained gap triggers an ntfy push (same topic as the bot's crash alerts).
Silent (log-only) if a run finds nothing new.

Usage: python ds3_monthly_check.py              -> gap-fill last month + full check
       python ds3_monthly_check.py --check-only  -> skip gap-fill, just validate
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from kiteconnect import KiteConnect
from kiteconnect.exceptions import NetworkException

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
FW2_ROOT = SCRIPT_DIR.parent
DS3_DIR = FW2_ROOT / "data" / "historical" / "intraday_5min_DS3"
NIFTY_PATH = FW2_ROOT / "data" / "historical" / "daily" / "NIFTY50.parquet"
INTEGRITY_DIR = SCRIPT_DIR / "ds3_integrity"
INTEGRITY_DIR.mkdir(parents=True, exist_ok=True)
KNOWN_ISSUES_PATH = INTEGRITY_DIR / "known_issues.json"
KNOWN_EVENTS_PATH = INTEGRITY_DIR / "known_events.json"
RUN_LOG_PATH = INTEGRITY_DIR / "run_log.md"

BOT_ENV_PATH = Path("/home/ubuntu/kite_oracle_papertrading/.env")
NTFY_TOPIC = "https://ntfy.sh/codeponting-kitebot-x7j2m9"

PERIOD = 14  # ATR window, matches add_wilder_atr_ds3.py
MA_PERIOD = 20
JUMP_THRESHOLD = 0.15  # 15% single-day move triggers investigation
SPLIT_RATIO_TOLERANCE = 0.03  # within 3% of a common ratio counts as a match
COMMON_SPLIT_RATIOS = [2.0, 3.0, 4.0, 5.0, 10.0, 1.5, 2.5, 3.5, 7.0]  # incl. bonus (1.5=3:2 etc.)
MIN_TRADING_STOCKS_FOR_MARKET_DAY = 5  # below this, treat as a market-wide holiday

SYMBOLS = [
    "ADANIPORTS", "ASHOKLEY", "AXISBANK", "BAJFINANCE", "BANDHANBNK",
    "BHARTIARTL", "CIPLA", "COALINDIA", "DABUR", "DIVISLAB",
    "HDFCBANK", "HINDALCO", "ICICIBANK", "INDUSINDBK", "INFY",
    "ITC", "JSWSTEEL", "NATIONALUM", "NTPC", "ONGC",
    "PNB", "POWERGRID", "RELIANCE", "SBIN", "SUNPHARMA",
    "TATAMOTORS", "TATASTEEL", "TECHM", "VEDL", "WIPRO",
]
TOKENS = {
    "ADANIPORTS": 3861249, "ASHOKLEY": 54273, "AXISBANK": 1510401, "BAJFINANCE": 81153,
    "BANDHANBNK": 579329, "BHARTIARTL": 2714625, "CIPLA": 177665, "COALINDIA": 5215745,
    "DABUR": 197633, "DIVISLAB": 2800641, "HDFCBANK": 341249, "HINDALCO": 348929,
    "ICICIBANK": 1270529, "INDUSINDBK": 1346049, "INFY": 408065, "ITC": 424961,
    "JSWSTEEL": 3001089, "NATIONALUM": 1629185, "NTPC": 2977281, "ONGC": 633601,
    "PNB": 2730497, "POWERGRID": 3834113, "RELIANCE": 738561, "SBIN": 779521,
    "SUNPHARMA": 857857, "TATAMOTORS": 884737, "TATASTEEL": 895745, "TECHM": 3465729,
    "VEDL": 784129, "WIPRO": 969473, "NIFTY50": 256265,
}


# ── Indicator math (matches add_wilder_atr_ds3.py exactly) ──────────────────
def true_range(high, low, close):
    n = len(close)
    tr = np.full(n, np.nan)
    if n < 2:
        return tr
    pc = close[:-1]
    h, l = high[1:], low[1:]
    tr[1:] = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    return tr


def simple_atr(tr, period):
    return pd.Series(tr).rolling(period, min_periods=period).mean().to_numpy()


def wilder_atr(tr, period):
    n = len(tr)
    atr = np.full(n, np.nan)
    i = 0
    while i < n:
        if np.isnan(atr[i - 1]) if i > 0 else True:
            if np.isnan(tr[i]):
                i += 1
                continue
            run_start = i
            j = i
            while j < n and not np.isnan(tr[j]) and (j - run_start) < period:
                j += 1
            if (j - run_start) < period:
                i = j + 1
                continue
            seed_end = j - 1
            atr[seed_end] = float(np.mean(tr[run_start:j]))
            i = seed_end + 1
            continue
        if np.isnan(tr[i]):
            atr[i] = np.nan
        else:
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        i += 1
    return atr


def recompute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute ma20/atr14/atr14_wilder over the WHOLE file (cheap enough at
    this row count) so a single-day fix's ripple through the rolling windows
    is handled correctly rather than patched by hand."""
    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    tr = true_range(high, low, close)
    df["ma20"] = pd.Series(close).rolling(MA_PERIOD, min_periods=MA_PERIOD).mean().to_numpy()
    df["atr14"] = simple_atr(tr, PERIOD)
    df["atr14_wilder"] = wilder_atr(tr, PERIOD)
    return df


# ── Retry wrapper (matches monthly_reconciliation.py) ────────────────────────
def with_retry(fn, *args, max_attempts=5, base_delay=3, **kwargs):
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except NetworkException as e:
            if attempt == max_attempts:
                raise
            delay = base_delay * attempt
            print(f"  [retry] {e} - attempt {attempt}/{max_attempts}, waiting {delay}s...")
            time.sleep(delay)


def get_kite() -> KiteConnect:
    load_dotenv(dotenv_path=BOT_ENV_PATH, override=True)
    kite = KiteConnect(api_key=os.getenv("KITE_API_KEY"))
    kite.set_access_token(os.getenv("KITE_ACCESS_TOKEN"))
    return kite


def load_json(path: Path, default):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path: Path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=str)


# ── Phase 1: gap-fill ─────────────────────────────────────────────────────
def gap_fill(kite: KiteConnect) -> dict:
    """Append missing 5-min bars per symbol (and NIFTY50 daily) from the day
    after each file's last date through yesterday. Never overwrites existing
    rows. Returns a summary dict for the run log."""
    yesterday = date.today() - timedelta(days=1)
    summary = {}

    for symbol in SYMBOLS:
        path = DS3_DIR / f"{symbol}.parquet"
        df = pd.read_parquet(path)
        df["datetime"] = pd.to_datetime(df["datetime"])
        last_date = df["datetime"].max().date()
        if last_date >= yesterday:
            summary[symbol] = {"rows_added": 0, "reason": "already current"}
            continue
        from_dt = last_date + timedelta(days=1)
        token = TOKENS[symbol]
        candles = with_retry(
            kite.historical_data, token, from_date=from_dt, to_date=yesterday, interval="5minute"
        )
        if not candles:
            summary[symbol] = {"rows_added": 0, "reason": "no new candles returned"}
            continue
        new_rows = pd.DataFrame(candles)
        new_rows = new_rows.rename(columns={"date": "datetime"})
        new_rows["datetime"] = pd.to_datetime(new_rows["datetime"]).dt.tz_localize(None)
        for col in ("ma20", "atr14", "atr14_wilder"):
            new_rows[col] = np.nan
        combined = pd.concat([df, new_rows[df.columns]], ignore_index=True)
        combined = combined.sort_values("datetime").reset_index(drop=True)
        combined = recompute_indicators(combined)
        combined.to_parquet(path, index=False)
        summary[symbol] = {"rows_added": len(new_rows), "from": str(from_dt), "to": str(yesterday)}
        time.sleep(0.4)  # rate-limit courtesy, matches monthly_reconciliation.py's cadence

    # NIFTY50 daily
    nifty_df = pd.read_parquet(NIFTY_PATH)
    nifty_df["datetime"] = pd.to_datetime(nifty_df["datetime"])
    last_date = nifty_df["datetime"].max().date()
    if last_date < yesterday:
        candles = with_retry(
            kite.historical_data, TOKENS["NIFTY50"], from_date=last_date + timedelta(days=1),
            to_date=yesterday, interval="day",
        )
        if candles:
            new_rows = pd.DataFrame(candles).rename(columns={"date": "datetime"})
            new_rows["datetime"] = pd.to_datetime(new_rows["datetime"]).dt.tz_localize(None)
            combined = pd.concat([nifty_df, new_rows[nifty_df.columns]], ignore_index=True)
            combined = combined.sort_values("datetime").reset_index(drop=True)
            combined.to_parquet(NIFTY_PATH, index=False)
            summary["NIFTY50"] = {"rows_added": len(new_rows)}
    return summary


# ── Phase 2: integrity checks ────────────────────────────────────────────
def check_zero_negative_ohlc(df: pd.DataFrame, symbol: str) -> list[dict]:
    bad = df[(df[["open", "high", "low", "close"]] <= 0).any(axis=1)]
    return [{"symbol": symbol, "date": str(d), "type": "zero_negative_ohlc"}
            for d in sorted(set(pd.to_datetime(bad["datetime"]).dt.date.astype(str)))]


def build_trading_day_consensus(all_dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Per-day count of how many of the 30 stocks have at least one bar that
    day. Used to distinguish real market holidays (near-zero count) from a
    single stock's own data gap (most stocks traded, this one didn't)."""
    per_day = {}
    for symbol, df in all_dfs.items():
        days = set(pd.to_datetime(df["datetime"]).dt.date)
        for d in days:
            per_day.setdefault(d, set()).add(symbol)
    rows = [{"date": d, "n_traded": len(syms), "symbols": syms} for d, syms in per_day.items()]
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def check_missing_day_gaps(all_dfs: dict[str, pd.DataFrame], consensus: pd.DataFrame) -> list[dict]:
    market_days = consensus[consensus["n_traded"] >= MIN_TRADING_STOCKS_FOR_MARKET_DAY]
    n = len(SYMBOLS)
    quorum = max(int(n * 0.8), n - 5)  # >=25 of 30 traded = "most did"
    real_market_days = market_days[market_days["n_traded"] >= quorum]
    # A symbol's own first-ever date in DS3 (e.g. BANDHANBNK listed ~2018, well
    # after DS3's 2015 start) — never flag a "gap" before a stock's own real
    # listing date, that's not a defect, it's the stock not existing yet.
    first_date = {s: pd.to_datetime(df["datetime"]).dt.date.min() for s, df in all_dfs.items()}
    gaps = []
    for _, row in real_market_days.iterrows():
        missing = set(SYMBOLS) - row["symbols"]
        for symbol in missing:
            if row["date"] < first_date[symbol]:
                continue  # pre-listing, not a data gap
            gaps.append({"symbol": symbol, "date": str(row["date"]), "type": "missing_day_gap",
                         "n_other_stocks_traded": row["n_traded"]})
    return gaps


def daily_close_series(df: pd.DataFrame) -> pd.Series:
    d = df.copy()
    d["day"] = pd.to_datetime(d["datetime"]).dt.date
    return d.groupby("day")["close"].last()


def check_price_jumps(df: pd.DataFrame, symbol: str, known_events: list[dict]) -> list[dict]:
    closes = daily_close_series(df)
    rets = closes.pct_change()
    flagged = rets[rets.abs() > JUMP_THRESHOLD]
    out = []
    for d, ret in flagged.items():
        d_str = str(d)
        is_known_event = any(ev["start"] <= d_str <= ev["end"] for ev in known_events)
        if is_known_event:
            continue  # real, expected market-wide move — not a defect
        if ret <= -0.999:
            matched_split = None  # -100%-ish move (e.g. zero-fill) is never a real split ratio
        else:
            ratio = 1.0 / (1.0 + ret) if ret < 0 else (1.0 + ret)
            matched_split = next(
                (r for r in COMMON_SPLIT_RATIOS if abs(ratio - r) / r <= SPLIT_RATIO_TOLERANCE), None
            )
        out.append({
            "symbol": symbol, "date": d_str, "return_pct": round(ret * 100, 2),
            "type": "suspected_split_bonus" if matched_split else "unexplained_jump",
            "matched_ratio": matched_split,
        })
    return out


def query_nse_corporate_actions(symbol: str, from_date: str, to_date: str) -> list[dict]:
    """Best-effort — NSE's public corporate-actions endpoint (no auth needed,
    confirmed reachable 2026-09-12). Returns [] on any failure; this is
    informational for the Category-2 proposal, never blocks the run."""
    url = (f"https://www.nseindia.com/api/corporates-corporateActions"
           f"?index=equities&symbol={symbol}&from_date={from_date}&to_date={to_date}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return [{"error": str(e)}]


def to_nse_date(iso_date: str) -> str:
    return date.fromisoformat(iso_date).strftime("%d-%m-%Y")


# ── Phase 3: Category 1 auto-fix ─────────────────────────────────────────
def apply_category1_fix(kite: KiteConnect, symbol: str, bad_date: str) -> dict:
    """Re-fetch one specific day fresh from Kite and splice it into the
    existing file in place of whatever was there, then recompute indicators
    over the whole file. Logged with a before/after row count for the diff."""
    path = DS3_DIR / f"{symbol}.parquet"
    df = pd.read_parquet(path)
    df["datetime"] = pd.to_datetime(df["datetime"])
    d = date.fromisoformat(bad_date)
    before_rows = df[df["datetime"].dt.date == d]
    n_before = len(before_rows)

    candles = with_retry(kite.historical_data, TOKENS[symbol], from_date=d, to_date=d, interval="5minute")
    if not candles:
        return {"symbol": symbol, "date": bad_date, "status": "refetch_returned_nothing"}
    fresh = pd.DataFrame(candles).rename(columns={"date": "datetime"})
    fresh["datetime"] = pd.to_datetime(fresh["datetime"]).dt.tz_localize(None)
    for col in ("ma20", "atr14", "atr14_wilder"):
        fresh[col] = np.nan

    df = df[df["datetime"].dt.date != d]
    df = pd.concat([df, fresh[df.columns]], ignore_index=True).sort_values("datetime").reset_index(drop=True)
    df = recompute_indicators(df)
    df.to_parquet(path, index=False)
    return {"symbol": symbol, "date": bad_date, "status": "fixed",
            "rows_before": n_before, "rows_after": len(fresh)}


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    check_only = "--check-only" in sys.argv
    run_started = pd.Timestamp.now()
    print(f"DS3 monthly check — {run_started}")

    kite = get_kite()
    known_issues = load_json(KNOWN_ISSUES_PATH, {
        "resolved": [], "pending_category2": [],
        "pending_unexplained_jump": [], "confirmed_real_events": [],
    })
    known_issues.setdefault("pending_unexplained_jump", [])
    known_issues.setdefault("confirmed_real_events", [])
    known_events = load_json(KNOWN_EVENTS_PATH, [
        {"start": "2020-03-09", "end": "2020-03-24", "label": "COVID crash"},
        {"start": "2017-10-24", "end": "2017-10-26", "label": "PSU bank recapitalization rally"},
        {"start": "2024-06-03", "end": "2024-06-05", "label": "2024 election result crash"},
    ])
    resolved_keys = {(r["symbol"], r["date"]) for r in known_issues["resolved"]}
    pending_keys = {(p["symbol"], p["date"]) for p in known_issues["pending_category2"]}
    pending_jump_keys = {(p["symbol"], p["date"]) for p in known_issues["pending_unexplained_jump"]}
    real_event_keys = {(e["symbol"], e["date"]) for e in known_issues["confirmed_real_events"]}

    gap_summary = {}
    if not check_only:
        print("Phase 1: gap-fill...")
        gap_summary = gap_fill(kite)

    print("Phase 2: loading all symbols for integrity check...")
    all_dfs = {s: pd.read_parquet(DS3_DIR / f"{s}.parquet") for s in SYMBOLS}
    for df in all_dfs.values():
        df["datetime"] = pd.to_datetime(df["datetime"])

    zero_neg = []
    jumps = []
    for symbol, df in all_dfs.items():
        zero_neg += check_zero_negative_ohlc(df, symbol)
        jumps += check_price_jumps(df, symbol, known_events)
    consensus = build_trading_day_consensus(all_dfs)
    gaps = check_missing_day_gaps(all_dfs, consensus)

    # Category 1 = unambiguous data defects, safe to auto-fix with no review:
    # zero/negative OHLC and missing-day gaps. Unexplained jumps are NOT auto-
    # fixed here even though a blind re-fetch would be equally safe (matches
    # Kite either way) — reviewing them first is a deliberate quant practice
    # (2026-09-13 decision): confirming whether a big move is real news builds
    # an event history, rather than letting real volatility silently vanish
    # into an unremarked-on "auto-fix".
    category1_candidates = [
        z for z in zero_neg if (z["symbol"], z["date"]) not in resolved_keys
    ] + [
        g for g in gaps if (g["symbol"], g["date"]) not in resolved_keys
    ]
    category2_candidates = [
        j for j in jumps if j["type"] == "suspected_split_bonus"
        and (j["symbol"], j["date"]) not in pending_keys
        and (j["symbol"], j["date"]) not in resolved_keys
    ]
    unexplained_jump_candidates = [
        j for j in jumps if j["type"] == "unexplained_jump"
        and (j["symbol"], j["date"]) not in resolved_keys
        and (j["symbol"], j["date"]) not in pending_jump_keys
        and (j["symbol"], j["date"]) not in real_event_keys
    ]

    print(f"  zero/negative OHLC: {len(zero_neg)} | missing-day gaps: {len(gaps)} | "
          f"unexplained jumps: {len([j for j in jumps if j['type']=='unexplained_jump'])} | "
          f"suspected split/bonus: {len(category2_candidates)}")
    print(f"  NEW category-1 candidates (auto-fixable): {len(category1_candidates)}")
    print(f"  NEW category-2 candidates (needs review): {len(category2_candidates)}")
    print(f"  NEW unexplained-jump candidates (needs review): {len(unexplained_jump_candidates)}")

    fixes_applied = []
    if not check_only:
        for item in category1_candidates:
            print(f"  [category 1 fix] {item['symbol']} {item['date']} ({item['type']})...")
            result = apply_category1_fix(kite, item["symbol"], item["date"])
            fixes_applied.append(result)
            if result["status"] == "fixed":
                known_issues["resolved"].append({
                    "symbol": item["symbol"], "date": item["date"], "type": item["type"],
                    "fixed_on": str(date.today()),
                })

    category2_proposals = []
    for item in category2_candidates:
        nse_actions = query_nse_corporate_actions(
            item["symbol"], to_nse_date((date.fromisoformat(item["date"]) - timedelta(days=30)).isoformat()),
            to_nse_date((date.fromisoformat(item["date"]) + timedelta(days=5)).isoformat()),
        )
        proposal = {**item, "nse_corporate_actions_nearby": nse_actions}
        category2_proposals.append(proposal)
        known_issues["pending_category2"].append({
            "symbol": item["symbol"], "date": item["date"], "matched_ratio": item["matched_ratio"],
            "flagged_on": str(date.today()),
        })

    # Unexplained jumps: never auto-fixed, just staged for review. Use
    # `ds3_monthly_check.py --mark SYMBOL DATE real "one-line note"` (confirmed
    # real event, data stays as-is, logged to confirmed_real_events.md) or
    # `--mark SYMBOL DATE baddata` (applies the same re-fetch fix as category 1).
    for item in unexplained_jump_candidates:
        known_issues["pending_unexplained_jump"].append({
            "symbol": item["symbol"], "date": item["date"], "return_pct": item["return_pct"],
            "flagged_on": str(date.today()),
        })

    save_json(KNOWN_ISSUES_PATH, known_issues)
    save_json(KNOWN_EVENTS_PATH, known_events)

    # ── Run log ──
    with open(RUN_LOG_PATH, "a") as f:
        f.write(f"\n## {run_started}\n")
        f.write(f"Gap-fill: {json.dumps(gap_summary, default=str)}\n\n")
        f.write(f"Zero/negative OHLC found: {len(zero_neg)}\n")
        f.write(f"Missing-day gaps found: {len(gaps)}\n")
        f.write(f"Category 1 (auto-fixed this run): {json.dumps(fixes_applied, default=str)}\n")
        f.write(f"Category 2 (pending review): {json.dumps(category2_proposals, default=str, indent=2)}\n")
        f.write(f"Unexplained jumps (pending review): "
                f"{json.dumps(unexplained_jump_candidates, default=str, indent=2)}\n")

    # ── Alert ──
    any_new = bool(fixes_applied) or bool(category2_proposals) or bool(unexplained_jump_candidates)
    unfixed = [f for f in fixes_applied if f["status"] != "fixed"]
    if any_new or unfixed:
        msg_lines = [f"DS3 check {date.today()}:"]
        if fixes_applied:
            msg_lines.append(f"{len(fixes_applied)} category-1 day(s) auto-fixed")
        if unfixed:
            msg_lines.append(f"{len(unfixed)} FAILED to auto-fix — needs manual attention")
        if category2_proposals:
            msg_lines.append(f"{len(category2_proposals)} category-2 (corp-action) proposal(s) awaiting review")
        if unexplained_jump_candidates:
            msg_lines.append(f"{len(unexplained_jump_candidates)} unexplained jump(s) need review:")
            for j in unexplained_jump_candidates[:10]:
                msg_lines.append(f"  {j['symbol']} {j['date']} ({j['return_pct']:+.1f}%)")
        try:
            urllib.request.urlopen(urllib.request.Request(
                NTFY_TOPIC, data="\n".join(msg_lines).encode(), method="POST"
            ), timeout=10)
        except Exception as e:
            print(f"  [ntfy alert failed: {e}]")
        print("ALERT SENT:", " | ".join(msg_lines))
    else:
        print("Clean run — nothing new to report.")

    print(f"Done. Full log: {RUN_LOG_PATH}")


def mark_command():
    """python ds3_monthly_check.py --mark SYMBOL DATE real|baddata ["note"]"""
    args = sys.argv[2:]
    if len(args) < 3:
        print('Usage: --mark SYMBOL DATE real|baddata ["note"]')
        sys.exit(1)
    symbol, day, verdict = args[0], args[1], args[2]
    note = args[3] if len(args) > 3 else ""

    known_issues = load_json(KNOWN_ISSUES_PATH, {
        "resolved": [], "pending_category2": [],
        "pending_unexplained_jump": [], "confirmed_real_events": [],
    })
    known_issues["pending_unexplained_jump"] = [
        p for p in known_issues["pending_unexplained_jump"]
        if not (p["symbol"] == symbol and p["date"] == day)
    ]
    known_issues["pending_category2"] = [
        p for p in known_issues["pending_category2"]
        if not (p["symbol"] == symbol and p["date"] == day)
    ]

    if verdict == "real":
        known_issues["confirmed_real_events"].append({
            "symbol": symbol, "date": day, "note": note, "confirmed_on": str(date.today()),
        })
        save_json(KNOWN_ISSUES_PATH, known_issues)
        events_md = INTEGRITY_DIR / "confirmed_real_events.md"
        with open(events_md, "a") as f:
            f.write(f"- **{day}** {symbol} — {note} (confirmed {date.today()})\n")
        print(f"Logged {symbol} {day} as a confirmed real event. Won't be re-flagged.")
    elif verdict == "baddata":
        kite = get_kite()
        result = apply_category1_fix(kite, symbol, day)
        if result["status"] == "fixed":
            known_issues["resolved"].append({
                "symbol": symbol, "date": day, "type": "unexplained_jump_confirmed_bad",
                "fixed_on": str(date.today()), "note": note,
            })
            print(f"Fixed {symbol} {day} — re-fetched fresh from Kite.")
        else:
            print(f"Re-fetch did not resolve it: {result}")
        save_json(KNOWN_ISSUES_PATH, known_issues)
    else:
        print('verdict must be "real" or "baddata"')
        sys.exit(1)


if __name__ == "__main__":
    if "--mark" in sys.argv:
        mark_command()
    else:
        main()
