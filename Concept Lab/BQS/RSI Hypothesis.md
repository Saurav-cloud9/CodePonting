BQS-R2 M2 — RSI at Touch

Hypothesis:
Oversold RSI (<30) at MA touch = price beaten down + MA support = strong bounce candidate
Neutral RSI (30–60) = no clear bias, ambiguous outcome
Overbought RSI (>60) = shallow pullback in uptrend = uncertain, could go either way
Expected: winners cluster at RSI extremes, losers in neutral zone

Math:
RSI = 100 - (100 / (1 + RS))
RS  = avg gain (14 periods) / avg loss (14 periods)
Computed at touch candle using DS3 raw 5-min closes

DS3 Validation Results (2022–2025, 28,085 trades):

w1 (target hit, baseline 14.8%):
<20     10 trades   20.0%  +5.2pp  (too thin)
20–30  285 trades    9.8%  -5.0pp
30–40  2937 trades  13.3%  -1.5pp
40–50  11434 trades 13.9%  -0.9pp
50–60  11099 trades 15.4%  +0.6pp
60–70  2159 trades  18.7%  +3.9pp
>70    146 trades   23.3%  +8.5pp  (too thin)

w2 (Upstox profitable, baseline 32.5%):
<20     10 trades   50.0%  +17.5pp (too thin)
20–30  285 trades   28.4%  -4.1pp
30–40  2937 trades  33.1%  +0.6pp
40–50  11434 trades 31.5%  -1.0pp
50–60  11099 trades 33.0%  +0.5pp
60–70  2159 trades  35.2%  +2.7pp
>70    146 trades   31.5%  -1.0pp

w3 (Kite profitable, baseline 35.3%):
<20     10 trades   50.0%  +14.7pp (too thin)
20–30  285 trades   30.5%  -4.8pp
30–40  2937 trades  36.1%  +0.8pp
40–50  11434 trades 34.3%  -1.0pp
50–60  11099 trades 35.8%  +0.5pp
60–70  2159 trades  37.4%  +2.1pp
>70    146 trades   32.2%  -3.1pp

Key finding:
Hypothesis REVERSED for w1 — higher RSI = better win rate (opposite of expected)
91% of trades cluster in 40–70 band with only ±1pp difference
Extreme buckets too thin to trust (<20 = 10 trades, >70 = 146 trades)
No star bucket. VERDICT: WEAK — same class as R1 metrics. Parked.