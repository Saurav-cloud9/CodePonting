# Handoff Note — 2026-09-05 (fv2 VM session)

## Current State — Strategy raw-edge search, all 6 variants locked + deployed

The main thread from the last several sessions is DONE: all 6 `strategies/` variants are
locked (ma_short_v1 SL=4.5/TP=3.0, ma_short_v2vwap SL=4.5/TP=3.0, 6bce_v0 SL=8.0/TP=3.0,
6bce_v1vwap SL=4.5/TP=3.0, ma_long_flip_v0 SL=7.0/TP=3.0, ma_long_flip_vwap SL=4.0/TP=3.0),
and `monthly_reconciliation.py` on the live bot VM (`~/kite_oracle_papertrading/scripts/`)
has been rebuilt to replay all 6 side by side against LIVE/RECONCILE/FRESH, with corrected
raw-₹ alpha methodology, dual NIFTY/basket benchmarks, exit-mix diagnostics, and an `sl_tp`
combo column. August 2026 run completed and verified — both `monthly_recon_nifty.csv` and
`monthly_recon_basket.csv` saved under `data/recon/monthly/2026-08/`.

**Key August 2026 finding**: all 9 sources show negative alpha point estimates; several
reach p<0.05 (LIVE, RECONCILE, FRESH, MASHORT_V2VWAP, 6BCE_V0, 6BCE_V1VWAP, MALONGFLIP_VWAP)
but MASHORT_V1 (p=0.105) and MALONGFLIP_V0 (p=0.051) don't — one month of data, treat as a
data point, not a verdict on any variant yet.

## Immediate next steps (no priority order among these — Saurav to pick)

1. DS3 data bug (ICICIBANK/ITC/SBIN zero-filled OHLC, 2015) — still unresolved. Use direct
   Kite Connect API (`kiteconnect` lib + live bot's `.env` creds), NOT Kite MCP's
   `get_historical_data` (confirmed broken app-side).
2. Resume SMC rebuild (Liquidity/FVG/OB) — was explicitly on hold pending the
   monthly_reconciliation.py deploy, which is now done. Rebuild fresh from
   `strategies/smc/smc_concepts_summary.md` (original backtest results live on a bookmarked
   claude.ai session, not recovered here).
3. Diff-review `strategies/_archive_pre_strategies_consolidation/` (4 archived folders) to
   decide what's safe to permanently delete — low priority, not urgent.
4. Live bot core file renaming (`ma_rejection_v1_core.py` → ma_short naming convention) —
   deferred "to another day" by Saurav's own explicit call, not blocking anything.
5. Run `monthly_reconciliation.py` again for future months as they close, to build up more
   than one month of alpha evidence before drawing conclusions on any of the 6 variants.

## Key methodology locked in this session (apply going forward)

- **Alpha regression must use raw ₹/day zpnl**, never normalized by pcap or any other daily-
  varying capital base — pcap is a console-monitoring metric only (confirmed via
  kite_oracle_papertrading/PROGRESS.md), not designed for regression use. Cumulative alpha
  (`alpha × n`) is only mathematically exact under this raw-₹ convention.
- **Significance is `alpha/SE`, not alpha magnitude alone** — a bigger point estimate can
  still be less significant if the underlying daily P&L series is noisier (higher day-to-day
  std across the same number of trading days). Don't reason from trade count; check the
  actual daily-aggregated std when comparing SEs across variants.
- **Exit-mix diagnostic (SL%/TP%/EOD+%/EOD-%/EOD%) stays mandatory** for any SL/TP lock —
  a genuine plateau can still hide an EOD-riding artifact at a *nearby* TP value (caught for
  ma_long_flip_vwap: TP=4.0 looked better raw but had EOD%=56.9%, same red flag pattern).

## Known issues / open threads

- RS peer check-ins from 2026-09-04 (cplearning, cpfable, mathmode, cpgeneric) — no replies
  ever logged; not re-sent this session since the thread's own next steps didn't need them.
- TODO.md P2 (MemLabs #53 feature-screening decision point) — still untouched, unrelated to
  this thread, pick up whenever Saurav wants to switch focus.
- Kite access token needed a manual weekend refresh (`auto_kite_auth.py`) — will need this
  again on any Saturday/Sunday session since `kite-auto-login.timer` only fires weekdays.
