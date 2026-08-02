# Session Log — 2026-07-31

## MemLabs autoregressive model — built and tested against author's actual technique
- Extracted the MemLabs video author's exact code (via Google AI Studio transcript+frame
  pull) into script 18. Confirmed no Pearson r used anywhere in his implementation, and that
  our earlier PA1/incremental-scaler fixes already matched his real online-learning approach.
- Corrected the analogy we'd been testing: the author's model is genuinely autoregressive
  (x = lag-1 of the SAME series as y), not feature-based. Rebuilt accordingly with
  x = previous trade's PnL, y = current trade's PnL (not ATR%-lag, which would still be
  feature-based, not autoregressive).
- Found a real, if modest, persistent OOS edge over baseline on the Test segment at the
  current live SL/TP (2.0/4.5): Baseline ZPnL -79.18 -> Model-filtered ZPnL -50.41.
- Tested the same model against the SL/TP sweep's "best" combo (6.0/6.0) - the edge nearly
  vanishes (ZPnL -66.60 -> -63.53). Traced the mechanism: wider SL/TP -> longer holding
  (104.1min -> 188.2min, +81%) and wider trade gaps (1448.4min -> 1876.0min, +30%), diluting
  the short-term serial dependence the autoregressive signal likely depends on. Confirms the
  "better" SL/TP combo may be trading away the one edge we'd actually found - a real
  collateral-damage tradeoff, not just noise.

## ATR formula exploration — delegated to Grok, validated, closed out
- User did ATR groundwork research (chatgpt_recommendation.md) proposing Simple vs Wilder,
  10/14/20 periods, and signal-bar vs entry-bar ATR sourcing as cheap, clean experiments.
- Wrote grok_instructions.md specifying all 12 variants (6 formulas x 2 sources), SL/TP
  locked at 2.0/4.5 (current live, explicitly NOT the 6.0/6.0 "best" sweep combo - that combo
  isn't a confirmed destination per the MemLabs finding above), exact ZPF/ZSh(D) output format
  matching the SL/TP sweep doc, explicit output-location instructions after Saurav caught two
  missing-path gaps in the first draft.
- Grok's results (atr_formula_exploration_results.md): sanity check passed exactly (Simple14/
  Signal reproduces precomputed atr14 bit-for-bit, 1.000000 match rate). ZPF spans only
  0.760-0.767 across all 12 variants - the current live formula (Simple14/Signal) is actually
  the BEST of the 12, not worst. Conclusion: ATR formula/period/source is not a lever that
  fixes this strategy's viability.
- Validated a discrepancy Saurav flagged (N=110,641 here vs N=109,282 in the earlier SL/TP
  sweep at the same 2.0/4.5): traced to the reference script (ma_30_rejection_v1.py, correctly
  used per instructions) lacking the sweep script's `hour[entry_idx]>=15` skip. Confirmed via
  exact PF/Sh(D) match (charges-blind metrics identical) that the extra 1,359 trades are all
  zero-raw-pnl EOD-immediate-exits that still eat Zerodha charges - explains the ZPF/ZSh(D)
  gap precisely, not a bug.
- Discussed possibly adding that EOD-entry skip to the reference script; not yet decided.
- Decision (agreed, do tomorrow if time allows): run the full 90-combo SL/TP sweep across all
  6 ATR formula variants via Grok "just for the sake of it," but this is NOT the priority -
  primary focus resumes on the ML/autoregressive thread from where it diverted into ATR work.

## SL/TGT -> SL/TP naming convention — bulk renamed across the project
- Renamed all SL/TGT -> SL/TP (content + filenames) across Framework_V2 (core/, guides/,
  backtesting_rules/, outputs/, scripts/trials/, baseline_reserve/), Framework_V1 + fv1_
  sandbox, Framework_V0, paper_trading_bot_ec2_backup, CLAUDE.md, TODO.md - ~130 files content-
  edited, 32 files/images renamed (all `sl_tgt_*` -> `sl_tp_*`).
- Explicitly excluded (user instruction + standing rules): kite_oracle_papertrading/ (already
  on SL/TP convention independently), .claude/worktrees/* (stale leftover agent copies),
  PROGRESS_HISTORY.md (append-only audit trail rule).
- Caught and reverted one over-eager change mid-run (kite_oracle_papertrading/SESSION_SUMMARY.md
  got touched by the script before the exclusion was added - reverted cleanly via git checkout).
- Audited for accidental corruption before finishing: found a near-miss where an old JWT
  access token in a Framework_V0 file contains mixed-case "TgTQ" that could have been mangled
  by a blind case-sensitive replace - it wasn't touched only because the case pattern didn't
  exactly match any of the 3 replace patterns used (TGT/Tgt/tgt). Ran a full scoped re-grep
  after finishing to confirm zero remaining TGT/Tgt/tgt in the approved scope and no genuine
  secrets/tokens altered.
- TODO.md glossary note about "existing files keep TP, not retroactively renamed" is now
  stale - most existing files WERE retroactively renamed tonight; needs updating.

## Next session priorities (explicitly agreed with the user)
1. PRIMARY: resume the MemLabs ML/autoregressive thread from where it diverted into the ATR
   exploration - multi-stock test is the natural next step (single-stock TATAMOTORS noise
   floor may be too high to see anything real regardless of feature/method).
2. If time allows: run the full 90-combo SL/TP sweep across all 6 ATR formula variants via
   Grok (secondary/nice-to-have, not primary).
3. Separately (Saurav working with VM CC, not this session): validate 31st July's live kite
   bot trades and reconcile the complete 27-31 July weekly results. Known upfront that the
   currently-deployed strategy doesn't hold enough edge to matter financially - framed
   explicitly as process-development practice, not a results-driven exercise.
