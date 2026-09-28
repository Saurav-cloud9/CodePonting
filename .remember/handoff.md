# Handoff Note — 2026-09-16 (fv2 VM session)

## Current State — memlabs #54: dispersion lead RULED OUT, notebook needs a correction pass

Since the last handoff (2026-09-13), the session was almost entirely a long, meticulous
Q&A walkthrough of `#54`'s statistics (r, ACF1, null-calibration, multiple-testing) —
Saurav verifying every mechanic before allowing more action items. Two real pieces of
work got done along the way:

1. **`54c_oos_dispersion_gate.py`** (new) — out-of-sample test of Fable's "Q5 dispersion
   gate" finding from last session (chronological 70/30 split, cutoff chosen on TRAIN
   only, 2015-02-04—2023-04-11 vs 2023-04-12—2026-08-31). RESULT: FAILS. Own-period
   quintile tables show TRAIN's real best bucket is Q4 (ZPF 1.157), not Q5 (0.994, flat);
   TEST period has every quintile under 1.0, with Q5 (highest dispersion) one of the
   WORST buckets (0.813) — a full reversal. Dispersion's one concrete deployable form is
   ruled out — no `54d` build off this pair.
2. **`54c_10feature_screen.py`** (new) — full 10-candidate r-vs-daily_zpnl comparison,
   prompted by Saurav catching that the notebook's §3 "combined null" only ever
   corrected for 2 of the 10 built candidates (never confirmed that was the true count of
   "looks" taken). Surprise: `gap_pct` (r=-0.0625) edges out dispersion (0.0573) as the
   single strongest of all 10 — previously unscreened, no theory check done yet. Under
   max-of-10 iid null (ceil95=0.0555, ceil99=0.0676) both still clear 95th, not 99th —
   the under-correction concern didn't flip the verdict, but hasn't been combined with
   the circular-shift fix yet (stricter still).

`54c_screen.ipynb` itself was **NOT edited this session** — only diagnosed. Full resume
spec written into `54_6bceh_short_vwap_rsi_baseline.md` §3, under "RESUME HERE".

## Next (in order, from the baseline doc's "RESUME HERE")

1. Edit `54c_screen.ipynb`: make circular-shift the primary null (§2/§3, keep iid as
   secondary reference); widen §3 from max-of-2 to max-of-10 (don't delete the section —
   the concept is correct, only the scope was wrong); rewrite §6's verdict to the final
   combined read — dispersion borderline-real by r (clears 95th under both fixes, never
   99th) but its deployable form (Q5 gate) failed OOS — net verdict RULED OUT.
2. Screen `gap_pct` properly: its own null-calibration (iid + circular-shift), a theory
   check (does an overnight gap have a plausible mechanism, or is it closer to trend —
   dead on weak-form efficiency — than to dispersion?), then an OOS gate test if it
   survives both, before any enthusiasm.
3. Build `volume_surge` (definition locked, not yet built): today's volume ÷ that
   stock's own trailing 20-day average, basket-averaged across 30 stocks, shifted 1 day.
4. `54c.4` interaction/XOR check (trend x dispersion) — still worth running once for the
   learning-value confirmation, low priority given trend is already dead two ways over
   (fails every r/null test; weak-form efficiency argues against it having any
   information at all, linear or not).

## Context

Saurav is meticulously verifying every #54 stats mechanic before allowing more action
items — this session was ~90% Q&A (ACF1 vs r, multiple-testing/coin-flip analogy, weak-
form efficiency scope, XOR/interaction theory, theory-first vs. search-then-validate
feature engineering) and ~10% new computation. Expect the same pace next session —
don't rush past a concept check to get to code. `cpfable` (codeponting-35) is Saurav's
own separate quant-finance consultation thread, not something to act on unprompted.
README hasn't had a genuine content update in 8 days (last: 2026-09-08) — flagged, no
action taken.
