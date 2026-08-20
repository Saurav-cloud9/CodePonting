# -*- coding: utf-8 -*-
"""
Comprehensive NSE Kaggle Dataset Validation  — 1 March 2026
=============================================================
Checks DS1 (105 stocks) and DS2 (499 stocks) for:
  CHECK 1 — Internal consistency
  CHECK 2 — Volume outlier scan
  CHECK 3 — Cross-compare DS2 vs FV1 5-min parquets

Outputs:
  Algo_Trading/Kaggle/validation/validation_report.md
  Algo_Trading/Kaggle/validation/known_anomalies.csv
"""

import sys, warnings, time as _time
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import time as dtime
from collections import defaultdict

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

t0 = _time.time()

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE    = Path("c:/Users/saurav/CodePonting")
DS1     = BASE / "Algo_Trading/Kaggle/dataset1"
DS2     = BASE / "Algo_Trading/Kaggle/dataset2"
FV1     = BASE / "Algo_Trading/Framework_V1/data/historical/intraday_5min"
OUT_DIR = BASE / "Algo_Trading/Kaggle/validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Constants ──────────────────────────────────────────────────────────────────
MKT_OPEN_T   = dtime(9, 15)
MKT_CLOSE_T  = dtime(15, 30)
PRICE_TOL    = 0.001     # 0.1%
VOL_TOL      = 0.20      # 20%
VOL_SPIKE    = 10        # candle vol > 10x avg per-minute vol
VOL_DAY_MULT = 2.0       # daily vol > 2x rolling median → doubled
COMPARE_START = "2022-01-01"
COMPARE_END   = "2025-12-31"

# ── Global anomaly list ────────────────────────────────────────────────────────
anomalies = []

def add_anomaly(stock, date, issue_type, source, severity):
    anomalies.append({
        "stock":      stock,
        "date":       str(date)[:10],
        "issue_type": issue_type,
        "source":     source,
        "severity":   severity,
    })


# ── Loaders ───────────────────────────────────────────────────────────────────
def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        path, parse_dates=["date"],
        dtype={"open": "float32", "high": "float32",
               "low": "float32", "close": "float32", "volume": "int64"},
    )
    df = df.set_index("date").sort_index()
    df.columns = df.columns.str.lower()
    return df


def stock_name(path: Path) -> str:
    return path.stem.replace("_minute", "")


# ── Infer NSE trading days ─────────────────────────────────────────────────────
def infer_trading_days(csv_dir: Path, anchor: str = "SBIN") -> pd.DatetimeIndex:
    """
    Use the anchor stock (always liquid) to determine NSE trading days.
    Weekdays in its date range where it has at least one candle = trading day.
    """
    path = csv_dir / f"{anchor}_minute.csv"
    if not path.exists():
        # fallback: take union from first 5 files
        paths = sorted(csv_dir.glob("*_minute.csv"))[:5]
        days = set()
        for p in paths:
            df = load_csv(p)
            days.update(df.index.normalize().unique().tolist())
        idx = pd.DatetimeIndex(sorted(days))
    else:
        df = load_csv(path)
        idx = df.index.normalize().unique()
    return idx[idx.weekday < 5].sort_values()


