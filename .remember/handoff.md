# Handoff Note — 2026-07-20

## Current State — fv2 backtesting (6BCE / TODO.md thread)
- 6BCE SHORT confirmed dead (best ZPF=0.888, all 90 combos below 1.0, ZSh(D) negative everywhere)
- Cache built: sweep_cache_6bce.npz with overall_grid + yearly_grid + yearly_zshd_grid
- 4 chart scripts in Backtesting Extended/6BCE/ — all working, all load from cache
- No change since 2026-07-19 — untouched this session

## Current State — Kite paper trading bot (Algo_Trading/kite_oracle_papertrading/)
- Kite auth working (kite_auth.py); TATAMOTORS→TMPV mapping confirmed, DS3 unaffected
- Shared core logic extracted: ma_rejection_v1_core.py (StockState, process_bar,
  update_indicators, is_shortable stub) — used by both offline and live scripts
- Offline engine (ma_30_rejection_v1_offline.py) refactored to use core module, still validated
- **Live engine built and successfully tested live for the first time today**
  (ma_30_rejection_v1_live.py) — KiteTicker-based, tick-built bars, tick-based SL/TP exits,
  historical_data warm-up only. Real signals fired (DABUR/WIPRO/JSWSTEEL), first real trade
  closed (WIPRO SL hit) with verified-correct PnL math
- Two bugs found + fixed live: CSV PermissionError crash (now caught, skip+retry), EOD-hour
  exit was ~5min late (now tick-based, mirrors SL/TP) — EOD fix NOT yet confirmed live
  (applied after today's session was manually stopped, needs tomorrow's test)
- Reconciliation script built (ma_rejection_v1_reconcile.py) — bar-level + trade-level diff
  vs Kite's official data. First real run found bigger-than-expected divergence: 48/270 bars
  (17.8%) with real OHLC diffs up to ₹4.50, only 7/13 live trades matched official-replay.
  Hypothesized causes (mid-bucket startup effect, ticks as periodic snapshots not full trade
  feed) NOT yet confirmed with a concrete traced example — full detail in today.md
- live_bars.csv/live_trades.csv get OVERWRITTEN each run — no persistence across days;
  today's data was not auto-archived (user saved manually)

## Next Step (START HERE)

### fv2 backtesting thread (unchanged from 2026-07-19)
1. **P1 — Cloud engine**: build backtesting REST API on Oracle Cloud (primary) / AWS (fallback)
2. **P2 — baseline_reserve**: copy ma_bounce.py + ma_rejection.py from baseline_explorations/
3. **P3 — New signals via Grok**: feed backtesting_rules_v2.md to Grok; delegate 90-combo sweeps
4. **P4 — v1_vwap sweep**: no fresh 90-combo sweep done yet
5. **P5 — DS3 recompute (parked)**: only revisit if real inconsistencies appear, not the known
   floating-point tie-break already documented

### Kite paper trading bot thread
1. **Confirm the EOD-hour tick-based fix works live** — first priority tomorrow, test not
   yet done (fix applied after today's session already stopped)
2. **Dig into the reconciliation gap with a concrete traced example** — pick one mismatched
   bar (e.g. DIVISLAB 14:25 open diff=4.50) or one mismatched trade, trace it precisely like
   the DS3 floating-point tie was traced, before accepting the hypothesized causes as confirmed
3. Build CSV archival (dated folder, e.g. data/trades/archive/YYYY-MM-DD/) so live_bars.csv/
   live_trades.csv aren't silently overwritten each run
4. Make the reconciliation script save its findings to a file (console-only right now),
   suggest a format (CSV/markdown) + location (paired with the archived CSVs)
5. Add position sizing (1% risk, compounding) — still deferred, per-share PnL only
6. Wire up the real shortability/MIS check (currently stubbed as always-True)
7. Build automation wrapper (cron on Oracle Cloud VM, EOD report generation) — deploy target
   is the Oracle Cloud VM, not local PC (local is dev/test only)

## Known Issues
- Old baseline sweep scripts (baseline_explorations/) still use monthly Sharpe — not compliant with ZSh(D) standard
- v1_vwap (ma_30_rejection_v1_vwap.py) has no 90-combo sweep done yet
- Both baselines (ma_bounce.py + ma_rejection.py) not yet copied to baseline_reserve/
- Kite paper bot: cron cannot automate the actual Zerodha login (2FA/TOTP) — manual login each
  morning to start (option 1); headless automation (option 2, stored creds + pyotp) to test later
- Kite paper bot: reconciliation gap (48/270 bars, 6/13 trades not matching official) not yet
  root-caused with certainty — hypotheses documented in today.md, need concrete confirmation
- Kite paper bot: EOD-hour tick-based fix applied but not yet live-tested
