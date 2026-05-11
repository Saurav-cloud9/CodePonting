# fv2 Param Spec — Formula + H5 Implementation
# One param per section. Formula locked before implementation.
# ──────────────────────────────────────────────────────────────

## H5 Design Decisions

| Decision | Rule |
|---|---|
| Gate evaluation | All gates evaluated independently — no cascade |
| Param-level N/A | Individual param can't be evaluated (e.g. edge case) → param = N/A, gate still evaluated |
| Gate-level N/A | All params within a gate are N/A → gate itself = N/A |
| Cross-gate N/A | Gate N/A never forces downstream gates to N/A |
| H5 modes | **Explore mode** — all params observed, no filtering, full data collection. **Filter mode** — params act as pipeline, active gates must pass for signal to survive. |

---

## Param Types
| Type | Description | H5 control |
|---|---|---|
| Tunable threshold | Numeric cutoff — slider controls pass/fail boundary | Slider |
| Tunable count | Integer count — slider controls minimum required | Slider (int) |
| Tunable range | Min + max both matter | Range slider |
| Binary/Quality | Structural prerequisite — met or not | Toggle |

---

## G1 — Pre-touch Regime

---

### #01 — slope_threshold

| Field           | Value                                                         |
|-----------------|---------------------------------------------------------------|
| Gate            | G1                                                            |
| Formula         | `((ma20[T0] - ma20[T0-5]) / ma20[T0]) * 100`                |
| Pass condition  | `slope >= threshold`                                          |
| Data source     | Computed from `ma20` column in CSV at signal detection time   |
| H5 control      | Slider                                                        |
| Range           | 0.00% to 0.50%, step 0.01%                                   |
| Default         | 0.05%                                                         |

---

### #02 — slope_offset

| Field           | Value                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------|
| Gate            | G1                                                                                         |
| Formula         | `((ma20[T0-3] - ma20[T0-8]) / ma20[T0-3]) * 100`                                         |
| Pass condition  | `slope_offset >= threshold`                                                                |
| Data source     | Computed from `ma20` column in CSV at signal detection time                                |
| H5 control      | Slider                                                                                     |
| Range           | 0.00% to 0.20%, step 0.01%                                                                |
| Default         | 0.05%                                                                                      |
| Note            | High slope at T0-3 may indicate move already exhausted before touch — upper bound kept tight intentionally |

---

### #03 — candles_above

| Field           | Value                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------|
| Gate            | G1                                                                                         |
| Formula         | Count of consecutive bars before T0 where `low > ma20`                                    |
| Pass condition  | `count >= threshold` (minimum 1 bar approaching from above)                               |
| Data source     | Computed from `low` and `ma20` columns in CSV                                              |
| H5 control      | Slider (integer)                                                                           |
| Range           | 1 to 5, step 1                                                                             |
| Default         | 1                                                                                          |
| Note            | Prerequisite for #04 — if #03 fails, #04 is N/A                                           |

---

### #04 — pullback_bars

