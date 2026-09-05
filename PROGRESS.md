# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every RS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. fv2: consolidated Algo_Trading/Framework_V2/strategies/ as the single home for ma_short
   (v0/v1/v2_vwap), 6bce (v0/v1_vwap), ma_long_archived (confirmed non-viable), ma_short_flip_
   archived (ruled out), ma_long_flip/v0 (new). Old scattered locations (baseline_reserve/
   baseline_explorations/Backtesting Extended) kept as-is — cleanup deferred to a later step.
2. Found and fixed a project-wide methodology gap: every family's raw-ZPF-ranked #1 combo was
   sitting at the edge of the swept SL/TP grid and was 68-78% EOD-riding (SL/TP too wide to bind
   intraday), not genuine edge. Added mandatory SL%/TP%/EOD+%/EOD-% exit-mix diagnostic to
   backtesting_rules.md (healthy threshold EOD%<=30) + an out-of-sample-validation guard.
3. CAPM alpha/p-value testing (vs NIFTY50 AND a 30-stock basket, cross-validated) found ALL 8
   shortlisted combos (ma_short v1/v2_vwap, 6bce v0/v1_vwap) show statistically significant
   NEGATIVE alpha (p<0.0001) — a real, consistent negative edge, not noise. Tested and ruled out
   the "flip to LONG" hypothesis this implied (worse on every metric); the mirror hypothesis
   ("SHORT on ma_bounce", ma_long_flip) looked promising raw but landed mid-pack after scrutiny.
4. New SL/TP sweet-spot methodology: hold TP fixed, sweep SL, track ZPF+NetZPnL+Alpha together
   to find the genuine plateau (not just where the grid ends). Locked SL=4.5x/TP=3.0x for 3 of
   5 families (ma_short_v1, ma_short_v2vwap, 6bce_v1vwap) — clean interior peak on all 3 metrics.
   6bce_v0 and ma_long_flip don't plateau at 4.5 — extended 6bce_v0's grid to 10.0, found its
   real plateau at SL~7.5-8.0 but with EOD%=56-57% (open decision for next session).
5. Found a real DS3 data bug (ICICIBANK/ITC/SBIN, 11/11/3 days zero-filled in 2015 — confirmed
   at Zerodha's own source, not a build bug) and a Kite MCP historical_data issue (app-level,
   direct Kite Connect API works fine). CLAUDE.md corrected (DS3 date range, new git-sync-before-
   cross-agent-handoff rule). Full detail: PROGRESS_HISTORY.md 2026-09-03/04 entry.

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Found + fixed a systematic EOD-riding artifact affecting every fv2 strategy family's top-ranked SL/TP combo (2026-09-04) — raw ZPF rankings were inflated by wide-SL/TP combos barely binding intraday, not genuine edge; now a mandatory backtesting_rules.md diagnostic (SL%/TP%/EOD+%/EOD-%)
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), crash-safe position recovery, warmup-boundary duplicate/gap bug fully fixed, and data-loss-on-restart fixed — all tested and confirmed working on real market data (2026-07-23/24)
5. CAPM alpha/p-value testing formally confirmed the live strategy family (MA-short/6BCE) carries a statistically significant NEGATIVE alpha (p<0.0001, both vs NIFTY50 and a 30-stock basket) — not just "no edge," a real and consistent negative one, reframing the raw-edge search (2026-09-04)