# ── CHECK 1: Internal consistency ─────────────────────────────────────────────
def check_internal(df: pd.DataFrame, stock: str, source: str,
                   trading_days: pd.DatetimeIndex) -> dict:
    r = {}

    # 1a — Missing trading days
    stock_days = df.index.normalize().unique()
    d_min = df.index.min().normalize()
    d_max = df.index.max().normalize()
    expected = trading_days[(trading_days >= d_min) & (trading_days <= d_max)]
    missing  = expected.difference(stock_days)
    r["missing_days"]          = int(len(missing))
    r["total_expected_days"]   = int(len(expected))
    r["coverage_pct"]          = round(100 * (1 - len(missing) / max(len(expected), 1)), 2)
    sev = "high" if len(missing) > 20 else ("medium" if len(missing) > 5 else "low")
    for d in missing:
        add_anomaly(stock, d.date(), "missing_trading_day", source, sev)

    # 1b — Candles outside market hours
    ts = df.index.time
    pre  = (ts < MKT_OPEN_T)
    post = (ts > MKT_CLOSE_T)
    r["pre_market_candles"]  = int(pre.sum())
    r["post_market_candles"] = int(post.sum())
    for idx2 in df.index[pre][:20]:
        add_anomaly(stock, idx2.date(), "pre_market_candle", source, "medium")
    for idx2 in df.index[post][:20]:
        add_anomaly(stock, idx2.date(), "post_market_candle", source, "medium")

    # 1c — OHLC violations
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    bad = (h < l) | (c > h) | (c < l) | (o > h) | (o < l)
    r["ohlc_violations"] = int(bad.sum())
    for idx2 in df.index[bad][:20]:
        add_anomaly(stock, idx2.date(), "ohlc_violation", source, "high")

    # 1d — Duplicate timestamps
    dupes = int(df.index.duplicated().sum())
    r["duplicate_timestamps"] = dupes
    if dupes:
        dup_days = df.index[df.index.duplicated(keep=False)].normalize().unique()
        for d in dup_days[:10]:
            add_anomaly(stock, d.date(), "duplicate_timestamp", source, "high")

    # 1e — Zero volume candles
    zvol = int((df["volume"] == 0).sum())
    r["zero_volume_candles"] = zvol
    if zvol:
        for idx2 in df.index[df["volume"] == 0][:10]:
            add_anomaly(stock, idx2.date(), "zero_volume", source, "low")

    r["pass_consistency"] = (
        r["ohlc_violations"] == 0 and
        r["duplicate_timestamps"] == 0 and
        r["missing_days"] / max(r["total_expected_days"], 1) < 0.02
    )
    return r


# ── CHECK 2: Volume outliers ───────────────────────────────────────────────────
def check_volume(df: pd.DataFrame, stock: str, source: str) -> dict:
    r = {}

    daily_vol = df["volume"].resample("D").sum()
    trading_daily = daily_vol[daily_vol > 0]
    if len(trading_daily) == 0:
        r["volume_spike_candles"] = 0
        r["doubled_volume_days"]  = 0
        r["pass_volume"] = True
        return r

    median_daily = float(trading_daily.median())
    avg_per_min  = median_daily / 375.0  # 375 candles per day

    # 2a — Candle-level spikes
    thresh = VOL_SPIKE * avg_per_min
    spikes = df["volume"] > thresh
    r["volume_spike_candles"] = int(spikes.sum())
    spike_days = set()
    for idx2 in df.index[spikes]:
        d = idx2.date()
        if d not in spike_days:
            add_anomaly(stock, d, "volume_spike_10x", source, "medium")
            spike_days.add(d)
        if len(spike_days) >= 20:
            break

    # 2b — Day-level doubled volume (rolling 10-day median, centered)
    roll_med = trading_daily.rolling(window=10, min_periods=3, center=True).median()
    doubled  = trading_daily[trading_daily > VOL_DAY_MULT * roll_med]
    r["doubled_volume_days"] = int(len(doubled))
    for d, v in list(doubled.items())[:20]:
        add_anomaly(stock, d.date(), "doubled_volume", source, "high")

    r["pass_volume"] = (r["volume_spike_candles"] == 0 and r["doubled_volume_days"] < 5)
    return r


