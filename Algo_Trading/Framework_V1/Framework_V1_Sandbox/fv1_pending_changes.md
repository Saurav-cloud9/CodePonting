# FV1 Pending Code Changes
# Generated from: fv1_strategy_review.md (all verdicts + resolutions)
# Date: 2026-03-09
# Status: AWAITING USER APPROVAL before implementation
#
# This document lists every code change required based on verdicts/resolutions
# in fv1_strategy_review.md. No changes have been applied yet.
# Ordered by priority (Sandbox-blockers first, then enhancements).

---

## LEGEND

- **SANDBOX-BLOCKER** — must be done before any Sandbox run
- **SANDBOX-ENHANCEMENT** — improves Sandbox test fidelity
- **DEFERRED** — explicitly deferred to DS3 / Optuna / FV2 phase
- **NO CHANGE** — verdict concluded no code change required

---

## CHANGE 1 — Remove `compute_daily_mas()` from runner

**Source:** Verdict #1 / Resolution "Why is daily MA data computed but never used?"
**Priority:** SANDBOX-BLOCKER
**File:** `scripts/run_backtest.py`
**Function:** module-level batch loop (lines 85–87 area)

**Changes required:**
1. Line 22: Remove `compute_daily_mas` from the import:
   - Before: `from core.indicators import add_intraday_indicators, compute_daily_mas, add_atr`
   - After: `from core.indicators import add_intraday_indicators, add_atr`
2. Line 86: Remove the call entirely:
   - Delete: `df = compute_daily_mas(df)`

**Note:** The `compute_daily_mas()` function in `core/indicators.py` must NOT be deleted — it is kept for future regime filter work (GSS / Optuna OP-5). Only the call in the runner is removed.

---

## CHANGE 2 — Delete `max_hold_bars` parameter

**Source:** Verdict #2 / Resolution "Why does max_hold_bars exist?"
**Priority:** SANDBOX-BLOCKER
**File:** `core/portfolio.py`
**Function:** `Portfolio.__init__()`

**Changes required:**
1. Remove `max_hold_bars=80` from the `__init__` signature (line 30).
2. Remove `self.max_hold_bars = max_hold_bars` from `__init__` body (line 38).

**Note:** No update loop references `max_hold_bars`, so no other lines are affected.

---

## CHANGE 3 — Enforce max 1 open position per stock

**Source:** Verdict #3
**Priority:** SANDBOX-BLOCKER
**File:** `core/engine.py`
**Function:** `BacktestEngine.run()` — entry block (lines 63–67)

**Change required:**
Add a guard before `self.portfolio.open_position()` that skips the signal if any position is currently open. Since each `BacktestEngine` instance processes a single stock, any open position in the portfolio means this stock already has an active trade.

- Before:
  ```python
  if dt in signal_map:
      for sig in signal_map[dt]:
          self.portfolio.open_position(sig, bar, i)
  ```
- After:
  ```python
  if dt in signal_map:
      for sig in signal_map[dt]:
          if len(self.portfolio.positions) > 0:
              continue   # skip: position already open on this stock
          self.portfolio.open_position(sig, bar, i)
  ```

---

## CHANGE 4 — Remove cross-month boundary check

**Source:** Verdict #5
**Priority:** SANDBOX-BLOCKER
**File:** `core/strategy.py`
**Function:** `BounceStrategy.generate_signals()`

**Change required:**
Delete the cross-month check block (lines 83–92 in current file):
```python
# Discard cross-month signals: v1.4.5 processes data
# month-by-month, so it can never use a touch candle (i)
# from month M to generate an entry in month M+1.
# Checking i vs next_idx is strictly stronger than j vs
# next_idx and also covers the lookahead-crosses-month
# case where touch is in M-1, reclaim crosses into M, and
# entry lands in M (j-vs-entry check would miss those).
if (datetime_arr[i].year, datetime_arr[i].month) != \
   (datetime_arr[next_idx].year, datetime_arr[next_idx].month):
    break
```
Delete all 10 lines. The 14:30 entry cutoff and EOD exit already ensure touch and entry are on the same day; cross-month signals are mathematically impossible.

---

## CHANGE 5 — Replace `initial_capital` with `current_equity` in position sizing

