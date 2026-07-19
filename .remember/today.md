# Session Log — 2026-07-19

## Key Work Done

### backtesting_rules_v2.md final alignment
- Confirmed full alignment with CC scripts
- Added LONG charge direction note: `stt = exit × 0.00025`, `stamp = entry × 0.000003`

### 6BCE SHORT strategy — full sweep and analysis
- Built sl_tgt_sweep_6bce_short.py: 90-combo sweep (SL 1.5-6.0 × TGT 2.0-6.0), Zerodha charges, DS3 30 stocks 2015-2025
- Best ZPF = 0.888 (SL=6.0/TGT=6.0) — all 90 combos below ZPF=1.0; strategy dead
- ZSh(D) negative all years for all combos
- Post-2022 structural decay confirmed

### Charts built (all in Backtesting Extended/6BCE/)
- chart_zpf_lines_6bce.py — ZPF vs TGT, 10 SL lines, plasma colormap (user: "one of the better graphs")
- chart_consistency_6bce.py — scatter + year-wise ZPF lines; cache save added
- chart_spaghetti_6bce.py — all 90 combos overlaid; smoothest (cyan) vs volatile (red dashed)
- chart_spaghetti_zshd_6bce.py — same format but Y-axis = ZSh(D) per year

### Cache system
- sweep_cache_6bce.npz: overall_grid (10×9) + yearly_grid (10×9×11) + yearly_zshd_grid (10×9×11)
- Downstream chart scripts load from cache — no re-run needed

### Key findings
- Smoothest ≠ best: SL=2.0/TGT=2.0 (std=0.06) is consistently bad (ZPF=0.714)
- Best ZPF = Best ZSh(D) = same combo (SL=6.0/TGT=6.0); ZSh(D) adds no new info here
- Best consistency (mean−std): SL=6.0/TGT=5.5; only 2020 had ZPF>1.0 across any combo
- Plan: delegate sweep/chart work to Grok CLI; CC focuses on cloud engine build

## Key Numbers
- 6BCE best ZPF: 0.888 (SL=6.0/TGT=6.0)
- 6BCE best consistency: SL=6.0/TGT=5.5, cs=0.8198
- All combos ZSh(D) negative (mean ≈ -1.5 best case)

---

## Kite Paper Trading Bot (CC session, Algo_Trading/kite_oracle_papertrading/)

### Setup
- kite_auth.py built: login → request_token → access_token exchange, saves to .env, re-run daily
- AVG Internet Security found intercepting SSL (HTTPS scanning); uninstalled all 4 AVG products
  (Internet Security, Update Helper, Driver Updater, TuneUp) — redundant with Windows Defender
- Kite Connect auth validated end-to-end: login → instrument lookup → historical_data pull

### TATAMOTORS demerger discovery
- Tata Motors demerged Nov 2025 → TMPV (Passenger Vehicles, instrument_token 884737, continuing
  entity) + TMCV (Commercial Vehicles, new listing, token 194504193)
- Confirmed DS3's TATAMOTORS.parquet IS the TMPV entity (same token, price continuity verified) —
  no rebuild needed. Live bot must query symbol TMPV, not TATAMOTORS, going forward
- All other 29 DS3 universe stocks verified still resolve correctly against Kite's instrument list

### Data architecture decided
- Live engine: ticks only (KiteTicker) — builds own 5-min bars for signal/entry, real-time
  monitoring for exits. No historical_data/LTP polling in the live path at all
- historical_data reserved for a separate offline reconciliation script (script 2, not yet built) —
  compares tick-built bars + trades against Kite's official bars, after the session
- Compared against fv0 (legacy Upstox bot): used historical-candle (1-min→5-min manual convert
  until v3 API, then direct 5-min) + LTP polling (5-min scan, LTP every 5s for positions) — no
  WebSocket ticker; our approach upgrades this same hybrid idea

### SL/TP naming convention
- Established "SL/TP" (Stop Loss/Take Profit) as standard shortform going forward, replacing "TGT"
  in all new scripts (existing files keep TGT, not retroactively renamed). Added to TODO.md glossary

### Locked combo re-validated
- Found iteration_log.md: v1 clean-touch SHORT locked combo = SL=2.0x/TP=4.5x, N=110,641,
  PF=1.135, Sharpe=2.358 (not the 2.5x/4.0x used provisionally earlier in planning)
- Validated by re-running 5 sample combos from the 90-combo sweep — exact match on N/PF/Sharpe

### Offline paper-trading engine built (ma_30_rejection_v1_offline.py)
- Bar-by-bar, live-shaped architecture: explicit per-stock state (position/pending_entry),
  incrementally computed MA20/ATR14 (deque-based, not read from precomputed columns),
  chronologically interleaved across all 30 stocks (not stock-by-stock batches)
- Validated against ma_30_rejection_v1_reference.py (array-based backtest): PF=1.135/Sharpe=2.358
  exact match; N=110,637 vs 110,641 reference (4 trades / 0.0036% off)
- Root cause of the N diff fully diagnosed: exact floating-point tie at one bar (close=91.08,
  ma20=91.08000000000001) — pandas' incremental rolling mean accumulates rounding drift over
  11 years of updates; deque's fresh-sum-every-time doesn't. Neither is "wrong"; cascades via
  position-guard into ~126 non-overlapping trades net-4 difference. Documented, not fixed —
  DS3 regen parked as TODO P5 (only revisit if real inconsistencies appear, not this)
- Independently corroborated by Grok's review (grok_review.md): identical N/PF/Sharpe/trade-level
  breakdown, same root-cause diagnosis

### Automation plan discussed (not yet built)
- Deployment target: Oracle Cloud VM (Linux), not local PC — local is dev/test only
- Scheduling: cron (Linux equivalent of Task Scheduler), auto-launch ~9:10-9:14am IST
- Kite login: cron cannot automate the actual Zerodha login (requires browser + 2FA/TOTP) —
  starting with manual login each morning (option 1); full headless automation via stored
  credentials + pyotp (option 2) to be tested later, only switched to once fully confident

### Still open / not yet built
- Position sizing (1% risk, compounding) — not yet implemented in offline engine (currently
  per-share PnL only, matching reference script's style)
- Shortability check — stubbed as always-True, real MIS/ASM-GSM check not wired up
- Reconciliation script (script 2) — not built
- Live script (KiteTicker ingestion, warm-up pull, reconnect handling) — not built
- Automation wrapper (cron + EOD report generation) — not built
