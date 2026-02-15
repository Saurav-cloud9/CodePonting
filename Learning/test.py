import sqlite3
conn = sqlite3.connect(r"C:\Users\saurav\CodePonting\Algo_Trading\Equity\Strategy Developer\MA Bounce Strategy\BackTesting_Realistic_Execution\mega_backtest_48M_30S_v1_4_5.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", cursor.fetchall())
conn.close()