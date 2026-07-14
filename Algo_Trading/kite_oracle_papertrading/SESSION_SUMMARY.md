# Kite Paper Trading Bot — Session Summary

Session date: 2026-07-12 to 2026-07-13

## Goal
Build a local paper-trading bot for the MA20 wick-only rejection short strategy
(`scripts/kite_oracle_ma_30_rejection_v1.py`, SL=2.5x ATR / TGT=4.0x ATR,
backtest PF=1.080, Sharpe=1.546 on DS3), using Kite Connect (paid subscription)
as the broker, running on the local PC (not Oracle Cloud, despite folder name).

## Setup completed
- Kite Connect app: `CodePonting-fv2`, API key/secret configured in `.env`
- `kite_auth.py` (root of this folder) — login URL → paste redirect URL/request_token
  → exchanges for access_token → saves `KITE_ACCESS_TOKEN` into `.env` automatically.
  Re-run every morning (token expires ~7:30am daily).
- Verified end-to-end: auth → instrument lookup → `historical_data` 5-min pull, all working.

## Folder structure
```
kite_oracle_papertrading/
├── .env                                  (KITE_API_KEY, KITE_API_SECRET, KITE_ACCESS_TOKEN)
├── kite_auth.py                          (daily login/token refresh)
├── scripts/
│   └── kite_oracle_ma_30_rejection_v1.py (strategy source — backtest logic)
├── test/
│   └── test_historical_data.py           (one-off smoke test, already passed)
└── data/
    ├── trades/                           (for future trade logs)
    └── reports/                          (for future reports)
```

## Environment issue found and fixed
- AVG Internet Security was doing SSL/TLS interception (HTTPS scanning), breaking
  Python's certificate verification for `api.kite.trade`.
- Resolution: uninstalled all 4 AVG products (Internet Security, Update Helper,
  Driver Updater, TuneUp) — redundant with Windows Defender + Windows Update.
  No workaround (`pip-system-certs`) left in place; removed cleanly instead.

## Major finding: TATAMOTORS demerger
- Tata Motors demerged in Nov 2025 into two NSE entities: **TMPV** (Tata Motors
  Passenger Vehicles, instrument_token 884737) and **TMCV** (Tata Motors
  Commercial Vehicles, new listing, token 194504193).
- Confirmed **TMPV retains the original instrument_token (884737)** — DS3's
  `TATAMOTORS.parquet` data (last row 2025-12-31, close ≈367.65) matches Kite's
  daily candle for token 884737 on the same date (367.35) almost exactly.
- **Conclusion: DS3 dataset and fv2 backtest work are unaffected** — no rebuild
  needed. Only change: live/paper bot must query symbol `TMPV`, not `TATAMOTORS`,
  for this stock going forward (same instrument_token).
- Checked all other 29 DS3 universe stocks against Kite's current instrument
  list — all resolve cleanly, no other renames/corporate actions found.

## Data architecture decided
Three Kite data options identified:
1. `KiteTicker` (WebSocket) — live streaming ticks, push-based
2. `historical_data()` — REST, ranged OHLC candles (the "historical" endpoint,
   also used for near-real-time recent bars, not just backtest-era data)
3. `quote()`/`ltp()`/`ohlc()` — REST, current-snapshot only, pull-based

**Decision: full tick-based live engine.**
- Signal detection/entry: build our own 5-min bars from the tick stream in
  real time (not `historical_data` polling) — eliminates detection-to-entry
  lag/slippage, since we react the instant a bar boundary closes rather than
  waiting for a scheduled poll.
- Exits: monitor open positions via ticks directly, in real time — matches the
  backtest's own assumption of "fill the instant SL/target is crossed."
- `historical_data` is used only in a **separate offline reconciliation
  script** (script 2), run after the trading session:
  - Compares our tick-built bars against Kite's official bars (bar-level check)
  - Reruns the backtest logic on official bars, compares trades against what
    the live engine actually did (trade-level check)
  - Some divergence is expected (real slippage vs. backtest's clean fill
    assumptions) — the goal is catching *structural* mismatches (missed/extra
    signals), not zero difference.

