# Handoff Note — 2026-09-06 (fv2 VM session)

## Current State — monthly_reconciliation.py deploy VALIDATED, 2 real bugs found+fixed

The main thread from the last several sessions is now genuinely complete AND validated
(not just deployed). Saurav's own idea — parity-check the 6 new replay engines against
DS3 (same August month, trade-by-trade diff) — surfaced 2 real bugs:

1. **One-bar-stale indicators** (all 3 new engines: `replay_ma_short_vwap`, `replay_6bce`,
   `replay_ma_long_flip`) — were reading ma20/atr14 BEFORE calling `update_indicators()`
   for that bar, not after (opposite of `v1_core.process_bar()`'s own ordering, confirmed
   correct via exact match against DS3's own precomputed columns).
2. **Indicators skipped during position-guard skip-ahead** (`replay_ma_short_vwap` and
   `replay_ma_long_flip` only) — the `i=k+1` fast-forward after a trade closes also
   skipped `update_indicators()` for every bar in between, desyncing the deque from DS3's
   fully-vectorized (never-skips-a-bar) computation.

Both fixed. All 6 locked variants now show 99.6-100% trade-level parity with DS3
(remaining 1-3 trades/variant are boundary artifacts, same class already accepted for
ma_short_v1's 1/786). **The pre-fix August numbers reported earlier the same day for 5 of
6 variants were wrong and are superseded** — always use the post-fix
`monthly_recon_nifty.csv`/`monthly_recon_basket.csv` under `data/recon/monthly/2026-08/`.

Also added this session: **95% CI columns** (`ci_low_capm`/`ci_high_capm`) — distinguishes
"confidently near-zero" (narrow CI hugging zero) from "inconclusive" (wide CI that happens
to cross zero) from "confidently not-zero" (CI clear of zero entirely) — same p<0.05
threshold, very different practical read. Concrete case this caught: `ma_long_flip_v0`
(p=0.061, CI=(-62.55,+1.49)) is genuinely inconclusive, not "confidently zero" — same
fragility class as `6bce_v0`.

**Post-fix August 2026 verdict** (basket-factor report): all 9 sources negative alpha.
Confidently negative (CI entirely below zero): LIVE, RECONCILE, FRESH, MASHORT_V2VWAP,
6BCE_V0, 6BCE_V1VWAP, MALONGFLIP_VWAP. Genuinely inconclusive (wide CI crossing zero):
MASHORT_V1, MALONGFLIP_V0. One month — not a verdict on any variant yet, but no variant
is currently "confidently positive" either.

## Immediate next steps (no priority order among these — Saurav to pick)

1. **Resume SMC rebuild** (Liquidity/FVG/OB) — was on hold pending this deploy, now fully
   unblocked. Rebuild fresh from `strategies/smc/smc_concepts_summary.md` (original
   backtest results live on a bookmarked claude.ai session, not recovered here).
2. DS3 data bug (ICICIBANK/ITC/SBIN zero-filled OHLC, 2015) — still unresolved. Use direct
   Kite Connect API (`kiteconnect` lib + live bot's `.env` creds), NOT Kite MCP's
   `get_historical_data` (confirmed broken app-side).
3. Diff-review `strategies/_archive_pre_strategies_consolidation/` (4 archived folders) to
   decide what's safe to permanently delete — low priority, not urgent.
4. Live bot core file renaming (`ma_rejection_v1_core.py` → ma_short naming convention) —
   deferred "to another day" by Saurav's own explicit call, not blocking anything.
5. Run `monthly_reconciliation.py` again for future months as they close — a single
   confidently-positive month wouldn't be enough on its own anyway (multiple-testing risk
   across 9 sources tracked monthly); need repeated confirmation across months before any
   variant earns real trust either direction.

## Key methodology locked this session (apply going forward)

- **Naming**: `n` = number of trading DAYS in a CAPM regression; `n_trades` = trade count
  (the CSV's own column). These were both being called "n" and caused real confusion — now
  in TODO.md's GLOSSARY, locked.
- **CI > p-value alone for reading significance nuance** — always check `ci_low_capm`/
  `ci_high_capm` width, not just whether p<0.05. A non-significant p can mean "genuinely
  small, precisely measured" (narrow CI) or "can't tell yet" (wide CI) — very different
  practical conclusions from the same p-value.
- **Parity-check any new replay engine against its source-of-truth sweep script** before
  trusting its output — even carefully-written reimplementations can silently diverge on
  indicator-timing details (as both bugs this session were). Cheap to do (trade-by-trade
  diff on one overlapping month), catches real bugs raw-metric comparison alone would miss.
- **Pcap/Tcap are live-console-display-only** (CLAUDE.md, new section) — never feed into
  alpha/regression computation without Saurav's explicit direction for that specific case.
- `sl_tp` column uses "x" separator (`4.5x3.0`), not "/" — avoids Excel's date-parsing
  auto-reinterpretation of slash-joined number pairs.

## Known issues / open threads

- RS check-ins sent to cplearning/cpfable/mathmode/cpgeneric at the end of this session —
  check replies before assuming nothing happened elsewhere.
- TODO.md P2 (MemLabs #53 feature-screening decision point) — still untouched, unrelated to
  this thread, pick up whenever Saurav wants to switch focus.
- Kite access token needed a manual weekend refresh (`auto_kite_auth.py`) on 2026-09-05/06
  (both Sat/Sun) — will need this again on any weekend session since `kite-auto-login.timer`
  only fires weekdays.
