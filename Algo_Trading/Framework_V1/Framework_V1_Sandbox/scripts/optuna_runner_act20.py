"""
Optuna Optimization Runner — Option 1 (Activation Threshold Trailing)
======================================================================
Variant D: trail only activates after price moves activation_threshold×ATR in profit.
activation_threshold search range: 2.0 – 5.0 ATR  (step 0.5)
trailing_dist         search range: 0.5 – 3.0 ATR  (step 0.5)
FF: ENABLED (trial parameter)

Base config  : Extreme-2 (sl_mult=2.5, tp_mult=4.5)
Stocks       : 29 (VI excluded)
Data window  : 2022-2025
Trials       : 200
Objective    : maximize CAGR
"""

import sys, time
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import optuna
except ImportError:
    print("Optuna not installed. Run:  pip install optuna")
    sys.exit(1)

optuna.logging.set_verbosity(optuna.logging.WARNING)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.indicators import add_intraday_indicators, add_atr


# ─── CONSTANTS ────────────────────────────────────────────────────────────────
INITIAL_CAPITAL = 1_000_000
YEARS           = 4
NUM_STOCKS      = 30
EXCLUDE         = {"NIFTY50", "VI"}
ATR_MULT_STOP   = 2.5
RR_TARGET       = 4.5 / 2.5   # 1.8
RISK_PER_TRADE  = 0.01
VOL_MULT        = 1.2
LOOKAHEAD       = 3
_EOD_INT        = 1500
_CUTOFF_DEFAULT = 1430
_CUTOFF_LATE    = 1445
_AUCTION_INT    = 945

SCRIPT_DIR   = Path(__file__).resolve().parent
FV1_DIR      = SCRIPT_DIR.parent.parent
DS3_DIR      = FV1_DIR / "data/historical/intraday_5min_DS3"


# ─── STEP 1: LOAD & PREPROCESS STOCK DATA ─────────────────────────────────────
print("Step 1: Loading stock data...", flush=True)
t0 = time.time()

stock_files = sorted(
    f for f in DS3_DIR.glob("*.parquet")
    if f.stem not in EXCLUDE
)
print(f"  {len(stock_files)} stocks", flush=True)

stock_arrays = {}
stock_dfs    = {}

