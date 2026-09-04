# CCG Orchestration — Claude Code ↔ Grok

Standing instructions file for delegating tasks from CC (Claude Code) to Grok.
New entries appended at the top (most recent first), each timestamped. Grok
should read this file when told to, follow the most recent unaddressed
instruction, and report back — CC keeps this file updated going forward.

---

## 2026-09-04 (pending — Grok) — Exit-type breakdown for top-10 SL/TP combos, 4 strategy versions

**Context**: Overnight (2026-09-04 00:39–02:18 VM time) 4 full 90-combo SL/TP
sweeps ran with the refined live-matching cutoff (`LAST_TOUCH_TIME=14:45`,
`ENTRY_CUTOFF_TIME=14:50`, per `Framework_V2/backtesting_rules/backtesting_rules.md`)
freshly added. All 4 picked their #1-ranked-by-ZPF combo at or near SL=6.0/TP=6.0 —
the very edge of the swept grid (`SL_VALS`/`TP_VALS` both cap at 6.0). Checked
6×ATR14 against actual price data: it's ~1.6–2.1% of price, roughly a full day's
typical intraday range for these stocks — meaning at that width, SL/TP barely
bind intraday and most trades likely just ride to the 15:00 EOD square-off
regardless of the entry signal's actual quality. That inflates ZPF by changing
the *exit-type mix* (fewer full stop-loss hits), not by reflecting genuine
directional edge — a trap, not a real result.

**Task**: instrument each of the 4 existing sweep scripts (below) to additionally
count, per combo, the exit-type breakdown across all trades: **SL-hit%, TP-hit%,
EOD+% (EOD exit with pnl>0), EOD-% (EOD exit with pnl<=0)** — four buckets
summing to 100% of that combo's trade count. This is a small addition: each
script's `run_combo()` already has an exit-priority branch (date-change → hour≥15
EOD → SL hit → TP hit, in that order) — just tag which branch fired per trade
alongside the existing pnl/exit_px append, then tally per combo.

**Scope — rerun the FULL 90-combo grid for all 4 versions, not just the current
top-10.** Restricting the recheck to the existing top-10-by-ZPF would be
circular: that subset is exactly where the suspected EOD-exit artifact
concentrates, so a genuinely healthy narrower-band combo sitting outside the
current top-10 (e.g. rank #35, disadvantaged by *not* benefiting from the
artifact) would never get surfaced. Full-grid instrumentation lets you re-rank
every combo by "ZPF among combos with a healthy exit-mix" directly, rather than
trusting a list built from the very metric under suspicion.

**The 4 scripts** (all under `Algo_Trading/Framework_V2/strategies/`, already
using DS3 data at `Framework_V2/data/historical/intraday_5min_DS3/`, all already
carry the refined cutoff — do not touch the entry/exit logic itself, only add
the tagging/counting):
1. `ma_short/v1/sweep_v1.py`
2. `ma_short/v2_vwap/sweep_v2_vwap.py`
3. `6bce/v0/sweep_v0.py`
4. `6bce/v1_vwap/sweep_v1_vwap.py`
Each already sweeps `SL_VALS = [1.5..6.0]` × `TP_VALS = [2.0..6.0]` (90 combos)
— reuse that grid, just add the new tagging/counting to `run_combo()`.

**Output**: one CSV per version, 90 rows each (one per combo), columns:
`sl, tp, n, pf, zpf, shd, zshd, sl_hit_pct, tp_hit_pct, eod_plus_pct, eod_minus_pct`.
Save alongside each script (e.g. `ma_short/v1/exit_breakdown_full.csv`), plus
one combined `strategies/exit_breakdown_summary.md` per version showing: (a) the
current #1-by-raw-ZPF combo's exit-mix and whether EOD% (eod_plus_pct +
eod_minus_pct) exceeds ~25–30% (the threshold CC and Saurav agreed marks
"SL/TP no longer doing real work"), and (b) the top-5 combos ranked by ZPF
**after excluding any combo whose EOD% exceeds that threshold** — this
healthy-subset top-5 is the one to carry forward, not the raw-ZPF top-5.

**Report back**: the 4 CSVs + summary.md, plus a one-line verdict per version
(does the raw #1 pick survive the health filter, or does the healthy-subset
top-5 look meaningfully different from what we had).

