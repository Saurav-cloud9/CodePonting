import pandas as pd

# Read Excel and save as CSV
df = pd.read_excel('RKO_Tracker_1.xlsx')
df.to_csv('RKO_Tracker_1.csv', index=False)
