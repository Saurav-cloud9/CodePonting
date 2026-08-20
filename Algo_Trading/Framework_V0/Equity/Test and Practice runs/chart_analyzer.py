import pandas as pd

stock = 'RELIANCE'
data = pd.read_csv(f'{stock}_3months.csv', skiprows=2)
data.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume', 'MA20', 'MA50']
data['Date'] = pd.to_datetime(data['Date'])
data['MA50'] = pd.to_numeric(data['MA50'], errors='coerce')

# Find first non-NaN MA50
first_ma50 = data[data['MA50'].notna()].iloc[0]

print(f"First date with MA50 data: {first_ma50['Date']}")
print(f"MA50 value: {first_ma50['MA50']}")
print(f"\nThis is day number: {data[data['MA50'].notna()].index[0] + 1}")