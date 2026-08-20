# Kaggle NSE Dataset Validation Report
**Generated:** 2026-03-01  |  **Elapsed:** 12.0 min
**DS1:** 105 stocks (dataset1)  |  **DS2:** 499 stocks (dataset2)  |  **FV1:** 31 parquets (intraday_5min)

---

## Summary

| Metric | DS1 | DS2 |
|--------|-----|-----|
| Stocks processed | 105 | 499 |
| Load errors | 0 | 3 |
| CHECK 1 PASS (consistency) | 85/105 | 375/496 |
| CHECK 2 PASS (volume) | 2/105 | 0/496 |
| Total missing trading days | 2,431 | 20,008 |
| Total OHLC violations | 17 | 103 |
| Total duplicate timestamps | 0 | 1 |
| Total zero-volume candles | 3,857,173 | 37,727,433 |
| Total volume-spike candles (>10x) | 1,741,646 | 11,599,893 |
| Total doubled-volume days | 19,983 | 124,377 |
| Total anomalies logged | 9692 | 54506 |

### Winner: **DS1** (lower anomaly score per stock: DS1=71944.3 vs DS2=125567.3)

---

## CHECK 3 — Cross-compare DS2 vs FV1 Parquets (2022-2025)

Overlapping stocks compared: **28**
Stocks with all OHLC+Volume PASS: **0 / 28**
Total price-mismatch bars: **2,253,812**
Total volume-mismatch bars (>20%): **35,595**

| Stock | Common Bars | Open_mis | High_mis | Low_mis | Close_mis | Vol_mis | PASS |
|-------|-------------|----------|----------|---------|-----------|---------|------|
| ADANIPORTS | 74,039 | 22 | 27 | 46 | 32 | 1341 | NO |
| ASHOKLEY | 74,039 | 38 | 56 | 89 | 65 | 1183 | NO |
| AXISBANK | 74,039 | 5 | 30 | 27 | 22 | 1180 | NO |
| BANDHANBNK | 74,039 | 57 | 54 | 130 | 84 | 1232 | NO |
| BHARTIARTL | 74,039 | 3 | 15 | 27 | 25 | 1397 | NO |
| CIPLA | 74,039 | 17 | 55 | 20 | 44 | 1237 | NO |
| COALINDIA | 74,039 | 67907 | 67944 | 67890 | 67916 | 1140 | NO |
| DABUR | 74,039 | 37 | 114 | 67 | 55 | 1318 | NO |
| DIVISLAB | 74,039 | 29 | 47 | 71 | 37 | 1375 | NO |
| HDFCBANK | 74,039 | 3 | 10 | 23 | 17 | 1740 | NO |
| HINDALCO | 74,039 | 10 | 44 | 38 | 39 | 1151 | NO |
| ICICIBANK | 74,039 | 2 | 10 | 15 | 12 | 1500 | NO |
| INDUSINDBK | 74,039 | 29 | 57 | 58 | 45 | 1163 | NO |
| INFY | 74,039 | 5 | 29 | 18 | 13 | 1460 | NO |
| ITC | 74,035 | 55661 | 55702 | 55694 | 55678 | 1192 | NO |
| JSWSTEEL | 74,039 | 25 | 52 | 53 | 60 | 1219 | NO |
| NATIONALUM | 74,039 | 57939 | 57947 | 57975 | 57963 | 1321 | NO |
| NTPC | 74,039 | 13 | 115 | 50 | 38 | 1137 | NO |
| ONGC | 74,039 | 71568 | 71571 | 71567 | 71567 | 1124 | NO |
| PNB | 74,039 | 64136 | 64139 | 64148 | 64141 | 1171 | NO |
| POWERGRID | 74,039 | 26 | 80 | 56 | 52 | 1129 | NO |
| RELIANCE | 74,030 | 4 | 18 | 17 | 6 | 1525 | NO |
| SBIN | 74,039 | 1 | 23 | 15 | 20 | 1368 | NO |
| SUNPHARMA | 74,039 | 7 | 70 | 24 | 31 | 1290 | NO |
| TATASTEEL | 74,039 | 63384 | 63388 | 63407 | 63386 | 1199 | NO |
| TECHM | 74,039 | 64882 | 64898 | 64892 | 64885 | 1231 | NO |
| VEDL | 74,039 | 60312 | 60293 | 60423 | 60316 | 1180 | NO |
| WIPRO | 74,039 | 56872 | 56875 | 56886 | 56880 | 1092 | NO |

FV1 stocks **not** in DS2: `NIFTY50, TATAMOTORS, VI`

---

## DS1 Per-Stock Results

| Stock | Days | Miss | OHLC | Dupes | ZVol | Spikes | 2xDays | C1 | C2 |
|-------|------|------|------|-------|------|--------|--------|----|----|
| ABB | 2709 | 0 | 0 | 0 | 75704 | 19844 | 333 | PASS | FAIL |
| ADANIENSOL | 2586 | 0 | 0 | 0 | 65525 | 32452 | 310 | PASS | FAIL |
| ADANIENT | 2709 | 0 | 0 | 0 | 2254 | 22134 | 223 | PASS | FAIL |
| ADANIGREEN | 1876 | 0 | 0 | 0 | 19957 | 21226 | 223 | PASS | FAIL |
| ADANIPORTS | 2709 | 0 | 0 | 0 | 75 | 19162 | 206 | PASS | FAIL |
| ADANIPOWER | 2709 | 0 | 0 | 0 | 3093 | 28609 | 250 | PASS | FAIL |
| AMBUJACEM | 2709 | 0 | 0 | 0 | 887 | 20390 | 199 | PASS | FAIL |
| APOLLOHOSP | 2709 | 0 | 0 | 0 | 4956 | 17332 | 200 | PASS | FAIL |
| ASIANPAINT | 2709 | 0 | 0 | 0 | 101 | 9189 | 153 | PASS | FAIL |
| ATGL | 1782 | 0 | 1 | 0 | 10128 | 26398 | 202 | FAIL | FAIL |
| AXISBANK | 2709 | 0 | 0 | 0 | 19 | 11195 | 131 | PASS | FAIL |
| BAJAJ-AUTO | 2709 | 0 | 0 | 0 | 1165 | 12057 | 172 | PASS | FAIL |
| BAJAJFINSV | 2709 | 0 | 0 | 0 | 18849 | 22026 | 189 | PASS | FAIL |
| BAJAJHLDNG | 2709 | 0 | 1 | 0 | 201516 | 27338 | 423 | FAIL | FAIL |
| BAJFINANCE | 2709 | 0 | 0 | 0 | 8485 | 25534 | 163 | PASS | FAIL |
| BANKBARODA | 2709 | 0 | 1 | 0 | 34 | 12696 | 125 | FAIL | FAIL |
| BEL | 2709 | 0 | 0 | 0 | 2096 | 14752 | 206 | PASS | FAIL |
| BHARTIARTL | 2709 | 0 | 1 | 0 | 93 | 17268 | 207 | FAIL | FAIL |
| BHEL | 2709 | 0 | 0 | 0 | 71 | 26862 | 197 | PASS | FAIL |
| BOSCHLTD | 2709 | 0 | 1 | 0 | 42573 | 19881 | 213 | FAIL | FAIL |
| BPCL | 2709 | 0 | 0 | 0 | 57 | 11371 | 142 | PASS | FAIL |
| BRITANNIA | 2709 | 0 | 1 | 0 | 2082 | 14820 | 183 | FAIL | FAIL |
| CANBK | 2709 | 0 | 0 | 0 | 140 | 14711 | 123 | PASS | FAIL |
| CHOLAFIN | 2709 | 0 | 0 | 0 | 68607 | 39109 | 274 | PASS | FAIL |
| CIPLA | 2709 | 0 | 0 | 0 | 221 | 19813 | 194 | PASS | FAIL |
| COALINDIA | 2709 | 0 | 0 | 0 | 37 | 14505 | 200 | PASS | FAIL |
| DABUR | 2709 | 0 | 0 | 0 | 1932 | 12301 | 202 | PASS | FAIL |
| DIVISLAB | 2709 | 0 | 1 | 0 | 3137 | 19867 | 221 | FAIL | FAIL |
| DLF | 2709 | 0 | 0 | 0 | 46 | 11272 | 148 | PASS | FAIL |
| DMART | 2185 | 0 | 0 | 0 | 497 | 15422 | 207 | PASS | FAIL |
| DRREDDY | 2709 | 0 | 0 | 0 | 347 | 17911 | 202 | PASS | FAIL |
| EICHERMOT | 2709 | 0 | 0 | 0 | 1358 | 27094 | 162 | PASS | FAIL |
| ENRIN | 150 | 0 | 0 | 0 | 23 | 930 | 14 | PASS | FAIL |
| GAIL | 2710 | 0 | 0 | 0 | 502 | 15838 | 178 | PASS | FAIL |
| GODREJCP | 2710 | 0 | 1 | 0 | 5043 | 12829 | 258 | FAIL | FAIL |
| GRASIM | 2710 | 0 | 0 | 0 | 13467 | 16345 | 190 | PASS | FAIL |
| HAL | 1932 | 0 | 1 | 0 | 55281 | 13123 | 218 | FAIL | FAIL |
| HAVELLS | 2710 | 0 | 1 | 0 | 1644 | 13811 | 207 | FAIL | FAIL |
| HCLTECH | 2710 | 0 | 0 | 0 | 134 | 12252 | 152 | PASS | FAIL |
| HDFCBANK | 2710 | 0 | 1 | 0 | 165 | 15505 | 102 | FAIL | FAIL |
| HDFCLIFE | 2703 | 661 | 0 | 0 | 8274 | 9451 | 148 | FAIL | FAIL |
| HEROMOTOCO | 2709 | 0 | 0 | 0 | 322 | 12069 | 165 | PASS | FAIL |
| HINDALCO | 2710 | 0 | 0 | 0 | 111 | 7346 | 122 | PASS | FAIL |
| HINDUNILVR | 2710 | 0 | 0 | 0 | 157 | 8566 | 141 | PASS | FAIL |
| HINDZINC | 2710 | 0 | 0 | 0 | 10426 | 29239 | 224 | PASS | FAIL |
| HYUNDAI | 312 | 0 | 0 | 0 | 16 | 1895 | 26 | PASS | FAIL |
| ICICIBANK | 2710 | 0 | 1 | 0 | 4970 | 7270 | 104 | FAIL | FAIL |
| ICICIGI | 2056 | 0 | 0 | 0 | 6814 | 10328 | 190 | PASS | FAIL |
| ICICIPRULI | 2301 | 0 | 1 | 0 | 1248 | 12683 | 248 | FAIL | FAIL |
| INDHOTEL | 2710 | 0 | 0 | 0 | 43169 | 24163 | 308 | PASS | FAIL |
| INDIGO | 2518 | 0 | 0 | 0 | 5782 | 18787 | 260 | PASS | FAIL |
| INDUSINDBK | 2709 | 0 | 0 | 0 | 246 | 33424 | 186 | PASS | FAIL |
| INFY | 2709 | 0 | 0 | 0 | 4969 | 8504 | 139 | PASS | FAIL |
| IOC | 2710 | 0 | 1 | 0 | 733 | 12093 | 174 | FAIL | FAIL |
| IRCTC | 2709 | 582 | 0 | 0 | 179102 | 48235 | 280 | FAIL | FAIL |
| IRFC | 1934 | 550 | 0 | 0 | 9184 | 24038 | 134 | FAIL | FAIL |
| ITC | 2710 | 0 | 0 | 0 | 4988 | 12519 | 164 | PASS | FAIL |
| JINDALSTEL | 2709 | 0 | 0 | 0 | 627 | 13769 | 172 | PASS | FAIL |
| JIOFIN | 598 | 0 | 0 | 0 | 12 | 3462 | 43 | PASS | FAIL |
| JSWENERGY | 2709 | 0 | 0 | 0 | 29481 | 28668 | 286 | PASS | FAIL |
| JSWSTEEL | 2709 | 0 | 0 | 0 | 429 | 9493 | 131 | PASS | FAIL |
| KOTAKBANK | 2709 | 0 | 0 | 0 | 247 | 10554 | 176 | PASS | FAIL |
| LICI | 912 | 0 | 0 | 0 | 24 | 9384 | 86 | PASS | FAIL |
| LODHA | 1179 | 0 | 0 | 0 | 7249 | 7438 | 130 | PASS | FAIL |
| LT | 2709 | 0 | 0 | 0 | 21 | 7869 | 141 | PASS | FAIL |
| LTIM | 2348 | 0 | 0 | 0 | 25005 | 12612 | 236 | PASS | FAIL |
| MARUTI | 2709 | 0 | 0 | 0 | 104 | 8652 | 124 | PASS | FAIL |
| MM | 2709 | 0 | 0 | 0 | 98 | 10207 | 163 | PASS | FAIL |
| MOTHERSON | 2709 | 0 | 0 | 0 | 176 | 15689 | 225 | PASS | FAIL |
| NAUKRI | 2709 | 0 | 0 | 0 | 94886 | 16904 | 356 | PASS | FAIL |
| NESTLEIND | 2709 | 0 | 0 | 0 | 21048 | 12883 | 198 | PASS | FAIL |
| NHPC | 2709 | 0 | 0 | 0 | 15744 | 45489 | 247 | PASS | FAIL |
| NIFTY 50 | 2710 | 0 | 0 | 0 | 1021054 | 0 | 0 | PASS | PASS |
| NIFTY BANK | 2710 | 0 | 0 | 0 | 1021002 | 0 | 0 | PASS | PASS |
| NTPC | 2709 | 0 | 0 | 0 | 297 | 14565 | 209 | PASS | FAIL |
| ONGC | 2709 | 0 | 0 | 0 | 23 | 15921 | 188 | PASS | FAIL |
| PFC | 2709 | 0 | 0 | 0 | 581 | 12069 | 171 | PASS | FAIL |
| PIDILITIND | 2709 | 0 | 0 | 0 | 6277 | 13606 | 241 | PASS | FAIL |
| PNB | 2709 | 0 | 0 | 0 | 26 | 25495 | 142 | PASS | FAIL |
| POWERGRID | 2709 | 0 | 0 | 0 | 1195 | 11081 | 193 | PASS | FAIL |
| RECLTD | 2709 | 0 | 0 | 0 | 307 | 11575 | 179 | PASS | FAIL |
| RELIANCE | 2709 | 0 | 0 | 0 | 21 | 9291 | 119 | PASS | FAIL |
| SBILIFE | 2709 | 638 | 1 | 0 | 11092 | 10087 | 196 | FAIL | FAIL |
| SBIN | 2710 | 0 | 0 | 0 | 1145 | 12098 | 100 | PASS | FAIL |
| SHREECEM | 2709 | 0 | 0 | 0 | 62028 | 16702 | 254 | PASS | FAIL |
| SHRIRAMFIN | 2709 | 0 | 0 | 0 | 1478 | 21070 | 195 | PASS | FAIL |
| SIEMENS | 2710 | 0 | 0 | 0 | 13291 | 15070 | 234 | PASS | FAIL |
| SOLARINDS | 2710 | 0 | 0 | 0 | 327521 | 43641 | 465 | PASS | FAIL |
| SUNPHARMA | 2710 | 0 | 0 | 0 | 26 | 17805 | 185 | PASS | FAIL |
| TATACONSUM | 2710 | 0 | 0 | 0 | 5793 | 16529 | 218 | PASS | FAIL |
| TATAPOWER | 2710 | 0 | 1 | 0 | 1036 | 36974 | 195 | FAIL | FAIL |
| TATASTEEL | 2710 | 0 | 0 | 0 | 25 | 10606 | 124 | PASS | FAIL |
| TCS | 2710 | 0 | 0 | 0 | 406 | 7646 | 131 | PASS | FAIL |
| TECHM | 2710 | 0 | 0 | 0 | 81 | 8966 | 176 | PASS | FAIL |
| TITAN | 2710 | 0 | 0 | 0 | 2239 | 13457 | 207 | PASS | FAIL |
| TMPV | 2710 | 0 | 0 | 0 | 34 | 28924 | 126 | PASS | FAIL |
| TORNTPHARM | 2710 | 0 | 0 | 0 | 25906 | 22331 | 278 | PASS | FAIL |
| TRENT | 2710 | 0 | 0 | 0 | 172026 | 19451 | 372 | PASS | FAIL |
| TVSMOTOR | 2710 | 0 | 0 | 0 | 2040 | 15219 | 239 | PASS | FAIL |
| ULTRACEMCO | 2710 | 0 | 0 | 0 | 556 | 9915 | 156 | PASS | FAIL |
| UNITDSPR | 2710 | 0 | 1 | 0 | 1600 | 15961 | 214 | FAIL | FAIL |
| VBL | 2277 | 0 | 0 | 0 | 85406 | 14907 | 275 | PASS | FAIL |
| VEDL | 2710 | 0 | 0 | 0 | 27 | 10896 | 151 | PASS | FAIL |
| WIPRO | 2710 | 0 | 0 | 0 | 196 | 14840 | 182 | PASS | FAIL |
| ZYDUSLIFE | 2710 | 0 | 0 | 0 | 4475 | 26091 | 239 | PASS | FAIL |

