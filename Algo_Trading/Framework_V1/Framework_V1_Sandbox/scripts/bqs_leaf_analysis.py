"""
bqs_leaf_analysis.py — BQS Step 4.4b: Top 10 DT Leaf Bucket Analysis
======================================================================
For each target (w1, w2, w3):
  - Train DT(max_depth=4, class_weight=balanced)
  - Extract all leaf paths + stats from the fitted tree
  - Filter: min 500 trades per bucket
  - Rank by win rate descending, print top 10
  - Print combined best-bucket summary at end

Winner definitions:
  w1  = exit_reason == 'target'   baseline 14.8%
  w2  = net_pnl_upstox > 0        baseline 32.5%
  w3  = net_pnl_kite   > 0        baseline 35.3%
"""

import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, _tree
from sklearn.impute import SimpleImputer

SANDBOX_DIR = Path(__file__).resolve().parent.parent
BQS_PATH    = SANDBOX_DIR / "outputs/bqs/bqs_trades.parquet"

# ── FEATURE LISTS ─────────────────────────────────────────────────────────────

R1_FEATURES = [
    "m1_volume_ratio", "m2_bounce_strength_pct", "m3_wick_ratio",
    "m4_candle_color", "m5_hours_until_close",   "m6_touch_candle_index",
    "m7_bounce_gap",   "m8_ma20_distance_pct",   "m9_prev_candle_dir",
]
R2_FEATURES = [
    "r2_m1_ma20_slope",  "r2_m2_rsi14",        "r2_m3_freshness",
    "r2_m4_vol_trend",   "r2_m5_day_position",  "r2_m6_body_ratio",
    "r2_m61_wick_body",  "r2_m7_candle_type",   "r2_m8_dow",
    "r2_m9_vol_ratio",   "r2_m10_gap_open",
]
ALL_FEATURES = R1_FEATURES + R2_FEATURES

# Short display names for inline rule strings
ABBREV = {
    "m1_volume_ratio":        "vol_ratio",
    "m2_bounce_strength_pct": "bounce_str",
    "m3_wick_ratio":          "wick_ratio",
    "m4_candle_color":        "cand_color",
    "m5_hours_until_close":   "hrs_close",
    "m6_touch_candle_index":  "touch_idx",
    "m7_bounce_gap":          "bounce_gap",
    "m8_ma20_distance_pct":   "ma20_dist%",
    "m9_prev_candle_dir":     "prev_dir",
    "r2_m1_ma20_slope":       "ma20_slope",
    "r2_m2_rsi14":            "rsi14",
    "r2_m3_freshness":        "freshness",
    "r2_m4_vol_trend":        "vol_trend",
    "r2_m5_day_position":     "day_pos",
    "r2_m6_body_ratio":       "body_ratio",
    "r2_m61_wick_body":       "wick_body",
    "r2_m7_candle_type":      "cand_type",
    "r2_m8_dow":              "dow",
    "r2_m9_vol_ratio":        "r2_vol_rat",
    "r2_m10_gap_open":        "gap_open%",
}

BASELINES = {"w1": 14.8, "w2": 32.5, "w3": 35.3}
TARGET_LABELS = {
    "w1": "W1 — target hit      (baseline 14.8%)",
    "w2": "W2 — net Upstox +ve  (baseline 32.5%)",
    "w3": "W3 — net Kite +ve    (baseline 35.3%)",
}
MIN_TRADES = 500


# ── HELPERS ───────────────────────────────────────────────────────────────────

def get_leaf_rules(dt, feature_names, abbrev):
    """
    Traverse a fitted DT and return:
        { leaf_node_id : ["feat<=thresh", "feat2>thresh2", ...] }
    Left child  = feature <= threshold
    Right child = feature >  threshold
    """
    tree_ = dt.tree_
    names = [
        abbrev.get(feature_names[i], feature_names[i][:12])
        if i != _tree.TREE_UNDEFINED else "__leaf__"
        for i in tree_.feature
    ]

    leaf_rules = {}

    def recurse(node, path):
        if tree_.feature[node] == _tree.TREE_UNDEFINED:
            leaf_rules[node] = list(path)
        else:
            thr = tree_.threshold[node]
            nm  = names[node]
            recurse(tree_.children_left[node],  path + [f"{nm}<={thr:.3f}"])
            recurse(tree_.children_right[node], path + [f"{nm}>{thr:.3f}"])

    recurse(0, [])
    return leaf_rules