**Source:** Verdict #6 / Resolution "Why is risk_per_trade fixed at 1% of initial capital?"
**Priority:** SANDBOX-BLOCKER
**File:** `core/portfolio.py`
**Function:** `Portfolio.open_position()`

**Changes required:**

1. Add a `current_equity` property or compute it inline before sizing:
   ```python
   current_equity = self.cash + sum(
       (p["entry_price"]) * p["qty"]   # approximation: entry value (no mark-to-market needed for sizing)
       for p in self.positions if p["status"] == "open"
   )
   ```
   A simpler acceptable form: `current_equity = self.cash` (conservative; open position value not yet realized).

2. In `open_position()`, replace:
   - Before: `risk_amt = self.initial_capital * self.risk_per_trade`
   - After: `risk_amt = current_equity * self.risk_per_trade`

3. Replace dynamic capital-per-stock ceiling:
   - Before: `max_qty_by_capital = int(self.capital_per_stock / entry)`
     (where `capital_per_stock = initial_capital / num_stocks`)
   - After: `max_qty_by_capital = int((current_equity / self.num_stocks) / entry)`
   - This requires storing `self.num_stocks = num_stocks` in `__init__` (already stored via `self.capital_per_stock` but needs `num_stocks` separately).

**Additional `__init__` change:** Store `self.num_stocks = num_stocks` as an attribute so `open_position` can compute the dynamic per-stock ceiling.

---

## CHANGE 6 — Add deduplication counter (Phase 1 diagnostic)

**Source:** Verdict #13
**Priority:** SANDBOX-BLOCKER (low-effort; needed before DS3 run to collect the data)
**File:** `core/strategy.py`
**Function:** `BounceStrategy.generate_signals()`

**Change required:**
In the deduplication block (lines 111–117), count how many signals are dropped and log the result:

- Before:
  ```python
  seen_times = set()
  unique_signals = []
  for sig in signals:
      if sig["datetime"] not in seen_times:
          unique_signals.append(sig)
          seen_times.add(sig["datetime"])

  return unique_signals
  ```
- After:
  ```python
  seen_times = set()
  unique_signals = []
  dedup_dropped = 0
  for sig in signals:
      if sig["datetime"] not in seen_times:
          unique_signals.append(sig)
          seen_times.add(sig["datetime"])
      else:
          dedup_dropped += 1

  if dedup_dropped > 0:
      print(f"[strategy] dedup dropped {dedup_dropped} duplicate signals "
            f"({dedup_dropped / max(len(signals), 1) * 100:.1f}% of raw)")

  return unique_signals
  ```

---

## CHANGE 7 — Model transaction costs (Upstox + Kite) and slippage

**Source:** Verdict #4
**Priority:** SANDBOX-ENHANCEMENT
**File:** `core/portfolio.py`
**Functions:** `Portfolio.open_position()` and `Portfolio._close()`

**Changes required:**

### 7a — Entry slippage in `open_position()`
After computing `entry = signal["entry_price"]`, apply slippage:
```python
atr = bar["atr_14"]
entry = signal["entry_price"] + 0.1 * atr   # conservative fill above open
```
(The `atr` line already exists; adjust the entry assignment only.)

### 7b — SL exit slippage in `update()`
When reason is `"stop"`, fill 1 tick below the stop level. Define a tick size constant (NSE minimum tick = 0.05):
```python
_TICK = 0.05   # module-level constant

# In SL fill lines (both bullish and bearish branches):
# Before: exit_price = pos["stop"]
# After:  exit_price = pos["stop"] - _TICK
```
Apply to both branches (lines 118 and 130 in current file).

### 7c — Transaction cost computation in `_close()`
Add a helper function `_compute_charges(entry, exit_price, qty, broker)` that computes:
- Brokerage: 0.05% per side (Upstox) or 0.03% per side (Kite), capped at ₹20/order
- STT: 0.025% on sell-side turnover only
- Exchange fee: 0.00345% per side
- SEBI charge: 0.0001% per side
- GST: 18% on (brokerage + exchange + SEBI)
- Stamp duty: 0.003% on buy-side turnover