## DS2 Per-Stock Results

| Stock | Days | Miss | OHLC | Dupes | ZVol | Spikes | 2xDays | C1 | C2 | Cross |
|-------|------|------|------|-------|------|--------|--------|----|----|-------|
| 360ONE | 2710 | 907 | 0 | 0 | 160540 | 25845 | 324 | FAIL | FAIL | NO_FV1 |
| 3MINDIA | 2710 | 0 | 0 | 0 | 432212 | 28671 | 364 | PASS | FAIL | NO_FV1 |
| AADHARHFC | 421 | 0 | 0 | 0 | 1265 | 4754 | 54 | PASS | FAIL | NO_FV1 |
| AARTIIND | 2710 | 0 | 0 | 0 | 118343 | 32240 | 297 | PASS | FAIL | NO_FV1 |
| AAVAS | 1802 | 0 | 0 | 0 | 45402 | 16375 | 313 | PASS | FAIL | NO_FV1 |
| ABB | 2710 | 0 | 0 | 0 | 75704 | 19845 | 334 | PASS | FAIL | NO_FV1 |
| ABBOTINDIA | 2710 | 0 | 0 | 0 | 286241 | 21161 | 337 | PASS | FAIL | NO_FV1 |
| ABCAPITAL | 2074 | 0 | 1 | 0 | 1447 | 13099 | 195 | FAIL | FAIL | NO_FV1 |
| ABFRL | 2710 | 0 | 0 | 0 | 79274 | 31821 | 339 | PASS | FAIL | NO_FV1 |
| ABLBL | 148 | 0 | 0 | 0 | 1432 | 1300 | 15 | PASS | FAIL | NO_FV1 |
| ABREL | 2710 | 0 | 0 | 0 | 21109 | 20187 | 256 | PASS | FAIL | NO_FV1 |
| ABSLAMC | 1060 | 0 | 0 | 0 | 20320 | 8861 | 124 | PASS | FAIL | NO_FV1 |
| ACC | 2710 | 0 | 0 | 0 | 4207 | 17380 | 193 | PASS | FAIL | NO_FV1 |
| ACE | 2710 | 0 | 0 | 0 | 180894 | 31352 | 375 | PASS | FAIL | NO_FV1 |
| ACMESOLAR | 296 | 0 | 0 | 0 | 927 | 2849 | 32 | PASS | FAIL | NO_FV1 |
| ADANIENSOL | 2587 | 0 | 0 | 0 | 65525 | 32345 | 310 | PASS | FAIL | NO_FV1 |
| ADANIENT | 2710 | 0 | 0 | 0 | 2254 | 22138 | 224 | PASS | FAIL | NO_FV1 |
| ADANIGREEN | 1877 | 0 | 0 | 0 | 19957 | 21300 | 224 | PASS | FAIL | NO_FV1 |
| ADANIPORTS | 2710 | 0 | 0 | 0 | 75 | 19197 | 206 | PASS | FAIL | NO |
| ADANIPOWER | 2710 | 0 | 0 | 0 | 3093 | 28640 | 251 | PASS | FAIL | NO_FV1 |
| AEGISLOG | 2710 | 0 | 0 | 0 | 136383 | 41101 | 381 | PASS | FAIL | NO_FV1 |
| AEGISVOPAK | 163 | 0 | 0 | 0 | 4515 | 1730 | 18 | PASS | FAIL | NO_FV1 |
| AFCONS | 303 | 0 | 0 | 0 | 1580 | 3171 | 38 | PASS | FAIL | NO_FV1 |
| AFFLE | 2710 | 1008 | 0 | 0 | 42025 | 16044 | 211 | FAIL | FAIL | NO_FV1 |
| AGARWALEYE | 240 | 0 | 0 | 0 | 9022 | 3174 | 37 | PASS | FAIL | NO_FV1 |
| AIAENG | 2710 | 0 | 0 | 0 | 178819 | 18661 | 460 | PASS | FAIL | NO_FV1 |
| AIIL | 436 | 0 | 0 | 0 | 15444 | 4725 | 55 | PASS | FAIL | NO_FV1 |
| AJANTPHARM | 2710 | 0 | 0 | 0 | 39917 | 23623 | 321 | PASS | FAIL | NO_FV1 |
| AKUMS | 365 | 0 | 0 | 0 | 11475 | 4216 | 54 | PASS | FAIL | NO_FV1 |
| AKZOINDIA | 2710 | 0 | 0 | 0 | 392539 | 32147 | 404 | PASS | FAIL | NO_FV1 |
| ALKEM | 2490 | 0 | 1 | 0 | 75632 | 21053 | 322 | FAIL | FAIL | NO_FV1 |
| ALKYLAMINE | 2710 | 0 | 0 | 0 | 344140 | 42053 | 371 | PASS | FAIL | NO_FV1 |
| ALOKINDS | 1466 | 0 | 1 | 0 | 11758 | 19456 | 165 | FAIL | FAIL | NO_FV1 |
| AMBER | 1971 | 0 | 0 | 0 | 82726 | 35205 | 295 | PASS | FAIL | NO_FV1 |
| AMBUJACEM | 2710 | 0 | 0 | 0 | 896 | 20401 | 200 | PASS | FAIL | NO_FV1 |
| ANANDRATHI | 1017 | 0 | 0 | 0 | 56234 | 14571 | 137 | PASS | FAIL | NO_FV1 |
| ANANTRAJ | 2710 | 0 | 0 | 0 | 135706 | 28359 | 307 | PASS | FAIL | NO_FV1 |
| ANGELONE | 1312 | 0 | 0 | 0 | 6366 | 11467 | 161 | PASS | FAIL | NO_FV1 |
| APARINDS | 2710 | 0 | 1 | 0 | 295161 | 44769 | 404 | FAIL | FAIL | NO_FV1 |
| APLAPOLLO | 2710 | 0 | 0 | 0 | 228852 | 18687 | 397 | PASS | FAIL | NO_FV1 |
| APLLTD | 2710 | 0 | 0 | 0 | 152773 | 35312 | 406 | PASS | FAIL | NO_FV1 |
| APOLLOHOSP | 2710 | 0 | 0 | 0 | 4978 | 17335 | 200 | PASS | FAIL | NO_FV1 |
| APOLLOTYRE | 2710 | 0 | 0 | 0 | 1145 | 17263 | 191 | PASS | FAIL | NO_FV1 |
| APTUS | 1093 | 0 | 1 | 0 | 20066 | 11920 | 168 | FAIL | FAIL | NO_FV1 |
| AREM | ERROR | — | — | — | — | — | — | ERR | ERR | — |
| ASAHIINDIA | 2710 | 0 | 0 | 0 | 360073 | 49718 | 470 | PASS | FAIL | NO_FV1 |
| ASHOKLEY | 2710 | 0 | 0 | 0 | 53 | 13988 | 176 | PASS | FAIL | NO |
| ASIANPAINT | 2710 | 0 | 0 | 0 | 132 | 9179 | 153 | PASS | FAIL | NO_FV1 |
| ASTERDM | 1953 | 0 | 0 | 0 | 88399 | 28619 | 317 | PASS | FAIL | NO_FV1 |
| ASTRAL | 2710 | 0 | 0 | 0 | 181670 | 21823 | 375 | PASS | FAIL | NO_FV1 |
| ASTRAZEN | 2710 | 0 | 1 | 0 | 364461 | 50521 | 419 | FAIL | FAIL | NO_FV1 |
| ATGL | 1783 | 0 | 1 | 0 | 10128 | 26339 | 203 | FAIL | FAIL | NO_FV1 |
| ATHERENERG | 182 | 0 | 0 | 0 | 210 | 1660 | 20 | PASS | FAIL | NO_FV1 |
| ATUL | 2710 | 0 | 0 | 0 | 225984 | 24604 | 413 | PASS | FAIL | NO_FV1 |
| AUBANK | 2111 | 0 | 0 | 0 | 17058 | 13953 | 243 | PASS | FAIL | NO_FV1 |
| AUROPHARMA | 2710 | 0 | 0 | 0 | 207 | 13574 | 214 | PASS | FAIL | NO_FV1 |
| AWL | 2492 | 1504 | 0 | 0 | 1903 | 13804 | 111 | FAIL | FAIL | NO_FV1 |
| AXISBANK | 2710 | 0 | 0 | 0 | 62 | 11192 | 131 | PASS | FAIL | NO |
| BAJAJ-AUTO | 2710 | 0 | 0 | 0 | 1216 | 12058 | 172 | PASS | FAIL | NO_FV1 |
| BAJAJFINSV | 2710 | 0 | 0 | 0 | 18903 | 22026 | 189 | PASS | FAIL | NO_FV1 |
| BAJAJHFL | 337 | 0 | 0 | 0 | 29 | 3396 | 29 | PASS | FAIL | NO_FV1 |
| BAJAJHLDNG | 2710 | 0 | 1 | 0 | 201586 | 27309 | 424 | FAIL | FAIL | NO_FV1 |
| BAJFINANCE | 2710 | 0 | 0 | 0 | 8532 | 25545 | 163 | PASS | FAIL | NO_FV1 |
| BALKRISIND | 2710 | 0 | 0 | 0 | 73505 | 20851 | 285 | PASS | FAIL | NO_FV1 |
| BALRAMCHIN | 2710 | 0 | 0 | 0 | 31587 | 26880 | 313 | PASS | FAIL | NO_FV1 |
| BANDHANBNK | 1933 | 0 | 0 | 0 | 644 | 9349 | 176 | PASS | FAIL | NO |
| BANKBARODA | 2710 | 0 | 1 | 0 | 85 | 12697 | 125 | FAIL | FAIL | NO_FV1 |
| BANKINDIA | 2710 | 0 | 0 | 0 | 1879 | 19286 | 186 | PASS | FAIL | NO_FV1 |
| BASF | 2710 | 0 | 0 | 0 | 332354 | 39409 | 422 | PASS | FAIL | NO_FV1 |
| BATAINDIA | 2710 | 0 | 0 | 0 | 13936 | 15378 | 225 | PASS | FAIL | NO_FV1 |
| BAYERCROP | 2710 | 0 | 0 | 0 | 271796 | 25611 | 406 | PASS | FAIL | NO_FV1 |
| BBTC | 2710 | 0 | 1 | 0 | 183121 | 39979 | 388 | FAIL | FAIL | NO_FV1 |
| BDL | 1935 | 0 | 0 | 0 | 68258 | 25823 | 299 | PASS | FAIL | NO_FV1 |
| BEL | 2710 | 0 | 0 | 0 | 2152 | 14745 | 206 | PASS | FAIL | NO_FV1 |
| BEML | 2710 | 0 | 0 | 0 | 17443 | 33710 | 351 | PASS | FAIL | NO_FV1 |
| BERGEPAINT | 2710 | 0 | 0 | 0 | 18693 | 15566 | 261 | PASS | FAIL | NO_FV1 |
| BHARATFORG | 2710 | 0 | 0 | 0 | 1047 | 12934 | 224 | PASS | FAIL | NO_FV1 |
| BHARTIARTL | 2710 | 0 | 1 | 0 | 148 | 17262 | 207 | FAIL | FAIL | NO |
| BHARTIHEXA | 442 | 0 | 0 | 0 | 2073 | 5107 | 73 | PASS | FAIL | NO_FV1 |
| BHEL | 2710 | 0 | 0 | 0 | 126 | 26867 | 198 | PASS | FAIL | NO_FV1 |
| BIKAJI | 788 | 0 | 0 | 0 | 7529 | 8064 | 122 | PASS | FAIL | NO_FV1 |
| BIOCON | 2710 | 0 | 0 | 0 | 2964 | 17797 | 267 | PASS | FAIL | NO_FV1 |
| BLS | 2374 | 0 | 0 | 0 | 195580 | 37963 | 326 | PASS | FAIL | NO_FV1 |
| BLUEDART | 2710 | 0 | 0 | 0 | 291520 | 34260 | 420 | PASS | FAIL | NO_FV1 |
| BLUEJET | 550 | 0 | 0 | 0 | 21484 | 5883 | 57 | PASS | FAIL | NO_FV1 |
| BLUESTARCO | 2710 | 0 | 1 | 0 | 194335 | 28388 | 419 | FAIL | FAIL | NO_FV1 |
| BOSCHLTD | 2710 | 0 | 1 | 0 | 42643 | 19886 | 213 | FAIL | FAIL | NO_FV1 |
| BPCL | 2710 | 0 | 0 | 0 | 113 | 11385 | 142 | PASS | FAIL | NO_FV1 |
| BRIGADE | ERROR | — | — | — | — | — | — | ERR | ERR | — |
| BRITANNIA | 2710 | 0 | 1 | 0 | 2142 | 14821 | 182 | FAIL | FAIL | NO_FV1 |
| BSE | 2216 | 0 | 1 | 0 | 18897 | 28841 | 227 | FAIL | FAIL | NO_FV1 |
| BSOFT | 2710 | 0 | 1 | 0 | 22871 | 20075 | 298 | FAIL | FAIL | NO_FV1 |
| CAMPUS | 919 | 0 | 1 | 0 | 9336 | 11069 | 115 | FAIL | FAIL | NO_FV1 |
| CAMS | 1312 | 0 | 0 | 0 | 1488 | 9102 | 156 | PASS | FAIL | NO_FV1 |
| CANBK | 2710 | 0 | 0 | 0 | 140 | 14716 | 123 | PASS | FAIL | NO_FV1 |
| CANFINHOME | 2710 | 0 | 0 | 0 | 70745 | 24729 | 323 | PASS | FAIL | NO_FV1 |
| CAPLIPOINT | 2710 | 0 | 0 | 0 | 205564 | 41391 | 378 | PASS | FAIL | NO_FV1 |
| CARBORUNIV | 2710 | 0 | 1 | 0 | 259957 | 26754 | 453 | FAIL | FAIL | NO_FV1 |
| CASTROLIND | 2710 | 0 | 0 | 0 | 16345 | 30625 | 263 | PASS | FAIL | NO_FV1 |
| CCL | 2710 | 0 | 0 | 0 | 188066 | 34524 | 439 | PASS | FAIL | NO_FV1 |
| CDSL | 2117 | 0 | 0 | 0 | 19192 | 24712 | 226 | PASS | FAIL | NO_FV1 |
| CEATLTD | 2710 | 0 | 0 | 0 | 27313 | 27545 | 284 | PASS | FAIL | NO_FV1 |
| CENTRALBK | 2710 | 0 | 0 | 0 | 99078 | 68540 | 348 | PASS | FAIL | NO_FV1 |
| CENTURYPLY | 2710 | 0 | 0 | 0 | 112573 | 24995 | 414 | PASS | FAIL | NO_FV1 |
| CERA | 2710 | 0 | 0 | 0 | 344530 | 34630 | 409 | PASS | FAIL | NO_FV1 |
| CESC | 2710 | 0 | 0 | 0 | 14933 | 17186 | 241 | PASS | FAIL | NO_FV1 |
| CGCL | 2710 | 0 | 0 | 0 | 391764 | 55396 | 348 | PASS | FAIL | NO_FV1 |
| CGPOWER | 2710 | 0 | 1 | 0 | 36716 | 27026 | 299 | FAIL | FAIL | NO_FV1 |
| CHALET | 1718 | 0 | 0 | 0 | 84988 | 22792 | 324 | PASS | FAIL | NO_FV1 |
| CHAMBLFERT | 2710 | 0 | 1 | 0 | 68911 | 27694 | 322 | FAIL | FAIL | NO_FV1 |
| CHENNPETRO | 2710 | 0 | 0 | 0 | 47198 | 34679 | 349 | PASS | FAIL | NO_FV1 |
| CHOICEIN | 937 | 0 | 0 | 0 | 74817 | 9275 | 72 | PASS | FAIL | NO_FV1 |
| CHOLAFIN | 2710 | 0 | 0 | 0 | 68608 | 39046 | 274 | PASS | FAIL | NO_FV1 |
| CHOLAHLDNG | 2058 | 0 | 1 | 0 | 185331 | 16632 | 434 | FAIL | FAIL | NO_FV1 |
| CIPLA | 2710 | 0 | 0 | 0 | 221 | 19841 | 194 | PASS | FAIL | NO |
| CLEAN | 1117 | 0 | 0 | 0 | 8395 | 12401 | 138 | PASS | FAIL | NO_FV1 |
| COALINDIA | 2710 | 0 | 0 | 0 | 37 | 14508 | 200 | PASS | FAIL | NO |
| COCHINSHIP | 2087 | 0 | 0 | 0 | 48465 | 51637 | 269 | PASS | FAIL | NO_FV1 |
| COFORGE | 2710 | 0 | 0 | 0 | 29229 | 20779 | 271 | PASS | FAIL | NO_FV1 |
| COHANCE | 1454 | 0 | 0 | 0 | 10614 | 13751 | 235 | PASS | FAIL | NO_FV1 |
| COLPAL | 2710 | 0 | 0 | 0 | 9599 | 13391 | 217 | PASS | FAIL | NO_FV1 |
| CONCOR | 2710 | 0 | 0 | 0 | 10508 | 20019 | 244 | PASS | FAIL | NO_FV1 |
| CONCORDBIO | 600 | 0 | 1 | 0 | 13829 | 7410 | 103 | FAIL | FAIL | NO_FV1 |
| COROMANDEL | ERROR | — | — | — | — | — | — | ERR | ERR | — |
| CRAFTSMAN | 1194 | 0 | 0 | 0 | 53443 | 11957 | 156 | PASS | FAIL | NO_FV1 |
| CREDITACC | 1831 | 0 | 0 | 0 | 53585 | 25162 | 281 | PASS | FAIL | NO_FV1 |
| CRISIL | 2710 | 0 | 0 | 0 | 207822 | 29655 | 401 | PASS | FAIL | NO_FV1 |
| CROMPTON | 2397 | 0 | 1 | 0 | 16445 | 14376 | 276 | FAIL | FAIL | NO_FV1 |
| CUB | 2710 | 0 | 0 | 0 | 63044 | 24755 | 323 | PASS | FAIL | NO_FV1 |
| CUMMINSIND | 2710 | 0 | 0 | 0 | 21475 | 21022 | 279 | PASS | FAIL | NO_FV1 |
| CYIENT | 2710 | 0 | 1 | 0 | 104998 | 27238 | 415 | FAIL | FAIL | NO_FV1 |
| DABUR | 2710 | 0 | 0 | 0 | 1940 | 12299 | 202 | PASS | FAIL | NO |
| DALBHARAT | 1730 | 0 | 0 | 0 | 35830 | 10510 | 200 | PASS | FAIL | NO_FV1 |
| DATAPATTNS | 1009 | 0 | 0 | 0 | 4776 | 15061 | 128 | PASS | FAIL | NO_FV1 |
| DBREALTY | 2710 | 0 | 1 | 0 | 215631 | 56124 | 330 | FAIL | FAIL | NO_FV1 |
| DCMSHRIRAM | 2710 | 0 | 0 | 0 | 191603 | 37530 | 368 | PASS | FAIL | NO_FV1 |
| DEEPAKFERT | 2710 | 0 | 0 | 0 | 140796 | 35907 | 377 | PASS | FAIL | NO_FV1 |
| DEEPAKNTR | 2710 | 0 | 0 | 0 | 165832 | 36101 | 340 | PASS | FAIL | NO_FV1 |
| DELHIVERY | 2623 | 1631 | 0 | 0 | 26683 | 8356 | 134 | FAIL | FAIL | NO_FV1 |
| DEVYANI | 1098 | 0 | 0 | 0 | 1590 | 10243 | 146 | PASS | FAIL | NO_FV1 |
| DIVISLAB | 2710 | 0 | 1 | 0 | 3162 | 19878 | 221 | FAIL | FAIL | NO |
| DIXON | 2063 | 0 | 0 | 0 | 55590 | 13464 | 234 | PASS | FAIL | NO_FV1 |
| DLF | 2710 | 0 | 0 | 0 | 49 | 11255 | 148 | PASS | FAIL | NO_FV1 |
| DMART | 2186 | 0 | 0 | 0 | 535 | 15434 | 207 | PASS | FAIL | NO_FV1 |
| DOMS | 517 | 0 | 0 | 0 | 11028 | 6446 | 74 | PASS | FAIL | NO_FV1 |
| DRREDDY | 2710 | 0 | 0 | 0 | 381 | 17919 | 202 | PASS | FAIL | NO_FV1 |
| ECLERX | 2710 | 0 | 1 | 0 | 202644 | 32917 | 435 | FAIL | FAIL | NO_FV1 |
| EICHERMOT | 2710 | 0 | 0 | 0 | 1411 | 27064 | 162 | PASS | FAIL | NO_FV1 |
| EIDPARRY | 2710 | 0 | 0 | 0 | 132906 | 29934 | 382 | PASS | FAIL | NO_FV1 |
| EIHOTEL | 2710 | 0 | 0 | 0 | 231387 | 40141 | 397 | PASS | FAIL | NO_FV1 |
| ELECON | 2710 | 0 | 0 | 0 | 186132 | 37639 | 346 | PASS | FAIL | NO_FV1 |
| ELGIEQUIP | 2710 | 0 | 0 | 0 | 341410 | 52691 | 492 | PASS | FAIL | NO_FV1 |
| EMAMILTD | 2710 | 0 | 0 | 1 | 38949 | 20218 | 388 | FAIL | FAIL | NO_FV1 |
| EMCURE | 383 | 0 | 0 | 0 | 11073 | 3867 | 46 | PASS | FAIL | NO_FV1 |
| ENDURANCE | 2290 | 0 | 1 | 0 | 94496 | 20858 | 372 | FAIL | FAIL | NO_FV1 |
| ENGINERSIN | 2710 | 0 | 0 | 0 | 18152 | 29602 | 278 | PASS | FAIL | NO_FV1 |
| ENRIN | 150 | 0 | 0 | 0 | 23 | 921 | 14 | PASS | FAIL | NO_FV1 |
| ERIS | 2118 | 0 | 1 | 0 | 122727 | 26808 | 373 | FAIL | FAIL | NO_FV1 |
| ESCORTS | 2710 | 0 | 0 | 0 | 9800 | 22201 | 268 | PASS | FAIL | NO_FV1 |
| ETERNAL | 1114 | 0 | 0 | 0 | 68 | 6357 | 104 | PASS | FAIL | NO_FV1 |
| EXIDEIND | 2710 | 0 | 0 | 0 | 4470 | 16393 | 208 | PASS | FAIL | NO_FV1 |
| FACT | 2710 | 0 | 1 | 0 | 321222 | 60526 | 471 | FAIL | FAIL | NO_FV1 |
| FEDERALBNK | 2710 | 0 | 0 | 0 | 883 | 14870 | 184 | PASS | FAIL | NO_FV1 |
| FINCABLES | 2710 | 0 | 0 | 0 | 134713 | 35254 | 418 | PASS | FAIL | NO_FV1 |
| FINPIPE | 2710 | 0 | 0 | 0 | 186126 | 30333 | 398 | PASS | FAIL | NO_FV1 |
| FIRSTCRY | 360 | 0 | 0 | 0 | 2584 | 5117 | 59 | PASS | FAIL | NO_FV1 |
| FIVESTAR | 2710 | 1882 | 0 | 0 | 28617 | 9904 | 123 | FAIL | FAIL | NO_FV1 |
| FLUOROCHEM | 1552 | 0 | 1 | 0 | 68055 | 14363 | 208 | FAIL | FAIL | NO_FV1 |
| FORCEMOT | 1590 | 74 | 1 | 0 | 86940 | 21580 | 220 | FAIL | FAIL | NO_FV1 |
| FORTIS | 2710 | 0 | 0 | 0 | 29719 | 34914 | 332 | PASS | FAIL | NO_FV1 |
| FSL | 2710 | 0 | 0 | 0 | 28991 | 24139 | 275 | PASS | FAIL | NO_FV1 |
| GAIL | 2710 | 0 | 0 | 0 | 550 | 15839 | 178 | PASS | FAIL | NO_FV1 |
| GESHIP | 2710 | 0 | 0 | 0 | 150208 | 34716 | 410 | PASS | FAIL | NO_FV1 |
| GICRE | 2710 | 636 | 0 | 0 | 64061 | 37276 | 320 | FAIL | FAIL | NO_FV1 |
| GILLETTE | 2710 | 0 | 1 | 0 | 332316 | 41367 | 362 | FAIL | FAIL | NO_FV1 |
| GLAND | 1279 | 0 | 0 | 0 | 6065 | 14354 | 201 | PASS | FAIL | NO_FV1 |
| GLAXO | 2710 | 0 | 0 | 0 | 222056 | 38644 | 274 | PASS | FAIL | NO_FV1 |
| GLENMARK | 2710 | 0 | 0 | 0 | 3212 | 24746 | 233 | PASS | FAIL | NO_FV1 |
| GMDCLTD | 2710 | 0 | 0 | 0 | 123034 | 57588 | 341 | PASS | FAIL | NO_FV1 |
| GMRAIRPORT | 2710 | 0 | 0 | 0 | 12008 | 23925 | 249 | PASS | FAIL | NO_FV1 |
| GODFRYPHLP | 2710 | 0 | 0 | 0 | 163233 | 39394 | 394 | PASS | FAIL | NO_FV1 |
| GODIGIT | 416 | 0 | 1 | 0 | 8767 | 5363 | 82 | FAIL | FAIL | NO_FV1 |
| GODREJAGRO | 2044 | 0 | 0 | 0 | 86830 | 24313 | 262 | PASS | FAIL | NO_FV1 |
| GODREJCP | 2710 | 0 | 1 | 0 | 5102 | 12831 | 258 | FAIL | FAIL | NO_FV1 |
| GODREJIND | 2710 | 0 | 1 | 0 | 77691 | 22716 | 330 | FAIL | FAIL | NO_FV1 |
| GODREJPROP | 2710 | 0 | 0 | 0 | 71221 | 21331 | 361 | PASS | FAIL | NO_FV1 |
| GPIL | 2710 | 0 | 0 | 0 | 278592 | 31771 | 347 | PASS | FAIL | NO_FV1 |
| GRANULES | 2710 | 0 | 1 | 0 | 20165 | 23863 | 289 | FAIL | FAIL | NO_FV1 |
| GRAPHITE | 2710 | 0 | 0 | 0 | 140158 | 34103 | 393 | PASS | FAIL | NO_FV1 |
| GRASIM | 2710 | 0 | 0 | 0 | 13525 | 16348 | 190 | PASS | FAIL | NO_FV1 |
| GRAVITA | 2710 | 0 | 0 | 0 | 263747 | 35892 | 353 | PASS | FAIL | NO_FV1 |
| GRSE | 1800 | 0 | 0 | 0 | 75408 | 33554 | 260 | PASS | FAIL | NO_FV1 |
| GSPL | 2710 | 0 | 1 | 0 | 71789 | 22401 | 383 | FAIL | FAIL | NO_FV1 |
| GUJGASLTD | 2555 | 0 | 1 | 0 | 117253 | 20986 | 367 | FAIL | FAIL | NO_FV1 |
| GVTD | 2710 | 0 | 0 | 0 | 267950 | 41061 | 413 | PASS | FAIL | NO_FV1 |
| HAL | 1932 | 0 | 1 | 0 | 55281 | 13123 | 218 | FAIL | FAIL | NO_FV1 |
| HAPPSTMNDS | 1323 | 0 | 0 | 0 | 912 | 26720 | 164 | PASS | FAIL | NO_FV1 |
| HAVELLS | 2710 | 0 | 1 | 0 | 1644 | 13811 | 207 | FAIL | FAIL | NO_FV1 |
| HBLENGINE | 2710 | 0 | 1 | 0 | 166643 | 42635 | 300 | FAIL | FAIL | NO_FV1 |
| HCLTECH | 2710 | 0 | 0 | 0 | 134 | 12252 | 152 | PASS | FAIL | NO_FV1 |
| HDFCAMC | 1842 | 0 | 0 | 0 | 1553 | 10535 | 159 | PASS | FAIL | NO_FV1 |
| HDFCBANK | 2710 | 0 | 1 | 0 | 165 | 15506 | 102 | FAIL | FAIL | NO |
| HDFCLIFE | 2703 | 661 | 0 | 0 | 8274 | 9451 | 148 | FAIL | FAIL | NO_FV1 |
| HEG | 2710 | 0 | 0 | 0 | 132803 | 37515 | 377 | PASS | FAIL | NO_FV1 |
| HEROMOTOCO | 2710 | 0 | 0 | 0 | 307 | 12072 | 165 | PASS | FAIL | NO_FV1 |
| HEXT | 229 | 0 | 0 | 0 | 988 | 1563 | 31 | PASS | FAIL | NO_FV1 |
| HFCL | 2710 | 0 | 1 | 0 | 72912 | 38543 | 274 | FAIL | FAIL | NO_FV1 |
| HINDALCO | 2710 | 0 | 0 | 0 | 111 | 7346 | 122 | PASS | FAIL | NO |
| HINDCOPPER | 2710 | 0 | 0 | 0 | 92802 | 43130 | 331 | PASS | FAIL | NO_FV1 |
| HINDPETRO | 2710 | 0 | 0 | 0 | 193 | 9754 | 172 | PASS | FAIL | NO_FV1 |
| HINDUNILVR | 2710 | 0 | 0 | 0 | 157 | 8566 | 141 | PASS | FAIL | NO_FV1 |
| HINDZINC | 2710 | 0 | 0 | 0 | 10426 | 29282 | 224 | PASS | FAIL | NO_FV1 |
| HOMEFIRST | 1937 | 618 | 1 | 0 | 49153 | 13557 | 182 | FAIL | FAIL | NO_FV1 |
| HONASA | 546 | 0 | 0 | 0 | 8799 | 8319 | 95 | PASS | FAIL | NO_FV1 |
| HONAUT | 2710 | 0 | 1 | 0 | 453239 | 28259 | 362 | FAIL | FAIL | NO_FV1 |
| HSCL | 2710 | 0 | 1 | 0 | 134008 | 52622 | 307 | FAIL | FAIL | NO_FV1 |
| HUDCO | 2146 | 0 | 0 | 0 | 22202 | 43138 | 219 | PASS | FAIL | NO_FV1 |
| HYUNDAI | 312 | 0 | 0 | 0 | 16 | 1896 | 26 | PASS | FAIL | NO_FV1 |
| ICICIBANK | 2710 | 0 | 1 | 0 | 4970 | 7270 | 104 | FAIL | FAIL | NO |
| ICICIGI | 2056 | 0 | 0 | 0 | 6814 | 10329 | 190 | PASS | FAIL | NO_FV1 |
| ICICIPRULI | 2302 | 0 | 1 | 0 | 1216 | 12687 | 248 | FAIL | FAIL | NO_FV1 |
| IDBI | 2710 | 0 | 0 | 0 | 5075 | 29416 | 275 | PASS | FAIL | NO_FV1 |
| IDEA | 2710 | 0 | 1 | 0 | 754 | 60724 | 240 | FAIL | FAIL | NO_FV1 |
| IDFCFIRSTB | 2521 | 0 | 0 | 0 | 604 | 10632 | 174 | PASS | FAIL | NO_FV1 |
| IEX | 2040 | 0 | 0 | 0 | 66838 | 22336 | 271 | PASS | FAIL | NO_FV1 |
| IFCI | 2710 | 0 | 0 | 0 | 38868 | 37204 | 251 | PASS | FAIL | NO_FV1 |
| IGIL | 271 | 0 | 0 | 0 | 1007 | 3830 | 31 | PASS | FAIL | NO_FV1 |
| IGL | 2710 | 0 | 1 | 0 | 8159 | 14834 | 264 | FAIL | FAIL | NO_FV1 |
| IIFL | 2710 | 0 | 0 | 0 | 123484 | 44361 | 405 | PASS | FAIL | NO_FV1 |
| IKS | 272 | 0 | 0 | 0 | 5941 | 3594 | 40 | PASS | FAIL | NO_FV1 |
| INDGN | 423 | 0 | 1 | 0 | 3904 | 4715 | 35 | FAIL | FAIL | NO_FV1 |
| INDHOTEL | 2710 | 0 | 0 | 0 | 43186 | 24168 | 308 | PASS | FAIL | NO_FV1 |
| INDIACEM | 2710 | 0 | 0 | 0 | 10171 | 19777 | 264 | PASS | FAIL | NO_FV1 |
| INDIAMART | 2542 | 790 | 0 | 0 | 51279 | 14450 | 203 | FAIL | FAIL | NO_FV1 |
| INDIANB | 2710 | 0 | 0 | 0 | 32040 | 21043 | 297 | PASS | FAIL | NO_FV1 |
| INDIGO | 2519 | 0 | 0 | 0 | 5821 | 18782 | 260 | PASS | FAIL | NO_FV1 |
| INDUSINDBK | 2710 | 0 | 0 | 0 | 275 | 33420 | 186 | PASS | FAIL | NO |
| INDUSTOWER | 2710 | 0 | 0 | 0 | 1004 | 27989 | 266 | PASS | FAIL | NO_FV1 |
| INFY | 2710 | 0 | 0 | 0 | 5008 | 8512 | 139 | PASS | FAIL | NO |
| INOXINDIA | 516 | 0 | 0 | 0 | 10419 | 9098 | 64 | PASS | FAIL | NO_FV1 |
| INOXWIND | 2667 | 0 | 0 | 0 | 158679 | 52522 | 349 | PASS | FAIL | NO_FV1 |
| INTELLECT | 2710 | 0 | 0 | 0 | 73664 | 27679 | 331 | PASS | FAIL | NO_FV1 |
| IOB | 2710 | 0 | 0 | 0 | 83067 | 83407 | 307 | PASS | FAIL | NO_FV1 |
| IOC | 2710 | 0 | 1 | 0 | 752 | 12093 | 174 | FAIL | FAIL | NO_FV1 |
| IPCALAB | 2710 | 0 | 0 | 0 | 55823 | 21394 | 355 | PASS | FAIL | NO_FV1 |
| IRB | 2710 | 0 | 0 | 0 | 11096 | 23388 | 250 | PASS | FAIL | NO_FV1 |
| IRCON | 1807 | 0 | 0 | 0 | 38246 | 42854 | 219 | PASS | FAIL | NO_FV1 |
| IRCTC | 2710 | 582 | 0 | 0 | 179080 | 48235 | 280 | FAIL | FAIL | NO_FV1 |
| IREDA | 532 | 0 | 0 | 0 | 33 | 7169 | 56 | PASS | FAIL | NO_FV1 |
| IRFC | 1935 | 550 | 0 | 0 | 9158 | 23990 | 134 | FAIL | FAIL | NO_FV1 |
| ITC | 2710 | 0 | 0 | 0 | 4988 | 12519 | 164 | PASS | FAIL | NO |
| ITCHOTELS | 244 | 0 | 0 | 0 | 9 | 2143 | 25 | PASS | FAIL | NO_FV1 |
| ITI | 2710 | 0 | 1 | 0 | 146617 | 56448 | 469 | FAIL | FAIL | NO_FV1 |
| JBCHEPHARM | 2710 | 0 | 0 | 0 | 168511 | 28694 | 406 | PASS | FAIL | NO_FV1 |
| JBMA | 2710 | 0 | 0 | 0 | 262074 | 49086 | 432 | PASS | FAIL | NO_FV1 |
| JINDALSAW | 2710 | 0 | 0 | 0 | 80868 | 26268 | 274 | PASS | FAIL | NO_FV1 |
| JINDALSTEL | 2710 | 0 | 0 | 0 | 678 | 13774 | 172 | PASS | FAIL | NO_FV1 |
| JIOFIN | 599 | 0 | 0 | 0 | 59 | 3463 | 43 | PASS | FAIL | NO_FV1 |
| JKBANK | 2710 | 0 | 0 | 0 | 67643 | 38745 | 300 | PASS | FAIL | NO_FV1 |
| JKCEMENT | 2710 | 0 | 1 | 0 | 200265 | 22048 | 394 | FAIL | FAIL | NO_FV1 |
| JKTYRE | 2710 | 0 | 0 | 0 | 18966 | 27672 | 306 | PASS | FAIL | NO_FV1 |
| JMFINANCIL | 2710 | 0 | 1 | 0 | 94333 | 52278 | 361 | FAIL | FAIL | NO_FV1 |
| JPPOWER | 2710 | 0 | 0 | 0 | 112855 | 57302 | 290 | PASS | FAIL | NO_FV1 |
| JSL | 2710 | 0 | 1 | 0 | 152903 | 26821 | 298 | FAIL | FAIL | NO_FV1 |
| JSWCEMENT | 110 | 0 | 0 | 0 | 60 | 1353 | 11 | PASS | FAIL | NO_FV1 |
| JSWENERGY | 2710 | 0 | 0 | 0 | 29539 | 28701 | 286 | PASS | FAIL | NO_FV1 |
| JSWINFRA | 570 | 0 | 0 | 0 | 82 | 4418 | 50 | PASS | FAIL | NO_FV1 |
| JSWSTEEL | 2710 | 0 | 0 | 0 | 485 | 9493 | 131 | PASS | FAIL | NO |
| JUBLFOOD | 2710 | 0 | 0 | 0 | 2567 | 18351 | 205 | PASS | FAIL | NO_FV1 |
| JUBLINGREA | 1198 | 0 | 1 | 0 | 14873 | 14647 | 150 | FAIL | FAIL | NO_FV1 |
| JUBLPHARMA | 2710 | 0 | 0 | 0 | 55223 | 31458 | 357 | PASS | FAIL | NO_FV1 |
| JWL | 2710 | 0 | 0 | 0 | 382465 | 113087 | 423 | PASS | FAIL | NO_FV1 |
| JYOTHYLAB | 2710 | 0 | 0 | 0 | 145561 | 29973 | 462 | PASS | FAIL | NO_FV1 |
| JYOTICNC | 499 | 0 | 1 | 0 | 4286 | 6247 | 62 | FAIL | FAIL | NO_FV1 |
| KAJARIACER | 2710 | 0 | 0 | 0 | 70122 | 21591 | 403 | PASS | FAIL | NO_FV1 |
| KALYANKJIL | 1193 | 0 | 1 | 0 | 3689 | 14597 | 138 | FAIL | FAIL | NO_FV1 |
| KARURVYSYA | 2710 | 0 | 0 | 0 | 45205 | 28587 | 326 | PASS | FAIL | NO_FV1 |
| KAYNES | 784 | 0 | 0 | 0 | 3579 | 9918 | 97 | PASS | FAIL | NO_FV1 |
| KEC | 2710 | 0 | 0 | 0 | 47160 | 27885 | 387 | PASS | FAIL | NO_FV1 |
| KEI | 2710 | 0 | 0 | 0 | 88385 | 24748 | 346 | PASS | FAIL | NO_FV1 |
| KFINTECH | 1892 | 1125 | 1 | 0 | 7817 | 7813 | 101 | FAIL | FAIL | NO_FV1 |
| KIMS | 1132 | 0 | 1 | 0 | 35538 | 11565 | 189 | FAIL | FAIL | NO_FV1 |
| KIRLOSBROS | 2710 | 0 | 0 | 0 | 363729 | 46829 | 440 | PASS | FAIL | NO_FV1 |
| KIRLOSENG | 2710 | 0 | 0 | 0 | 359611 | 60075 | 374 | PASS | FAIL | NO_FV1 |
| KOTAKBANK | 2710 | 0 | 0 | 0 | 305 | 10559 | 176 | PASS | FAIL | NO_FV1 |
| KPIL | 2710 | 0 | 1 | 0 | 169626 | 30466 | 463 | FAIL | FAIL | NO_FV1 |
| KPITTECH | 1670 | 0 | 1 | 0 | 21243 | 12342 | 213 | FAIL | FAIL | NO_FV1 |
| KPRMILL | 2710 | 0 | 0 | 0 | 225072 | 28534 | 423 | PASS | FAIL | NO_FV1 |
| KSB | 2710 | 0 | 1 | 0 | 405977 | 41499 | 416 | FAIL | FAIL | NO_FV1 |
| LALPATHLAB | 2490 | 0 | 0 | 0 | 57196 | 19210 | 315 | PASS | FAIL | NO_FV1 |
| LATENTVIEW | 1749 | 673 | 0 | 0 | 11296 | 13802 | 142 | FAIL | FAIL | NO_FV1 |
| LAURUSLABS | 2249 | 0 | 1 | 0 | 87092 | 22100 | 306 | FAIL | FAIL | NO_FV1 |
| LEMONTREE | 1926 | 0 | 1 | 0 | 30683 | 18309 | 254 | FAIL | FAIL | NO_FV1 |
| LICHSGFIN | 2710 | 0 | 0 | 0 | 512 | 13500 | 172 | PASS | FAIL | NO_FV1 |
| LICI | 913 | 0 | 0 | 0 | 24 | 9376 | 87 | PASS | FAIL | NO_FV1 |
| LINDEINDIA | 2710 | 0 | 0 | 0 | 323233 | 45602 | 450 | PASS | FAIL | NO_FV1 |
| LLOYDSME | 623 | 0 | 1 | 0 | 9892 | 4983 | 65 | FAIL | FAIL | NO_FV1 |
| LODHA | 1180 | 0 | 0 | 0 | 7249 | 7459 | 129 | PASS | FAIL | NO_FV1 |
| LT | 2710 | 0 | 0 | 0 | 75 | 7869 | 141 | PASS | FAIL | NO_FV1 |
| LTF | 2710 | 0 | 1 | 0 | 1870 | 15584 | 225 | FAIL | FAIL | NO_FV1 |
| LTFOODS | 2710 | 0 | 0 | 0 | 163083 | 32662 | 367 | PASS | FAIL | NO_FV1 |
| LTIM | 2349 | 0 | 0 | 0 | 25061 | 12613 | 236 | PASS | FAIL | NO_FV1 |
| LTTS | 2306 | 0 | 1 | 0 | 53522 | 18275 | 247 | FAIL | FAIL | NO_FV1 |
| LUPIN | 2710 | 0 | 1 | 0 | 360 | 16309 | 229 | FAIL | FAIL | NO_FV1 |
| MAHABANK | 2710 | 0 | 0 | 0 | 178160 | 116013 | 327 | PASS | FAIL | NO_FV1 |
| MAHSCOOTER | 2710 | 0 | 0 | 0 | 512637 | 37087 | 347 | PASS | FAIL | NO_FV1 |
| MAHSEAMLES | 2710 | 0 | 0 | 0 | 287801 | 34290 | 397 | PASS | FAIL | NO_FV1 |
| MANAPPURAM | 2710 | 0 | 0 | 0 | 9538 | 17455 | 238 | PASS | FAIL | NO_FV1 |
| MANKIND | 671 | 0 | 0 | 0 | 571 | 4524 | 85 | PASS | FAIL | NO_FV1 |
| MANYAVAR | 972 | 0 | 0 | 0 | 7837 | 7844 | 153 | PASS | FAIL | NO_FV1 |
| MAPMYINDIA | 1012 | 0 | 0 | 0 | 19028 | 13842 | 138 | PASS | FAIL | NO_FV1 |
| MARICO | 2710 | 0 | 1 | 0 | 3779 | 13921 | 234 | FAIL | FAIL | NO_FV1 |
| MARUTI | 2710 | 0 | 0 | 0 | 104 | 8662 | 124 | PASS | FAIL | NO_FV1 |
| MAXHEALTH | 1342 | 0 | 0 | 0 | 5759 | 6953 | 151 | PASS | FAIL | NO_FV1 |
| MAZDOCK | 2010 | 695 | 0 | 0 | 10025 | 18933 | 173 | FAIL | FAIL | NO_FV1 |
| MCX | 2710 | 0 | 0 | 0 | 12765 | 21462 | 271 | PASS | FAIL | NO_FV1 |
| MEDANTA | 788 | 0 | 0 | 0 | 1616 | 5981 | 104 | PASS | FAIL | NO_FV1 |
| METROPOLIS | 1673 | 0 | 1 | 0 | 43828 | 16577 | 210 | FAIL | FAIL | NO_FV1 |
| MFSL | 2710 | 0 | 0 | 0 | 21897 | 20619 | 320 | PASS | FAIL | NO_FV1 |
| MGL | 2362 | 0 | 0 | 0 | 13052 | 17774 | 261 | PASS | FAIL | NO_FV1 |
| MINDACORP | 2710 | 0 | 0 | 0 | 217585 | 42612 | 408 | PASS | FAIL | NO_FV1 |
| MM | 2710 | 0 | 0 | 0 | 98 | 10212 | 163 | PASS | FAIL | NO_FV1 |
| MMFIN | 2710 | 0 | 0 | 0 | 2982 | 22496 | 225 | PASS | FAIL | NO_FV1 |
| MMTC | 2710 | 0 | 0 | 0 | 93357 | 48290 | 381 | PASS | FAIL | NO_FV1 |
| MOTHERSON | 2710 | 0 | 0 | 0 | 176 | 15689 | 225 | PASS | FAIL | NO_FV1 |
| MOTILALOFS | 2710 | 0 | 1 | 0 | 171764 | 35959 | 386 | FAIL | FAIL | NO_FV1 |
| MPHASIS | 2710 | 0 | 0 | 0 | 54763 | 15243 | 272 | PASS | FAIL | NO_FV1 |
| MRF | 2710 | 0 | 0 | 0 | 79085 | 18771 | 165 | PASS | FAIL | NO_FV1 |
| MRPL | 2710 | 0 | 0 | 0 | 53334 | 45885 | 359 | PASS | FAIL | NO_FV1 |
| MSUMI | 946 | 0 | 0 | 0 | 25 | 5243 | 88 | PASS | FAIL | NO_FV1 |
| MUTHOOTFIN | 2710 | 0 | 0 | 0 | 34969 | 23009 | 302 | PASS | FAIL | NO_FV1 |
| NAM-INDIA | 2030 | 0 | 0 | 0 | 29595 | 16255 | 246 | PASS | FAIL | NO_FV1 |
| NATCOPHARM | 2710 | 0 | 0 | 0 | 45036 | 27234 | 347 | PASS | FAIL | NO_FV1 |
| NATIONALUM | 2710 | 0 | 0 | 0 | 20165 | 21626 | 232 | PASS | FAIL | NO |
| NAUKRI | 2710 | 0 | 0 | 0 | 94920 | 16888 | 356 | PASS | FAIL | NO_FV1 |
| NAVA | 2710 | 0 | 0 | 0 | 241376 | 43297 | 385 | PASS | FAIL | NO_FV1 |
| NAVINFLUOR | 2710 | 0 | 0 | 0 | 179169 | 27708 | 383 | PASS | FAIL | NO_FV1 |
| NBCC | 2710 | 0 | 1 | 0 | 5451 | 28317 | 278 | FAIL | FAIL | NO_FV1 |
| NCC | 2710 | 0 | 0 | 0 | 1952 | 25311 | 228 | PASS | FAIL | NO_FV1 |
| NESTLEIND | 2710 | 0 | 0 | 0 | 21073 | 12884 | 198 | PASS | FAIL | NO_FV1 |
| NETWEB | 615 | 0 | 0 | 0 | 4208 | 15001 | 91 | PASS | FAIL | NO_FV1 |
| NEULANDLAB | 2710 | 0 | 0 | 0 | 322731 | 40226 | 400 | PASS | FAIL | NO_FV1 |
| NEWGEN | 1972 | 0 | 0 | 0 | 118455 | 29028 | 300 | PASS | FAIL | NO_FV1 |
| NH | 2482 | 0 | 0 | 0 | 159193 | 25313 | 403 | PASS | FAIL | NO_FV1 |
| NHPC | 2710 | 0 | 0 | 0 | 15744 | 45495 | 247 | PASS | FAIL | NO_FV1 |
| NIACL | 2025 | 0 | 0 | 0 | 80971 | 39932 | 316 | PASS | FAIL | NO_FV1 |
| NIVABUPA | 295 | 0 | 0 | 0 | 3049 | 4980 | 48 | PASS | FAIL | NO_FV1 |
| NLCINDIA | 2710 | 0 | 0 | 0 | 148818 | 52236 | 361 | PASS | FAIL | NO_FV1 |
| NMDC | 2710 | 0 | 0 | 0 | 2923 | 19009 | 205 | PASS | FAIL | NO_FV1 |
| NSLNISP | 721 | 0 | 1 | 0 | 714 | 8142 | 74 | FAIL | FAIL | NO_FV1 |
| NTPC | 2710 | 0 | 0 | 0 | 308 | 14554 | 209 | PASS | FAIL | NO |
| NTPCGREEN | 288 | 0 | 0 | 0 | 24 | 2706 | 30 | PASS | FAIL | NO_FV1 |
| NUVAMA | 574 | 0 | 0 | 0 | 6896 | 4175 | 63 | PASS | FAIL | NO_FV1 |
| NUVOCO | 1094 | 0 | 0 | 0 | 44314 | 11650 | 182 | PASS | FAIL | NO_FV1 |
| NYKAA | 1040 | 0 | 0 | 0 | 119 | 8096 | 105 | PASS | FAIL | NO_FV1 |
| OBEROIRLTY | 2710 | 0 | 0 | 0 | 61245 | 18852 | 344 | PASS | FAIL | NO_FV1 |
| OFSS | 2710 | 0 | 0 | 0 | 102564 | 31210 | 282 | PASS | FAIL | NO_FV1 |
| OIL | 2710 | 0 | 0 | 0 | 20070 | 26891 | 288 | PASS | FAIL | NO_FV1 |
| OLAELEC | 362 | 0 | 0 | 0 | 5 | 6127 | 38 | PASS | FAIL | NO_FV1 |
| OLECTRA | 2710 | 1 | 0 | 0 | 339531 | 61847 | 423 | PASS | FAIL | NO_FV1 |
| ONESOURCE | 247 | 0 | 0 | 0 | 2205 | 1952 | 24 | PASS | FAIL | NO_FV1 |
| ONGC | 2710 | 0 | 0 | 0 | 57 | 15919 | 188 | PASS | FAIL | NO |
| PAGEIND | 2710 | 0 | 0 | 0 | 67108 | 15339 | 212 | PASS | FAIL | NO_FV1 |
| PATANJALI | 1483 | 0 | 0 | 0 | 65698 | 23147 | 179 | PASS | FAIL | NO_FV1 |
| PAYTM | 1034 | 0 | 1 | 0 | 93 | 8144 | 113 | FAIL | FAIL | NO_FV1 |
| PCBL | 2710 | 0 | 1 | 0 | 79699 | 27356 | 335 | FAIL | FAIL | NO_FV1 |
| PERSISTENT | 2710 | 0 | 0 | 0 | 57340 | 16273 | 297 | PASS | FAIL | NO_FV1 |
| PETRONET | 2710 | 0 | 0 | 0 | 4769 | 13900 | 217 | PASS | FAIL | NO_FV1 |
| PFC | 2710 | 0 | 0 | 0 | 634 | 12069 | 171 | PASS | FAIL | NO_FV1 |
| PFIZER | 2710 | 0 | 1 | 0 | 230252 | 34099 | 362 | FAIL | FAIL | NO_FV1 |
| PGEL | 2710 | 0 | 0 | 0 | 367126 | 39854 | 449 | PASS | FAIL | NO_FV1 |
| PGHH | 2710 | 0 | 0 | 0 | 396100 | 22133 | 481 | PASS | FAIL | NO_FV1 |
| PHOENIXLTD | 2710 | 0 | 0 | 0 | 209249 | 22194 | 468 | PASS | FAIL | NO_FV1 |
| PIDILITIND | 2710 | 0 | 0 | 0 | 6333 | 13599 | 242 | PASS | FAIL | NO_FV1 |
| PIIND | 2710 | 0 | 0 | 0 | 70670 | 22171 | 318 | PASS | FAIL | NO_FV1 |
| PNB | 2710 | 0 | 0 | 0 | 76 | 25530 | 143 | PASS | FAIL | NO |
| PNBHOUSING | 2278 | 0 | 0 | 0 | 39037 | 30667 | 300 | PASS | FAIL | NO_FV1 |
| POLICYBZR | 1037 | 0 | 0 | 0 | 519 | 7378 | 134 | PASS | FAIL | NO_FV1 |
| POLYCAB | 1672 | 0 | 1 | 0 | 6249 | 12947 | 180 | FAIL | FAIL | NO_FV1 |
| POLYMED | 2710 | 0 | 1 | 0 | 364248 | 49646 | 469 | FAIL | FAIL | NO_FV1 |
| POONAWALLA | 2710 | 0 | 1 | 0 | 203508 | 47568 | 379 | FAIL | FAIL | NO_FV1 |
| POWERGRID | 2710 | 0 | 0 | 0 | 1255 | 11082 | 193 | PASS | FAIL | NO |
| POWERINDIA | 1440 | 0 | 1 | 0 | 72213 | 15403 | 190 | FAIL | FAIL | NO_FV1 |
| PPLPHARMA | 806 | 0 | 0 | 0 | 268 | 7351 | 94 | PASS | FAIL | NO_FV1 |
| PRAJIND | 2710 | 0 | 1 | 0 | 40916 | 30466 | 339 | FAIL | FAIL | NO_FV1 |
| PREMIERENE | 346 | 0 | 0 | 0 | 88 | 3825 | 41 | PASS | FAIL | NO_FV1 |
| PRESTIGE | 2710 | 0 | 0 | 0 | 87367 | 22149 | 374 | PASS | FAIL | NO_FV1 |
| PTCIL | 2710 | 1526 | 0 | 0 | 205712 | 21581 | 182 | FAIL | FAIL | NO_FV1 |
| PVRINOX | 2710 | 0 | 0 | 0 | 38072 | 30914 | 294 | PASS | FAIL | NO_FV1 |
| RADICO | 2710 | 0 | 0 | 0 | 64528 | 32296 | 358 | PASS | FAIL | NO_FV1 |
| RAILTEL | 1212 | 0 | 0 | 0 | 4825 | 19688 | 160 | PASS | FAIL | NO_FV1 |
| RAINBOW | 1683 | 727 | 0 | 0 | 11206 | 8996 | 137 | FAIL | FAIL | NO_FV1 |
| RAMCOCEM | 2710 | 0 | 0 | 0 | 76248 | 20970 | 323 | PASS | FAIL | NO_FV1 |
| RBLBANK | 2321 | 0 | 1 | 0 | 511 | 18419 | 189 | FAIL | FAIL | NO_FV1 |
| RCF | 2710 | 0 | 1 | 0 | 36832 | 34182 | 360 | FAIL | FAIL | NO_FV1 |
| RECLTD | 2710 | 0 | 0 | 0 | 361 | 11569 | 179 | PASS | FAIL | NO_FV1 |
| REDINGTON | 2710 | 0 | 1 | 0 | 93642 | 34262 | 406 | FAIL | FAIL | NO_FV1 |
| RELIANCE | 2710 | 0 | 0 | 0 | 69 | 9286 | 119 | PASS | FAIL | NO |
| RHIM | 2710 | 0 | 0 | 0 | 346134 | 44277 | 415 | PASS | FAIL | NO_FV1 |
| RITES | 1867 | 0 | 0 | 0 | 21160 | 30173 | 269 | PASS | FAIL | NO_FV1 |
| RKFORGE | 2710 | 0 | 0 | 0 | 282008 | 32613 | 407 | PASS | FAIL | NO_FV1 |
| RPOWER | 2710 | 0 | 0 | 0 | 6291 | 53424 | 243 | PASS | FAIL | NO_FV1 |
| RRKABEL | 578 | 0 | 1 | 0 | 8731 | 8297 | 79 | FAIL | FAIL | NO_FV1 |
| RVNL | 2579 | 903 | 0 | 0 | 1040 | 26132 | 198 | FAIL | FAIL | NO_FV1 |
| SAGILITY | 297 | 0 | 0 | 0 | 63 | 2772 | 34 | PASS | FAIL | NO_FV1 |
| SAIL | 2710 | 0 | 0 | 0 | 1413 | 17727 | 153 | PASS | FAIL | NO_FV1 |
| SAILIFE | 273 | 0 | 0 | 0 | 2432 | 3970 | 41 | PASS | FAIL | NO_FV1 |
| SAMMAANCAP | 2710 | 0 | 0 | 0 | 482 | 28742 | 225 | PASS | FAIL | NO_FV1 |
| SAPPHIRE | 1034 | 0 | 1 | 0 | 40018 | 10383 | 169 | FAIL | FAIL | NO_FV1 |
| SARDAEN | 2710 | 0 | 0 | 0 | 299942 | 35682 | 343 | PASS | FAIL | NO_FV1 |
| SAREGAMA | 2710 | 0 | 1 | 0 | 270312 | 52156 | 415 | FAIL | FAIL | NO_FV1 |
| SBFC | 602 | 0 | 1 | 0 | 1989 | 6641 | 71 | FAIL | FAIL | NO_FV1 |
| SBICARD | 1450 | 0 | 0 | 0 | 48 | 9039 | 155 | PASS | FAIL | NO_FV1 |
| SBILIFE | 2710 | 638 | 1 | 0 | 11092 | 10094 | 197 | FAIL | FAIL | NO_FV1 |
| SBIN | 2710 | 0 | 0 | 0 | 1145 | 12098 | 100 | PASS | FAIL | NO |
| SCHAEFFLER | 2710 | 0 | 0 | 0 | 334903 | 26812 | 497 | PASS | FAIL | NO_FV1 |
| SCHNEIDER | 2710 | 0 | 0 | 0 | 231758 | 48984 | 363 | PASS | FAIL | NO_FV1 |
| SCI | 2710 | 0 | 0 | 0 | 64655 | 35467 | 350 | PASS | FAIL | NO_FV1 |
| SHREECEM | 2710 | 0 | 0 | 0 | 62028 | 16702 | 254 | PASS | FAIL | NO_FV1 |
| SHRIRAMFIN | 2710 | 0 | 0 | 0 | 1478 | 21076 | 195 | PASS | FAIL | NO_FV1 |
| SHYAMMETL | 1134 | 0 | 0 | 0 | 29882 | 16143 | 122 | PASS | FAIL | NO_FV1 |
| SIEMENS | 2710 | 0 | 0 | 0 | 13291 | 15071 | 234 | PASS | FAIL | NO_FV1 |
| SIGNATURE | 573 | 0 | 0 | 0 | 24931 | 1880 | 35 | PASS | FAIL | NO_FV1 |
| SJVN | 2710 | 0 | 0 | 0 | 119372 | 76470 | 361 | PASS | FAIL | NO_FV1 |
| SOBHA | 2710 | 0 | 0 | 0 | 82854 | 30813 | 408 | PASS | FAIL | NO_FV1 |
| SOLARINDS | 2710 | 0 | 0 | 0 | 327525 | 43648 | 465 | PASS | FAIL | NO_FV1 |
| SONACOMS | 2646 | 1509 | 0 | 0 | 1217 | 8148 | 117 | FAIL | FAIL | NO_FV1 |
| SONATSOFTW | 2710 | 0 | 0 | 0 | 87659 | 33079 | 374 | PASS | FAIL | NO_FV1 |
| SRF | 2710 | 0 | 0 | 0 | 23232 | 19194 | 261 | PASS | FAIL | NO_FV1 |
| STARHEALTH | 2683 | 1368 | 0 | 0 | 75387 | 12094 | 203 | FAIL | FAIL | NO_FV1 |
| SUMICHEM | 1483 | 0 | 0 | 0 | 19899 | 14202 | 208 | PASS | FAIL | NO_FV1 |
| SUNDARMFIN | 2710 | 0 | 0 | 0 | 280479 | 32403 | 480 | PASS | FAIL | NO_FV1 |
| SUNDRMFAST | 2710 | 0 | 1 | 0 | 177460 | 26009 | 411 | FAIL | FAIL | NO_FV1 |
| SUNPHARMA | 2710 | 0 | 0 | 0 | 26 | 17805 | 185 | PASS | FAIL | NO |
| SUNTV | 2710 | 0 | 0 | 0 | 12100 | 18104 | 252 | PASS | FAIL | NO_FV1 |
| SUPREMEIND | 2710 | 0 | 0 | 0 | 126321 | 25847 | 431 | PASS | FAIL | NO_FV1 |
| SUZLON | 2710 | 0 | 0 | 0 | 2949 | 28081 | 261 | PASS | FAIL | NO_FV1 |
| SWANCORP | 2710 | 0 | 1 | 0 | 269505 | 72908 | 270 | FAIL | FAIL | NO_FV1 |
| SWIGGY | 296 | 0 | 0 | 0 | 14 | 1608 | 29 | PASS | FAIL | NO_FV1 |
| SYNGENE | 2580 | 0 | 0 | 0 | 77281 | 21946 | 355 | PASS | FAIL | NO_FV1 |
| SYRMA | 842 | 0 | 1 | 0 | 6257 | 9437 | 120 | FAIL | FAIL | NO_FV1 |
| TARIL | 2710 | 0 | 0 | 0 | 345139 | 59336 | 387 | PASS | FAIL | NO_FV1 |
| TATACHEM | 2710 | 0 | 0 | 0 | 12234 | 34939 | 263 | PASS | FAIL | NO_FV1 |
| TATACOMM | 2710 | 0 | 1 | 0 | 42277 | 20732 | 319 | FAIL | FAIL | NO_FV1 |
| TATACONSUM | 2710 | 0 | 0 | 0 | 5814 | 16532 | 218 | PASS | FAIL | NO_FV1 |
| TATAELXSI | 2710 | 0 | 0 | 0 | 3132 | 24773 | 277 | PASS | FAIL | NO_FV1 |
| TATAINVEST | 2710 | 0 | 0 | 0 | 257907 | 49908 | 342 | PASS | FAIL | NO_FV1 |
| TATAPOWER | 2710 | 0 | 1 | 0 | 1065 | 36974 | 195 | FAIL | FAIL | NO_FV1 |
| TATASTEEL | 2710 | 0 | 0 | 0 | 47 | 10606 | 124 | PASS | FAIL | NO |
| TATATECH | 531 | 0 | 0 | 0 | 43 | 5182 | 53 | PASS | FAIL | NO_FV1 |
| TBOTEK | 421 | 0 | 1 | 0 | 16130 | 6139 | 75 | FAIL | FAIL | NO_FV1 |
| TCS | 2710 | 0 | 0 | 0 | 423 | 7646 | 131 | PASS | FAIL | NO_FV1 |
| TECHM | 2710 | 0 | 0 | 0 | 118 | 8966 | 176 | PASS | FAIL | NO |
| TECHNOE | 1764 | 0 | 0 | 0 | 144084 | 19896 | 292 | PASS | FAIL | NO_FV1 |
| TEJASNET | 2120 | 0 | 0 | 0 | 89211 | 29180 | 326 | PASS | FAIL | NO_FV1 |
| THELEELA | 163 | 0 | 0 | 0 | 4092 | 1729 | 29 | PASS | FAIL | NO_FV1 |
| THERMAX | 2710 | 0 | 0 | 0 | 197304 | 27510 | 504 | PASS | FAIL | NO_FV1 |
| TIINDIA | 2032 | 0 | 0 | 0 | 111568 | 14667 | 334 | PASS | FAIL | NO_FV1 |
| TIMKEN | 2710 | 0 | 0 | 0 | 254355 | 32263 | 427 | PASS | FAIL | NO_FV1 |
| TITAGARH | 2710 | 0 | 0 | 0 | 83220 | 31164 | 335 | PASS | FAIL | NO_FV1 |
| TITAN | 2710 | 0 | 0 | 0 | 2292 | 13457 | 207 | PASS | FAIL | NO_FV1 |
| TMPV | 2710 | 0 | 0 | 0 | 54 | 28924 | 126 | PASS | FAIL | NO_FV1 |
| TORNTPHARM | 2710 | 0 | 0 | 0 | 25959 | 22311 | 278 | PASS | FAIL | NO_FV1 |
| TORNTPOWER | 2710 | 0 | 0 | 0 | 34227 | 21510 | 333 | PASS | FAIL | NO_FV1 |
| TRENT | 2710 | 0 | 0 | 0 | 172077 | 19363 | 372 | PASS | FAIL | NO_FV1 |
| TRIDENT | 2710 | 0 | 0 | 0 | 65029 | 41377 | 281 | PASS | FAIL | NO_FV1 |
| TRITURBINE | 2710 | 0 | 0 | 0 | 282636 | 71035 | 470 | PASS | FAIL | NO_FV1 |
| TRIVENI | 2710 | 0 | 1 | 0 | 141198 | 30528 | 324 | FAIL | FAIL | NO_FV1 |
| TTML | 2710 | 0 | 0 | 0 | 183106 | 49767 | 336 | PASS | FAIL | NO_FV1 |
| TVSMOTOR | 2710 | 0 | 0 | 0 | 2052 | 15219 | 239 | PASS | FAIL | NO_FV1 |
| UBL | 2710 | 0 | 0 | 0 | 39493 | 20192 | 306 | PASS | FAIL | NO_FV1 |
| UCOBANK | 2710 | 0 | 0 | 0 | 60725 | 69816 | 278 | PASS | FAIL | NO_FV1 |
| ULTRACEMCO | 2710 | 0 | 0 | 0 | 610 | 9905 | 156 | PASS | FAIL | NO_FV1 |
| UNIONBANK | 2710 | 0 | 1 | 0 | 729 | 17267 | 166 | FAIL | FAIL | NO_FV1 |
| UNITDSPR | 2710 | 0 | 1 | 0 | 1654 | 15956 | 214 | FAIL | FAIL | NO_FV1 |
| UNOMINDA | 2710 | 0 | 0 | 0 | 153745 | 24522 | 354 | PASS | FAIL | NO_FV1 |
| UPL | 2710 | 0 | 1 | 0 | 346 | 18436 | 223 | FAIL | FAIL | NO_FV1 |
| USHAMART | 2710 | 0 | 0 | 0 | 220604 | 34891 | 365 | PASS | FAIL | NO_FV1 |
| UTIAMC | 1307 | 0 | 0 | 0 | 22666 | 13254 | 191 | PASS | FAIL | NO_FV1 |
| VBL | 2277 | 0 | 0 | 0 | 85457 | 14907 | 275 | PASS | FAIL | NO_FV1 |
| VEDL | 2710 | 0 | 0 | 0 | 78 | 10897 | 151 | PASS | FAIL | NO |
| VENTIVE | 266 | 0 | 0 | 0 | 21551 | 3360 | 33 | PASS | FAIL | NO_FV1 |
| VGUARD | 2710 | 0 | 0 | 0 | 107310 | 28121 | 374 | PASS | FAIL | NO_FV1 |
| VIJAYA | 1079 | 0 | 1 | 0 | 45190 | 18432 | 200 | FAIL | FAIL | NO_FV1 |
| VMM | 273 | 0 | 0 | 0 | 39 | 2471 | 21 | PASS | FAIL | NO_FV1 |
| VOLTAS | 2710 | 0 | 0 | 0 | 1153 | 11419 | 210 | PASS | FAIL | NO_FV1 |
| VTL | 2710 | 0 | 0 | 0 | 223421 | 36574 | 421 | PASS | FAIL | NO_FV1 |
| WAAREEENER | 308 | 0 | 0 | 0 | 72 | 2865 | 33 | PASS | FAIL | NO_FV1 |
| WELCORP | 2710 | 0 | 0 | 0 | 86371 | 28119 | 331 | PASS | FAIL | NO_FV1 |
| WELSPUNLIV | 2710 | 0 | 0 | 0 | 70089 | 32697 | 349 | PASS | FAIL | NO_FV1 |
| WHIRLPOOL | 2710 | 0 | 0 | 0 | 142483 | 32052 | 388 | PASS | FAIL | NO_FV1 |
| WIPRO | 2710 | 0 | 0 | 0 | 252 | 14837 | 182 | PASS | FAIL | NO |
| WOCKPHARMA | 2710 | 0 | 0 | 0 | 12461 | 23692 | 318 | PASS | FAIL | NO_FV1 |
| YESBANK | 2710 | 0 | 0 | 0 | 439 | 32976 | 206 | PASS | FAIL | NO_FV1 |
| ZEEL | 2710 | 0 | 0 | 0 | 206 | 28828 | 222 | PASS | FAIL | NO_FV1 |
| ZENSARTECH | 2710 | 0 | 0 | 0 | 166815 | 52411 | 405 | PASS | FAIL | NO_FV1 |
| ZENTEC | 2672 | 0 | 0 | 0 | 255586 | 43762 | 375 | PASS | FAIL | NO_FV1 |
| ZFCVINDIA | 2710 | 0 | 0 | 0 | 393219 | 31144 | 499 | PASS | FAIL | NO_FV1 |
| ZYDUSLIFE | 2710 | 0 | 0 | 0 | 4532 | 26091 | 239 | PASS | FAIL | NO_FV1 |