def run_leaf_analysis(X, y, target, baseline, label):
    """Train DT(depth=4), extract leaf buckets, print top-10 table."""
    dt = DecisionTreeClassifier(max_depth=4, class_weight="balanced", random_state=42)
    dt.fit(X, y)

    leaf_ids   = dt.apply(X)
    leaf_rules = get_leaf_rules(dt, ALL_FEATURES, ABBREV)

    # Aggregate per leaf
    rows = []
    for lid in np.unique(leaf_ids):
        mask    = leaf_ids == lid
        cnt     = int(mask.sum())
        win_cnt = int(y[mask].sum())
        wr      = win_cnt / cnt * 100 if cnt > 0 else 0.0
        rules   = " AND ".join(leaf_rules.get(lid, []))
        rows.append({
            "trades":  cnt,
            "winners": win_cnt,
            "wr":      wr,
            "vs":      wr - baseline,
            "combo":   rules,
        })

    # Filter + sort
    rows = [r for r in rows if r["trades"] >= MIN_TRADES]
    rows.sort(key=lambda x: x["wr"], reverse=True)

    print(f"\n{'='*100}", flush=True)
    print(f"  TARGET: {label}", flush=True)
    print(f"  DT max_depth=4 | class_weight=balanced | min {MIN_TRADES:,} trades per bucket", flush=True)
    print(f"{'='*100}", flush=True)
    print(
        f"  {'Rank':<5} {'Trades':>7} {'Winners':>8} {'Win%':>7} {'vs Base':>8}  Combination",
        flush=True,
    )
    print(f"  {'─'*97}", flush=True)

    for rank, row in enumerate(rows[:10], 1):
        sign = "+" if row["vs"] >= 0 else ""
        # Truncate very long combos to keep lines readable
        combo = row["combo"]
        if len(combo) > 62:
            combo = combo[:59] + "..."
        print(
            f"  #{rank:<4} {row['trades']:>7,} {row['winners']:>8,}"
            f" {row['wr']:>6.1f}% {sign}{row['vs']:>5.1f}pp  {combo}",
            flush=True,
        )

    best = rows[0] if rows else None
    return rows, best


# ── LOAD PARQUET ──────────────────────────────────────────────────────────────

print("Loading bqs_trades.parquet...", flush=True)
df = pd.read_parquet(BQS_PATH)
df = df.reset_index(drop=True)
n  = len(df)
print(f"  {n:,} trades  |  {df.shape[1]} columns", flush=True)

if "w1" not in df.columns and "winner" in df.columns:
    df["w1"] = df["winner"]

missing = [c for c in ALL_FEATURES + ["w1", "w2", "w3"] if c not in df.columns]
if missing:
    print(f"  ERROR: missing columns: {missing}", flush=True)
    sys.exit(1)


# ── PREPARE FEATURES ──────────────────────────────────────────────────────────

print(f"Preparing features (median imputation)...", flush=True)
X_raw   = df[ALL_FEATURES].values.astype(float)
imputer = SimpleImputer(strategy="median")
X       = imputer.fit_transform(X_raw)
print(f"  {len(ALL_FEATURES)} features  |  {int(np.isnan(X_raw).sum()):,} NaN imputed", flush=True)


# ── RUN ANALYSIS ──────────────────────────────────────────────────────────────

summary = {}

for target in ["w1", "w2", "w3"]:
    y    = df[target].values.astype(int)
    rows, best = run_leaf_analysis(
        X, y, target, BASELINES[target], TARGET_LABELS[target]
    )
    summary[target] = {"rows": rows, "best": best}


# ── COMBINED SUMMARY ──────────────────────────────────────────────────────────

print(f"\n{'='*100}", flush=True)
print("  COMBINED SUMMARY — Best Bucket per Target", flush=True)
print(f"{'='*100}", flush=True)
print(
    f"  {'Target':<8} {'Trades':>7} {'Winners':>8} {'Win%':>7} {'vs Base':>9}",
    flush=True,
)
print(f"  {'─'*48}", flush=True)

for target in ["w1", "w2", "w3"]:
    b = summary[target]["best"]
    if b is None:
        print(f"  {target:<8} — no bucket with {MIN_TRADES}+ trades", flush=True)
        continue
    sign = "+" if b["vs"] >= 0 else ""
    print(
        f"  {target:<8} {b['trades']:>7,} {b['winners']:>8,}"
        f" {b['wr']:>6.1f}%  {sign}{b['vs']:>5.1f}pp",
        flush=True,
    )

print(f"\n  Best combos:", flush=True)
for target in ["w1", "w2", "w3"]:
    b = summary[target]["best"]
    if b:
        print(f"  {target}: {b['combo']}", flush=True)

# Also print top-3 per target side by side (compact view)
print(f"\n  Top-3 Buckets — Quick Reference", flush=True)
print(f"  {'─'*97}", flush=True)
for target in ["w1", "w2", "w3"]:
    rows = summary[target]["rows"]
    base = BASELINES[target]
    print(f"\n  [{target}  base={base}%]", flush=True)
    for rank, row in enumerate(rows[:3], 1):
        sign = "+" if row["vs"] >= 0 else ""
        combo = row["combo"]
        if len(combo) > 55:
            combo = combo[:52] + "..."
        print(
            f"    #{rank} {row['trades']:>6,} trades  {row['wr']:>5.1f}%  {sign}{row['vs']:>5.1f}pp  {combo}",
            flush=True,
        )

print(f"\n{'='*100}", flush=True)
