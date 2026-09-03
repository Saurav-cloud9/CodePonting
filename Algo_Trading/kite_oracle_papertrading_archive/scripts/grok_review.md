# Grok Review — Offline vs Reference Backtest

**Date:** 2026-07-19  
**Reviewed by:** Grok  
**Location:** `Algo_Trading/kite_oracle_papertrading/scripts/`

---

## Files compared

| File | Role |
|------|------|
| `ma_30_rejection_v1_reference.py` | Batch/array backtest (precomputed MA20/ATR14 from parquet) |
| `ma_30_rejection_v1_offline.py` | Bar-by-bar offline paper engine (incremental MA20/ATR14, live-shaped state) |

Both use the same locked params from the v1 sweep:

- **Strategy:** MA Rejection v1 SHORT (clean-touch)  
- **Signal:** `high >= MA20` AND `open < MA20` AND `close < MA20` → short at next bar open  
- **SL / TP:** 2.0× / 4.5× ATR14  
- **Data:** `Framework_V2/data/historical/intraday_5min_DS3` (30 stocks, 2015–2025)  
- **EOD hour:** 15  

---

## How they were run

```text
Python 3.12
C:\Users\saurav\AppData\Local\Programs\Python\Python312\python.exe
```

| Script | Runtime (approx) | Exit |
|--------|------------------|------|
| Reference | ~277 s | 0 |
| Offline | ~58 s | 0 |

Offline trade log written to:

```text
kite_oracle_papertrading/data/trades/offline_trades.csv
```

---

## Headline results

| Metric | Reference | Offline | Exact match? |
|--------|----------:|--------:|:------------:|
| **N (trades)** | 110,641 | 110,637 | No (−4) |
| **PF** | 1.135 | 1.135 | Yes (3 d.p.) |
| **Sharpe (monthly, annualised √12)** | 2.358 | 2.358 | Yes |
| **Net PnL (₹, 1 share)** | 19,655.04 | 19,655.93 | ~same (Δ ≈ 0.89) |

**More precise PF / net (from trade-level recompute):**

| | Reference | Offline |
|--|----------:|--------:|
| PF | 1.134710859 | 1.134715486 |
| Net | 19,655.0418 | 19,655.9282 |

### Reference console summary (TOTAL line)

```text
TOTAL  N=110641  Prof_WR=42.3%  BE_prof=40.4%  Pure_WR=16.1%  BE_pure=30.8%  PF=1.135  Sharpe=2.358  Net=19655.04
```

### Offline console summary

```text
110,637 trades written to ...\offline_trades.csv
N=110,637  PF=1.135  Sharpe=2.358
```

---

## Verdict

**Outputs do not match exactly.**

They are **statistically equivalent** for decision-making (same rounded PF and Sharpe; net PnL within ~₹1).  
They are **not bit-identical** on trade count or full trade set.

---

## Trade-level comparison

Reference was re-run with full trade capture (symbol, entry_dt, entry, exit, outcome, pnl) and merged against `offline_trades.csv` on `(symbol, entry_dt)`.

| Category | Count |
|----------|------:|
| Exact match (same symbol + entry_dt; identical pnl & outcome) | **110,576** |
| Only in offline | 61 |
| Only in reference | 65 |
| Matched trades with \|pnl\| diff > 1e-6 | **0** |
| Matched trades with outcome mismatch | **0** |

### Interpretation

- Every trade that appears in **both** engines with the same entry time exits the same way (same pnl, same outcome label).  
- Divergence is almost entirely **which signals are taken** (different entry timestamps), not exit logic on shared entries.  
- Net N gap is only **4** trades (110,641 − 110,637), but **~126** trades sit in non-overlapping sets (61 + 65) because position-guard cascades shift subsequent entries.

---

## Per-symbol trade-count diffs (nonzero only)

| Symbol | Offline N | Reference N | Diff (off − ref) |
|--------|----------:|------------:|-----------------:|
| NATIONALUM | 3601 | 3603 | −2 |
| ONGC | 3617 | 3619 | −2 |
| ITC | 3688 | 3689 | −1 |
| HDFCBANK | 3743 | 3744 | −1 |
| PNB | 3770 | 3771 | −1 |
| TATASTEEL | 3750 | 3751 | −1 |
| NTPC | 3684 | 3683 | +1 |
| HINDALCO | 3725 | 3724 | +1 |
| TATAMOTORS | 3698 | 3697 | +1 |
| VEDL | 3722 | 3721 | +1 |

All other symbols: **identical** N.

---

## Sample non-overlapping trades

These illustrate timing divergence (same stock/day clusters, different entry bars), not random unrelated signals.

### Only offline (sample)

| Symbol | entry_dt | entry | pnl | outcome |
|--------|----------|------:|----:|---------|
| ASHOKLEY | 2015-09-16 13:20 | 41.20 | +0.20 | EOD+ |
| ASHOKLEY | 2016-05-27 13:05 | 50.30 | −0.27 | L |
| BANDHANBNK | 2024-07-26 10:25 | 186.48 | −1.66 | L |
| CIPLA | 2016-02-01 14:25 | 602.80 | +3.97 | W |
| HDFCBANK | 2019-03-26 10:40 | 570.40 | −1.90 | L |