In `_close()`, compute charges for both brokers and store three PnL columns in the trade dict:
```python
raw_pnl = (exit_price - entry_price) * qty
net_pnl_upstox = raw_pnl - _compute_charges(..., broker='upstox')
net_pnl_kite   = raw_pnl - _compute_charges(..., broker='kite')
```
Trade dict entries: `raw_pnl`, `net_pnl_upstox`, `net_pnl_kite` (keep `pnl` as alias for `raw_pnl` for backward compatibility).

---

## CHANGE 8 — Implement SL variants B, C, D + Sandbox variant parameters

**Source:** Verdict #12
**Priority:** SANDBOX-ENHANCEMENT
**Files:** `core/portfolio.py` and Sandbox runner (new file)

### 8a — `Portfolio.__init__()` additions
Add two new parameters:
```python
sl_variant = "A"          # "A" | "B" | "C" | "D"
breakeven_trigger = None  # ATR multiples above entry to trigger breakeven (variants B, C)
trailing_dist = None      # ATR multiples for trailing stop (variant D)
```
Store as `self.sl_variant`, `self.breakeven_trigger`, `self.trailing_dist`.

### 8b — `Portfolio.open_position()` additions
Store ATR at entry in the position dict (needed by variants B/C/D in update):
```python
position["atr_at_entry"] = atr
position["breakeven_moved"] = False   # flag for variants B and C
position["trailing_stop"] = None      # current trailing stop level for variant D
```

### 8c — `Portfolio.update()` additions
After determining the bar is not an EOD/SL/target exit, add SL variant logic before checking exits:

**Variant B (Breakeven-1.5ATR):**
```python
if self.sl_variant == "B" and not pos["breakeven_moved"]:
    trigger_level = pos["entry_price"] + 1.5 * pos["atr_at_entry"]
    if bar.high >= trigger_level:
        pos["stop"] = pos["entry_price"]
        pos["breakeven_moved"] = True
```

**Variant C (Breakeven-2.5ATR):**
```python
if self.sl_variant == "C" and not pos["breakeven_moved"]:
    trigger_level = pos["entry_price"] + 2.5 * pos["atr_at_entry"]
    if bar.high >= trigger_level:
        pos["stop"] = pos["entry_price"]
        pos["breakeven_moved"] = True
```

**Variant D (Trailing SL 1.5ATR, no fixed target):**
```python
if self.sl_variant == "D":
    new_trail = bar.high - 1.5 * pos["atr_at_entry"]
    if pos["trailing_stop"] is None or new_trail > pos["trailing_stop"]:
        pos["trailing_stop"] = new_trail
    pos["stop"] = pos["trailing_stop"]
    # Variant D has no fixed target; disable target check
    pos["target"] = float("inf")
```

---

## CHANGE 9 — Make entry cutoff configurable (Sandbox variant F)

**Source:** Resolution "Why 14:30 as entry cutoff?" → variant F (14:45)
**Priority:** SANDBOX-ENHANCEMENT
**File:** `core/strategy.py`
**Function:** `BounceStrategy.__init__()` and `generate_signals()`

**Changes required:**

1. In `__init__`, add parameter `entry_cutoff_time=_time(14, 30)` and store as `self.entry_cutoff`.
2. In `generate_signals()`, replace the hardcoded reference:
   - Before: `if pd.Timestamp(datetime_arr[next_idx]).time() >= _ENTRY_CUTOFF:`
   - After: `if pd.Timestamp(datetime_arr[next_idx]).time() >= self.entry_cutoff:`
3. Module-level `_ENTRY_CUTOFF` constant can remain as the default sentinel; no other change needed there.

---

## CHANGE 10 — Add open auction filter (Sandbox variant E)

**Source:** Verdict #11 → variant E (skip entries before 09:45)
**Priority:** SANDBOX-ENHANCEMENT
**File:** `core/strategy.py`
**Function:** `BounceStrategy.__init__()` and `generate_signals()`

**Changes required:**

1. In `__init__`, add parameter `block_open_auction=False` and store as `self.block_open_auction`.
2. In `generate_signals()`, inside the `if close_arr[j] > ma_touch:` block, before appending the signal:
   ```python
   if self.block_open_auction:
       entry_time = pd.Timestamp(datetime_arr[next_idx]).time()
       if entry_time < _time(9, 45):
           break   # skip: entry in noisy open auction window
   ```

---

## CHANGE 11 — Implement SB-G Fixed Fractional sizing mode

