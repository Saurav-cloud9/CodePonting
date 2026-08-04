"""
MemLabs Model Replication — author's exact CSV as PRIMARY data source.

Data
----
PRIMARY: BTCUSDT-1d_author.csv  (recovered from
  https://raw.githubusercontent.com/memlabs-research/datasets/main/BTCUSDT-1d.csv
  columns t,T,s,i,o,c,h,l,v,n — already 2020-08-19..2026-05-16, 2097 rows)
OPTIONAL context: BTCUSDT_1d_binance.csv full history (if present)

Models (exactly 3; skip Sliding Window, RL, MA-alone-only)
  A — Base AR          features=['close_log_return_lag_1']
  B — Memory combined  features=['close_log_return_lag_1','close_log_return_ma_lag_1']
  C — Online PA1       streaming SGDRegressor (not backtest_model)

Math is verbatim from 18_regime_change_author_reference_code.py.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, SGDRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

OUT_DIR = Path(__file__).resolve().parent
AUTHOR_CSV = OUT_DIR / "BTCUSDT-1d_author.csv"
AUTHOR_URL = "https://raw.githubusercontent.com/memlabs-research/datasets/main/BTCUSDT-1d.csv"
BINANCE_CSV = OUT_DIR / "BTCUSDT_1d_binance.csv"

np.random.seed(0)


# ---------------------------------------------------------------------------
# Author's backtest_model() verbatim (reference lines 44-62)
# ---------------------------------------------------------------------------
def backtest_model(df, features, target, test_split=0.25):
    df = df.dropna()

    df_train, df_test = train_test_split(df, test_size=test_split, shuffle=False)

    X_train, X_test, y_train, y_test = (
        df_train[features],
        df_test[features],
        df_train[target],
        df_test[target],
    )

    model = LinearRegression()
    model.fit(X_train, y_train)
    print(model.coef_, model.intercept_)

    backtest = df.copy()
    backtest["y_hat"] = model.predict(backtest[features])
    backtest["signal"] = np.sign(backtest["y_hat"])
    backtest["trade_log_return"] = backtest["close_log_return"] * backtest["signal"]
    backtest["cum_trade_log_return"] = backtest["trade_log_return"].cumsum()

    return model, backtest


def ensure_author_csv() -> Path:
    if AUTHOR_CSV.exists():
        return AUTHOR_CSV
    print(f"Downloading author CSV from {AUTHOR_URL} ...")
    df = pd.read_csv(AUTHOR_URL)
    df.to_csv(AUTHOR_CSV, index=False)
    print(f"Saved {len(df)} rows -> {AUTHOR_CSV.name}")
    return AUTHOR_CSV


def load_author() -> pd.DataFrame:
    path = ensure_author_csv()
    df = pd.read_csv(path)
    df["t"] = pd.to_datetime(df["t"])
    df = df.set_index("t").sort_index()
    # Author code uses column `c` directly — keep as-is
    return df


def load_binance_full() -> pd.DataFrame | None:
    if not BINANCE_CSV.exists():
        return None
    raw = pd.read_csv(BINANCE_CSV)
    raw["date"] = pd.to_datetime(raw["date"])
    raw = raw.sort_values("date").set_index("date")
    raw["c"] = raw["close"]
    return raw


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Shared setup (author lines 40-41, 74). Operates on a copy."""
    out = df.copy()
    out["close_log_return"] = np.log(out["c"] / out["c"].shift())
    out["close_log_return_lag_1"] = out["close_log_return"].shift()
    # rolling of the LAG series — not of close_log_return (leakage trap)
    out["close_log_return_ma_lag_1"] = out["close_log_return_lag_1"].rolling(40).mean()
    return out