# ── CHECK 3: Cross-compare DS2 vs FV1 ─────────────────────────────────────────
def check_cross(stock: str) -> dict:
    fv1_path = FV1 / f"{stock}.parquet"
    ds2_path = DS2 / f"{stock}_minute.csv"

    if not fv1_path.exists():
        return {"status": "NO_FV1"}
    if not ds2_path.exists():
        return {"status": "NO_DS2"}

    # Load FV1 (5-min, IST-aware → strip tz for alignment)
    fv1 = pd.read_parquet(fv1_path)
    fv1["datetime"] = pd.to_datetime(fv1["datetime"]).dt.tz_localize(None)
    fv1 = fv1.set_index("datetime")[["open", "high", "low", "close", "volume"]]
    fv1 = fv1.loc[COMPARE_START:COMPARE_END].sort_index()
    if fv1.empty:
        return {"status": "FV1_EMPTY"}

    # Load DS2 1-min → resample to 5-min
    ds2_1m = load_csv(ds2_path).loc[COMPARE_START:COMPARE_END]
    if ds2_1m.empty:
        return {"status": "DS2_EMPTY"}
    ds2_5m = ds2_1m.resample("5min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    ).dropna(subset=["open"])

    common = fv1.index.intersection(ds2_5m.index)
    if len(common) == 0:
        return {"status": "NO_OVERLAP"}

    a = fv1.loc[common]
    b = ds2_5m.loc[common]

    def pct_diff_arr(x, y):
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(y != 0, np.abs((x.astype(float) - y.astype(float)) / y.astype(float)), np.nan)

    r = {"status": "OK", "common_bars": int(len(common))}
    price_bad_total = 0
    for col in ["open", "high", "low", "close"]:
        diff = pct_diff_arr(a[col].values, b[col].values)
        bad  = int(np.nansum(diff > PRICE_TOL))
        r[f"{col}_mismatch"] = bad
        price_bad_total += bad
        if bad:
            bad_idx = common[diff > PRICE_TOL]
            seen = set()
            for ts in bad_idx[:10]:
                d = ts.date()
                if d not in seen:
                    add_anomaly(stock, d, f"price_mismatch_{col}", "DS2_vs_FV1", "high")
                    seen.add(d)

    vdiff = pct_diff_arr(a["volume"].values, b["volume"].values)
    vbad  = int(np.nansum(vdiff > VOL_TOL))
    r["volume_mismatch"] = vbad
    if vbad:
        bad_idx = common[vdiff > VOL_TOL]
        seen = set()
        for ts in bad_idx[:10]:
            d = ts.date()
            if d not in seen:
                add_anomaly(stock, d, "volume_mismatch", "DS2_vs_FV1", "medium")
                seen.add(d)

    r["price_mismatch_total"] = price_bad_total
    r["pass_cross"] = (price_bad_total == 0 and vbad == 0)
    return r


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 72)
print("  NSE Kaggle Dataset Validation  —  1 March 2026")
print("=" * 72)

# ── Infer trading days ────────────────────────────────────────────────────────
print("\n[0] Inferring NSE trading days from SBIN anchor...")
td_ds1 = infer_trading_days(DS1)
td_ds2 = infer_trading_days(DS2)
print(f"    DS1 trading days: {len(td_ds1)}  ({td_ds1.min().date()} → {td_ds1.max().date()})")
print(f"    DS2 trading days: {len(td_ds2)}  ({td_ds2.min().date()} → {td_ds2.max().date()})")

# ── DS1 ───────────────────────────────────────────────────────────────────────
ds1_files  = sorted(DS1.glob("*_minute.csv"))
ds1_res    = {}
print(f"\n[1] Processing DS1 — {len(ds1_files)} stocks")
for i, f in enumerate(ds1_files, 1):
    stock = stock_name(f)
    try:
        df = load_csv(f)
        r  = check_internal(df, stock, "DS1", td_ds1)
        r.update(check_volume(df, stock, "DS1"))
        ds1_res[stock] = r
        status = "PASS" if (r["pass_consistency"] and r["pass_volume"]) else "FAIL"
        print(f"  [{i:3d}/{len(ds1_files)}] {stock:<18} {status}  "
              f"miss={r['missing_days']:3d}  ohlc={r['ohlc_violations']:4d}  "
              f"dupes={r['duplicate_timestamps']:3d}  zvol={r['zero_volume_candles']:4d}  "
              f"spikes={r['volume_spike_candles']:4d}  2xdays={r['doubled_volume_days']:3d}")
    except Exception as e:
        ds1_res[stock] = {"error": str(e)}
        print(f"  [{i:3d}/{len(ds1_files)}] {stock:<18} ERROR: {e}")