**Validation baseline — read before running**: current known-good `.npz`
caches + full stdout logs from last night's (pre-instrumentation) runs are
backed up at `strategies/_baseline_2026-09-04/` (do not overwrite or read
FROM this folder as input — it's a reference copy only). Since instrumentation
is purely additive (same signal, same data, same cutoff, same trade loop —
just tagging which exit branch fired), your rerun's `pf`/`zpf`/`n` per combo
must exactly match the corresponding baseline grid cell. Diff your own output
against the baseline before reporting back; if any combo's pf/zpf/n doesn't
match, that means the script edit broke something in the underlying logic —
flag this explicitly rather than reporting the exit-breakdown numbers as
trustworthy.

---

## 2026-08-06 (done — Grok) — WFA NIFTY50 Model B gate

Walk-forward of NIFTY50 Model B Sell-gate on 30-stock SHORT trades **completed**.

- **Script:** `Framework_V2/scripts/trials/regime_model/memlabs/33_wfa_nifty50_model_b_gate.py`
- **Outputs:** `33_wfa_config1_results.csv` (270 rows, 9 folds × 30), `33_wfa_config2_results.csv` (120 rows, 4 folds × 30), `33_wfa_summary.md`
- **Config1:** 3yr/1yr slide 1yr — folds 2018-02…2026-07 (final partial)
- **Config2:** 5yr/20mo slide 20mo — 4 folds through 2026-07
- **Result:** no robust multi-window edge. Book ZPnL negative every fold. Best Config1 consistency = BANDHANBNK 5/9 (only +total ZPnL); Config2 = NATIONALUM 3/4 (marginal). Single-split “winners” fail WFA. See summary bottom line.

---

## 2026-08-06 (pending — completed above)

**Walk-Forward Analysis (WFA) — rolling window, NIFTY50 Model B gate on fv2 SHORT trades.**

Context: single-split validation (75/25, one fixed Train/Test boundary) already
showed the "best gate" result is fragile — the top-5-stock results collapsed
when the Train/Test boundary shifted by a few months (after a data refresh),
and 4 of 5 stocks' entire edge was carried by one single day (2024-06-04,
the election-result crash). WFA is the next validation step: does ANY edge
survive being tested across multiple, independent, rolling time windows
instead of one arbitrary split?

**Reference/index**: notebook 31, scripts 25-29 and 32 in
`Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/` — same
methodology (NIFTY50 daily Model B: `close_log_return_lag_1` +
`close_log_return_ma_lag_1` → `close_log_return`, Train-only fit,
`signal=sign(y_hat)`, gate = only count a stock's SHORT (ma_rejection_v1_core.py
live logic) trade if that day's NIFTY50 signal is Sell), applied here as TWO
separate rolling-window configs instead of one fixed split.

**Data**: `Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3/` (30
stocks, 2015-02-02 → 2026-07-31) and
`Algo_Trading/Framework_V2/data/historical/daily/NIFTY50.parquet` (same range).
Both already gap-filled and validated — no fetching needed for this task.

**Config 1 — 3yr Train / 1yr Test, rolling, fixed-size** (both windows slide
forward together, old data drops off as new data is added — NOT expanding):
Fold 1: Train 2015-02→2018-02, Test 2018-02→2019-02. Fold 2: Train
2016-02→2019-02, Test 2019-02→2020-02. Continue sliding by 1 year until data
runs out (final fold's Test will be partial, ending 2026-07-31).

**Config 2 — 5yr Train / ~1.67yr (20mo) Test, rolling, fixed-size**, same
75/25 ratio as the original single-split validation, just repeated as a
sliding window: Fold 1: Train 2015-02→2020-02, Test 2020-02→2021-10. Fold 2:
Train 2016-10→2021-10, Test 2021-10→2023-06. Continue sliding until data
runs out (final fold partial).

**For each fold, each config**: refit NIFTY50 Model B fresh on that fold's
Train window ONLY (no lookahead — never fit on data outside that window, even
if it exists in the full dataset). Compute the day-level signal for that
fold's Test window using the fold's own fitted coefficients. Gate all 30
stocks' SHORT trades (build each stock's full-history trade log ONCE, reused
across folds — the trade log itself doesn't depend on the NIFTY signal, only
the gate does) whose `entry_dt` falls in that Test window. Report per stock,
per fold, per config: N, PF, net PnL, net ZPnL, ZPF (Zerodha-cost-adjusted,
same `zerodha_short()` formula as scripts 25-29/32).