def run_online_learning(df: pd.DataFrame):
    """Author lines 91-166 streaming loop, verbatim math."""
    df_clean = df.dropna()
    features = ["close_log_return_lag_1"]
    target = "close_log_return"

    X_stream = df_clean[features].to_numpy()
    y_stream = df_clean[target].to_numpy()

    model = SGDRegressor(
        loss="epsilon_insensitive",
        epsilon=0.0002,
        penalty=None,
        learning_rate="pa1",
        eta0=0.01,
        random_state=69,
    )
    scaler = StandardScaler()
    records = []

    for t in range(len(X_stream)):
        X_t = X_stream[t].reshape(1, -1)
        y_t = np.array([y_stream[t]])

        scaler.partial_fit(X_t)
        X_t_scaled = scaler.transform(X_t)

        if t == 0:
            pred_y = 0.0
        else:
            pred_y = model.predict(X_t_scaled)[0]

        if t > 0 and y_t[0] != 0 and pred_y != 0:
            sign_match = "YES" if np.sign(y_t[0]) == np.sign(pred_y) else "NO"
        else:
            sign_match = "Warmup"

        model.partial_fit(X_t_scaled, y_t)

        current_weight = model.coef_[0]
        current_bias = model.intercept_[0]
        signal = np.sign(pred_y)
        trade_log_return = signal * y_t[0]

        if sign_match != "Warmup":
            records.append(
                {
                    "tick": t,
                    "sign_match": sign_match,
                    "model_weight": current_weight,
                    "model_bias": current_bias,
                    "signal": signal,
                    "trade_log_return": trade_log_return,
                }
            )

    df_results = pd.DataFrame(records).set_index("tick")
    df_results["cum_trade_log_return"] = df_results["trade_log_return"].cumsum()

    evaluated_mask = df_results["sign_match"].isin(["YES", "NO"])
    hit_rate = (
        (df_results[evaluated_mask]["sign_match"] == "YES").mean() * 100
        if evaluated_mask.sum() > 0
        else float("nan")
    )
    print(f"\nDataframe Evaluated Hit Rate: {hit_rate:.2f}%")

    final_weight = float(df_results["model_weight"].iloc[-1])
    final_bias = float(df_results["model_bias"].iloc[-1])
    return model, df_results, hit_rate, final_weight, final_bias


def signal_counts(signal: pd.Series) -> dict:
    vc = signal.value_counts().to_dict()
    return {
        "buy_plus1": int(vc.get(1.0, vc.get(1, 0))),
        "sell_minus1": int(vc.get(-1.0, vc.get(-1, 0))),
        "zero": int(vc.get(0.0, vc.get(0, 0))),
    }


def summarize_ab(label: str, model, backtest: pd.DataFrame) -> dict:
    counts = signal_counts(backtest["signal"])
    final_cum = float(backtest["cum_trade_log_return"].iloc[-1])
    win_rate = float((np.sign(backtest["trade_log_return"]) > 0).mean())
    coef = [float(x) for x in np.atleast_1d(model.coef_)]
    intercept = float(model.intercept_)
    print(f"\n=== {label} ===")
    print(f"  n_rows={len(backtest)}")
    print(f"  coef_={coef}")
    print(f"  intercept_={intercept}")
    print(
        f"  signal +1={counts['buy_plus1']} -1={counts['sell_minus1']} 0={counts['zero']}"
    )
    print(f"  final_cum={final_cum:.6f}")
    print(f"  win_rate={win_rate:.6f} ({win_rate*100:.2f}%)")
    return {
        "label": label,
        "n_rows": len(backtest),
        "coef": coef,
        "intercept": intercept,
        "counts": counts,
        "final_cum": final_cum,
        "win_rate": win_rate,
        "hit_rate_pct": None,
        "final_weight": None,
        "final_bias": None,
    }


def summarize_c(label, df_results, hit_rate, final_weight, final_bias) -> dict:
    counts = signal_counts(df_results["signal"])
    final_cum = float(df_results["cum_trade_log_return"].iloc[-1])
    print(f"\n=== {label} ===")
    print(f"  n_evaluated={len(df_results)}")
    print(f"  final_weight={final_weight} final_bias={final_bias}")
    print(
        f"  signal +1={counts['buy_plus1']} -1={counts['sell_minus1']} 0={counts['zero']}"
    )
    print(f"  final_cum={final_cum:.6f}")
    print(f"  hit_rate={hit_rate:.2f}%")
    return {
        "label": label,
        "n_rows": len(df_results),
        "coef": None,
        "intercept": None,
        "counts": counts,
        "final_cum": final_cum,
        "win_rate": None,
        "hit_rate_pct": hit_rate,
        "final_weight": final_weight,
        "final_bias": final_bias,
    }


def plot_equity(cum: pd.Series, close: pd.Series, title: str, out_path: Path):
    plt.style.use("dark_background")
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(cum.values, color="#00d4ff", linewidth=1.4, label="cum trade_log_return")
    ax1.set_ylabel("Cumulative trade log return", color="#00d4ff")
    ax1.tick_params(axis="y", labelcolor="#00d4ff")
    ax1.set_xlabel("bar index")
    ax2 = ax1.twinx()
    close_vals = close.values
    if len(close_vals) != len(cum) and len(close_vals) > len(cum):
        close_vals = close_vals[-len(cum) :]
    ax2.plot(close_vals, color="#ffaa00", linewidth=1.0, alpha=0.75, label="close price")
    ax2.set_ylabel("Close price", color="#ffaa00")
    ax2.tick_params(axis="y", labelcolor="#ffaa00")
    ax1.set_title(title)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", framealpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  saved plot -> {out_path.name}")


