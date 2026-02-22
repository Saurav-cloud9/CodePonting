# Reorganisation Plan — BackTesting_Realistic_Execution
Generated: 2026-02-20 | **READ-ONLY — No files have been renamed.**

---

## Naming Convention Rules

### Pattern
```
{prefix}_{version}[_{variant}]_{type}.{ext}
```

| Segment | Description | Examples |
|---|---|---|
| `{prefix}` | Broad category of file | `mb` (mega_backtest), `doc` (documentation), `sql` (SQL query dumps), `util` (utilities), `data` (raw data) |
| `{version}` | Version number, dots → underscores | `v1_4`, `v1_4_3`, `v1_4_5` |
| `{variant}` | Optional sub-variant | `opt`, `data`, `fixed`, `fixed1`, `batch`, `tatasteel`, `vedanta` |
| `{type}` | What the file contains | `script`, `db`, `trades`, `monthly`, `consistency`, `results`, `flowchart`, `output` |
| `{ext}` | File extension unchanged | `.py`, `.csv`, `.db`, `.md` |

### Key Rules
1. **Version always uses underscores** — no dots (e.g. `v1_4_3` not `v1.4.3`)
2. **Prefix groups files by category** — alphabetical sort clusters `mb_*`, `doc_*`, `sql_*`, `util_*` together
3. **Version sorts chronologically** — `v1_4` → `v1_4_2` → `v1_4_3` → `v1_4_3_opt` → `v1_4_4` → `v1_4_5` → `v1_4_6`
4. **Variant comes before type** — e.g. `mb_v1_4_5_tatasteel_trades.csv`
5. **File extension is the source-of-truth for type** — `.py`=script, `.db`=database, `.csv`/`.md`=output
6. **`_script` suffix on `.py` files** — makes scripts explicit when sorted alongside `.csv` and `.db` of same version

---

## Rename Mapping

### Python Scripts (.py)

| Current Filename | Proposed Filename |
|---|---|
| `mega_backtest_48M_30S_v1_4.py` | `mb_v1_4_script.py` |
| `mega_backtest_48M_30S_v1_4_FIXED.py` | `mb_v1_4_fixed_script.py` |
| `mega_backtest_48M_30S_v1_4_FIXED_1.py` | `mb_v1_4_fixed1_script.py` |
| `mega_backtest_48M_30S_v1_4_2.py` | `mb_v1_4_2_script.py` |
| `mega_backtest_48M_30S_v1_4_3.py` | `mb_v1_4_3_script.py` |
| `mega_backtest_48M_30S_v1_4_3_DATA.py` | `mb_v1_4_3_data_script.py` |
| `mega_backtest_48M_30S_v1_4_3_Optimized.py` | `mb_v1_4_3_opt_script.py` |
| `mega_backtest_48M_30S_v1_4_4.py` | `mb_v1_4_4_script.py` |
| `mega_backtest_48M_30S_v1_4_5.py` | `mb_v1_4_5_script.py` |
| `mega_backtest_48M_30S_v1_4_5_batch.py` | `mb_v1_4_5_batch_script.py` |
| `mega_backtest_48M_30S_v1_4_5_tatasteel.py` | `mb_v1_4_5_tatasteel_script.py` |
| `mega_backtest_48M_30S_v1_4_5_vedanta.py` | `mb_v1_4_5_vedanta_script.py` |
| `mega_backtest_48M_30S_v1_4_6.py` | `mb_v1_4_6_script.py` |
| `SQL.py` | `util_sql_explorer.py` ⚠️ *see clarifications* |
| `ma_bounce_bot_v1_3_PRODUCTION_2.py` | ⚠️ *see clarifications* |
| `gss_core_option_A_validation.py` | ⚠️ *see clarifications* |

---

### Databases (.db)

| Current Filename | Proposed Filename |
|---|---|
| `backtest_results_v1_4_3.db` | `mb_v1_4_3_db.db` |
| `mega_backtest_48M_30S_v1_4_3_optimized.db` | `mb_v1_4_3_opt_db.db` |
| `mega_backtest_48M_30S_v1_4_4.db` | `mb_v1_4_4_db.db` |
| `mega_backtest_48M_30S_v1_4_5.db` | `mb_v1_4_5_db.db` |
| `mega_backtest_48M_30S_v1_4_5_tatasteel.db` | `mb_v1_4_5_tatasteel_db.db` |
| `mega_backtest_48M_30S_v1_4_5_vedanta.db` | `mb_v1_4_5_vedanta_db.db` |

---

### CSV Outputs (.csv)