**Source:** Resolution "Why is risk_per_trade fixed at 1% of initial capital?" → SB-G variant
**Priority:** SANDBOX-ENHANCEMENT
**File:** `core/portfolio.py`
**Function:** `Portfolio.__init__()` and `Portfolio.open_position()`

**Changes required:**

1. In `__init__`, add parameter `sizing_mode="capital_and_risk"`:
   - `"capital_and_risk"` = current behaviour (capital ceiling + risk constraint, min wins)
   - `"fixed_fractional"` = risk constraint only, no capital ceiling, emergency guard of ₹1,00,000 max position value
   Store as `self.sizing_mode`.

2. In `open_position()`, add a branch for `"fixed_fractional"`:
   ```python
   if self.sizing_mode == "fixed_fractional":
       qty = max(int(risk_amt / stop_dist), 1)
       # Emergency guard: cap position value at 1,00,000
       max_qty_by_emergency = int(100000 / entry)
       qty = min(qty, max_qty_by_emergency)
   else:   # "capital_and_risk" (default)
       max_qty_by_capital = int((current_equity / self.num_stocks) / entry)
       max_qty_by_risk = int(risk_amt / stop_dist)
       qty = max(min(max_qty_by_capital, max_qty_by_risk), 1)
   ```

3. For SB-G, `risk_per_trade` should be set in the range 0.002–0.003 (i.e., ₹2,000–₹3,000 at initial capital) when instantiating the Portfolio in the Sandbox runner.

---

## DEFERRED / NO CHANGE ITEMS

| # | Verdict | Status | Reason |
|---|---------|--------|--------|
| 7 | ATR on 5-min bars is correct | NO CHANGE | Intentional for intraday; daily ATR would break strategy |
| 8 | Entry price = next bar's open | NO CHANGE | Covered by entry slippage in Change 7a |
| 9 | Mark-to-market per instrument | DEFERRED | Zero impact on CAGR/PnL/win rate; implement in DS3 phase |
| 10 | Short side | NO CHANGE | Long-only is intentional for FV1 |
| OP-1 | Lookahead window {1,2,3} | DEFERRED | Already parameterized; add to Optuna search space |
| OP-3 | Volume multiplier | DEFERRED | Already parameterized; add to Optuna search space |
| OP-5 | Regime filter (GSS) | DEFERRED | Post-Sandbox, Step 3 of master plan |
| OP-6 | Risk % range (0.2–1.0%) | DEFERRED | Add to Optuna search space |

---

## SANDBOX TEST MATRIX (result of all changes above)

7 variants × 4 ATR configs = **28 combinations**

| Variant | Description | Key changes |
|---------|-------------|-------------|
| A | Fixed ATR baseline | Changes 1–6 only (blockers) |
| B | Breakeven at 1.5 ATR | Change 8 (breakeven_trigger=1.5) |
| C | Breakeven at 2.5 ATR | Change 8 (breakeven_trigger=2.5) |
| D | Trailing SL at 1.5 ATR | Change 8 (sl_variant="D") |
| E | Open auction filter | Change 10 (block_open_auction=True) |
| F | Entry cutoff 14:45 | Change 9 (entry_cutoff=14:45) |
| G | Fixed fractional sizing | Change 11 (sizing_mode="fixed_fractional", risk_per_trade=0.002–0.003) |

ATR configs: Extreme-1 (SL=2.5, TP=4.0), Extreme-2 (2.5/4.5), Extreme-3 (3.0/4.5), Extreme-4 (3.0/5.0)

---

## IMPLEMENTATION ORDER (suggested)

1. Change 1 — Remove compute_daily_mas() call (1 line delete)
2. Change 2 — Delete max_hold_bars (2 lines delete)
3. Change 3 — Add 1-position-per-stock guard in engine (3 lines add)
4. Change 4 — Remove cross-month check (10 lines delete)
5. Change 5 — Compounding position sizing (modify open_position)
6. Change 6 — Dedup counter (5 lines add)
7. Change 7 — Transaction costs + slippage (new helper, modify _close + open_position)
8. Change 8 — SL variants B/C/D (modify __init__ + open_position + update)
9. Change 9 — Configurable entry cutoff (param addition)
10. Change 10 — Open auction filter (param + 3-line check)
11. Change 11 — Fixed fractional sizing (SB-G mode)

