# Weekly Summary — week of 2026-03-15 to 2026-03-21

## Major milestones
- Step 4.3a complete: BQS R1 (9 metrics) validated — M5/M6 best signals but correlated
- Step 4.3b complete: BQS R2 (10 new metrics, M1–M10) validated — no star bucket found
- bqs_export.py fixed: raw_touch_idx + raw_bounce_idx retained in parquet
- remember plugin installed; MCP cc-memory server built and registered in Claude Desktop
- CLAUDE.md updated: mandatory /remember:remember call added to session protocol
- PROGRESS.md restructured with clean step numbering (4.3 → 4.3a → 4.3b → 4.4)

## BQS R2 leaderboard summary
| Metric        | Best lift | Verdict  |
|---------------|-----------|----------|
| M1 MA slope   | +0.8pp w1 | WEAK     |
| M2 RSI-14     | +8.5pp w1 | WEAK (146 trades) |
| M3 Freshness  | +4.7pp w1 | WEAK (anomaly) |
| M4 Vol trend  | 0.0pp     | EXCLUDE  |
| M5 Day pos    | +1.6pp w1 | WEAK     |
| M6 Body ratio | +1.6pp w1 | EXCLUDE  |
| M6.1 Wick/body| +1.4pp w1 | EXCLUDE  |
| M7 Doji type  | +2.0pp w1 | EXCLUDE  |
| M8 Day of week| +1.1pp w1 | EXCLUDE  |
| M9 Vol ratio  | +1.2pp w1 | EXCLUDE  |
| M10 Gap open  | +6.3pp w2 | WEAK (242 trades) |

## Conclusion
No single metric is strong enough as a standalone filter.
Step 4.4 (DT/RF) is the correct next move — find combo effects.