**Aggregate and report**: per stock, per config — how many of the folds show
ZPF ≥ 1.0 (consistency count, not just average), plus the mean/median ZPF
across folds. Flag explicitly if a stock's apparent edge is concentrated in
one or two folds vs. spread evenly — that's the actual question this analysis
is answering.

**Output**: ONE long-format CSV per config (not per stock, not per fold as
separate files), columns: symbol, config, fold_num, train_start, train_end,
test_start, test_end, n, pf, pnl, zpnl, zpf. Save both under the `33_` prefix
in the memlabs folder (e.g. `33_wfa_config1_results.csv`,
`33_wfa_config2_results.csv`), plus a short `33_wfa_summary.md` with the
per-stock consistency-count table for both configs.

---

## 2026-08-06 (done — Grok)

DS3 gap-fill **completed** for 2026-01-01 → 2026-07-31 (append-only).

- **Stocks (30):** +**10,725** 5-min bars each (except **VEDL +10,722** — 3 fewer
  bars in Kite response on chunk2). All files end `2026-07-31 15:25:00+05:30`.
  Pre-2026 history preserved (`final_first` still ~2015-02-02 / BANDHANBNK 2018).
- **TATAMOTORS:** continuous via **NSE:TMPV** token `884737`.
- **Indicators:** `ma20` = 20-SMA close; `atr14` = 14-SMA true range; recomputed
  on append with 30-bar warmup from existing tail.
- **NIFTY50 daily:** +**143** rows → final 2845 rows, last `2026-07-31`.
- **Missing weekdays in span (NSE holidays / non-trading, same for all):**
  2026-01-15, 01-26, 03-03, 03-26, 03-31, 04-03, 04-14, 05-01, 05-28, 06-26.
- **Artifacts:** staging `Framework_V2/data/staging_ds3_2026/`;
  report `.../staging_ds3_2026/append_report.json`;
  script `Framework_V2/scripts/append_ds3_2026_gap.py`.
- **Note:** August 2026 still open — separate gap-fill after month close.
- **MCP-only:** local kiteconnect DNS unusable; all history via Kite MCP.

---

## 2026-08-06 (original request)

Fetch missing DS3 data: 30 stocks, 2026-01-01 through 2026-07-31 (5-min OHLCV
bars) — stop at July month-end; August is still in progress, add it as a
separate gap-fill once the month closes. Matching the existing DS3 format at
`Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3/` (columns:
datetime, open, high, low, close, volume, oi — plus ma20/atr14 precomputed,
matching that folder's existing files, not the older
`Framework_V1/data/historical/intraday_5min_archived/` copy which lacks those
two columns).

Symbols: ADANIPORTS, ASHOKLEY, AXISBANK, BAJFINANCE, BANDHANBNK, BHARTIARTL,
CIPLA, COALINDIA, DABUR, DIVISLAB, HDFCBANK, HINDALCO, ICICIBANK, INDUSINDBK,
INFY, ITC, JSWSTEEL, NATIONALUM, NTPC, ONGC, PNB, POWERGRID, RELIANCE, SBIN,
SUNPHARMA, TATAMOTORS, TATASTEEL, TECHM, VEDL, WIPRO.

Append the fetched rows onto each existing stock's parquet file (don't
overwrite the whole file — the existing 2015-2025 history must stay intact).
Recompute ma20/atr14 for the appended rows the same way the existing file's
columns were computed (rolling 20-bar mean for ma20, standard ATR14 formula —
check the existing file's last ~50 rows before the gap to confirm the exact
window/method used, don't guess).

Also fetch NIFTY50 daily data for the same gap (2026-01-01 to 2026-07-31) and
append to `Algo_Trading/Framework_V2/data/historical/daily/NIFTY50.parquet`
(same format as existing rows: datetime, open, high, low, close, volume, oi).

Report back: rows added per symbol, final date range per file, any gaps/
missing trading days flagged explicitly rather than silently skipped.
