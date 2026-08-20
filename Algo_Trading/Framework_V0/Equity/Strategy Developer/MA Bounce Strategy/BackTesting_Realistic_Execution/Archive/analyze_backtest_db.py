# Analysis Script for Mega Backtest v1.5 Database
# Use this to query and analyze your backtest results without re-running the entire backtest

import sqlite3
import pandas as pd
import numpy as np

# Connect to database
DB_FILE = 'mega_backtest_v1_5_GSS.db'
conn = sqlite3.connect(DB_FILE)

print(f"Connected to {DB_FILE}")
print("="*70)

# ═══════════════════════════════════════════════════════════════
# EXAMPLE QUERIES - Modify as needed
# ═══════════════════════════════════════════════════════════════

# 1. Best performing stocks overall
print("\n1. TOP 10 BEST PERFORMING STOCKS")
print("-"*70)
query1 = """
SELECT stock, 
       COUNT(*) as total_trades,
       SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
       SUM(pnl) as total_profit,
       AVG(pnl_pct) as avg_return_pct
FROM trades
GROUP BY stock
ORDER BY total_profit DESC
LIMIT 10
"""
df1 = pd.read_sql(query1, conn)
print(df1.to_string(index=False))

# 2. Best filter + ATR configuration combo
print("\n\n2. TOP 10 FILTER + ATR CONFIGURATIONS")
print("-"*70)
query2 = """
SELECT filter, atr_config,
       COUNT(*) as total_trades,
       SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
       SUM(pnl) as total_profit,
       AVG(pnl_pct) as avg_return_pct
FROM trades
GROUP BY filter, atr_config
ORDER BY total_profit DESC
LIMIT 10
"""
df2 = pd.read_sql(query2, conn)
print(df2.to_string(index=False))

# 3. Exit reason analysis
print("\n\n3. EXIT REASON BREAKDOWN")
print("-"*70)
query3 = """
SELECT reason,
       COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM trades), 2) as percentage,
       SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
       AVG(pnl_pct) as avg_return_pct
FROM trades
GROUP BY reason
ORDER BY count DESC
"""
df3 = pd.read_sql(query3, conn)
print(df3.to_string(index=False))

# 4. Time-based analysis (which hours perform best?)
print("\n\n4. HOURLY PERFORMANCE ANALYSIS")
print("-"*70)
query4 = """
SELECT strftime('%H', entry_time) as hour,
       COUNT(*) as trades,
       SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
       AVG(pnl_pct) as avg_return_pct
FROM trades
GROUP BY hour
ORDER BY avg_return_pct DESC
"""
df4 = pd.read_sql(query4, conn)
print(df4.to_string(index=False))

# 5. Monthly performance trend
print("\n\n5. MONTHLY PERFORMANCE TREND")
print("-"*70)
query5 = """
SELECT strftime('%Y-%m', entry_time) as month,
       COUNT(*) as trades,
       SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
       SUM(pnl) as total_profit
FROM trades
GROUP BY month
ORDER BY month
"""
df5 = pd.read_sql(query5, conn)
print(df5.to_string(index=False))

# 6. Best stock for each filter type
print("\n\n6. BEST STOCK FOR EACH FILTER TYPE")
print("-"*70)
query6 = """
WITH RankedStocks AS (
    SELECT filter, stock,
           SUM(pnl) as total_profit,
           COUNT(*) as trades,
           ROW_NUMBER() OVER (PARTITION BY filter ORDER BY SUM(pnl) DESC) as rn
    FROM trades
    GROUP BY filter, stock
)
SELECT filter, stock, total_profit, trades
FROM RankedStocks
WHERE rn = 1
ORDER BY total_profit DESC
"""
df6 = pd.read_sql(query6, conn)
print(df6.to_string(index=False))

# 7. Win rate vs Profit correlation by stock
print("\n\n7. STOCKS WITH HIGHEST WIN RATE (MIN 50 TRADES)")
print("-"*70)
query7 = """
SELECT stock,
       COUNT(*) as total_trades,
       SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
       SUM(pnl) as total_profit
FROM trades
GROUP BY stock
HAVING COUNT(*) >= 50
ORDER BY win_rate DESC
LIMIT 10
"""
df7 = pd.read_sql(query7, conn)
print(df7.to_string(index=False))

# 8. Longest winning/losing streaks (requires window functions)
print("\n\n8. AVERAGE PROFIT/LOSS BY EXIT REASON & FILTER")
print("-"*70)
query8 = """
SELECT filter, reason,
       COUNT(*) as count,
       AVG(pnl) as avg_pnl,
       AVG(pnl_pct) as avg_pnl_pct
FROM trades
GROUP BY filter, reason
ORDER BY filter, avg_pnl DESC
"""
df8 = pd.read_sql(query8, conn)
print(df8.to_string(index=False))

conn.close()

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
print("\nTIP: Modify these queries or add your own!")
print("Database has 2 tables:")
print("  - 'summary': Aggregated results by filter/ATR/stock")
print("  - 'trades': Individual trade details")
print("="*70)
