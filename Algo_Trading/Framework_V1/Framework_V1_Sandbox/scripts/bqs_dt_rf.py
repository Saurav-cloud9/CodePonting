"""
bqs_dt_rf.py — BQS Step 4.4b P3: Decision Tree / Random Forest
================================================================
Runs DT and RF on all 20 BQS features (R1 M1-M9 + R2 M1-M10 + M6.1)
for targets w1, w2, w3.

NaN handling: median imputation (SimpleImputer) before fitting.
Class imbalance: class_weight='balanced' on all models.

For each target:
  - DecisionTreeClassifier(max_depth=4)
  - RandomForestClassifier(n_estimators=200)
  - Top 10 feature importances (DT + RF)
  - Top 3 decision rules (depth-2 DT text)
  - Precision / Recall / F1 for winner class (train diagnostics)
  - Consensus ranking (avg DT + RF rank)
"""

import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.impute import SimpleImputer

SANDBOX_DIR = Path(__file__).resolve().parent.parent
BQS_PATH    = SANDBOX_DIR / "outputs/bqs/bqs_trades.parquet"

# ── FEATURE DEFINITIONS ───────────────────────────────────────────────────────

R1_FEATURES = [
    "m1_volume_ratio",
    "m2_bounce_strength_pct",
    "m3_wick_ratio",
    "m4_candle_color",
    "m5_hours_until_close",
    "m6_touch_candle_index",
    "m7_bounce_gap",
    "m8_ma20_distance_pct",
    "m9_prev_candle_dir",
]

R2_FEATURES = [
    "r2_m1_ma20_slope",
    "r2_m2_rsi14",
    "r2_m3_freshness",
    "r2_m4_vol_trend",
    "r2_m5_day_position",
    "r2_m6_body_ratio",
    "r2_m61_wick_body",
    "r2_m7_candle_type",
    "r2_m8_dow",
    "r2_m9_vol_ratio",
    "r2_m10_gap_open",
]

ALL_FEATURES = R1_FEATURES + R2_FEATURES
TARGETS      = ["w1", "w2", "w3"]
TARGET_NAMES = {
    "w1": "W1 — target hit      (14.8% base)",
    "w2": "W2 — net Upstox +ve  (32.5% base)",
    "w3": "W3 — net Kite +ve    (35.3% base)",
}


# ── STEP 1: LOAD ──────────────────────────────────────────────────────────────

print("Step 1: Loading parquet...", flush=True)
df = pd.read_parquet(BQS_PATH)
n  = len(df)
print(f"  {n:,} trades  |  {df.shape[1]} columns", flush=True)

missing_cols = [c for c in ALL_FEATURES if c not in df.columns]
if missing_cols:
    print(f"  ERROR: Missing feature columns: {missing_cols}", flush=True)
    print(f"  Ensure P1 (bqs_export.py) and P2 (bqs_r2_join.py) have been run.", flush=True)
    sys.exit(1)

# w1 is stored as 'winner' in the parquet — add alias
if "w1" not in df.columns and "winner" in df.columns:
    df["w1"] = df["winner"]
    print(f"  w1 aliased from 'winner' column", flush=True)

missing_targets = [t for t in TARGETS if t not in df.columns]
if missing_targets:
    print(f"  ERROR: Missing target columns: {missing_targets}", flush=True)
    sys.exit(1)

print(f"  All {len(ALL_FEATURES)} features and {len(TARGETS)} targets present.", flush=True)


# ── STEP 2: PREPARE FEATURES ──────────────────────────────────────────────────

print("\nStep 2: Preparing features (median imputation for NaN)...", flush=True)

X_raw = df[ALL_FEATURES].values.astype(float)
imputer = SimpleImputer(strategy="median")
X = imputer.fit_transform(X_raw)

nan_counts = np.isnan(X_raw).sum(axis=0)
total_nan  = int(nan_counts.sum())
print(f"  Total NaN values imputed: {total_nan:,}", flush=True)
if total_nan > 0:
    print(f"  Top NaN columns:", flush=True)
    top_nan = sorted(zip(nan_counts, ALL_FEATURES), reverse=True)
    for cnt, name in top_nan:
        if cnt > 0:
            print(f"    {name:<28} {int(cnt):>7,}  ({cnt/n*100:.1f}%)", flush=True)


# ── STEP 3: CLASS BALANCE ─────────────────────────────────────────────────────

print(f"\n{'='*72}", flush=True)
print("  CLASS BALANCE CHECK", flush=True)
print(f"{'='*72}", flush=True)
print(f"  {'Target':<8} {'Positive':>10} {'Negative':>10} {'Imbalance':>12}", flush=True)
print(f"  {'─'*44}", flush=True)

for t in TARGETS:
    pos   = int(df[t].sum())
    neg   = n - pos
    ratio = neg / pos if pos > 0 else float("inf")
    print(f"  {t:<8} {pos:>10,} {neg:>10,} {ratio:>10.1f}:1", flush=True)

