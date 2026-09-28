# Session Log — 2026-09-16 (fv2 VM session)

## Mostly a long, careful stats Q&A — Saurav verifying #54's mechanics one at a time
Picked up right where last session paused, answering a chain of foundational questions:
ACF1 vs r (confirmed numerically — NIFTY single-day return acf1=-0.025 vs its own 10-day
trend acf1=0.905, same underlying data, proving the trend feature's high self-persistence
is a mechanical overlap artifact, not genuine regime persistence); the circular-shift null
worked through with a 5-day toy example (why iid shuffle destroys zpnl's own structure,
why that understates the true noise ceiling for an autocorrelated feature like dispersion);
N! vs N-1 possible shuffles (iid vs circular); multiple-testing correction via a coin-flip
analogy (why "best of many tries" needs a stricter bar than "one committed test"); weak-
form efficiency's actual scope (directional/first-moment features only — trend — NOT
magnitude/second-moment ones like dispersion, volatility, volume, which is why vol
clustering doesn't contradict market efficiency); theory-first vs. search-then-validate
feature engineering (why grid-searching many transformations of one raw feature and
keeping the best r is a bigger, undisclosed version of the multiple-testing problem,
unless done with proper train/test discipline); the design spec's complexity cap (1-2
threshold conditions max, plain AND only, no fitted regression/logistic combination).

## Two real pieces of work
- **`54c_oos_dispersion_gate.py`** — out-of-sample test of last session's "Q5 dispersion
  gate" finding (Fable's first ZPF>1.0 slice). Chronological 70/30 split, cutoff chosen
  on TRAIN only. RESULT: FAILS decisively. Own-period quintile tables show TRAIN's real
  best bucket is Q4 (1.157) not Q5 (0.994, flat); TEST period has every quintile under
  1.0, Q5 (highest dispersion) is one of the WORST buckets (0.813) — full reversal. This
  specific dispersion-gate lead is ruled out; no `54d` build from it.
- **`54c_10feature_screen.py`** — Saurav caught that the notebook's §3 "combined null"
  (max-of-2) never confirmed only 2 of the 10 built candidates were actually screened.
  Ran the honest 10-feature comparison: `gap_pct` (r=-0.0625) is marginally the single
  strongest of all 10 — bigger than dispersion (0.0573), completely unscreened until now.
  Under a max-of-10 iid null, both still clear 95th not 99th — didn't flip the earlier
  verdict, but hasn't been combined with the circular-shift fix yet.

## Notebook still not updated
`54c_screen.ipynb` was diagnosed, not edited, this session. Precise "RESUME HERE" spec
written into `54_6bceh_short_vwap_rsi_baseline.md` §3 for next session: correct the
notebook (circular-shift primary, max-of-10 scope, honest final verdict), then screen
`gap_pct` and `volume_surge` (definition locked: today's volume ÷ own trailing 20d avg,
basket-averaged, shifted 1 day) with the same rigor before treating either as promising.

## End of session
Saurav confirmed the plan and signed off ("Gn"). RS run: PROGRESS.md, TODO.md,
handoff.md, PROGRESS_HISTORY.md updated; no peer updates folded in (all 4 peer sessions
idle). README flagged stale (8 days since last genuine content change, 2026-09-08) — no
action taken, informational only.