| Field           | Value                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------|
| Gate            | G1                                                                                         |
| Formula         | Bar count from swing high to T0, where swing high = local peak (`high[i] > high[i-1]` AND `high[i] > high[i+1]`), with lower highs AND descending lows from swing high → T0 |
| Pass condition  | `bar_count >= min_slider` AND `bar_count <= max_slider`                                   |
| Data source     | Computed from `high`, `low`, `ma20` columns in CSV                                        |
| H5 control      | Range slider (min + max, integer)                                                          |
| Range           | min: 1–8, max: 1–8 (default min=3, max=8)                                                 |
| Default         | min=3, max=8 (H1 observed range — hypothesis to test, not hard constraint)                |
| Structural reqs | Lower highs AND descending lows from swing high → T0 (always required when #04 active)    |
| Note            | #03 is prerequisite. Min starts at 1 since #03 already guarantees approach exists. 3–8 default from H1 visual review — Optuna may tighten this. |

---

## G2 — Touch & Bounce Quality

---

### #05 — shoot_depth

| Field           | Value                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------|
| Gate            | G2                                                                                         |
| Type            | Tunable range                                                                              |
| Formula         | `(ma20[T0] - low[T0]) / atr14[T0]`                                                        |
| Pass condition  | `shoot_depth >= min_slider` AND `shoot_depth <= max_slider`                               |
| Data source     | Computed from `ma20`, `low`, and ATR14 (ATR14 not in CSV — compute from OHLCV)            |
| H5 control      | Range slider                                                                               |
| Range           | 0.0 to 2.0, step 0.05                                                                     |
| Default         | min=0.0, max=1.0                                                                           |
| Note            | < 0.5 = shallow touch, > 1.0 = overextended. Sweet spot expected in middle. From H1.1 colour bands. |

---

### #06 — touch_body_pct

| Field           | Value                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------|
| Gate            | G2                                                                                         |
| Type            | Tunable threshold (ceiling)                                                                |
| Formula         | `(abs(close[T0] - open[T0]) / (high[T0] - low[T0])) * 100`                              |
| Pass condition  | `touch_body_pct <= threshold` (smaller body = better; large body = seller conviction)     |
| Data source     | Computed from `open`, `close`, `high`, `low` columns in CSV                               |
| H5 control      | Slider                                                                                     |
| Range           | 0% to 100%, step 5%                                                                        |
| Default         | 50%                                                                                        |
| Note            | One-sided ceiling cutoff. Large body = bearish marubozu at touch = sellers dominated. Small body = wick absorption = price probed and recovered. |

---

### #07 — wick_defence_ratio

| Field           | Value                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------|
| Gate            | G2                                                                                         |
| Type            | Tunable threshold (floor)                                                                  |
| Formula         | `(min(open[T0], close[T0]) - ma20[T0]) / (ma20[T0] - low[T0])`                           |
| Pass condition  | `wick_defence_ratio >= threshold`                                                          |
| Data source     | Computed from `open`, `close`, `low`, `ma20` columns in CSV                               |
| H5 control      | Slider                                                                                     |
| Range           | 0.0 to 5.0, step 0.1                                                                      |
| Default         | 1.0 (ratio > 1 = buyers recovered more than they overshot)                                |
| Edge case       | `low >= ma20` → denominator <= 0 → param = N/A (no valid shoot). `min(open,close) < ma20` → numerator negative → param = N/A. Explore: signal stays alive. Filter: N/A = rejection. |
| Note            | Higher = stronger buyer defence at MA. < 1 = weak defence. > 1 = buyers dominated recovery. |

---

### #08 — bounce_vr_abs

| Field           | Value                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------|
| Gate            | G2                                                                                         |
| Type            | Tunable threshold (floor)                                                                  |
| Formula         | `volume[bounce_bar] / vol_ma20[bounce_bar]`                                               |
| Pass condition  | `bounce_vr_abs >= threshold`                                                               |
| Data source     | Computed from `volume` column; vol_ma20 = 20-bar rolling average volume                   |
| H5 control      | Slider                                                                                     |
| Range           | 0.5 to 3.0, step 0.1                                                                      |
| Default         | 1.2                                                                                        |
| Note            | Confirms buyer conviction at bounce bar. > 1.2 = above-average volume = genuine interest. |

---

### #09 — bounce_vr_rel

| Field           | Value                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------|
| Gate            | G2                                                                                         |
| Type            | Binary/Quality                                                                             |
| Formula         | `vr[bounce_bar] > vr[T0]`                                                                 |
| Pass condition  | Bounce Volume Ratio (VR) > touch VR                                                       |
| Data source     | Computed from `volume` and vol_ma20                                                        |
| H5 control      | Toggle                                                                                     |
| Note            | Relative spike — bounce bar showed more conviction than touch bar. |

---

## ⚠ same_candle_tb — OBSERVATION COLUMN (not a gate param)

| Field           | Value                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------|
| Column name     | `same_candle_tb`                                                                           |
| Formula         | `touch_bar == bounce_bar` (touch-to-bounce gap = 0)                                       |
| Data source     | Derived from signal detection logic                                                        |
| Status          | **Reclassified 2026-05-10** — removed from gate param list. Kept as standalone observation column in CSV and signal detail tables. Never gates a signal in any mode. Tracks same-candle vs split-candle performance for Optuna data collection only. |

---

## G3 — Post-bounce Follow-through

**G3 params: #10–#11 (2 params)**

---

### #10 — G3a (entry_close_above_bounce)

| Field           | Value                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------|
| Gate            | G3                                                                                         |
| Type            | Binary/Quality                                                                             |
| Formula         | `close[entry_bar] > close[bounce_bar]`                                                    |
| Pass condition  | Entry bar closed above bounce close                                                        |
| Data source     | Computed from `close` column                                                               |
| H5 control      | Toggle                                                                                     |
| Note            | Red entry bar closing below bounce close = selling pressure during entry = genuine G3a fail. Close is the right proxy for follow-through conviction, not high or open. |

---

### #11 — G3b (entry_vr_holds)

| Field           | Value                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------|
| Gate            | G3                                                                                         |
| Type            | Binary/Quality                                                                             |
| Formula         | `vr[entry_bar] >= vr[bounce_bar]`                                                         |
| Pass condition  | Entry bar volume ratio ≥ bounce bar volume ratio                                           |
| Data source     | Computed from `volume` and vol_ma20                                                        |
| H5 control      | Toggle                                                                                     |
| Note            | Volume conviction didn't fade into entry bar. Confirms buying interest sustained. |