for sp in stock_files:
    stock = sp.stem
    df = pd.read_parquet(sp)
    df["datetime"] = pd.to_datetime(df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S"))
    df = df.sort_values("datetime").reset_index(drop=True)
    _t = df["datetime"].dt.time
    df = df[_t.between(pd.Timestamp("09:15").time(), pd.Timestamp("15:30").time())]
    df = df.reset_index(drop=True)
    df = add_intraday_indicators(df)
    df = add_atr(df)
    stock_dfs[stock] = df

    dti = pd.DatetimeIndex(df["datetime"])
    date_int = (dti.year * 10000 + dti.month * 100 + dti.day).to_numpy()
    time_int = (dti.hour * 100 + dti.minute).to_numpy()

    stock_arrays[stock] = {
        "datetime": df["datetime"].to_numpy(),
        "open":     df["open"].to_numpy(dtype=float),
        "high":     df["high"].to_numpy(dtype=float),
        "low":      df["low"].to_numpy(dtype=float),
        "close":    df["close"].to_numpy(dtype=float),
        "atr":      df["atr_14"].to_numpy(dtype=float),
        "date_int": date_int,
        "time_int": time_int,
        "n":        len(df),
    }

print(f"  Done in {time.time()-t0:.1f}s", flush=True)


# ─── STEP 2: PRECOMPUTE SIGNAL MAPS ───────────────────────────────────────────
print("\nStep 2: Precomputing signal maps (4 configs × 29 stocks)...", flush=True)
t1 = time.time()


def _gen_signals_by_idx(stock, use_entry_cutoff, use_auction_filter):
    df   = stock_dfs[stock]
    arrs = stock_arrays[stock]
    n    = arrs["n"]

    ma20     = df["ma20"].to_numpy()
    avg_vol  = df["avg_volume"].to_numpy()
    vol      = df["volume"].to_numpy()
    low      = arrs["low"]
    close    = arrs["close"]
    open_    = arrs["open"]
    time_int = arrs["time_int"]
    cutoff   = _CUTOFF_LATE if use_entry_cutoff else _CUTOFF_DEFAULT

    raw_signals = []
    for i in range(0, n - 3):
        if np.isnan(ma20[i]):
            continue
        if not np.isnan(avg_vol[i]) and vol[i] < avg_vol[i] * VOL_MULT:
            continue
        if low[i] <= ma20[i]:
            ma_touch = ma20[i]
            for j in range(i, min(i + LOOKAHEAD + 1, n)):
                if close[j] > ma_touch:
                    nxt = j + 1
                    if nxt >= n:
                        break
                    t_nxt = time_int[nxt]
                    if t_nxt >= cutoff:
                        break
                    if use_auction_filter and t_nxt < _AUCTION_INT:
                        break
                    raw_signals.append((nxt, open_[nxt], ma_touch))
                    break

    seen   = set()
    sm_idx = {}
    for nxt, ep, ma_touch in raw_signals:
        if nxt not in seen:
            seen.add(nxt)
            sm_idx[nxt] = {"entry_price": ep, "ma20": ma_touch}
    return sm_idx


signal_cache = {}
for use_cutoff in [False, True]:
    for use_auction in [False, True]:
        key = (use_cutoff, use_auction)
        signal_cache[key] = {
            stock: _gen_signals_by_idx(stock, use_cutoff, use_auction)
            for stock in stock_arrays
        }

total_signals = sum(
    len(sm)
    for sm_map in signal_cache.values()
    for sm in sm_map.values()
)
print(f"  Done in {time.time()-t1:.1f}s  "
      f"({total_signals:,} total signals across 4 configs)", flush=True)


# ─── STEP 3: TRIAL RUNNER ─────────────────────────────────────────────────────
def run_trial(params):
    use_pg   = params["use_position_guard"]
    use_comp = params["use_compounding"]
    use_ff   = params["use_fixed_fractional"]
    sl_var   = params["sl_variant"]
    be_trig  = params.get("breakeven_trigger")
    tr_dist  = params.get("trailing_dist")
    act_thr  = params.get("activation_threshold")   # only for D
    sig_key  = (params["use_entry_cutoff"], params["use_auction_filter"])

    total_pnl = 0.0

    for stock, arrs in stock_arrays.items():
        sm = signal_cache[sig_key][stock]
        if not sm:
            continue

        open_arr  = arrs["open"]
        high_arr  = arrs["high"]
        low_arr   = arrs["low"]
        close_arr = arrs["close"]
        atr_arr   = arrs["atr"]
        date_arr  = arrs["date_int"]
        time_arr  = arrs["time_int"]
        n         = arrs["n"]

        cash      = INITIAL_CAPITAL
        positions = []
        # pos layout:
        # [0] entry_idx   [1] entry_date  [2] entry_price [3] qty
        # [4] stop        [5] target      [6] atr_at_entry
        # [7] be_moved    [8] trailing_stop

        for i in range(n):
            op  = open_arr[i]
            hi  = high_arr[i]
            lo  = low_arr[i]
            cl  = close_arr[i]
            atr = atr_arr[i]
            d   = date_arr[i]
            t   = time_arr[i]

            if i in sm:
                if not (use_pg and positions):
                    sig   = sm[i]
                    entry = sig["entry_price"]
                    sd    = atr * ATR_MULT_STOP
                    if sd <= 0:
                        sd = entry * 0.01

                    eq = cash if use_comp else INITIAL_CAPITAL
                    risk_amt    = eq * RISK_PER_TRADE
                    per_stk_cap = eq / NUM_STOCKS

                    if use_ff:
                        qty = max(int(risk_amt / sd), 1)
                        qty = min(qty, int(100_000 / entry))
                    else:
                        qty = max(
                            min(int(per_stk_cap / entry), int(risk_amt / sd)),
                            1
                        )

                    positions.append([
                        i,                      # 0 entry_idx
                        d,                      # 1 entry_date
                        entry,                  # 2 entry_price
                        qty,                    # 3 qty
                        entry - sd,             # 4 stop (initial)
                        entry + sd * RR_TARGET, # 5 target
                        atr,                    # 6 atr_at_entry
                        False,                  # 7 be_moved
                        None,                   # 8 trailing_stop
                    ])

            if not positions:
                continue

            is_bull = cl > op
            kept    = []

            for pos in positions:
                if pos[0] == i:
                    kept.append(pos)
                    continue

                # EOD forced exit
                if d == pos[1] and t >= _EOD_INT:
                    pnl = (op - pos[2]) * pos[3]
                    cash      += pnl
                    total_pnl += pnl
                    continue

                # SL variant: update stop before exit check
                if sl_var == "B" or sl_var == "C":
                    if not pos[7]:
                        if hi >= pos[2] + be_trig * pos[6]:
                            pos[4] = pos[2]
                            pos[7] = True

                elif sl_var == "D":
                    # Activation threshold: only start trailing after X×ATR profit
                    activation_price = pos[2] + act_thr * pos[6]
                    if hi >= activation_price:
                        new_trail = hi - tr_dist * pos[6]
                        if pos[8] is None or new_trail > pos[8]:
                            pos[8] = new_trail
                        pos[4] = pos[8]
                    # Before activation: pos[4] stays at original stop

                stop   = pos[4]
                target = pos[5]

                exit_p = None
                if is_bull:
                    if lo <= stop:      exit_p = stop
                    elif hi >= target:  exit_p = target
                else:
                    if hi >= target:    exit_p = target
                    elif lo <= stop:    exit_p = stop

                if exit_p is not None:
                    pnl = (exit_p - pos[2]) * pos[3]
                    cash      += pnl
                    total_pnl += pnl
                else:
                    kept.append(pos)

            positions = kept

    final_equity = INITIAL_CAPITAL + total_pnl
    if final_equity <= 0:
        return -99.0
    cagr = ((final_equity / INITIAL_CAPITAL) ** (1 / YEARS) - 1) * 100
    return cagr


# ─── STEP 4: OPTUNA OBJECTIVE ─────────────────────────────────────────────────
trial_count      = [0]
best_cagr_so_far = [-999.0]
t_study_start    = time.time()


def objective(trial):
    params = {
        "use_position_guard":   trial.suggest_categorical("use_position_guard",   [True, False]),
        "use_compounding":      trial.suggest_categorical("use_compounding",       [True, False]),
        "use_entry_cutoff":     trial.suggest_categorical("use_entry_cutoff",      [True, False]),
        "use_auction_filter":   trial.suggest_categorical("use_auction_filter",    [True, False]),
        "use_fixed_fractional": trial.suggest_categorical("use_fixed_fractional",  [True, False]),
        "sl_variant":           trial.suggest_categorical("sl_variant",            ["A", "B", "C", "D"]),
    }
    sv = params["sl_variant"]
    if sv in ("B", "C"):
        params["breakeven_trigger"]  = trial.suggest_float("breakeven_trigger",  0.5, 5.0, step=0.5)
    elif sv == "D":
        params["activation_threshold"] = trial.suggest_float("activation_threshold", 2.0, 5.0, step=0.5)
        params["trailing_dist"]        = trial.suggest_float("trailing_dist",        0.5, 3.0, step=0.5)

    cagr = run_trial(params)

    trial_count[0] += 1
    if cagr > best_cagr_so_far[0]:
        best_cagr_so_far[0] = cagr

    if trial_count[0] % 10 == 0:
        elapsed = time.time() - t_study_start
        avg     = elapsed / trial_count[0]
        eta     = avg * (200 - trial_count[0])
        print(
            f"  Trial {trial_count[0]:3d}/200 | "
            f"best: {best_cagr_so_far[0]:+.2f}% | "
            f"elapsed: {elapsed:.0f}s | "
            f"avg: {avg:.1f}s/trial | "
            f"ETA: {eta:.0f}s",
            flush=True
        )

    return cagr


# ─── STEP 5: WARM-UP ──────────────────────────────────────────────────────────
print("\nStep 3: Warm-up — verifying baseline (E2-A, no features)...", flush=True)
baseline_params = {
    "use_position_guard":   False,
    "use_compounding":      False,
    "use_entry_cutoff":     False,
    "use_auction_filter":   False,
    "use_fixed_fractional": False,
    "sl_variant":           "A",
}
tw = time.time()
baseline_cagr = run_trial(baseline_params)
warmup_elapsed = time.time() - tw
print(f"  Baseline CAGR: {baseline_cagr:.2f}%  (expected ~-11.00%)", flush=True)
print(f"  Trial time:    {warmup_elapsed:.1f}s  "
      f"=> 200 trials ~{200 * warmup_elapsed / 60:.0f} min", flush=True)


# ─── STEP 6: RUN OPTUNA ───────────────────────────────────────────────────────
print(f"\nStep 4: Running 200 Optuna trials...", flush=True)
print(f"  Config: activation_threshold range 2.0 – 5.0 ATR | FF enabled\n", flush=True)

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=200, show_progress_bar=False)