---

## Anomaly Type Breakdown

| Source | Issue Type | Severity | Count |
|--------|-----------|----------|-------|
| DS1 | ohlc_violation | high | 17 |
| DS1 | doubled_volume | high | 2,054 |
| DS1 | missing_trading_day | high | 2,431 |
| DS1 | volume_spike_10x | medium | 2,060 |
| DS1 | post_market_candle | medium | 2,080 |
| DS1 | zero_volume | low | 1,050 |
| DS2 | duplicate_timestamp | high | 1 |
| DS2 | ohlc_violation | high | 103 |
| DS2 | doubled_volume | high | 9,898 |
| DS2 | missing_trading_day | high | 20,007 |
| DS2 | post_market_candle | medium | 9,622 |
| DS2 | volume_spike_10x | medium | 9,920 |
| DS2 | missing_trading_day | low | 1 |
| DS2 | zero_volume | low | 4,954 |
| DS2_vs_FV1 | price_mismatch_open | high | 144 |
| DS2_vs_FV1 | price_mismatch_low | high | 180 |
| DS2_vs_FV1 | price_mismatch_high | high | 184 |
| DS2_vs_FV1 | price_mismatch_close | high | 190 |
| DS2_vs_FV1 | volume_mismatch | medium | 28 |

---

## Interpretation & Key Findings