print(f"\n  Using class_weight='balanced' on all models.", flush=True)


# ── STEP 4: DT + RF PER TARGET ────────────────────────────────────────────────

for target in TARGETS:
    y = df[target].values.astype(int)

    print(f"\n{'━'*72}", flush=True)
    print(f"  TARGET: {TARGET_NAMES[target]}", flush=True)
    print(f"{'━'*72}", flush=True)

    # ── Decision Tree ──────────────────────────────────────────────────────────
    print(f"\n  ─── Decision Tree  max_depth=4  class_weight=balanced ───", flush=True)

    dt = DecisionTreeClassifier(max_depth=4, class_weight="balanced", random_state=42)
    dt.fit(X, y)
    y_pred_dt = dt.predict(X)

    fi_dt = sorted(zip(ALL_FEATURES, dt.feature_importances_), key=lambda x: x[1], reverse=True)

    print(f"\n  Top 10 Feature Importances (DT):", flush=True)
    print(f"  {'Rank':<5} {'Feature':<28} {'Importance':>10}  Bar", flush=True)
    print(f"  {'─'*60}", flush=True)
    for rank, (feat, imp) in enumerate(fi_dt[:10], 1):
        bar = "█" * int(imp * 60)
        print(f"  {rank:<5} {feat:<28} {imp:>10.4f}  {bar}", flush=True)

    # Top 3 rules via depth-2 DT
    print(f"\n  Top decision rules (depth-2 DT):", flush=True)
    dt2 = DecisionTreeClassifier(max_depth=2, class_weight="balanced", random_state=42)
    dt2.fit(X, y)
    tree_lines = export_text(dt2, feature_names=list(ALL_FEATURES)).strip().split("\n")
    for line in tree_lines[:12]:
        print(f"    {line}", flush=True)

    # Train diagnostics
    rep = classification_report(y, y_pred_dt, target_names=["loser", "winner"], output_dict=True, zero_division=0)
    wr  = rep["winner"]
    print(f"\n  Train diagnostics — winner class:", flush=True)
    print(f"    Precision {wr['precision']:.3f}  |  Recall {wr['recall']:.3f}  |  F1 {wr['f1-score']:.3f}  |  Support {int(wr['support']):,}", flush=True)

    # ── Random Forest ──────────────────────────────────────────────────────────
    print(f"\n  ─── Random Forest  n=200  class_weight=balanced ───", flush=True)

    rf = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1)
    rf.fit(X, y)
    y_pred_rf = rf.predict(X)

    fi_rf = sorted(zip(ALL_FEATURES, rf.feature_importances_), key=lambda x: x[1], reverse=True)

    print(f"\n  Top 10 Feature Importances (RF):", flush=True)
    print(f"  {'Rank':<5} {'Feature':<28} {'Importance':>10}  Bar", flush=True)
    print(f"  {'─'*60}", flush=True)
    for rank, (feat, imp) in enumerate(fi_rf[:10], 1):
        bar = "█" * int(imp * 80)
        print(f"  {rank:<5} {feat:<28} {imp:>10.4f}  {bar}", flush=True)

    rep_rf = classification_report(y, y_pred_rf, target_names=["loser", "winner"], output_dict=True, zero_division=0)
    wr_rf  = rep_rf["winner"]
    print(f"\n  Train diagnostics — winner class:", flush=True)
    print(f"    Precision {wr_rf['precision']:.3f}  |  Recall {wr_rf['recall']:.3f}  |  F1 {wr_rf['f1-score']:.3f}  |  Support {int(wr_rf['support']):,}", flush=True)

    # ── Consensus ranking ──────────────────────────────────────────────────────
    rank_dt = {f: r for r, (f, _) in enumerate(fi_dt, 1)}
    rank_rf = {f: r for r, (f, _) in enumerate(fi_rf, 1)}
    consensus = sorted(
        [(f, (rank_dt[f] + rank_rf[f]) / 2.0) for f in ALL_FEATURES],
        key=lambda x: x[1]
    )

    print(f"\n  ─── Consensus Feature Ranking (avg DT + RF rank) ───", flush=True)
    print(f"  {'#':<4} {'Feature':<28} {'DT':>5} {'RF':>5} {'Avg':>6}  Group", flush=True)
    print(f"  {'─'*58}", flush=True)
    for rank, (feat, avg) in enumerate(consensus[:12], 1):
        grp = "R1" if feat in R1_FEATURES else "R2"
        print(f"  {rank:<4} {feat:<28} {rank_dt[feat]:>5} {rank_rf[feat]:>5} {avg:>6.1f}  {grp}", flush=True)

print(f"\n{'='*72}", flush=True)
print("  P3 COMPLETE — DT/RF results above", flush=True)
print(f"{'='*72}", flush=True)
