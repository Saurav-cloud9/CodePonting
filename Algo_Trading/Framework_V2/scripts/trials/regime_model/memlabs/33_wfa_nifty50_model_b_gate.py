"""
Step 33 — Walk-Forward Analysis (WFA) of NIFTY50 Model B gate on fv2 SHORT trades.

Same methodology as script 32 / notebook 31:
  NIFTY50 daily Model B: close_log_return_lag_1 + close_log_return_ma_lag_1
  → close_log_return; Train-only fit; signal = sign(y_hat); gate SHORT trades
  (ma_rejection_v1_core.py) only when that day's NIFTY signal is Sell (-1).

Unlike script 32's single chronological 75/25 split, this refits Model B on
each rolling Train window and evaluates gated SHORT trades only on that fold's
Test window.

Config 1 — 3yr Train / 1yr Test, fixed-size, slide 1yr
Config 2 — 5yr Train / 20mo Test, fixed-size, slide 20mo

Outputs:
  33_wfa_config1_results.csv
  33_wfa_config2_results.csv
  33_wfa_summary.md
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from sklearn.linear_model import LinearRegression

KITE_BOT_SCRIPTS = Path(
    r"C:\Users\Saurav\CodePonting\Algo_Trading\kite_oracle_papertrading\scripts"
)
sys.path.insert(0, str(KITE_BOT_SCRIPTS))
from ma_rejection_v1_core import StockState, process_bar  # noqa: E402

DS3_DIR = Path(
    r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3"
)
NIFTY_PATH = Path(
    r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\daily\NIFTY50.parquet"
)
OUT_DIR = Path(__file__).resolve().parent

SYMBOLS = [
    "ADANIPORTS",
    "ASHOKLEY",
    "AXISBANK",
    "BAJFINANCE",
    "BANDHANBNK",
    "BHARTIARTL",
    "CIPLA",
    "COALINDIA",
    "DABUR",
    "DIVISLAB",
    "HDFCBANK",
    "HINDALCO",
    "ICICIBANK",
    "INDUSINDBK",
    "INFY",
    "ITC",
    "JSWSTEEL",
    "NATIONALUM",
    "NTPC",
    "ONGC",
    "PNB",
    "POWERGRID",
    "RELIANCE",
    "SBIN",
    "SUNPHARMA",
    "TATAMOTORS",
    "TATASTEEL",
    "TECHM",
    "VEDL",
    "WIPRO",
]

FEATURES = ["close_log_return_lag_1", "close_log_return_ma_lag_1"]
DATA_END = pd.Timestamp("2026-07-31")
ANCHOR = pd.Timestamp("2015-02-01")


def zerodha_short(entry, exit_px):
    brok = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt = entry * 0.00025
    txn = (entry + exit_px) * 0.0000307
    sebi = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def load_nifty_features() -> pd.DataFrame:
    daily = pd.read_parquet(NIFTY_PATH)
    daily["datetime"] = pd.to_datetime(daily["datetime"])
    if daily["datetime"].dt.tz is not None:
        daily["datetime"] = daily["datetime"].apply(lambda x: x.replace(tzinfo=None))
    daily = daily.set_index("datetime").sort_index()
    daily = daily.rename(columns={"close": "c"})[["c"]]
    daily["close_log_return"] = np.log(daily["c"] / daily["c"].shift())
    daily["close_log_return_lag_1"] = daily["close_log_return"].shift()
    daily["close_log_return_ma_lag_1"] = daily["close_log_return_lag_1"].rolling(40).mean()
    return daily.dropna(subset=FEATURES + ["close_log_return"])


def load_bars(symbol: str) -> pd.DataFrame:
    f = DS3_DIR / f"{symbol}.parquet"
    df = pd.read_parquet(f, columns=["datetime", "open", "high", "low", "close"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    if df["datetime"].dt.tz is not None:
        df["datetime"] = df["datetime"].apply(lambda x: x.replace(tzinfo=None))
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] <= 0, col] = np.nan
    df["date"] = df["datetime"].dt.date
    df["hour"] = df["datetime"].dt.hour
    df.sort_values("datetime", inplace=True, kind="mergesort")
    df.reset_index(drop=True, inplace=True)
    return df


def build_short_trades(symbol: str, bars: pd.DataFrame) -> pd.DataFrame:
    state = StockState()
    trades = []
    for bar in bars.to_dict("records"):
        process_bar(symbol, bar, state, trades)
    tdf = pd.DataFrame(trades)
    if len(tdf) == 0:
        return tdf
    tdf["entry_dt"] = pd.to_datetime(tdf["entry_dt"])
    tdf["zpnl"] = tdf.apply(
        lambda r: r["pnl"] - zerodha_short(r["entry"], r["exit_price"]), axis=1
    )
    tdf["entry_date"] = tdf["entry_dt"].dt.normalize()
    return tdf


def summarize(sub: pd.DataFrame) -> dict:
    n = len(sub)
    if n == 0:
        return {"n": 0, "pf": 0.0, "pnl": 0.0, "zpnl": 0.0, "zpf": 0.0}
    gp = sub[sub["pnl"] > 0]["pnl"].sum()
    gl = -sub[sub["pnl"] <= 0]["pnl"].sum()
    pf = gp / gl if gl > 0 else 0.0
    zw = sub[sub["zpnl"] > 0]["zpnl"].sum()
    zl = -sub[sub["zpnl"] <= 0]["zpnl"].sum()
    zpf = zw / zl if zl > 0 else 0.0
    return {
        "n": n,
        "pf": round(float(pf), 3),
        "pnl": round(float(sub["pnl"].sum()), 2),
        "zpnl": round(float(sub["zpnl"].sum()), 2),
        "zpf": round(float(zpf), 3),
    }


def generate_folds_config1(data_end: pd.Timestamp = DATA_END) -> list[dict]:
    """3yr train / 1yr test, slide by 1 year. Final test may be partial."""
    folds = []
    fold_num = 1
    train_start = ANCHOR
    while True:
        train_end = train_start + relativedelta(years=3)
        test_start = train_end
        test_end = test_start + relativedelta(years=1)
        if test_start > data_end:
            break
        actual_test_end = min(test_end, data_end + pd.Timedelta(days=1))  # exclusive end
        # Need at least some room after train for a test slice
        if test_start >= data_end:
            break
        folds.append(
            {
                "fold_num": fold_num,
                "train_start": train_start,
                "train_end": train_end,
                "test_start": test_start,
                "test_end": actual_test_end,  # exclusive for filtering; report as last inclusive day
            }
        )
        fold_num += 1
        train_start = train_start + relativedelta(years=1)
        # stop if next train would leave no test days
        if train_start + relativedelta(years=3) >= data_end:
            # still allow last fold if train fits and some test remains
            next_train_end = train_start + relativedelta(years=3)
            if next_train_end >= data_end:
                break
    return folds


def generate_folds_config2(data_end: pd.Timestamp = DATA_END) -> list[dict]:
    """5yr train / 20mo test, slide by 20 months. Final test may be partial."""
    folds = []
    fold_num = 1
    train_start = ANCHOR
    while True:
        train_end = train_start + relativedelta(years=5)
        test_start = train_end
        test_end = test_start + relativedelta(months=20)
        if test_start >= data_end:
            break
        actual_test_end = min(test_end, data_end + pd.Timedelta(days=1))
        folds.append(
            {
                "fold_num": fold_num,
                "train_start": train_start,
                "train_end": train_end,
                "test_start": test_start,
                "test_end": actual_test_end,
            }
        )
        fold_num += 1
        train_start = train_start + relativedelta(months=20)
        if train_start + relativedelta(years=5) >= data_end:
            next_train_end = train_start + relativedelta(years=5)
            if next_train_end >= data_end:
                break
    return folds


def fit_signal_on_fold(nifty: pd.DataFrame, fold: dict) -> pd.Series:
    """
    Fit Model B on Train window ONLY; predict signal on Test window.
    Returns Series indexed by datetime (normalized dates) of test-period signal.
    """
    train_mask = (nifty.index >= fold["train_start"]) & (nifty.index < fold["train_end"])
    test_mask = (nifty.index >= fold["test_start"]) & (nifty.index < fold["test_end"])
    train = nifty.loc[train_mask]
    test = nifty.loc[test_mask]
    if len(train) < 50 or len(test) == 0:
        return pd.Series(dtype=float, name="signal")

    model = LinearRegression()
    model.fit(train[FEATURES], train["close_log_return"])
    y_hat = model.predict(test[FEATURES])
    signal = pd.Series(np.sign(y_hat), index=test.index, name="signal")
    return signal


def date_str(ts: pd.Timestamp) -> str:
    return pd.Timestamp(ts).strftime("%Y-%m-%d")


def report_end_inclusive(test_end_exclusive: pd.Timestamp) -> str:
    """CSV stores last calendar day included in test (exclusive bound - 1 day)."""
    return date_str(pd.Timestamp(test_end_exclusive) - pd.Timedelta(days=1))


def run_config(
    config_name: str,
    folds: list[dict],
    nifty: pd.DataFrame,
    trade_logs: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows = []
    print(f"\n===== {config_name}: {len(folds)} folds =====")
    for fold in folds:
        signal = fit_signal_on_fold(nifty, fold)
        n_sell = int((signal == -1).sum()) if len(signal) else 0
        n_buy = int((signal == 1).sum()) if len(signal) else 0
        print(
            f"  Fold {fold['fold_num']}: "
            f"Train {date_str(fold['train_start'])}->{date_str(fold['train_end'])} "
            f"Test {date_str(fold['test_start'])}->{report_end_inclusive(fold['test_end'])} "
            f"| signal days={len(signal)} Sell={n_sell} Buy={n_buy}"
        )
        if len(signal) == 0:
            for symbol in SYMBOLS:
                rows.append(
                    {
                        "symbol": symbol,
                        "config": config_name,
                        "fold_num": fold["fold_num"],
                        "train_start": date_str(fold["train_start"]),
                        "train_end": date_str(fold["train_end"]),
                        "test_start": date_str(fold["test_start"]),
                        "test_end": report_end_inclusive(fold["test_end"]),
                        "n": 0,
                        "pf": 0.0,
                        "pnl": 0.0,
                        "zpnl": 0.0,
                        "zpf": 0.0,
                    }
                )
            continue

        sig_df = signal.to_frame()
        for symbol in SYMBOLS:
            tdf = trade_logs.get(symbol)
            if tdf is None or len(tdf) == 0:
                metrics = {"n": 0, "pf": 0.0, "pnl": 0.0, "zpnl": 0.0, "zpf": 0.0}
            else:
                in_test = (tdf["entry_date"] >= fold["test_start"]) & (
                    tdf["entry_date"] < fold["test_end"]
                )
                sub = tdf.loc[in_test].join(sig_df, on="entry_date")
                sub = sub.dropna(subset=["signal"])
                gated = sub[sub["signal"] == -1]
                metrics = summarize(gated)

            rows.append(
                {
                    "symbol": symbol,
                    "config": config_name,
                    "fold_num": fold["fold_num"],
                    "train_start": date_str(fold["train_start"]),
                    "train_end": date_str(fold["train_end"]),
                    "test_start": date_str(fold["test_start"]),
                    "test_end": report_end_inclusive(fold["test_end"]),
                    **metrics,
                }
            )
    return pd.DataFrame(rows)


def build_summary_md(c1: pd.DataFrame, c2: pd.DataFrame, folds1: list, folds2: list) -> str:
    lines = []
    lines.append("# 33 — WFA NIFTY50 Model B gate on SHORT trades")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Setup")
    lines.append("")
    lines.append(
        "- **Signal**: NIFTY50 daily Model B "
        "(`close_log_return_lag_1` + `close_log_return_ma_lag_1` → `close_log_return`), "
        "fit **per fold on Train only**, `signal = sign(y_hat)`."
    )
    lines.append(
        "- **Gate**: count a stock SHORT trade only if NIFTY signal that day is Sell (−1)."
    )
    lines.append(
        "- **Trades**: full-history SHORT log once per stock via `ma_rejection_v1_core.py`; "
        "filtered by Test `entry_dt` per fold."
    )
    lines.append("- **Costs**: `zerodha_short()` same as scripts 25–29/32.")
    lines.append(f"- **Data end**: {DATA_END.date()} (final fold Test may be partial).")
    lines.append("")
    lines.append(f"### Config 1 folds ({len(folds1)}) — 3yr Train / 1yr Test, slide 1yr")
    lines.append("")
    for f in folds1:
        lines.append(
            f"- Fold {f['fold_num']}: Train {date_str(f['train_start'])} → {date_str(f['train_end'])}, "
            f"Test {date_str(f['test_start'])} → {report_end_inclusive(f['test_end'])}"
        )
    lines.append("")
    lines.append(f"### Config 2 folds ({len(folds2)}) — 5yr Train / 20mo Test, slide 20mo")
    lines.append("")
    for f in folds2:
        lines.append(
            f"- Fold {f['fold_num']}: Train {date_str(f['train_start'])} → {date_str(f['train_end'])}, "
            f"Test {date_str(f['test_start'])} → {report_end_inclusive(f['test_end'])}"
        )
    lines.append("")
    lines.append("## Consistency table")
    lines.append("")
    lines.append(
        "Per stock, per config: how many folds have **ZPF ≥ 1.0**, mean/median ZPF, "
        "and whether edge is concentrated (max fold ZPF share of positive-ZPF mass, "
        "or top-2 folds dominate)."
    )
    lines.append("")

    def consistency_table(df: pd.DataFrame, config_name: str) -> list[str]:
        out = []
        out.append(f"### {config_name}")
        out.append("")
        out.append(
            "| symbol | folds | n_folds_zpf>=1 | mean_zpf | median_zpf | "
            "mean_n | total_zpnl | concentration |"
        )
        out.append(
            "|--------|------:|---------------:|---------:|-----------:|"
            "-------:|-----------:|---------------|"
        )
        n_folds = df["fold_num"].nunique()
        rows_summary = []
        for symbol, g in df.groupby("symbol"):
            zpf = g["zpf"].astype(float)
            n_ok = int((zpf >= 1.0).sum())
            mean_zpf = float(zpf.mean())
            med_zpf = float(zpf.median())
            mean_n = float(g["n"].mean())
            total_zpnl = float(g["zpnl"].sum())
            # Concentration: among folds with n>0, is edge in 1-2 folds?
            pos = g[g["zpnl"] > 0]
            if len(pos) == 0 or total_zpnl <= 0:
                conc = "none/neg"
            else:
                ranked = pos.sort_values("zpnl", ascending=False)
                top1 = float(ranked.iloc[0]["zpnl"]) / total_zpnl if total_zpnl else 0
                top2 = float(ranked.head(2)["zpnl"].sum()) / total_zpnl if total_zpnl else 0
                if top1 >= 0.70:
                    conc = f"1-fold ({top1:.0%} zpnl)"
                elif top2 >= 0.80:
                    conc = f"2-fold ({top2:.0%} zpnl)"
                else:
                    conc = f"spread (top1 {top1:.0%})"
            rows_summary.append(
                (
                    symbol,
                    n_ok,
                    mean_zpf,
                    med_zpf,
                    mean_n,
                    total_zpnl,
                    conc,
                    n_folds,
                )
            )
        # sort by consistency then mean_zpf
        rows_summary.sort(key=lambda r: (r[1], r[2]), reverse=True)
        for symbol, n_ok, mean_zpf, med_zpf, mean_n, total_zpnl, conc, n_folds in rows_summary:
            out.append(
                f"| {symbol} | {n_folds} | {n_ok} | {mean_zpf:.3f} | {med_zpf:.3f} | "
                f"{mean_n:.1f} | {total_zpnl:.2f} | {conc} |"
            )
        out.append("")
        return out

    lines.extend(consistency_table(c1, "Config 1 (3yr/1yr)"))
    lines.extend(consistency_table(c2, "Config 2 (5yr/20mo)"))

    lines.append("## Reading notes")
    lines.append("")
    lines.append(
        "- **Consistency count** (folds with ZPF ≥ 1.0) is the primary question — "
        "not just average ZPF."
    )
    lines.append(
        "- **concentration = 1-fold / 2-fold** means most positive ZPnL came from "
        "one or two windows (fragile edge)."
    )
    lines.append(
        "- **spread** means ZPnL is distributed across more folds (more robust)."
    )
    lines.append(
        "- Stocks with few trades in a fold (low `mean_n`) have noisy ZPF; treat carefully."
    )
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append("- `33_wfa_config1_results.csv`")
    lines.append("- `33_wfa_config2_results.csv`")
    lines.append("- `33_wfa_summary.md` (this file)")
    lines.append("")
    return "\n".join(lines)


def main():
    print("Loading NIFTY50 features...")
    nifty = load_nifty_features()
    print(
        f"  NIFTY rows with features: {len(nifty)} "
        f"({nifty.index.min().date()} → {nifty.index.max().date()})"
    )

    folds1 = generate_folds_config1()
    folds2 = generate_folds_config2()
    print(f"Config 1 folds: {len(folds1)}")
    for f in folds1:
        print(
            f"  {f['fold_num']}: train {date_str(f['train_start'])}->{date_str(f['train_end'])} "
            f"test {date_str(f['test_start'])}->{report_end_inclusive(f['test_end'])}"
        )
    print(f"Config 2 folds: {len(folds2)}")
    for f in folds2:
        print(
            f"  {f['fold_num']}: train {date_str(f['train_start'])}->{date_str(f['train_end'])} "
            f"test {date_str(f['test_start'])}->{report_end_inclusive(f['test_end'])}"
        )

    print("\nBuilding full-history SHORT trade logs (once per stock)...")
    trade_logs: dict[str, pd.DataFrame] = {}
    for symbol in SYMBOLS:
        bars = load_bars(symbol)
        tdf = build_short_trades(symbol, bars)
        trade_logs[symbol] = tdf
        print(f"  {symbol}: {len(tdf)} short trades")

    c1 = run_config("config1_3y1y", folds1, nifty, trade_logs)
    c2 = run_config("config2_5y20mo", folds2, nifty, trade_logs)

    p1 = OUT_DIR / "33_wfa_config1_results.csv"
    p2 = OUT_DIR / "33_wfa_config2_results.csv"
    c1.to_csv(p1, index=False)
    c2.to_csv(p2, index=False)
    print(f"\nSaved {len(c1)} rows → {p1}")
    print(f"Saved {len(c2)} rows → {p2}")

    md = build_summary_md(c1, c2, folds1, folds2)
    pmd = OUT_DIR / "33_wfa_summary.md"
    pmd.write_text(md, encoding="utf-8")
    print(f"Saved summary → {pmd}")

    # quick console peek: top consistency config1
    print("\n--- Config1 consistency (folds with ZPF>=1.0) ---")
    for symbol, g in c1.groupby("symbol"):
        n_ok = int((g["zpf"] >= 1.0).sum())
        print(
            f"  {symbol:12s}  {n_ok}/{g['fold_num'].nunique()}  "
            f"mean_zpf={g['zpf'].mean():.3f}  med={g['zpf'].median():.3f}"
        )


if __name__ == "__main__":
    main()
