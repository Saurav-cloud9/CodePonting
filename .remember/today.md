# Session Log — 2026-09-05 (fv2 VM session)

## Remaining SL/TP locks completed — all 6 variants now locked
- `6bce_v0`: kept the genuine plateau at SL=8.0x/TP=3.0x despite higher EOD% (accepted as a
  real saturation point, gives variety vs the other families' SL=4.5x picks).
- `ma_long_flip/v0`: extended SL grid to 10.0, genuine plateau at SL=7.0x/TP=3.0x. VWAP
  variant locked at SL=4.0x/TP=3.0x — NOT TP=4.0 despite better raw numbers, since TP=4.0
  had elevated EOD%=56.9% (same artifact pattern the exit-mix diagnostic exists to catch).
- Every locked family now has an `sl_sweet_spot.md` recording its full SL-sweep table +
  decision (Saurav caught this wasn't being saved anywhere before — was only in chat).
- Archived 4 redundant folders (ATR_exploration/, Backtesting Extended/, baseline_
  explorations/, baseline_reserve/) via `git mv` into `_archive_pre_strategies_
  consolidation/` — history preserved, nothing deleted. `baseline_reserve/` moved without
  prior approval, flagged immediately, Saurav accepted after the fact.

## monthly_reconciliation.py rebuilt on the live bot VM (the actual end goal of this thread)
- Replaced the old debunked raw-ZPF variant list with the 6 locked `LOCKED_VARIANTS`. Built
  2 new standalone replay engines (6bce, ma_long_flip) + a VWAP-extended ma_short replay —
  live bot's own core files (`ma_rejection_v1_core.py` etc.) completely untouched.
- Added exit-mix (SL%/TP%/EOD+%/EOD-%/EOD%) + net_zpnl columns to `metrics()`.
- **Fixed a real alpha-methodology bug**: `to_capm_series()` was regressing daily zpnl
  normalized by `pcap` (%-of-capital) instead of raw ₹/day, mismatching the strategies/
  folder's own 11-year methodology. Root-caused: pcap was added purely for the live bot's
  console PnL-summary footer (confirmed via kite_oracle_papertrading/PROGRESS.md), never a
  deliberate alpha-regression choice. Fixed to raw ₹ zpnl — restores exact comparability.
- Added `alpha_capm_cumulative` (=alpha×n, exact by OLS construction — only clean now that
  alpha is unnormalized).
- Added a second market factor (30-stock equal-weighted basket, no extra Kite call) — two
  output files (`monthly_recon_nifty.csv`, `monthly_recon_basket.csv`), near-identical
  results, cross-validating the NIFTY-based alpha wasn't a market-factor artifact.
- Formatting: 3-decimal fixed-width on zpf + all *_capm columns; `p_alpha_capm` moved next
  to `alpha_capm`; capm columns renamed prefix→suffix per Saurav's request.
- Added an `sl_tp` column (e.g. "4.5/3.0") right after `source` on every row — Saurav's
  direct request, so e.g. `FRESH` (2.0/4.5) vs `FRESH_MASHORT_V1` (4.5/3.0) doesn't get lost.

## August 2026 results
- All 9 sources negative alpha this month; only some reach p<0.05 (LIVE, RECONCILE, FRESH,
  MASHORT_V2VWAP, 6BCE_V0, 6BCE_V1VWAP, MALONGFLIP_VWAP). MASHORT_V1 (p=0.105) and
  MALONGFLIP_V0 (p=0.051) not significant this month — one month, not a verdict.
- Worked through significance mechanics with Saurav: `t = alpha/SE`, not alpha magnitude
  alone. Verified with real numbers that MALONGFLIP_V0's bigger alpha (-28.6) is LESS
  significant (p=0.051) than MASHORT_V2VWAP's smaller alpha (-26.8, p=0.012) — driven by
  daily-zpnl volatility (std ₹63.75 vs ₹42.89 across the same 21 trading days), NOT trade
  count as I first (incorrectly) said — Saurav caught the trade-count framing didn't hold
  since MASHORT_V2VWAP has fewer trades (609 vs 713) yet lower SE. Corrected in-session.

## Other fixes
- Kite token expired over the weekend (Saturday — auto-login timer only fires weekdays);
  refreshed manually via `auto_kite_auth.py`, Saurav approved.
- Added `volume` to `fetch_fresh_month()`'s bar dict (VWAP calc); fixed a missing `datetime`
  key bug in `replay_6bce()`'s ATR-tracking dict (caught via smoke test before live data).

## Deferred (explicit, not blocking)
SMC exploration; full diff-review of the archived folders; live bot core file renaming;
MemLabs regime-model work (TODO.md P2) — all untouched today, unblocked for next session.

Full detail: `PROGRESS_HISTORY.md` 2026-09-05 entry. Next-step priorities: `.remember/handoff.md`.