# ── DS2 ───────────────────────────────────────────────────────────────────────
ds2_files  = sorted(DS2.glob("*_minute.csv"))
ds2_res    = {}
print(f"\n[2] Processing DS2 — {len(ds2_files)} stocks")
for i, f in enumerate(ds2_files, 1):
    stock = stock_name(f)
    try:
        df = load_csv(f)
        r  = check_internal(df, stock, "DS2", td_ds2)
        r.update(check_volume(df, stock, "DS2"))
        r["cross"] = check_cross(stock)
        ds2_res[stock] = r
        status  = "PASS" if (r["pass_consistency"] and r["pass_volume"]) else "FAIL"
        cc = r["cross"]
        cc_str = cc.get("status", "?")
        if cc.get("status") == "OK":
            cc_str = (f"OK  bars={cc['common_bars']:5d}  "
                      f"px_mis={cc['price_mismatch_total']:4d}  "
                      f"vol_mis={cc['volume_mismatch']:4d}")
        print(f"  [{i:3d}/{len(ds2_files)}] {stock:<18} {status}  "
              f"miss={r['missing_days']:3d}  ohlc={r['ohlc_violations']:4d}  "
              f"dupes={r['duplicate_timestamps']:3d}  zvol={r['zero_volume_candles']:4d}  "
              f"spikes={r['volume_spike_candles']:4d}  2xdays={r['doubled_volume_days']:3d}  "
              f"cross={cc_str}")
    except Exception as e:
        ds2_res[stock] = {"error": str(e)}
        print(f"  [{i:3d}/{len(ds2_files)}] {stock:<18} ERROR: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE OUTPUTS
# ══════════════════════════════════════════════════════════════════════════════

# ── Anomalies CSV ─────────────────────────────────────────────────────────────
anom_df = pd.DataFrame(anomalies, columns=["stock", "date", "issue_type", "source", "severity"])
anom_df = anom_df.sort_values(["severity", "stock", "date"],
                               key=lambda c: c.map({"high": 0, "medium": 1, "low": 2}) if c.name == "severity" else c)
anom_path = OUT_DIR / "known_anomalies.csv"
anom_df.to_csv(anom_path, index=False)
print(f"\n  Wrote {len(anom_df)} anomalies → {anom_path}")


# ── Validation Report MD ───────────────────────────────────────────────────────
def safe(r, key, default="-"):
    v = r.get(key, default)
    return default if v is None else v


def pass_fail(cond):
    return "PASS" if cond else "FAIL"


def agg_stats(res_dict):
    total = len(res_dict)
    errors = sum(1 for r in res_dict.values() if "error" in r)
    c1_pass = sum(1 for r in res_dict.values()
                  if "pass_consistency" in r and r["pass_consistency"])
    c2_pass = sum(1 for r in res_dict.values()
                  if "pass_volume" in r and r["pass_volume"])
    miss_total = sum(r.get("missing_days", 0) for r in res_dict.values() if "error" not in r)
    ohlc_total = sum(r.get("ohlc_violations", 0) for r in res_dict.values() if "error" not in r)
    dup_total  = sum(r.get("duplicate_timestamps", 0) for r in res_dict.values() if "error" not in r)
    zvol_total = sum(r.get("zero_volume_candles", 0) for r in res_dict.values() if "error" not in r)
    spk_total  = sum(r.get("volume_spike_candles", 0) for r in res_dict.values() if "error" not in r)
    dbl_total  = sum(r.get("doubled_volume_days", 0) for r in res_dict.values() if "error" not in r)
    return {
        "total": total, "errors": errors,
        "c1_pass": c1_pass, "c2_pass": c2_pass,
        "miss": miss_total, "ohlc": ohlc_total,
        "dups": dup_total,  "zvol": zvol_total,
        "spikes": spk_total, "doubled": dbl_total,
    }


s1 = agg_stats(ds1_res)
s2 = agg_stats(ds2_res)

# Cross-compare stats for DS2
cc_stocks = {k: v["cross"] for k, v in ds2_res.items()
             if "cross" in v and v["cross"].get("status") == "OK"}
cc_pass   = sum(1 for c in cc_stocks.values() if c.get("pass_cross"))
cc_px_mis = sum(c.get("price_mismatch_total", 0) for c in cc_stocks.values())
cc_v_mis  = sum(c.get("volume_mismatch", 0) for c in cc_stocks.values())

elapsed = _time.time() - t0
lines = []
L = lines.append

L("# Kaggle NSE Dataset Validation Report")
L(f"**Generated:** 2026-03-01  |  **Elapsed:** {elapsed/60:.1f} min")
L(f"**DS1:** {len(ds1_files)} stocks (dataset1)  "
  f"|  **DS2:** {len(ds2_files)} stocks (dataset2)  "
  f"|  **FV1:** {len(list(FV1.glob('*.parquet')))} parquets (intraday_5min)")
L("")
L("---")
L("")
L("## Summary")
L("")
L("| Metric | DS1 | DS2 |")
L("|--------|-----|-----|")
L(f"| Stocks processed | {s1['total']} | {s2['total']} |")
L(f"| Load errors | {s1['errors']} | {s2['errors']} |")
L(f"| CHECK 1 PASS (consistency) | {s1['c1_pass']}/{s1['total']-s1['errors']} | {s2['c1_pass']}/{s2['total']-s2['errors']} |")
L(f"| CHECK 2 PASS (volume) | {s1['c2_pass']}/{s1['total']-s1['errors']} | {s2['c2_pass']}/{s2['total']-s2['errors']} |")
L(f"| Total missing trading days | {s1['miss']:,} | {s2['miss']:,} |")
L(f"| Total OHLC violations | {s1['ohlc']:,} | {s2['ohlc']:,} |")
L(f"| Total duplicate timestamps | {s1['dups']:,} | {s2['dups']:,} |")
L(f"| Total zero-volume candles | {s1['zvol']:,} | {s2['zvol']:,} |")
L(f"| Total volume-spike candles (>10x) | {s1['spikes']:,} | {s2['spikes']:,} |")
L(f"| Total doubled-volume days | {s1['doubled']:,} | {s2['doubled']:,} |")
L(f"| Total anomalies logged | {len(anom_df[anom_df['source']=='DS1'])} | {len(anom_df[anom_df['source']=='DS2'])} |")
L("")

# Winner
def score(s):
    # lower = cleaner.  Weighted penalty
    return (s["ohlc"] * 100 + s["dups"] * 50 +
            s["miss"] * 5 + s["zvol"] * 1 +
            s["spikes"] * 2 + s["doubled"] * 10)

sc1, sc2 = score(s1), score(s2)
# Normalise by stock count
norm1 = sc1 / max(s1["total"] - s1["errors"], 1)
norm2 = sc2 / max(s2["total"] - s2["errors"], 1)
winner = "DS1" if norm1 <= norm2 else "DS2"
L(f"### Winner: **{winner}** (lower anomaly score per stock: DS1={norm1:.1f} vs DS2={norm2:.1f})")
L("")
L("---")
L("")
L("## CHECK 3 — Cross-compare DS2 vs FV1 Parquets (2022-2025)")
L("")
L(f"Overlapping stocks compared: **{len(cc_stocks)}**")
L(f"Stocks with all OHLC+Volume PASS: **{cc_pass} / {len(cc_stocks)}**")
L(f"Total price-mismatch bars: **{cc_px_mis:,}**")
L(f"Total volume-mismatch bars (>20%): **{cc_v_mis:,}**")
L("")
L("| Stock | Common Bars | Open_mis | High_mis | Low_mis | Close_mis | Vol_mis | PASS |")
L("|-------|-------------|----------|----------|---------|-----------|---------|------|")
for stock, c in sorted(cc_stocks.items()):
    L(f"| {stock} | {c.get('common_bars',0):,} | "
      f"{c.get('open_mismatch',0)} | {c.get('high_mismatch',0)} | "
      f"{c.get('low_mismatch',0)} | {c.get('close_mismatch',0)} | "
      f"{c.get('volume_mismatch',0)} | {'YES' if c.get('pass_cross') else 'NO'} |")
L("")

# Stocks in FV1 not found in DS2
fv1_stocks = {p.stem for p in FV1.glob("*.parquet")}
ds2_stocks  = {stock_name(f) for f in ds2_files}
fv1_missing_in_ds2 = fv1_stocks - ds2_stocks
L(f"FV1 stocks **not** in DS2: `{', '.join(sorted(fv1_missing_in_ds2)) if fv1_missing_in_ds2 else 'none'}`")
L("")
L("---")
L("")

# ── Per-stock tables ──────────────────────────────────────────────────────────
L("## DS1 Per-Stock Results")
L("")
L("| Stock | Days | Miss | OHLC | Dupes | ZVol | Spikes | 2xDays | C1 | C2 |")
L("|-------|------|------|------|-------|------|--------|--------|----|----|")
for stock, r in sorted(ds1_res.items()):
    if "error" in r:
        L(f"| {stock} | ERROR | — | — | — | — | — | — | ERR | ERR |")
        continue
    c1 = pass_fail(r.get("pass_consistency", False))
    c2 = pass_fail(r.get("pass_volume", False))
    L(f"| {stock} | {r.get('total_expected_days',0)} "
      f"| {r.get('missing_days',0)} "
      f"| {r.get('ohlc_violations',0)} "
      f"| {r.get('duplicate_timestamps',0)} "
      f"| {r.get('zero_volume_candles',0)} "
      f"| {r.get('volume_spike_candles',0)} "
      f"| {r.get('doubled_volume_days',0)} "
      f"| {c1} | {c2} |")

L("")
L("## DS2 Per-Stock Results")
L("")
L("| Stock | Days | Miss | OHLC | Dupes | ZVol | Spikes | 2xDays | C1 | C2 | Cross |")
L("|-------|------|------|------|-------|------|--------|--------|----|----|-------|")
for stock, r in sorted(ds2_res.items()):
    if "error" in r:
        L(f"| {stock} | ERROR | — | — | — | — | — | — | ERR | ERR | — |")
        continue
    c1 = pass_fail(r.get("pass_consistency", False))
    c2 = pass_fail(r.get("pass_volume", False))
    cc = r.get("cross", {})
    cc_str = cc.get("status", "-")
    if cc.get("status") == "OK":
        cc_str = "YES" if cc.get("pass_cross") else "NO"
    L(f"| {stock} | {r.get('total_expected_days',0)} "
      f"| {r.get('missing_days',0)} "
      f"| {r.get('ohlc_violations',0)} "
      f"| {r.get('duplicate_timestamps',0)} "
      f"| {r.get('zero_volume_candles',0)} "
      f"| {r.get('volume_spike_candles',0)} "
      f"| {r.get('doubled_volume_days',0)} "
      f"| {c1} | {c2} | {cc_str} |")

L("")
L("---")
L("")
L("## Anomaly Type Breakdown")
L("")
if len(anom_df):
    grp = anom_df.groupby(["source", "issue_type", "severity"]).size().reset_index(name="count")
    grp = grp.sort_values(["source", "severity", "count"],
                           key=lambda c: c.map({"high": 0, "medium": 1, "low": 2})
                           if c.name == "severity" else c)
    L("| Source | Issue Type | Severity | Count |")
    L("|--------|-----------|----------|-------|")
    for _, row in grp.iterrows():
        L(f"| {row['source']} | {row['issue_type']} | {row['severity']} | {row['count']:,} |")
L("")
L("---")
L("")
L("## Notes")
L("")
L("- **missing_trading_day**: Weekdays within a stock's date range where no candles exist.")
L("  Some will be NSE holidays (~15/year). High counts (>20) indicate genuine data gaps.")
L("- **ohlc_violation**: High < Low, Close > High, Close < Low, Open > High or Open < Low.")
L("  Any count > 0 is a hard data quality failure.")
L("- **volume_spike_10x**: Single candle volume > 10× median per-minute volume for that stock.")
L("  May indicate block trades or data encoding errors.")
L("- **doubled_volume**: Daily total > 2× rolling 10-day median (centred).")
L("  Common near results, dividends, or data errors (volume counted twice).")
L("- **price_mismatch_***: DS2 resampled 5-min OHLC differs from FV1 by > 0.1%.")
L("  Tolerance accounts for rounding and minor source differences.")
L("- **volume_mismatch**: DS2 resampled volume differs from FV1 by > 20%.")
L("")
L("*Report generated by validate_all_datasets.py*")

report_path = OUT_DIR / "validation_report.md"
with open(report_path, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")

print(f"\n  Wrote report → {report_path}")
print(f"\n  Total elapsed: {elapsed/60:.1f} min")
print("\nDONE.")