| Current Filename | Proposed Filename |
|---|---|
| `backtest_monthly_top10_v1_4_3.csv` | `mb_v1_4_3_monthly_top10.csv` |
| `backtest_stock_consistency_v1_4_3.csv` | `mb_v1_4_3_consistency.csv` |
| `backtest_trades_all_v1_4_3.csv` | `mb_v1_4_3_trades.csv` |
| `mega_backtest_48M_30S_v1_4_3_optimized_consistency.csv` | `mb_v1_4_3_opt_consistency.csv` |
| `mega_backtest_48M_30S_v1_4_3_optimized_monthly.csv` | `mb_v1_4_3_opt_monthly.csv` |
| `mega_backtest_48M_30S_v1_4_3_optimized_trades.csv` | `mb_v1_4_3_opt_trades.csv` |
| `mega_backtest_48M_30S_v1_4_4_consistency.csv` | `mb_v1_4_4_consistency.csv` |
| `mega_backtest_48M_30S_v1_4_4_monthly.csv` | `mb_v1_4_4_monthly.csv` |
| `mega_backtest_48M_30S_v1_4_4_trades.csv` | `mb_v1_4_4_trades.csv` |
| `mega_backtest_48M_30S_v1_4_5_consistency.csv` | `mb_v1_4_5_consistency.csv` |
| `mega_backtest_48M_30S_v1_4_5_monthly.csv` | `mb_v1_4_5_monthly.csv` |
| `mega_backtest_48M_30S_v1_4_5_trades.csv` | `mb_v1_4_5_trades.csv` |
| `mega_backtest_48M_30S_v1_4_5_tatasteel_monthly.csv` | `mb_v1_4_5_tatasteel_monthly.csv` |
| `mega_backtest_48M_30S_v1_4_5_tatasteel_trades.csv` | `mb_v1_4_5_tatasteel_trades.csv` |
| `mega_backtest_48M_30S_v1_4_5_vedanta_monthly.csv` | `mb_v1_4_5_vedanta_monthly.csv` |
| `mega_backtest_48M_30S_v1_4_5_vedanta_trades.csv` | `mb_v1_4_5_vedanta_trades.csv` |
| `v146_30stocks_results.csv` | `mb_v1_4_6_30stocks_results.csv` |
| `v146_all_trades.csv` | `mb_v1_4_6_trades.csv` |
| `_SELECT_month_COUNT_as_total_trades_Exit_reason_breakdown_SUM_CA_202602021303.csv` | `sql_query_20260202_1303.csv` |
| `backtest_v1_4_1_OPTIMIZED_results.csv` | ⚠️ *see clarifications* |
| `v145_30stocks_results.csv` | ⚠️ *see clarifications* |
| `v145_all_trades.csv` | ⚠️ *see clarifications* |

---

### Markdown Docs (.md)

| Current Filename | Proposed Filename |
|---|---|
| `DB_ANALYSIS_GUIDE.md` | `doc_db_analysis_guide.md` |
| `OPTIMIZATION_SUMMARY.md` | `doc_optimization_summary.md` |
| `OPTIMIZATION_SUMMARY_v1_4_2.md` | `doc_optimization_summary_v1_4_2.md` |
| `numpy_vs_pandas_performance.md` | `doc_numpy_vs_pandas_performance.md` |
| `trading_system_flowcharts.md` | `doc_trading_system_flowcharts.md` |
| `mega_backtest_48M_30S_v1_4_FIXED_1_flowchart.md` | `mb_v1_4_fixed1_flowchart.md` |
| `mega_backtest_48M_30S_v1_4_3_DATA_output.md` | `mb_v1_4_3_data_output.md` |
| `_SELECT_month_COUNT_as_total_trades_Exit_reason_breakdown_SUM_CA_202602021300.md` | `sql_query_20260202_1300.md` |
| `_SELECT_month_COUNT_as_total_trades_Exit_reason_breakdown_SUM_CA_202602021304.md` | `sql_query_20260202_1304.md` |
| `_SELECT_stock_atr_config_COUNT_as_trade_count_ROUND_AVG_pnl_2_as_202602021643.md` | `sql_query_20260202_1643.md` |
| `Claude Current SD.md` | ⚠️ *see clarifications* |

---

### Other Files

| Current Filename | Proposed Filename |
|---|---|
| `TATASTEEL.parquet` | `data_tatasteel.parquet` |
| `explore_atr_calculations.ipynb` | `util_explore_atr_calculations.ipynb` |

---

## Files Needing Clarification Before Renaming

| # | File | Question |
|---|---|---|
| 1 | `ma_bounce_bot_v1_3_PRODUCTION_2.py` | This is v1.3 — is it the live production bot or an older reference copy? Suggest `mb_v1_3_production_script.py` if it belongs here, or archive/move if it's from a different system. |
| 2 | `gss_core_option_A_validation.py` | What does `gss` stand for? What version does this validate? No matching script or output exists. Suggest `util_gss_optionA_validation.py` if version-agnostic, or `mb_v{X}_optionA_validation.py` if version-specific. |
| 3 | `SQL.py` | Is this a general utility or tied to a specific version? Suggest `util_sql_explorer.py` if general. |
| 4 | `backtest_v1_4_1_OPTIMIZED_results.csv` | There is no `v1_4_1` script in this folder. Was this output from `v1_4_FIXED` or `v1_4_FIXED_1`? Suggest clarifying the actual source version before renaming. |
| 5 | `v145_30stocks_results.csv` | Is this a duplicate of `mega_backtest_48M_30S_v1_4_5` outputs (different run / config), or the canonical 30-stock summary? If separate run: `mb_v1_4_5_30stocks_results.csv`. If duplicate: consider deleting. |
| 6 | `v145_all_trades.csv` | Same question as above — separate run or duplicate of `mb_v1_4_5_trades.csv`? |
| 7 | `Claude Current SD.md` | What does "SD" stand for (Strategy Developer? System Design?)? What version does this document? Suggest `doc_current_strategy_design.md` or similar once clarified. |

---

## Summary Count

| Category | Files | Rename-Ready | Needs Clarification |
|---|---|---|---|
| Scripts (.py) | 16 | 13 | 3 |
| Databases (.db) | 6 | 6 | 0 |
| CSVs (.csv) | 21 | 18 | 3 |
| Docs (.md) | 11 | 10 | 1 |
| Other (.parquet, .ipynb) | 2 | 2 | 0 |
| **Total** | **56** | **49** | **7** |