best  = study.best_trial
delta = best.value - baseline_cagr


# ─── STEP 7: PRINT RESULTS ────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("OPTUNA RESULTS — ACT20 (activation 2.0–5.0) | FF ENABLED")
print("=" * 65)
print(f"\n  Baseline (E2-A, no features) : {baseline_cagr:.2f}%")
print(f"  Best Optuna combo            : {best.value:.2f}%")
print(f"  Delta                        : {delta:+.2f}pp\n")

print("  Best trial parameters:")
for k, v in sorted(best.params.items()):
    flag = "<-- ENABLED" if v is True else ""
    print(f"    {k:<25} = {v!s:<10} {flag}")

total_elapsed = time.time() - t_study_start
print(f"\n  Total Optuna time: {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)")

print("\n" + "-" * 65)
print("  TOP 10 TRIALS")
print("-" * 65)
print(f"  {'Rank':<5} {'CAGR%':>8}   Key params")
trials_sorted = sorted(
    [t for t in study.trials if t.value is not None],
    key=lambda t: t.value, reverse=True
)
for rank, t in enumerate(trials_sorted[:10], 1):
    p = t.params
    sv  = p.get("sl_variant", "?")
    pg  = "PG" if p.get("use_position_guard")   else "--"
    cp  = "CP" if p.get("use_compounding")       else "--"
    ec  = "EC" if p.get("use_entry_cutoff")      else "--"
    af  = "AF" if p.get("use_auction_filter")    else "--"
    ff  = "FF" if p.get("use_fixed_fractional")  else "--"
    extra = ""
    if "breakeven_trigger" in p:
        extra = f"  BE={p['breakeven_trigger']}"
    elif "trailing_dist" in p:
        extra = f"  TR={p['trailing_dist']}  ACT={p.get('activation_threshold', '?')}"
    print(f"  {rank:<5} {t.value:>8.2f}%   SL={sv}  [{pg}|{cp}|{ec}|{af}|{ff}]{extra}")

print("\n  Legend: PG=position_guard  CP=compounding  EC=entry_cutoff")
print("          AF=auction_filter  FF=fixed_fractional")
print("          TR=trailing_dist   ACT=activation_threshold")

print("\n" + "=" * 65)
print("[STOP] Awaiting approval before merging features into Sandbox.")
print("=" * 65)
