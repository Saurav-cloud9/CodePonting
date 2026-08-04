"""
Methodical investigation of Model A/B gaps vs author's printed numbers,
using his exact recovered CSV: BTCUSDT-1d_author.csv
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

HIS_A_COEF = -0.02962972
HIS_A_INT = 0.0014044601596437902
HIS_A_BUY, HIS_A_SELL = 1891, 104
HIS_B_COEF = np.array([-0.03028802, -3.2349553])
HIS_B_INT = 0.00585814582674094
HIS_B_BUY, HIS_B_SELL = 1680, 307

np.random.seed(0)


def load_author():
    btcusdt = pd.read_csv("BTCUSDT-1d_author.csv")
    btcusdt["t"] = pd.to_datetime(btcusdt["t"])
    btcusdt = btcusdt.set_index("t")
    return btcusdt


def backtest_model(df, features, target, test_split=0.25, label=""):
    n_before = len(df)
    df = df.dropna()
    print(f"\n--- {label} ---")
    print(f"  n before dropna={n_before}, after={len(df)}, features={features}")
    df_train, df_test = train_test_split(df, test_size=test_split, shuffle=False)
    print(f"  train={len(df_train)} test={len(df_test)}  first_train={df_train.index[0].date()} last_train={df_train.index[-1].date()}")
    print(f"  first_test={df_test.index[0].date()} last_test={df_test.index[-1].date()}")
    X_train = df_train[features]
    y_train = df_train[target]
    model = LinearRegression()
    model.fit(X_train, y_train)
    print(f"  coef_={model.coef_}")
    print(f"  intercept_={model.intercept_}")
    print(f"  X_train shape={X_train.shape} dtypes={list(X_train.dtypes)}")
    backtest = df.copy()
    backtest["y_hat"] = model.predict(backtest[features])
    backtest["signal"] = np.sign(backtest["y_hat"])
    backtest["trade_log_return"] = backtest["close_log_return"] * backtest["signal"]
    backtest["cum_trade_log_return"] = backtest["trade_log_return"].cumsum()
    vc = backtest["signal"].value_counts()
    print(f"  signal value_counts:\n{vc}")
    print(f"  final_cum={backtest['cum_trade_log_return'].iloc[-1]:.6f}")
    print(f"  winrate={(np.sign(backtest['trade_log_return']) > 0).mean():.6f}")
    return model, backtest, df_train, df_test


def main():
    btcusdt = load_author()
    print("=== RAW LOAD ===")
    print(f"n={len(btcusdt)} cols={list(btcusdt.columns)}")
    print(f"c dtype={btcusdt['c'].dtype} head c={btcusdt['c'].head(3).tolist()}")
    print(f"span={btcusdt.index.min().date()} -> {btcusdt.index.max().date()}")

    # ---- Author exact feature order ----
    btcusdt["close_log_return"] = np.log(btcusdt["c"] / btcusdt["c"].shift())
    btcusdt["close_log_return_lag_1"] = btcusdt["close_log_return"].shift()

    print("\n=== AFTER LAG FEATURES (pre-MA, Model A notebook state) ===")
    print(f"n={len(btcusdt)}")
    print(btcusdt[["c", "close_log_return", "close_log_return_lag_1"]].head(5))
    print(btcusdt[["c", "close_log_return", "close_log_return_lag_1"]].tail(3))

    # ========== MODEL A variants ==========
    print("\n" + "=" * 70)
    print("MODEL A INVESTIGATION")
    print("=" * 70)
    print(f"HIS: coef=[{HIS_A_COEF}], int={HIS_A_INT}, buy={HIS_A_BUY}, sell={HIS_A_SELL}")

    # A1: exact author path - only cols present at Model A time
    df_a = btcusdt[["c", "close_log_return", "close_log_return_lag_1"]].copy()
    m_a, bt_a, tr_a, te_a = backtest_model(
        df_a, ["close_log_return_lag_1"], "close_log_return", label="A1 author path lag-only cols"
    )
    print(f"  DELTA coef={m_a.coef_[0] - HIS_A_COEF:.12e}  int={m_a.intercept_ - HIS_A_INT:.12e}")
    print(f"  DELTA buy={int(bt_a['signal'].value_counts().get(1.0, 0)) - HIS_A_BUY}")

    # A2: float32
    df_a32 = df_a.copy()
    for col in ["c", "close_log_return", "close_log_return_lag_1"]:
        df_a32[col] = df_a32[col].astype(np.float32)
    m_a32, bt_a32, _, _ = backtest_model(
        df_a32, ["close_log_return_lag_1"], "close_log_return", label="A2 float32 features"
    )

    # A3: different test_split values that might hit his buy count total 1995
    # 1891+104=1995 signals. If n after dropna = 1995, what was raw?
    print("\n--- A3: what n after dropna would give signal total 1995? ---")
    print("  our n after dropna for A:", len(df_a.dropna()))
    print("  his signal total:", HIS_A_BUY + HIS_A_SELL)

    # A4: predict only on test set?
    print("\n--- A4: signal counts on TEST only ---")
    yhat_test = m_a.predict(te_a[["close_log_return_lag_1"]])
    sig_test = np.sign(yhat_test)
    print(pd.Series(sig_test).value_counts())

    # A5: signal on train only
    print("\n--- A5: signal counts on TRAIN only ---")
    yhat_tr = m_a.predict(tr_a[["close_log_return_lag_1"]])
    print(pd.Series(np.sign(yhat_tr)).value_counts())

    # A6: use his printed coef to generate signals on our data
    print("\n--- A6: his printed weights applied to our full A frame ---")
    df_clean = df_a.dropna()
    yhat_his = HIS_A_COEF * df_clean["close_log_return_lag_1"].to_numpy() + HIS_A_INT
    sig_his = np.sign(yhat_his)
    print(pd.Series(sig_his).value_counts())
    # compare to our model signals
    yhat_ours = m_a.predict(df_clean[["close_log_return_lag_1"]])
    n_diff = (np.sign(yhat_his) != np.sign(yhat_ours)).sum()
    print(f"  rows where his weights vs our model disagree on sign: {n_diff}")

    # A7: borderline y_hat near zero
    print("\n--- A7: y_hat magnitude distribution (ours) ---")
    yh = m_a.predict(df_clean[["close_log_return_lag_1"]])
    print(f"  min={yh.min():.6e} max={yh.max():.6e} n_near0_1e-6={(np.abs(yh)<1e-6).sum()}")
    print(f"  n_neg y_hat={(yh<0).sum()} n_pos={(yh>0).sum()} n_zero={(yh==0).sum()}")

    # ========== MODEL B ==========
    print("\n" + "=" * 70)
    print("MODEL B INVESTIGATION (PRIORITY)")
    print("=" * 70)
    print(f"HIS: coef={HIS_B_COEF}, int={HIS_B_INT}, buy={HIS_B_BUY}, sell={HIS_B_SELL}")

    # Author line 74
    btcusdt["close_log_return_ma_lag_1"] = btcusdt["close_log_return_lag_1"].rolling(40).mean()

    print("\n=== AFTER MA FEATURE ===")
    print(btcusdt[["close_log_return", "close_log_return_lag_1", "close_log_return_ma_lag_1"]].iloc[38:45])

    # B1: exact author order
    m_b, bt_b, tr_b, te_b = backtest_model(
        btcusdt,
        ["close_log_return_lag_1", "close_log_return_ma_lag_1"],
        "close_log_return",
        label="B1 author path full df after MA",
    )
    print(f"  DELTA coef={m_b.coef_ - HIS_B_COEF}")
    print(f"  DELTA int={m_b.intercept_ - HIS_B_INT:.12e}")

    # B2: only needed columns
    df_b = btcusdt[
        ["c", "close_log_return", "close_log_return_lag_1", "close_log_return_ma_lag_1"]
    ].copy()
    m_b2, bt_b2, _, _ = backtest_model(
        df_b,
        ["close_log_return_lag_1", "close_log_return_ma_lag_1"],
        "close_log_return",
        label="B2 restricted columns only",
    )

    # B3: MA of return then lag (shift after rolling)
    tmp = btcusdt[["c"]].copy()
    tmp["close_log_return"] = np.log(tmp["c"] / tmp["c"].shift())
    tmp["close_log_return_lag_1"] = tmp["close_log_return"].shift()
    tmp["close_log_return_ma_lag_1"] = tmp["close_log_return"].rolling(40).mean().shift()
    m_b3, _, _, _ = backtest_model(
        tmp,
        ["close_log_return_lag_1", "close_log_return_ma_lag_1"],
        "close_log_return",
        label="B3 MA(return).shift() i.e. lag of MA",
    )

    # B4: MA of return directly (leakage-ish)
    tmp = btcusdt[["c"]].copy()
    tmp["close_log_return"] = np.log(tmp["c"] / tmp["c"].shift())
    tmp["close_log_return_lag_1"] = tmp["close_log_return"].shift()
    tmp["close_log_return_ma_lag_1"] = tmp["close_log_return"].rolling(40).mean()
    m_b4, _, _, _ = backtest_model(
        tmp,
        ["close_log_return_lag_1", "close_log_return_ma_lag_1"],
        "close_log_return",
        label="B4 MA(return) not MA(lag)",
    )

    # B5: feature order swapped
    m_b5, _, _, _ = backtest_model(
        df_b,
        ["close_log_return_ma_lag_1", "close_log_return_lag_1"],
        "close_log_return",
        label="B5 feature order swapped [ma, lag]",
    )

    # B6: MA-alone first then somehow combined differently? 
    # Maybe he used rolling window of 40 on something else
    for w in [20, 30, 40, 50, 60]:
        tmp = btcusdt[["c", "close_log_return", "close_log_return_lag_1"]].copy()
        tmp["close_log_return_ma_lag_1"] = tmp["close_log_return_lag_1"].rolling(w).mean()
        d = tmp.dropna()
        tr, te = train_test_split(d, test_size=0.25, shuffle=False)
        m = LinearRegression().fit(
            tr[["close_log_return_lag_1", "close_log_return_ma_lag_1"]],
            tr["close_log_return"],
        )
        print(f"  B6 window={w}: coef={m.coef_} int={m.intercept_:.6f}")

    # B7: target = close_return (pct) not log?
    tmp = btcusdt[["c"]].copy()
    tmp["close_return"] = tmp["c"].pct_change()
    tmp["close_log_return"] = np.log(tmp["c"] / tmp["c"].shift())  # keep name for trade?
    tmp["close_log_return_lag_1"] = tmp["close_log_return"].shift()
    tmp["close_log_return_ma_lag_1"] = tmp["close_log_return_lag_1"].rolling(40).mean()
    # fit on pct target
    d = tmp.dropna()
    tr, te = train_test_split(d, test_size=0.25, shuffle=False)
    m = LinearRegression().fit(
        tr[["close_log_return_lag_1", "close_log_return_ma_lag_1"]],
        tr["close_return"],
    )
    print(f"\n  B7 target=pct_change: coef={m.coef_} int={m.intercept_}")

    # B8: scale features (StandardScaler before LR)?
    from sklearn.preprocessing import StandardScaler
    d = df_b.dropna()
    tr, te = train_test_split(d, test_size=0.25, shuffle=False)
    sc = StandardScaler()
    Xtr = sc.fit_transform(tr[["close_log_return_lag_1", "close_log_return_ma_lag_1"]])
    m = LinearRegression().fit(Xtr, tr["close_log_return"])
    print(f"  B8 scaled X: coef={m.coef_} int={m.intercept_}")

    # B9: use np.linalg.lstsq
    d = df_b.dropna()
    tr, te = train_test_split(d, test_size=0.25, shuffle=False)
    X = tr[["close_log_return_lag_1", "close_log_return_ma_lag_1"]].to_numpy()
    y = tr["close_log_return"].to_numpy()
    X1 = np.column_stack([np.ones(len(X)), X])
    beta, _, rank, s = np.linalg.lstsq(X1, y, rcond=None)
    print(f"  B9 lstsq beta={beta} rank={rank} singular={s}")
    print(f"  cond(X)={np.linalg.cond(X):.2f}")
    print(f"  corr=\n{tr[['close_log_return_lag_1','close_log_return_ma_lag_1']].corr()}")

    # B10: maybe he centered features? or used Ridge?
    from sklearn.linear_model import Ridge, HuberRegressor, SGDRegressor
    for name, est in [
        ("Ridge1e-3", Ridge(alpha=1e-3)),
        ("Ridge1", Ridge(alpha=1.0)),
        ("Huber", HuberRegressor()),
    ]:
        est.fit(tr[["close_log_return_lag_1", "close_log_return_ma_lag_1"]], tr["close_log_return"])
        print(f"  B10 {name}: coef={est.coef_} int={est.intercept_}")

    # B11: train on FULL data (no split) — sometimes people fit on all
    m_full = LinearRegression().fit(
        d[["close_log_return_lag_1", "close_log_return_ma_lag_1"]],
        d["close_log_return"],
    )
    print(f"  B11 fit full sample no split: coef={m_full.coef_} int={m_full.intercept_}")

    # B12: test_size inverted (train 0.25)?
    tr, te = train_test_split(d, test_size=0.75, shuffle=False)  # train is first 25%
    m = LinearRegression().fit(
        tr[["close_log_return_lag_1", "close_log_return_ma_lag_1"]],
        tr["close_log_return"],
    )
    print(f"  B12 train first 25% only: n_train={len(tr)} coef={m.coef_} int={m.intercept_}")

    # B13: search for MA construction that yields his coef signs
    print("\n--- B13: search feature transforms for negative large MA coef ---")
    base = btcusdt[["c"]].copy()
    base["close_log_return"] = np.log(base["c"] / base["c"].shift())
    base["lag"] = base["close_log_return"].shift()
    candidates = {
        "ma40_lag": base["lag"].rolling(40).mean(),
        "ma40_ret": base["close_log_return"].rolling(40).mean(),
        "ma40_ret_shift": base["close_log_return"].rolling(40).mean().shift(),
        "ma20_lag": base["lag"].rolling(20).mean(),
        "cumsum_lag": base["lag"].cumsum(),
        "ewm40_lag": base["lag"].ewm(span=40, adjust=False).mean(),
        "ma40_lag_std": base["lag"].rolling(40).mean() / base["lag"].rolling(40).std(),
        "ma40_c": base["c"].pct_change().shift().rolling(40).mean(),
        "lag_minus_ma": base["lag"] - base["lag"].rolling(40).mean(),  # relative memory?
        "ma_minus_lag": base["lag"].rolling(40).mean() - base["lag"],
    }
    # "relative memory" might mean lag relative to MA as single combined feature with lag
    for name, series in candidates.items():
        tmp = base.copy()
        tmp["f2"] = series
        d = tmp[["close_log_return", "lag", "f2"]].dropna()
        tr, te = train_test_split(d, test_size=0.25, shuffle=False)
        m = LinearRegression().fit(tr[["lag", "f2"]], tr["close_log_return"])
        close = np.allclose(m.coef_, HIS_B_COEF, rtol=0.05, atol=0.05)
        sign_ok = np.sign(m.coef_[1]) == np.sign(HIS_B_COEF[1])
        print(
            f"  {name:20s} coef={m.coef_} int={m.intercept_:.6f} "
            f"sign_MA_match={sign_ok} close_to_his={close}"
        )

    # B14: relative memory as features [lag, lag - ma] or [lag, ma] with different formula
    print("\n--- B14: relative memory feature definitions ---")
    for name, f1, f2 in [
        ("lag + (lag-ma)", base["lag"], base["lag"] - base["lag"].rolling(40).mean()),
        ("lag + (ma-lag)", base["lag"], base["lag"].rolling(40).mean() - base["lag"]),
        ("lag + ma/lag", base["lag"], base["lag"].rolling(40).mean() / base["lag"].replace(0, np.nan)),
        ("lag + ma*40", base["lag"], base["lag"].rolling(40).mean() * 40),
        ("lag + sum40", base["lag"], base["lag"].rolling(40).sum()),
    ]:
        tmp = pd.DataFrame(
            {
                "close_log_return": base["close_log_return"],
                "f1": f1,
                "f2": f2,
            }
        ).dropna()
        tr, te = train_test_split(tmp, test_size=0.25, shuffle=False)
        m = LinearRegression().fit(tr[["f1", "f2"]], tr["close_log_return"])
        print(f"  {name:20s} coef={m.coef_} int={m.intercept_:.6f}")

    # B15: recreate MA-alone first (line 77) then combined - does shared state matter? No for LR.
    print("\n--- B15: MA-alone intermediate (line 77) for reference ---")
    m_ma, bt_ma, _, _ = backtest_model(
        btcusdt,
        ["close_log_return_ma_lag_1"],
        "close_log_return",
        label="B15 MA-alone only",
    )

    # B16: Check if HIS coef is reproducible via different y
    # Solve: what if sklearn version uses different solver - try SVD vs lstsq
    print("\n--- B16: LinearRegression with different positive/copy_X ---")
    d = df_b.dropna()
    tr, te = train_test_split(d, test_size=0.25, shuffle=False)
    X = tr[["close_log_return_lag_1", "close_log_return_ma_lag_1"]].values
    y = tr["close_log_return"].values
    for kwargs in [{}, {"positive": True}]:
        try:
            m = LinearRegression(**kwargs).fit(X, y)
            print(f"  kwargs={kwargs}: coef={m.coef_} int={m.intercept_}")
        except Exception as e:
            print(f"  kwargs={kwargs}: ERR {e}")

    # B17: Did he maybe print coef from a DIFFERENT model (standardized path)?
    # Check: if we scale y? unlikely.
    # Check: rolling(40).mean of lag but center=False etc - pandas default
    # Check: maybe he used ewm
    # Search: find alpha such that Ridge gives his coef
    print("\n--- B17: Ridge alpha sweep for negative MA coef near -3.23 ---")
    for alpha in np.logspace(-8, 2, 25):
        m = Ridge(alpha=alpha).fit(
            tr[["close_log_return_lag_1", "close_log_return_ma_lag_1"]],
            tr["close_log_return"],
        )
        if m.coef_[1] < -1.0:
            print(f"  alpha={alpha:.2e} coef={m.coef_} int={m.intercept_:.6f}")

    # B18: Perhaps close prices are used as float with fewer decimals
    print("\n--- B18: rounded close prices ---")
    for ndp in [1, 2, 4, 6, 8]:
        tmp = btcusdt[["c"]].copy()
        tmp["c"] = tmp["c"].round(ndp)
        tmp["close_log_return"] = np.log(tmp["c"] / tmp["c"].shift())
        tmp["close_log_return_lag_1"] = tmp["close_log_return"].shift()
        tmp["close_log_return_ma_lag_1"] = tmp["close_log_return_lag_1"].rolling(40).mean()
        d = tmp.dropna()
        tr, te = train_test_split(d, test_size=0.25, shuffle=False)
        m = LinearRegression().fit(
            tr[["close_log_return_lag_1", "close_log_return_ma_lag_1"]],
            tr["close_log_return"],
        )
        print(f"  round({ndp}) coef={m.coef_} int={m.intercept_:.6f}")

    # B19: compare first/last train rows and y stats
    print("\n--- B19: train set summary for standard Model B ---")
    d = df_b.dropna()
    tr, te = train_test_split(d, test_size=0.25, shuffle=False)
    print(tr[["close_log_return", "close_log_return_lag_1", "close_log_return_ma_lag_1"]].describe())
    print("first 3 train:")
    print(tr[["close_log_return", "close_log_return_lag_1", "close_log_return_ma_lag_1"]].head(3))
    print("last 3 train:")
    print(tr[["close_log_return", "close_log_return_lag_1", "close_log_return_ma_lag_1"]].tail(3))

    # B20: apply HIS weights to our features and see signal counts
    print("\n--- B20: his printed B weights on our features ---")
    d = df_b.dropna()
    X = d[["close_log_return_lag_1", "close_log_return_ma_lag_1"]].to_numpy()
    yhat = X @ HIS_B_COEF + HIS_B_INT
    sig = np.sign(yhat)
    print(pd.Series(sig).value_counts())
    print(f"  winrate with his weights: {(np.sign(d['close_log_return'].to_numpy()*sig)>0).mean():.4f}")

    # B21: maybe test_split is on raw before dropna? Unlikely in his function.
    # Or he dropna only subset
    print("\n--- B21: dropna subset how? ---")
    # dropna only on features+target
    d = btcusdt.dropna(subset=["close_log_return", "close_log_return_lag_1", "close_log_return_ma_lag_1"])
    print(f"  subset dropna n={len(d)} vs full dropna n={len(btcusdt.dropna())}")

    # B22: Use sklearn 1.x LinearRegression with sample_weight?
    # B23: maybe he used close_return (pct) as BOTH feature base
    print("\n--- B23: pct_change based features named log ---")
    tmp = btcusdt[["c"]].copy()
    tmp["close_log_return"] = tmp["c"].pct_change()  # misnamed
    tmp["close_log_return_lag_1"] = tmp["close_log_return"].shift()
    tmp["close_log_return_ma_lag_1"] = tmp["close_log_return_lag_1"].rolling(40).mean()
    m_b23, bt_b23, _, _ = backtest_model(
        tmp,
        ["close_log_return_lag_1", "close_log_return_ma_lag_1"],
        "close_log_return",
        label="B23 pct_change features (misnamed as log)",
    )

    # Model A with pct for comparison
    tmp_a = btcusdt[["c"]].copy()
    tmp_a["close_log_return"] = tmp_a["c"].pct_change()
    tmp_a["close_log_return_lag_1"] = tmp_a["close_log_return"].shift()
    m_ap, bt_ap, _, _ = backtest_model(
        tmp_a,
        ["close_log_return_lag_1"],
        "close_log_return",
        label="A-pct features",
    )
    print(f"  A-pct DELTA coef={m_ap.coef_[0]-HIS_A_COEF:.6e} int={m_ap.intercept_-HIS_A_INT:.6e}")

    # B24: include volume or other? no
    # B25: rolling window center=True
    tmp = btcusdt[["c", "close_log_return", "close_log_return_lag_1"]].copy()
    tmp["close_log_return_ma_lag_1"] = tmp["close_log_return_lag_1"].rolling(40, center=True).mean()
    m_b25, _, _, _ = backtest_model(
        tmp,
        ["close_log_return_lag_1", "close_log_return_ma_lag_1"],
        "close_log_return",
        label="B25 rolling center=True",
    )

    print("\n=== DONE INVESTIGATION ===")


if __name__ == "__main__":
    main()
