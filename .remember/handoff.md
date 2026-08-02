# Handoff Note — 2026-07-31

## Current State — MemLabs ML thread (PRIMARY focus going forward)
- Built and validated a genuinely autoregressive model (x=previous trade's PnL, y=current
  trade's PnL - not feature-based) matching the MemLabs author's actual technique (extracted
  from his real code via script 18). Found a real, if modest, OOS edge over baseline at the
  current live SL/TP (2.0/4.5): Baseline ZPnL -79.18 -> Model-filtered -50.41.
- Critical finding: this edge nearly vanishes at the SL/TP sweep's "best" combo (6.0/6.0):
  ZPnL -66.60 -> -63.53, almost no improvement. Wider SL/TP dilutes trade frequency/adjacency
  (holding +81%, gaps +30%), which the autoregressive signal likely depends on. This is a
  genuine collateral-damage tradeoff between "best backtest ZPF" and "best ML-filterable
  edge" - worth keeping in mind for any future SL/TP decision.
- Diverted from here into ATR formula exploration (now closed out, see below) - this is
  exactly where to resume.

## Current State — ATR formula exploration (CLOSED OUT, informed the ML resume)
- Delegated 12 variants (Simple/Wilder x 10/14/20 x Signal/Entry source) to Grok, SL/TP
  locked at 2.0/4.5. Results validated: ZPF spans only 0.760-0.767, current live formula
  (Simple14/Signal) is already the BEST of the 12. ATR formula/period/source is not a lever
  that fixes strategy viability - confirms the earlier SL/TP sweep's negative verdict wasn't
  an ATR-calc artifact.
- Full file: Algo_Trading/Framework_V2/scripts/trials/ATR_exploration/
  atr_formula_exploration_results.md
- Explained (not a bug) why N differs from the earlier SL/TP sweep at the same 2.0/4.5:
  reference script ma_30_rejection_v1.py lacks the sweep script's `hour[entry_idx]>=15` skip,
  creating ~1,359 zero-raw-pnl EOD-immediate-exit trades that still eat charges. Undecided
  whether to add that skip to the reference script - revisit if it matters for future work.
- Agreed (do tomorrow ONLY if time allows, not priority): run the full 90-combo SL/TP sweep
  across all 6 ATR variants via Grok "for the sake of it."

## Current State — SL/TGT -> SL/TP rename (DONE)
- ~130 files content-edited + 32 renamed across Framework_V2/V1/V0, baseline_reserve,
  paper_trading_bot_ec2_backup, CLAUDE.md, TODO.md. Excluded kite_oracle_papertrading/
  (already independently on SL/TP), .claude/worktrees/*, PROGRESS_HISTORY.md.
- One file (kite_oracle_papertrading/SESSION_SUMMARY.md) was touched before the exclusion
  was added mid-run - caught and reverted cleanly.
- Full corruption audit done post-run (checked for accidentally-mangled tokens/hashes) -
  clean. TODO.md's glossary note claiming "existing files not retroactively renamed" is now
  STALE and needs a correction (see Known Issues).

## Current State — Kite paper trading bot (Algo_Trading/kite_oracle_papertrading/)
- No changes this session (deliberately out of scope for the SL/TP rename per Saurav's
  explicit instruction - it's already on the SL/TP convention independently).
- Saurav is separately validating 31st July's live trades + the full 27-31 July weekly recon
  with VM CC (not this session). Explicitly framed as process-development practice, not
  expected to show real edge given the known viability gap.

## Next Step (START HERE) - explicitly agreed with the user

### Primary (this session/thread)
1. Resume MemLabs ML/autoregressive work from where it diverted - multi-stock test is next
   (single-stock TATAMOTORS noise floor may be too high to see anything real regardless of
   feature/method, same open question as before the ATR detour).
2. If genuinely spare time: full 90-combo SL/TP sweep x 6 ATR variants via Grok (secondary).

### Separate (Saurav + VM CC, kite bot thread)
1. Validate 31st July live trades
2. Reconcile complete 27-31 July weekly results

## Known Issues
- TODO.md glossary line (SL/TP entry) says "existing files keep TP, not retroactively
  renamed" - now FALSE after tonight's rename pass. Needs a one-line correction next session.
- Undecided: whether to add the `hour[entry_idx]>=15` entry-skip to ma_30_rejection_v1.py to
  align it with the sweep script's cleaner convention (doesn't change any conclusions reached
  so far, purely a hygiene question).
- MemLabs: multi-stock test for the autoregressive model not yet run - single-stock TATAMOTORS
  result (real but modest edge, vanishes at wider SL/TP) needs that check before trusting it
  further, per the standing multi-stock-noise-floor concern from the earlier correlation work.