def run_suite(raw: pd.DataFrame, tag: str, save_plots: bool) -> dict:
    print("\n" + "=" * 72)
    print(f"RUN: {tag}  n_raw={len(raw)}  span={raw.index.min().date()}..{raw.index.max().date()}")
    print("=" * 72)

    df = add_features(raw)
    results = {}

    # Model A — author ran this BEFORE adding MA, so dropna only sees lag NaNs
    df_a = df[["c", "close_log_return", "close_log_return_lag_1"]].copy()
    model_a, bt_a = backtest_model(
        df_a, features=["close_log_return_lag_1"], target="close_log_return"
    )
    results["A"] = summarize_ab(f"Model A [{tag}]", model_a, bt_a)
    if save_plots:
        plot_equity(
            bt_a["cum_trade_log_return"],
            bt_a["c"],
            f"Model A — Base AR | author CSV {raw.index.min().date()}..{raw.index.max().date()}",
            OUT_DIR / "20_btc_model_A.png",
        )

    # Model B — combined only (skip MA-alone line 77)
    df_b = df[
        ["c", "close_log_return", "close_log_return_lag_1", "close_log_return_ma_lag_1"]
    ].copy()
    model_b, bt_b = backtest_model(
        df_b,
        features=["close_log_return_lag_1", "close_log_return_ma_lag_1"],
        target="close_log_return",
    )
    results["B"] = summarize_ab(f"Model B [{tag}]", model_b, bt_b)
    if save_plots:
        plot_equity(
            bt_b["cum_trade_log_return"],
            bt_b["c"],
            f"Model B — Encoding Memory (combined) | author CSV",
            OUT_DIR / "20_btc_model_B.png",
        )

    # Model C — author dropna() after MA exists in notebook state
    df_c = df[
        ["c", "close_log_return", "close_log_return_lag_1", "close_log_return_ma_lag_1"]
    ].copy()
    _, df_results, hit_rate, fw, fb = run_online_learning(df_c)
    results["C"] = summarize_c(f"Model C [{tag}]", df_results, hit_rate, fw, fb)
    if save_plots:
        df_clean = df_c.dropna()
        close_for_plot = df_clean["c"].iloc[df_results.index]
        plot_equity(
            df_results["cum_trade_log_return"],
            close_for_plot,
            f"Model C — Online PA1 | author CSV",
            OUT_DIR / "20_btc_model_C.png",
        )

    # Also Model C lag-only dropna (if A-time notebook state) for comparison print
    df_c_lag = df[["c", "close_log_return", "close_log_return_lag_1"]].copy()
    _, df_results2, hit2, fw2, fb2 = run_online_learning(df_c_lag)
    results["C_lag_only_dropna"] = summarize_c(
        f"Model C lag-only-dropna [{tag}]", df_results2, hit2, fw2, fb2
    )

    results["_meta"] = {
        "tag": tag,
        "raw_n": len(raw),
        "start": str(raw.index.min().date()),
        "end": str(raw.index.max().date()),
    }
    return results


def dump_metrics(all_results: dict) -> str:
    lines = []
    for tag, res in all_results.items():
        meta = res["_meta"]
        lines.append(f"## {tag}")
        lines.append(f"raw_n={meta['raw_n']} span={meta['start']}..{meta['end']}")
        for key in res:
            if key.startswith("_"):
                continue
            r = res[key]
            lines.append(f"### {key}")
            lines.append(f"n_rows={r['n_rows']}")
            if r["coef"] is not None:
                lines.append(f"coef_={r['coef']}")
                lines.append(f"intercept_={r['intercept']}")
            else:
                lines.append(
                    f"final_weight={r['final_weight']} final_bias={r['final_bias']}"
                )
            c = r["counts"]
            lines.append(
                f"signal +1={c['buy_plus1']} -1={c['sell_minus1']} 0={c['zero']}"
            )
            lines.append(f"final_cum={r['final_cum']}")
            if r["win_rate"] is not None:
                lines.append(f"win_rate={r['win_rate']}")
            if r["hit_rate_pct"] is not None:
                lines.append(f"hit_rate_pct={r['hit_rate_pct']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    author = load_author()
    print(f"Author CSV: n={len(author)}  {author.index.min().date()} -> {author.index.max().date()}")
    if len(author) != 2097:
        print(f"WARNING: expected 2097 raw rows, got {len(author)}")

    all_results = {}
    all_results["author_csv"] = run_suite(author, tag="author_csv", save_plots=True)

    binance = load_binance_full()
    if binance is not None:
        all_results["binance_full"] = run_suite(
            binance, tag="binance_full", save_plots=False
        )
    else:
        print("Binance full-history CSV not found — skipping context run.")

    dump_path = OUT_DIR / "20_btc_models_metrics_dump.txt"
    dump_path.write_text(dump_metrics(all_results), encoding="utf-8")
    print(f"\nMetrics dump -> {dump_path.name}")
    print("Done. PNGs: 20_btc_model_{A,B,C}.png")


if __name__ == "__main__":
    main()