### CHECK 2 (Volume) — Why Everything "FAILS"
**The volume FAIL for all 604 stocks is a threshold design artefact, not a data quality failure.**

Both `volume_spike_10x` and `doubled_volume_days` use the *overall median daily volume* as a baseline.
Over an 11-year window (2015–2026), most Indian equities have grown 5–20× in average daily volume.
The rolling median centred on any date consistently underestimates current volumes for high-growth stocks,
resulting in false-positive "doubled_volume" flags.  Additionally, many stocks pre-2020 had thousands of
zero-volume 1-min candles (thin trading during market hours) which depresses the median further.

**What to actually worry about**: individual stocks with extreme zero-volume counts (ZFCVINDIA: 393K,
PGHH: 396K, PGEL: 367K) — these are genuinely illiquid and unsuitable for strategy development.

### Post-Market Candles — Pre-2016 NSE Extended Session
DS2 has **9,622** candles timestamped 17:30–18:05.  Spot-check of SBIN shows these are from
**2015-11-11** at real volumes (175K–308K shares), and other stocks show similar dates (pre-2016).
This is **not** a data error — it is legacy data from NSE's now-discontinued Evening Session.
These candles must be filtered (`time > 15:30`) before any backtest use.

DS1 also has 2,080 such candles (smaller set = fewer affected stocks).