# ── MASTER PLAN — SANDBOX STEPS ───────────────────────────────

Step 1  → fv1 code review + verdict (COMPLETE ✅)
           13 verdicts in fv1_pending_changes.md

Step 2  → Sandbox blockers implemented (COMPLETE ✅)
           Changes 1–6 from fv1_pending_changes.md

Step 3  → Sandbox feature Optuna (COMPLETE ✅)
  Step 3.1  → 16-combo brute-force feature sweep
  Step 3.2  → Optuna on SL variants (A/B/C/D) + 4 features
              Winner: SL=A, PG+CP+AF, CAGR=-2.15% (DS3)
              Merged as permanent sandbox defaults ✅
  Step 3.3  → Transaction costs + slippage merged ✅
              Slippage: 1-tick entry + SL exit
              Costs: raw/upstox/kite columns tracked
              Baseline: -8.62% raw CAGR (slippage only, no charges)

Step 4  → Regime filter Optuna — RE-RUNNING on full DS3 2015–2025 🔄
           Previous run was on 2022–2025 only → overfit, invalid.
           Script: Framework_V1_Sandbox/scripts/sb_regime_optuna.py
           Date filter: REMOVED — all years 2015–2025 included
           28 params (23 original + 5 new: PF10, MF6, TF5, MF7, SF1)
           Warm-up: 28 trials (one per filter, solo) via enqueue_trial()
           Sampler: TPE, 3000+ trials, fresh study DB
           Gate logic: OR and AND both in search space
           Optimize on: raw_pnl (raw CAGR)
           Baseline to beat: TBD after 2015–2025 baseline confirmed
           Stretch goal: net_pnl_kite CAGR positive
           Outputs: Framework_V1_Sandbox/outputs/optuna/
             ├── best_params.json
             ├── top20_trials.csv
             ├── optuna_study.db
             ├── optimization_history.png
             └── feature_importance.png

            Step 4.1 → Regime Filter Optuna — 2022–2025 (COMPLETE ✅)
             Best: Trial #2827, raw CAGR -4.48%, PF9+TF4, OR gate
             Finding: overfit — zero trades in 2015–2020
             Verdict: INVALID as general regime filter

            Step 4.2 → Regime Filter Optuna — Full DS3 2015–2025 (IN PROGRESS 🔄)
             Fresh run, date filter removed, dir_* TPE fix applied
             28 params, 3000 trials, TPE + 28 warm-up trials
             Baseline to beat: TBD after 2015–2025 baseline confirmed
             Constraint: no year should have zero trades with filter ON

            Step 4.3 → Bounce Quality Score

Step 5  → Full DS3 backtest 2015–2025 with Step 4 winner params
           Purpose: confirm Step 4 CAGR, update confirmed baseline
           This is a formality — sanity check only, no new Optuna run
           Status: PENDING Step 4 completion
STEP 6 → Python Phase 2 viewer ← AFTER backtest -> check the dedicated claude chat for tool list
STEP 7 → WFA + Optuna
STEP 8 → Paper trading (PENDING)
STEP 9 → Live trading

Parked for later steps:
  SL=D (trailing, ACT=3.0, TR=0.5) → revisit Step 7
  Fixed Fractional sizing (SB-G)   → revisit Step 7


# ─── FROM PAST CHATS — CAGR PROGRESSION ─────────────────
#
# Stocks involved: 29 stocks (fv1 baseline)
- Data window: 2022-2025

- CAGR progression:
-   No filter (F0):          -9.74%  ← fv1 raw baseline
-   Best single feature:     +2.07%  (MF4 active — MA50 prev day)
-   Best Optuna combo:       +2.69%  (PF8 | TF3 | MF4, OR gate)
-   Ground truth ceiling:    +8.95%  (same-day close, lookahead)

- ⚠️  The +2.07% and +2.69% used PREV DAY MA50 filter
-     (corrected version, no lookahead bias).
-     Ground truth +8.95% = same-day close = lookahead = invalid.

- ─── FOR STEP 3 COMPARISON ───────────────────────────────
- Our target: beat -9.74% with 16-combo Sandbox.
- If best combo > -9.74% → improvement confirmed.
- Then add prev-day regime filter → target beat +2.69% 🎯

