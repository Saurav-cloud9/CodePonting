# v2_vwap — Above vs Below VWAP decision (2026-09-04)

Compared v1 clean-touch + VWAP context filter, both sides, live-matching cutoff
(14:45 touch / 14:50 entry), 3 SL/TP combos, full 11yr DS3, 30 stocks.

| SL  | TP  | Side  | N      | PF    | ZPF   | Sh(D) | ZSh(D) |
|-----|-----|-------|--------|-------|-------|-------|--------|
| 2.5 | 4.0 | BELOW | 81,241 | 1.138 | 0.789 | 1.845 | -3.491 |
| 2.5 | 4.0 | ABOVE | 49,197 | 1.049 | 0.711 | 0.593 | -4.074 |
| 2.0 | 4.5 | BELOW | 83,531 | 1.149 | 0.782 | 1.992 | -3.688 |
| 2.0 | 4.5 | ABOVE | 51,365 | 1.065 | 0.706 | 0.783 | -4.205 |
| 6.0 | 6.0 | BELOW | 68,567 | 1.133 | 0.831 | 1.351 | -2.024 |
| 6.0 | 6.0 | ABOVE | 42,884 | 1.024 | 0.732 | 0.230 | -2.953 |

**Decision: BELOW VWAP locked as the v2_vwap entry signal.** Wins on every metric
(PF, ZPF, Sh(D), ZSh(D)) at every combo tested — not a close call. Signal is now:
v1 touch (`high>=MA20, open<MA20, close<MA20`) AND `close[i] < VWAP[i]`, entered
next bar open, same live-matching cutoff as v1. Full 90-combo sweep in
`sweep_v2_vwap.py` / `sweep_v2_vwap_results.md`.