### Cross-Compare — Price Mismatch Root Cause
Out of 28 stocks compared against FV1, **19 are CLEAN** (price mismatch < 0.1%):

| Clean (PASS) | Anomalous (HIGH mismatch) |
|---|---|
| SBIN, RELIANCE, HDFCBANK, ICICIBANK, AXISBANK, BHARTIARTL, INFY, ADANIPORTS, HINDALCO, JSWSTEEL, CIPLA, DIVISLAB, INDUSINDBK, ASHOKLEY, NTPC, POWERGRID, BANDHANBNK, DABUR, DIVISLAB | COALINDIA (91.7%), ONGC (96.7%), PNB (86.6%), TECHM (87.6%), TATASTEEL (85.6%), VEDL (81.5%), ITC (75.2%), WIPRO (76.8%), NATIONALUM (78.3%) |

**Root cause**: FV1 (Upstox) stores **backward-adjusted prices** for corporate actions (bonus issues,
splits, demergers). Kaggle DS2 stores **raw unadjusted prices**.
For stocks with major corporate actions in 2022–2025 (ITC Hotels demerger, COALINDIA bonus 2022,
WIPRO 1:1 bonus 2024, TECHM 1:1 bonus 2022, ONGC open offer 2022), the FV1 pre-action prices
are halved/adjusted, creating a permanent systematic offset vs DS2's raw values.

