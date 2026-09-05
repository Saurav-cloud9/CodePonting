# Session Log — 2026-09-03/04 (fv2 VM session)

## Strategies/ folder consolidation

- Built `Algo_Trading/Framework_V2/strategies/` as the single home for MA-short (v0 locked/
  v1/v2_vwap) and 6BCE (v0/v1_vwap), replacing scattered copies across `baseline_reserve/`,
  `baseline_explorations/`, `Backtesting Extended/`. Old locations kept as-is per Saurav's
  explicit "build first, remove later" instruction — cleanup is a separate future step.
- `ma_long` (bounce) renamed to `ma_long_archived/` — confirmed non-viable, no further work
  planned. Same treatment later given to `ma_short_flip` (the "flip to LONG" hypothesis,
  ruled out) → `ma_short_flip_archived/`.
- Renamed `exit_management/`'s baseline→v1 naming to match project convention.

## Found and fixed a real methodology bug: EOD-riding artifact

- Re-ran all 4 main sweeps (ma_short v1/v2_vwap, 6bce v0/v1_vwap) with the refined live-
  matching cutoff (14:45 touch / 14:50 entry cutoff). Found every family's raw-ZPF-ranked #1
  combo sat at the edge of the swept grid (SL/TP=6.0) and was 68-78% EOD-exit — meaning SL/TP
  barely binds intraday at that width, so the "good" ZPF was mostly an artifact of exit-type
  mix, not genuine directional edge.
- Diagnosed the mechanism via a touch-hour breakdown: a touch late in the day (14:00-15:00)
  has almost no runway left before the 15:00 hard EOD, so it resolves via EOD 79% of the time
  regardless of SL/TP width — an entirely structural effect, not a parameter-tuning problem.
- Added a mandatory exit-mix diagnostic (SL%/TP%/EOD+%/EOD-%, healthy threshold EOD%<=30) to
  `backtesting_rules.md`, plus an out-of-sample-validation guard for any time-window-restricted
  variant (protects against the same selection-bias trap discussed earlier this project with
  eta0/monthly-variant cherry-picking).
- Built + ran the instrumented sweeps myself after Grok's free tier ran out (delegation to
  Grok via CCG_ORCHESTRATION.md became unavailable mid-session) — smoke-tested each script on
  a single combo first before committing to the full 90-combo runs, caught one real bug this
  way (`flat_zpf` referenced before definition) before it could waste hours of compute.

## CAPM alpha/p-value testing — confirms a real, significant NEGATIVE edge

- Ran manual OLS alpha/p-value (daily aggregate zpnl vs NIFTY50 daily return, 30 stocks
  pooled) on 8 shortlisted combos (raw #1 + healthy-subset #1, for all 4 families). ALL 8
  came back significantly NEGATIVE (p<0.0001, as low as 1.23e-130) — not noise, a real
  and consistent negative edge. Cross-validated against a second market factor (30-stock
  equal-weighted basket return) with near-identical results.
- This reframed the whole investigation: negative alpha ≠ "flip the direction and profit" —
  tested that hypothesis directly (LONG on ma_short's bearish touch) and it came back worse
  on every metric, ruling it out. The mirror hypothesis (SHORT on ma_bounce's bullish touch,
  `ma_long_flip`) looked promising on 3 raw spot-checks but landed mid-pack once given the
  same exit-mix scrutiny as everything else.
- Along the way, found (and worked around) a genuine DS3 data bug: ICICIBANK, ITC, SBIN have
  entire trading days zero-filled across all OHLC fields (11/11/3 days, April-July 2015).
  Confirmed via direct Kite Connect historical_data fetch that this is Zerodha's own source
  gap, not a DS3 build bug — Yahoo Finance can't help either (intraday data only retains
  ~60 days). Delegation to cpgeneric (cross-session message) expired without Saurav's
  approval before it was delivered — still needs resending or a manual fix.
- Also diagnosed Kite MCP's `get_historical_data` as broken at the app level (generic
  failure even on recent dates, despite `search_instruments`/`login` working fine on the
  same connection) — direct Kite Connect API via the live bot's own cached credentials
  works perfectly and is the right path going forward for any historical fetch need.

## New SL/TP "sweet-spot" methodology

- Built a new diagnostic: hold TP fixed (3.0x), sweep all 10 SL values, track ZPF, NetZPnL,
  and alpha together to find where the numbers *genuinely* plateau (not just where the
  90-combo grid happened to end). Confirmed the mechanism behind it: widening SL shifts
  losing trades from SL-hit into EOD- (not EOD+) via the position-guard's "blocking" effect —
  an EOD-bound trade occupies its stock's slot until 15:00, silently losing any later same-day
  touch signal, while an SL-hit frees the slot for a possible re-entry (directly visible in
  falling trade counts as SL widens).
- Locked SL=4.5x/TP=3.0x for 3 of 5 families (`ma_short_v1`, `ma_short_v2vwap`, `6bce_v1vwap`)
  — clean interior peak on all three metrics simultaneously.
- `6bce_v0` and `ma_long_flip` didn't show that clean peak at SL=4.5 — extended `6bce_v0`'s
  grid to SL=10.0 and found its genuine plateau around SL=7.5-8.0, but at the cost of a much
  higher EOD% (56-57% vs ~47-50% for the others) — open decision for next session.
  `ma_long_flip`'s grid extension is still pending (not done yet).

## Housekeeping

- CLAUDE.md: corrected the stale DS3/NIFTY50 date range (was "2015-2025", actually extends
  live to 2026-08-31) and added a new hard rule (GIT SYNC BEFORE CROSS-AGENT HANDOFF) after
  discovering Grok had been executing a stale, uncommitted version of CCG_ORCHESTRATION.md
  for hours.
- 2 commits pushed today: `0f954a7` (CCG delegation instructions), `4ac0e9f` (the full
  strategies/ consolidation + all findings above).
- RS check-ins sent to cplearning, cpfable, mathmode, cpgeneric at end of session — no
  replies received before this write.

Full technical detail (all numbers, tables, exact combos): `PROGRESS_HISTORY.md`'s
2026-09-03/04 entry. Next-step priorities: `.remember/handoff.md`.
