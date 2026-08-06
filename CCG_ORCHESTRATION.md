# CCG Orchestration — Claude Code ↔ Grok

Standing instructions file for delegating tasks from CC (Claude Code) to Grok.
New entries appended at the top (most recent first), each timestamped. Grok
should read this file when told to, follow the most recent unaddressed
instruction, and report back — CC keeps this file updated going forward.

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