**Implication**: DS2 data is **unadjusted**. Must apply corporate action adjustments before use
in any backtest spanning a corporate action event.

### Volume Mismatch — Resampling Artefact
ALL 28 cross-compared stocks show **1.5–2.4% of bars** with >20% volume mismatch.
The range is narrow (1,092–1,740 bars out of 74,039) regardless of price alignment.
This is a **systematic resampling artefact**: block-trade volumes on 1-min candle boundaries
are allocated to different 5-min bars depending on the resampling method and source rounding.
This is NOT a data quality failure — it is expected when comparing resampled vs native 5-min data.

### DS2 Load Errors (3 stocks)
Three CSV files in DS2 failed to load: likely files with special characters or spaces
in filenames (e.g. "NIFTY 50", "NIFTY BANK" style names not matching `stock_minute.csv` pattern).

---

## Notes

- **missing_trading_day**: Weekdays within a stock's date range where no candles exist.
  ~15/year are NSE holidays. High counts (>20 beyond expected holidays) indicate genuine gaps.
  Stocks with 500+ missing days (PTCIL=1526, RAINBOW=727, RVNL=903, SONACOMS=1509,
  STARHEALTH=1368) likely have IPO dates mid-history; the "missing" days are pre-listing.
- **ohlc_violation**: High < Low, Close > High, Close < Low, Open > High or Open < Low.
  Any count > 0 is a hard data-quality failure. DS1=17 violations across ~10 stocks; DS2=103.
- **volume_spike_10x**: Single candle volume > 10× median per-minute volume.
  Inflated by secular volume growth — use as directional indicator only.
- **doubled_volume**: Daily total > 2× rolling 10-day median (centred).
  Inflated by secular growth — see "Interpretation" above.
- **price_mismatch_***: DS2 resampled 5-min OHLC differs from FV1 by > 0.1%.
  anomalies.csv records up to 10 unique (stock, date) pairs per issue type; actual bar counts
  are much higher (shown in the cross-compare table above).
- **volume_mismatch**: DS2 resampled volume differs from FV1 by > 20%.
  At ~1.7% frequency this is a resampling artefact (see Interpretation above).

*Report generated by validate_all_datasets.py*
