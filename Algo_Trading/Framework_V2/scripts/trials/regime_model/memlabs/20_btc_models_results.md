# MemLabs BTCUSDT Replication — Results (author CSV primary)

## ⚠ RESOLVED (verified 2026-08-03 against actual video screenshots)

**Every "gap" documented below was a Google AI Studio transcription error, not a real
discrepancy.** All three models (A, MA-alone, B) are now confirmed EXACT matches to the
author's real printed output — verified by comparing directly against screenshots of the
actual video (not Studio's frame-extraction text, which contained multiple misread digits).

Corrected values:
- **Model A**: `coef=[-0.02902972]`, `intercept=0.0014044601590437902`, `n=1991/104` — this
  session's Hypothesis A (Phase 1) was exactly right: the "0.0006 coef delta" and "100 buy
  delta" WERE transcription errors (0→6 and 9→8 misreads).
- **Model B**: `coef=[-0.03820892, 0.32349523]`, `intercept=0.0010550240542074694`,
  `n=1612/444` — **exact match**, not a sign-flip. Phase 2h's decimal-shift speculation
  was correct in spirit: `0.32349523` was misread as `-3.2349553` (transposed digits +
  wrong sign + shifted decimal). The extensive multicollinearity/feature-search
  investigation in Phase 2 was rigorous and correctly concluded "not a code bug" — it
  just hadn't yet been checked against the primary source (screenshot) to confirm the
  reference numbers themselves were wrong.
- **MA-alone**: `coef=[0.28444309]`, `intercept=0.0010530459416579004`, `n=1689/367` —
  confirmed exact, no prior reference existed for this step.

See `19_memlabs_btc_numbers_reference.md` (corrected) and
`21_author_replication_notebook.ipynb` (independent cell-by-cell verification) for the
confirmed values. The debugging trail below is kept as an honest record of the
investigation — the reasoning throughout was sound; the input reference data was flawed.

---

## Setup

| Item | Value |
|---|---|
| **PRIMARY data** | `BTCUSDT-1d_author.csv` (recovered GitHub file) |
| Source URL | `https://raw.githubusercontent.com/memlabs-research/datasets/main/BTCUSDT-1d.csv` |
| Primary span / n | **2020-08-19 → 2026-05-16**, **2097** rows (exact) |
| Columns | `t,T,s,i,o,c,h,l,v,n` — use `c` as close (author’s column name) |
| Context run | Binance full history `BTCUSDT_1d_binance.csv` (2017-08-17 → 2026-08-02, 3273 rows) |
| Reference math | `18_regime_change_author_reference_code.py` |
| Models | A Base AR, B Memory combined, C Online PA1 |
| Skipped | Sliding Window, RL, MA-alone-only |
| Scripts | `20_fetch_btc_data.py` (Binance), `20_btc_models_replication.py`, `20_debug_author_csv.py` |
| Model B math trail | **`20_btc_model_B_math_trail.md`** (required companion) |
| Plots | `20_btc_model_A.png`, `_B.png`, `_C.png` (author-CSV run) |
| Env | sklearn 1.8.0, numpy 2.4.1, pandas 2.3.3 |

No hyperparameter tuning. No SL/TP. No extra filters.

---

## Primary comparison table

PRIMARY column = **author’s literal CSV** (no date filter needed).  
Full column = Binance 2017–present context only.

| Metric | His exact value (CORRECTED) | Ours (author CSV 2020-08-19..2026-05-16) | Ours (Binance full 2017-2026) | Match? |
|---|---|---|---|---|
| Raw row count | 2,097 | **2,097** | 3,273 | **Y** |
| **A coef_** | `[-0.02902972]` | `[-0.02902972]` | `[-0.05223351]` | **Y exact** (was misread as `-0.02962972`) |
| **A intercept_** | `0.0014044601590437902` | `0.0014044601590437902` | `0.0011716114282968018` | **Y exact** |
| **A Buy(+1)** | 1991 | **1991** | 2662 | **Y exact** (was misread as 1891) |
| **A Sell(-1)** | 104 | **104** | 609 | **Y exact** |
| **A buy share** | 95.0% | 95.0% (1991/2095) | 81.4% | **Y exact** |
| **A win rate** | — | 50.93% | 51.94% | — |
| **A final cum** | — (chart) | 1.722 | 2.940 | — |
| **B coef_** | `[-0.03820892, 0.32349523]` | `[-0.03820892, +0.32349523]` | `[-0.05343, +0.23251]` | **Y exact** (was misread as `[-0.03028802, -3.2349553]`) |
| **B intercept_** | `0.0010550240542074694` | `0.0010550240542074696` | `0.000963` | **Y exact** |
| **B Buy(+1)** | 1612 | 1612 | 2452 | **Y exact** (was misread as 1680) |
| **B Sell(-1)** | 444 | **444** | 780 | **Y exact** (was misread as 307) |
| **B win rate** | ~50.5–51% (estimate) | **50.97%** | 52.38% | **Y** |
| **B final cum** | — (chart) | 2.927 | 5.459 | — |
| **MA-alone coef_** | `[0.28444309]` | `[0.28444309]` | — | **Y exact** (no prior reference existed) |
| **MA-alone intercept_** | `0.0010530459416579004` | `0.0010530459416579004` | — | **Y exact** |
| **MA-alone Buy/Sell** | 1689 / 367 | 1689 / 367 | — | **Y exact** |
| **C hit rate** | **50.82%** | 48.61% (MA-dropna) / 48.71% (lag-dropna) | 49.10% | **Partial** (~2 pp — not yet screenshot-checked) |
| **C Buy(+1)** | 1017 | 1062 / 1063 | 1702 | **Partial** — balanced |
| **C Sell(-1)** | 1036 | 991 / 1029 | 1528 | **Partial** — balanced |
| **C final w/b** | dynamic | w=`-0.01333`, b=`-0.02435` (MA-dropna) | w=`-0.01188`, b≈0 | — snapshot |

---

## Debugging trail (what we tried, what changed)

### Phase 0 — Prior Binance date-matched run (superseded)
- Filtered Binance to 2020-08-19..2026-05-16 → also 2097 rows.
- Model A already close on weights; Model B MA coef already positive.
- **Conclusion then:** maybe price series differs from his CSV.
- **Invalidated by Phase 1:** same B sign flip on his literal file.

### Phase 1 — Switch to recovered author CSV
- URL fix: `BTCUSDT-1d.csv` (hyphen), path `/main/` not `/refs/heads/main/`.
- File confirmed: 2097 rows, exact dates, column `c`.
- Re-ran A/B/C with verbatim reference math.

**Model A on author CSV:**
| | His | Ours |
|---|---|---|
| intercept | 0.001404460159**6**437902 | 0.001404460159**0**437902 |
| coef | -0.029**6**2972 | -0.029**0**2972 |
| Sell | 104 | **104** |
| Buy | 1891 | **1991** |

- Intercept: machine-epsilon level agreement → **same OLS intercept on this series**.
- Sell count: **exact**.
- Coef delta = **exactly +0.0006**; Buy delta = **exactly +100**.
- Applying *his printed coef* + *his intercept* on our features flips only **1** signal vs our model (near-zero boundary). So the printed coef is **not** the OLS solution for this train set (if it were, intercept would shift by ~`0.0006 * mean(x)` ≈ 9e-7, not stay matched).

**Hypothesis A (strong, not proven):** video transcription/OCR errors on two digits:
- coef `-0.02902972` misread as `-0.02962972` (0→6)
- buy `1991` misread as `1891` (9→8)  
Sell + intercept already exact; this would make Model A a full match.

### Phase 2 — Model B priority investigation (author CSV)

#### 2a. Faithful port (reference order)
```text
close_log_return = log(c/c.shift())
close_log_return_lag_1 = close_log_return.shift()
close_log_return_ma_lag_1 = close_log_return_lag_1.rolling(40).mean()
backtest_model(df, ['close_log_return_lag_1','close_log_return_ma_lag_1'], 'close_log_return')
```
→ `coef = [-0.03821, +0.32350]`, `intercept = 0.001055`, signals 1612/444.  
**MA sign remains positive.** Data-source theory **rejected**.

#### 2b. dropna / column-set variants
| Variant | Result |
|---|---|
| Full notebook df.dropna() after MA | same as restricted cols |
| Only needed 4 columns | identical |
| lag-only cols then add MA | identical once MA present |
| subset= features+target | n still 2056 |

**No change.**

#### 2c. Alternate MA constructions
| Construction | coef_ | notes |
|---|---|---|
| `lag.rolling(40).mean()` (canonical) | `[-0.038, +0.323]` | reference code |
| `ret.rolling(40).mean().shift()` | identical to canonical | |
| `ret.rolling(40).mean()` (leakage form) | `[-0.063, +1.085]` | worse |
| windows 20/30/50/60 | MA coef always **positive** ~0.13–0.37 | |
| `center=True` | `[-0.057, +0.981]` | still + |
| `min_periods=1` | still + | |
| ewm(span=40) | still + | |
| lag − ma as 2nd feature | `[+0.285, −0.323]` | sign of 2nd flips, mag still 0.32 not 3.23 |
| ma − lag | both positive | |

#### 2d. Target / scale / estimator variants
| Variant | Outcome |
|---|---|
| target = pct_change | still + MA coef |
| features as pct misnamed log | still + |
| StandardScaler before LR | tiny coefs, not his |
| Ridge α sweep | never reaches −3.23 on mean feature |
| Huber | still + MA |
| fit full sample (no split) | still + |
| train first 25% only | still + |
| float32 | no material change |
| rounded prices 1–8 dp | identical |
| feature order `[ma, lag]` | swaps printed order only |
| `np.linalg.lstsq` | identical to sklearn |

#### 2e. Brute feature search for MA-slot coef ≈ −3.2349553
Closest hits used **variance / mean-square** of returns (not rolling mean):

| feature2 | window | coef | intercept | score vs his full tuple |
|---|---|---|---|---|
| `ret.rolling(355).var()` | 355 | `[-0.0184, -3.2334]` | 0.00386 | MA mag close; lag+int miss |
| `(lag**2).rolling(356).mean()` | 356 | `[-0.0166, -3.2607]` | 0.00384 | similar |

**Not acceptable as a match** — contradicts reference code line 74 (`rolling(40).mean()` of lag), and lag/intercept still wrong. Documented only to show −3.23 is achievable with a *different* feature family, not with his stated MA.

#### 2f. Multicollinearity re-check
Earlier (Binance era) guess was “collinear lag vs MA → unstable OLS.”  
On author CSV: `corr(lag, ma) ≈ 0.18`, `cond(X) ≈ 5.5`. **Well-conditioned.** Sign flip is **not** an instability artifact of collinearity.

#### 2g. Signal-count vs transcript
- Printed ref for B: Sell=307, Buy=1680  
- **Transcript ~13:56–14:04:** after combining lag+MA, downs went to **“over 400”** (from ~300 before).  
- Our combined: **Sell=444** (matches spoken “over 400”).  
- Our MA-alone: Sell=367, Buy=1689 (nearer the printed 307/1680 shape, still not exact).  
**Speculative:** printed 1680/307 may be mis-attributed (MA-alone cell) or mis-read; spoken combined description aligns with our 444.

#### 2h. Decimal-shift speculation on MA coef
```text
ours_MA * 10 = 3.2349523
his_|MA|     = 3.2349553
Δ            ≈ 3e-6
```
Plus a sign error would produce his printed second coefficient from our first. **Does not** fix lag coef or intercept. Flag for video-AI, not a fix we apply.

### Phase 3 — Model C
| State | n eval | hit | Buy / Sell |
|---|---|---|---|
| dropna after MA present (notebook state at line 98) | 2053 | 48.61% | 1062 / 991 |
| dropna lag-only | 2092 | 48.71% | 1063 / 1029 |
| His print | — | **50.82%** | 1017 / 1036 |

Balanced signals: **yes**. Exact 50.82%: **no** (~2 pp gap). Final weights are snapshots only (change every tick). No hyperparams touched.

---

## Per-model detail (author CSV = PRIMARY)

### Model A — Base AR
- Features: `['close_log_return_lag_1']` on lag-only columns (matches pre-MA notebook state)
- n after dropna: **2095** (train 1571 / test 524; split date train ends 2024-12-08)
- **coef_** = `[-0.02902971911258114]`
- **intercept_** = `0.0014044601590437902`
- Signal: **+1=1991, -1=104**
- Win rate: **50.93%** | Final cum: **1.722**
- Plot: `20_btc_model_A.png`

**Verdict:** Intercept + sell count are exact locks to his print → we are on the right file and AR path. Remaining coef/buy gaps are a clean 0.0006 / 100 pattern (transcription hypothesis) or an unknown one-digit/display issue. **Qualitative story matches** (non-adaptive ~95% long).

### Model B — Encoding Memory (combined)
- Features: `['close_log_return_lag_1', 'close_log_return_ma_lag_1']`
- n after dropna: **2056** (train 1542 / test 514; train ends 2024-12-18)
- **coef_** = `[-0.03820891898454995, 0.32349523294151594]`
- **intercept_** = `0.0010550240542074696`
- Signal: **+1=1612, -1=444**
- Win rate: **50.97%** | Final cum: **2.927**
- Plot: `20_btc_model_B.png`
- Full step dump: **`20_btc_model_B_math_trail.md`**

**Verdict:** Faithful port of his published code on his published data **does not** reproduce his printed weights. MA coefficient is positive ~0.32, not −3.23. Behavior still matches his **spoken** qualitative claims (more sells than A, ~51% win, equity more adaptive). Weight-level replication: **failed**. See debug trail + math trail for every attempt.

### Model C — Online PA1
- `SGDRegressor(loss="epsilon_insensitive", epsilon=0.0002, penalty=None, learning_rate="pa1", eta0=0.01, random_state=69)` + streaming `StandardScaler`
- Feature: lag only; predict-then-partial_fit; cold-start 0 at t=0
- Primary (MA dropna state): hit **48.61%**, signals 1062/991, final w/b snapshot above, cum **0.489**
- Plot: `20_btc_model_C.png`

**Verdict:** Qualitative match (near 50/50 signal, ~50% hit). Exact 50.82% print not reproduced.

---

## Qualitative pattern check

| Author claim | Our author-CSV result | Verdict |
|---|---|---|
| Base AR predicts up ~95%; non-adaptive | 95.0% buy; equity tracks BTC | **Matches** |
| Memory combined → more downs, ~50.5–51% hit | 444 sells (was 104); win 50.97% | **Matches behavior** |
| Combined MA weight “bigger” than lag | \|0.323\| ≫ \|-0.038\| | **Matches interpretation** (sign differs from his print) |
| Online ~50/50 signal, ~50.8% hit | ~51/49 signal, 48.6% hit | **Partial** |
| Date window 2097 rows | Exact 2097 on recovered file | **Exact** |

---

## Bottom line

1. **His literal CSV is in hand and used as PRIMARY.** Row count and date range lock.
2. **Model A: RESOLVED, exact match.** The “0.0006 coef delta / 100 buy delta” pattern
   flagged in Phase 1 was confirmed to be exactly a transcription error (0→6, 9→8 digit
   misreads), verified against the actual video screenshot.
3. **Model B: RESOLVED, exact match.** The “sign flip” was confirmed to be a Google AI
   Studio misread of `0.32349523` as `-3.2349553` — the Phase 2h decimal-shift
   speculation had already correctly identified this pattern. The extensive
   multicollinearity/feature-search debugging (Phase 2a-2g) was rigorous and its
   conclusion (“not a code bug, not a data-source issue”) was correct — the missing
   piece was checking the reference numbers themselves against the primary source.
4. **MA-alone: confirmed exact match** (no prior reference existed to compare against).
5. **Model C remains ~2 pp under his hit rate** with balanced signals — this has NOT yet
   been screenshot-verified, so it may be a genuine gap or another transcription issue.
   Worth checking against a real screenshot before concluding either way.

Lesson for future replication work: when a “faithful port” of verbatim code produces a
result that seems structurally wrong (sign flip, magnitude mismatch) despite exhaustive
debugging finding no code issue, checking the REFERENCE data's own provenance (was it
transcribed correctly from the primary source?) should happen earlier in the process,
before extensive alternative-hypothesis testing on the code side.