Compared against fv0 (legacy Upstox live bot): consistently used
`historical-candle` (v2: 1-min bars + manual `convert_to_5min_candles()`;
v3 onward, starting `ma_bounce_bot_v1_1_PRODUCTION_FIXED_1.py`: direct 5-min
pull, no manual conversion) plus LTP polling (5-min scan cadence, LTP every
5 seconds for open-position monitoring). No WebSocket ticker was used in fv0 —
our tick-based approach is an upgrade on that same hybrid idea.

## Pre-build checklist (resolved)
1. **MA20/ATR14 warm-up** — tick-built bars start from zero each day, but the
   indicators need 20/14 prior bars. Fix: at startup, pull `historical_data`
   over a generously wide window (last ~10 calendar days) and take just the
   **last 20 candles** from the response — no day-counting logic needed.
2. **Position sizing** — compounding (risk % applied to current equity, not
   fixed capital), matching the sandbox's `risk_per_trade = 1%`,
   `capital = 1,000,000` convention. Chosen deliberately for how real trading
   should work, not to match the backtest (backtest can be changed later).
3. **Position limits** — no portfolio-wide cap on concurrent trades across the
   30 stocks; only the per-stock guard (max 1 trade per stock at a time,
   matching `kite_oracle_ma_30_rejection_v1.py`'s inherent sequential-loop
   behavior). Deliberate choice: this phase is about gathering as much trade
   data as possible to find which stocks/setups actually work, so no
   artificial cap on total concurrent signals firing.
4. **WebSocket reconnect handling** — on reconnect, ticks resume from "now"
   only; any gap is NOT auto-replayed. Fix: on reconnect, pull `historical_data`
   for the missed window to patch in official bars before resuming tick-building.
5. **Log schema** — two logs needed: (a) bar log (our tick-built 5-min bars,
   for comparing against Kite's official bars), (b) trade log (matching the
   backtest's existing trade output shape, for apples-to-apples comparison).
6. **Shortability** — not yet explicitly verified that all 30 stocks are
   MIS/intraday-shortable on the account. Still open.

## Open / provisional items for next session
- **SL/TGT ATR multiplier (2.5x / 4.0x)** — provisional. Latest sweep/baseline
  results live on the desktop, not this device. Revisit once back on desktop;
  nothing about the bot's architecture depends on the exact multiplier value.
- Script 1 (live tick-based paper engine) — not yet built, only planned.
- Script 2 (offline reconciliation script) — not yet built, only planned.
- Shortability check for all 30 stocks — not yet done.
- First real test can only happen live, during market hours (Kite has no
  historical tick data API — ticks only exist in real time, no way to
  backtest/dry-run the tick engine against past data).

## Kite tick data — mechanics learned
- Tick payloads are **binary on the wire**, never JSON — `pykiteconnect`'s
  `KiteTicker` decodes the binary packet into a Python dict for the `on_ticks()`
  callback. Only non-market messages (postbacks, subscribe requests) are JSON.
- A tick fires per matched trade on the exchange, but Kite's feed appears to
  send periodic snapshot packets (evidence: sample tick showed `timestamp` and
  `last_trade_time` differing by several seconds) rather than a strict 1:1
  push per individual trade — needs empirical confirmation once connected live.
- `last_price`/`last_quantity` = the specific last trade's price/quantity
  (varies per trade, not tied to liquidity in a simple way — liquidity mostly
  affects trade *frequency*, not individual trade size).
- `buy_quantity`/`sell_quantity` = aggregate **pending/unfilled** order book
  depth, unrelated to the last trade itself.
- `ohlc` inside a tick = current day's running OHLC snapshot, not a 5-min bar —
  confirms we must build our own 5-min bars from raw ticks; Kite doesn't hand
  us bar-level data via the tick stream.
- A single large order can generate multiple small trade prints (splitting
  across several resting counter-orders at different price levels) — this is
  why rapid bursts of small-quantity ticks happen even from one order.

## Kaggle data
- Checked `Algo_Trading/Kaggle/` — only 1-min OHLC CSVs (e.g. `ABB_minute.csv`),
  no tick-level data available there.
