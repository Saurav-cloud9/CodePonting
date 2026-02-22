import pandas as pd
df = pd.read_csv(r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V0\Equity\Strategy Developer\MA Bounce Strategy\BackTesting_Realistic_Execution\mega_backtest_48M_30S_v1_4_5_trades.csv')
summary = df[df['filter']=='No Filter'].groupby(['stock','atr_config'])['pnl'].sum().reset_index()
print(summary.sort_values('pnl', ascending=False).to_string())
