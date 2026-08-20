# fv2 MA Bounce — Iteration Log

Tracks each refinement step: what changed, trade count, and PF result.
Break-even target: PF > 1.01

---

## LONG Iterations

| # | Label | Change from previous | N | PF | Note |
|---|---|---|---|---|---|
| 1 | Baseline (v0) | — | 49,039 | 0.922 | All 5 touch types. Reference point. |
| 2 | v1 (wick-only) | Touch condition: `close > MA20` required | 39,589 | 0.908 | Removes 9,450 trades. PF drops slightly but VWAP split becomes clean (0.090 gap). |
| 3 | v1 + VWAP filter | Keep only above-VWAP touches | 20,474 | 0.949 | Cleanest group so far. Gap to break-even: ~0.06 PF points. |
| 4 | v1 + Below EMA (no VWAP) | EMA50–250 standalone on v1 | — | — | Below EMA consistently better than above across all lengths (PF 0.932–0.958). None cross 1.0 alone. Detail in EMA sweep table. |
| 5 | **v1.1** (v1 + Above VWAP + Below EMA100) | Built on #3 — add below EMA100 filter | 8,377 | 1.010 | Top combo: EMA100 wins. NPF=0.588 (Kotak Neo full charges). Detail in sweep table below. |
| 6 | **v1.2** (v1.1 + MACD state filter) | MACD vs Signal at touch bar (4 states A/B/C/D) | 8,377 | 1.010 | Dead end — no new version. State A=1.059, C=1.149 but C has N=538 (too thin). VWAP+EMA100 doing the work, not MACD state. Detail in sweep section below. |
| 7 | **ABC standalone** (long + short) | Trading ABC indicator — ZigZag + Fibonacci 38.2-61.8% + trend cloud + MA bounce | — | — | Dead end. Long best CBQ: SL=0.3 TP=1.5 (PF=1.039) → NPF=0.547 at qty=1000, never crosses 1.0. Short best CBQ: SL=0.3 TP=0.7 (PF=1.403, Sharpe=2.700) → NPF=0.646 at qty=1000, never crosses 1.0. Signal quality real, trade economics broken — 5-min ATR exits too small to overcome statutory charges at any scale. |
| 8 | **v1.1 CBQ** (best SL/TP sweep) | SL×TP grid on v1.1 signals — find best combo then run CBQ | 8,271 | 1.032 | Best combo: SL=2.5x TP=6.0x. CBQ: NPF=0.608 at qty=1, asymptotes at 0.893 at qty=1000 — never crosses 1.0. Default SL=2.5 TP=4.5 (N=8,304, PF=1.026) NPF=0.886 at qty=1000 — marginal difference. Raw edge PF=1.032 too thin to overcome charges at any scale. |

---

## SHORT Iterations

| # | Label | Change from previous | N | PF | Note |
|---|---|---|---|---|---|
| 1 | **v2** (Bare SHORT baseline) | Mirror of v0 — touch: high≥MA20, search MAX_TB_GAP=3 for close<MA20, entry SHORT next bar. SL=2.5x TP=4.5x | — | — | Pending run. |
| 2 | **v3** (SHORT wick-only) | Mirror of v1 — single bar: high≥MA20, open<MA20, close<MA20. SL=2.0x TP=3.5x | 42,612 | 1.076 | Best combo: SL=2.0x TP=3.5x, Sharpe=0.833. All 4 years profitable (2023=0.999). Stronger raw edge than LONG v1 (0.908) at the same structural level. CBQ: NPF=0.559@qty=1, asymptotes 0.898@qty=1000. |

---

## EMA Sweep — Below EMA (standalone) on v1 — iteration #4

| EMA | Below EMA | N | Above EMA | N |
|---|---|---|---|---|
| EMA50 | 0.932 | 16,309 | 0.894 | 23,280 |
| EMA100 | 0.951 | 17,642 | 0.877 | 21,947 |
| EMA150 | 0.942 | 17,811 | 0.883 | 21,778 |
| EMA200 | 0.952 | 17,762 | 0.875 | 21,827 |
| EMA250 | **0.958** | 17,713 | 0.870 | 21,876 |

None cross 1.0 alone. Below EMA consistently better than above across all lengths.

---

## EMA Sweep — v1 + Above VWAP + Below EMA — iteration #5 (filter-at-entry, realistic)

| EMA | PF | N | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| EMA50 | 1.003 | 6,420 | 1.040 | 0.966 | 1.100 | 0.907 |
| **EMA100** | **1.010** | **8,377** | 1.018 | 0.985 | 1.084 | 0.947 |
| EMA250 | 0.997 | 9,619 | 1.030 | 0.964 | 1.013 | 0.975 |

EMA100 wins on overall PF. Pattern: 2022 + 2024 consistently above 1.0, 2023 + 2025 below — regime effect, not filter weakness.

---

## Gap to break-even

| Iteration | PF | N | Gap to 1.01 |
|---|---|---|---|
| Baseline | 0.922 | 49,039 | -0.088 |
| v1 | 0.908 | 39,589 | -0.102 |
| v1 + Above VWAP | 0.949 | 20,474 | -0.061 |
| v1 + Above VWAP + Below EMA100 | 1.010 | 8,377 | +0.000 |

---

## Iteration #6 — MACD State Sweep (v1.1, baseline, v1)

| State | Baseline N | Baseline PF | v1 N | v1 PF | v2 N | v2 PF |
|---|---|---|---|---|---|---|
| A (MACD>Sig, >0) | 7,943 | 0.887 | 8,790 | 0.876 | 2,209 | 1.059 |
| B (MACD>Sig, <0) | 5,612 | 0.901 | 18,246 | 0.921 | 5,484 | 1.002 |
| C (MACD<Sig, >0) | 18,220 | 0.933 | 11,566 | 0.930 | 538 | 1.149 |
| D (MACD<Sig, <0) | 32,995 | 0.940 | 987 | 0.804 | 146 | 0.600 |
| **ALL** | 64,770 | 0.927 | 39,589 | 0.908 | 8,377 | 1.010 |

**Verdict: Dead end.** MACD state adds zero edge at baseline or v1 level — all states sub-1.0, narrow spread. On v2, State A (1.059) and C (1.149) look better but C has N=538 (too thin). The VWAP + EMA100 filters are doing the work, not MACD state. No v3 from this path.

## Candidates for next SHORT iteration (v3 build)

- v3: Structural change on v2 — TBD (equivalent of v1→v1.1 path for the SHORT side)
- v3.1: v3 + filters (VWAP, EMA — mirror of v1.1)
- RSI standalone signal (parked)
- Regime filter (parked)
