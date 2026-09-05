# ATR Formula Exploration — Instructions for Grok

**Baseline reference script:** `ma_30_rejection_v1.py` (this folder) — build your own script(s) from this. Do not change anything except the ATR calculation and (for the source test) which bar's ATR is used.

**Where to save your output:** both your new backtest script and the results `.md` file go in this same folder — `Algo_Trading/Framework_V2/scripts/trials/ATR_exploration/`. Do not save either file anywhere else.

**Data:** `Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3/*.parquet` — 30 stocks, 2015–2025. Same universe, same columns (`open, high, low, close, ma20, atr14, datetime`).

**Lock everything else identical to the baseline:**
- Signal: wick-only touch from below MA20 (`high >= ma20 AND open < ma20 AND close < ma20`)
- Entry: open of next bar (`i+1`), same day, else skip
- SL = `entry + SL_MULT × ATR` , TP = `entry - TP_MULT × ATR`
- **SL_MULT = 2.0, TP_MULT = 4.5** (current live-deployed combo — do NOT use the SL=6.0/TP=6.0 "best" combo from the earlier sweep; this study must isolate the ATR formula's effect on the combo we're actually running)
- Exit priority: date change → prior close, `hour>=15` → bar open, SL hit, TP hit
- Position guard: single-pass, resume at `i = k+1`
- Skip if `pd.isna(ma20)` or `pd.isna(atr_variant)`

## 1. What to build — 12 variants total

Two independent switches:

**A. ATR formula (6 combos):**
| # | Formula | Period |
|---|---|---|
| 1 | Simple (rolling mean of TR) | 10 |
| 2 | Simple | 14 *(= current baseline formula, sanity-check it reproduces existing atr14 results)* |
| 3 | Simple | 20 |
| 4 | Wilder (RMA: `ATR_t = (ATR_{t-1}×(N-1) + TR_t)/N`, seeded with simple mean of first N TR values) | 10 |
| 5 | Wilder | 14 |
| 6 | Wilder | 20 |

**B. ATR source (2 options, applied to each of the 6 above → 12 total):**
| Source | Meaning |
|---|---|
| Signal | ATR value at the touch/signal bar `i` (current baseline behavior — `atr = row['atr14']` at signal bar) |
| Entry | ATR value at the entry bar `i+1` instead |

Compute TR and ATR **per stock**, per-parquet, using the full OHLC history (not just post-warm-up rows) so smoothing (Wilder) has proper lookback — same warm-up convention as the existing `atr14` column (i.e. don't reset per calendar year).

`TR = max(high - low, abs(high - prev_close), abs(low - prev_close))`

## 2. Metrics — use the Zerodha SHORT charge model (same as the SL/TP sweep)

```
brok  = min(0.0003 × entry, 20) + min(0.0003 × exit, 20)
stt   = entry × 0.00025
txn   = (entry + exit) × 0.0000307
sebi  = (entry + exit) × 0.000001
stamp = exit × 0.000003
gst   = 0.18 × (brok + txn + sebi)
total = brok + stt + txn + sebi + stamp + gst
zpnl  = raw_pnl - total
```

Report for **each of the 12 variants**:
- N trades, PF (raw), **ZPF**, Sh(D) (raw), **ZSh(D)**, % profitable days
- ZPF = sum(winning zpnl) / abs(sum(losing zpnl))
- ZSh(D) = (mean(daily_zpnl) / std(daily_zpnl)) × √252

## 3. Output format — single results.md, same structure as the SL/TP sweep results doc at:
`Algo_Trading/Framework_V2/scripts/trials/Backtesting Extended/ma20_short_v1/sl_tp_sweep_v1_short_results.md`

1. Strategy definition table (as above, note SL/TP locked at 2.0/4.5)
2. **Summary table — all 12 variants**, sorted by ZPF descending:
   `| # | Formula | Period | Source | N | PF | ZPF | Sh(D) | ZSh(D) | %ProfDays |`
3. Call out: does variant #2 (Simple14/Signal) reproduce the existing baseline atr14 numbers exactly (sanity check)?
4. Year-wise breakdown (2015–2025) for the **best variant only** (same table style as sweep doc §5)
5. Raw console output appended in full at the end

No need to re-derive SL/TP — this study is ATR-formula-only, at the fixed 2.0/4.5 combo.