### Only reference (sample)

| Symbol | entry_dt | entry | pnl | outcome |
|--------|----------|------:|----:|---------|
| ASHOKLEY | 2015-09-16 10:15 | 41.30 | +0.30 | EOD+ |
| ASHOKLEY | 2016-05-27 12:25 | 50.60 | −0.33 | L |
| BANDHANBNK | 2024-07-26 10:40 | 186.43 | −1.19 | L |
| CIPLA | 2016-02-01 14:15 | 602.10 | +1.00 | EOD+ |
| HDFCBANK | 2019-03-26 10:35 | 570.30 | −1.99 | L |

Same days often appear in both “only” lists with different entry times → classic single-position guard cascade after one early signal flip.

---

## Root causes of divergence

### 1. Indicators

| | Reference | Offline |
|--|-----------|---------|
| MA20 | Precomputed column in parquet | Incremental SMA of last 20 closes (`deque`) |
| ATR14 | Precomputed column in parquet | Incremental mean of last 14 TRs after `prev_close` exists |

Any tiny difference at warm-up, gaps, or float precision on borderline touches (`high >= ma20`, etc.) flips a signal.

### 2. Execution model

| | Reference | Offline |
|--|-----------|---------|
| Scan order | Stock-by-stock full history | Global chronological merge of all 30 stocks |
| State | Index `i = k+1` after trade | Explicit `position` + `pending_entry` + `just_exited` |
| Indicators vs signal | Uses bar’s precomputed values | Updates indicators on bar, then checks touch |

Stock-level isolation means cross-stock ordering should not change per-stock trade sets if indicators/signals match. The observed diffs are therefore primarily **indicator / edge-case** related, then amplified by the position guard.

### 3. Cascading position guard

Once one signal is taken or skipped differently:

1. Entry bar changes  
2. Exit bar changes  
3. Resume bar (`i = k+1` / no re-touch on exit bar) shifts  
4. Later candidates in the same day (or later) diverge  

That explains why **N only differs by 4** overall while **~126** individual entries don’t line up on `entry_dt`.

---

## What matches well enough for paper-trading validation

- Same strategy definition and locked SL/TP  
- Same exit priority intent: date change → hour ≥ 15 → SL → TP  
- Same entry-next-open and no overnight carry  
- Matched trades: **identical** pnl and outcome  
- Aggregate: **PF 1.135**, **Sharpe 2.358** on both  

**Not yet exact parity** for a strict “offline must reproduce reference trade list 1:1” gate.

---

## Recommendations (if exact match is required)

1. **Align indicators** — either feed offline the same precomputed `ma20`/`atr14` as reference for a parity test, or recompute parquet indicators with the exact offline TR/MA formulas and re-run reference.  
2. **Diff harness** — keep a small script that merges on `(symbol, entry_dt)` and reports only_off / only_ref (as done for this review).  
3. **Accept band** — if exact 1:1 is not required, treat **|ΔN| ≤ 10** and **same PF/Sharpe to 3 d.p.** as validation pass for this strategy.  
4. **Note metrics gap vs `backtesting_rules_v2.md`** — both scripts report **raw PF** and **monthly Sharpe**, not ZPF / ZSh(D). Fine for engine parity; not the full rules-format report.

---

## Reference year-wise snapshot (reference script only)

| Year | N | PF | Sharpe | Net |
|-----:|--:|---:|-------:|----:|
| 2015 | 9203 | 1.181 | 3.527 | 1370.63 |
| 2016 | 9994 | 1.152 | 2.244 | 1128.62 |
| 2017 | 10032 | 1.162 | 3.104 | 1176.88 |
| 2018 | 10340 | 1.213 | 3.353 | 2264.26 |
| 2019 | 10380 | 1.182 | 2.619 | 1937.43 |
| 2020 | 10236 | 1.157 | 2.502 | 2249.78 |
| 2021 | 9974 | 1.198 | 2.978 | 3211.60 |
| 2022 | 10070 | 1.071 | 1.306 | 1192.58 |
| 2023 | 9893 | 1.026 | 0.602 | 354.62 |
| 2024 | 10020 | 1.130 | 3.034 | 2712.19 |
| 2025 | 10499 | 1.102 | 2.353 | 2056.43 |

*(Offline script does not print year-wise tables; not re-derived here.)*

---

## Bottom line

| Question | Answer |
|----------|--------|
| Do outputs match **exactly**? | **No** |
| Are they **functionally equivalent** for this lock? | **Yes** (PF/Sharpe identical to 3 d.p.; net ~same) |
| Main gap | N: 110,641 vs 110,637; ~126 non-overlapping entry times; 0 diffs on shared trades |
| Likely cause | Incremental vs precomputed MA/ATR + position-guard cascade |

---

*Generated from live runs of both scripts on local DS3 data, 2026-07-19.*
