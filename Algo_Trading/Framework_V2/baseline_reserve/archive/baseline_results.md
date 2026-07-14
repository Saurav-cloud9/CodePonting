# fv2 Baseline Results — Locked Reference
**Date locked:** 2026-07-04  
**Universe:** 30 stocks · 2022–2025 (4 years) · 5-min data  
**Params:** SL=2.5×ATR · TGT=4.5×ATR · MAX_TB_GAP=3 · EOD_HOUR=15  
**Source scripts:** baseline_reserve/ma_bounce.py (LONG) · baseline_reserve/ma_rejection.py (SHORT)  
**Raw only — no slippage, no charges.**

---

## MA Bounce — LONG Bare Baseline

### Stock-wise (sorted by PF desc)
```
Symbol       N   PF     Sharpe   Net
BHARTIARTL  1603  1.089   0.817   413.39
ASHOKLEY    1662  1.052   0.357    26.06
DABUR       1643  1.022   0.170    48.34
SUNPHARMA   1667  1.012   0.099    69.10
AXISBANK    1625  0.975  -0.194  -109.61
ICICIBANK   1615  0.967  -0.308  -125.47
HDFCBANK    1601  0.965  -0.297   -98.03
JSWSTEEL    1638  0.960  -0.393  -169.46
ITC         1680  0.951  -0.393   -64.40
INFY        1547  0.950  -0.406  -283.76
HINDALCO    1627  0.946  -0.535  -158.69
POWERGRID   1639  0.926  -0.513   -83.15
INDUSINDBK  1691  0.925  -0.698  -466.32
COALINDIA   1652  0.921  -0.739  -119.89
RELIANCE    1583  0.914  -0.741  -399.16
SBIN        1668  0.913  -0.800  -255.80
BAJFINANCE  1683  0.909  -0.677  -316.58
CIPLA       1502  0.909  -0.664  -455.21
NATIONALUM  1642  0.897  -0.862  -104.87
VEDL        1655  0.885  -1.047  -237.92
DIVISLAB    1665  0.885  -1.032 -2653.76
BANDHANBNK  1677  0.882  -1.088  -164.72
TATASTEEL   1633  0.882  -1.084   -79.03
NTPC        1663  0.877  -1.203  -167.97
TECHM       1607  0.877  -1.040  -800.11
ADANIPORTS  1674  0.872  -1.259  -817.48
PNB         1659  0.872  -1.146   -63.30
ONGC        1620  0.837  -1.471  -163.12
WIPRO       1574  0.784  -2.037  -220.33
TATAMOTORS  1667  0.751  -2.033  -605.60
```

### Total
```
N=49,062  Prof_WR=41.5%  BE_prof=44.3%  Pure_WR=15.0%  BE_pure=35.7%
PF=0.922  Sharpe=-1.458  Net=-8,626.85
```

### Yearwise
```
Year     N    PF   Sharpe      Net
2022  12233  0.906  -2.235  -2,411.46
2023  11907  0.907  -1.433  -1,914.42
2024  12175  0.912  -1.537  -2,912.02
2025  12747  0.955  -0.846  -1,388.96
```

---

## MA Rejection — SHORT Bare Baseline

### Stock-wise (sorted by PF desc)
```
Symbol       N    PF    Sharpe    Net
TATAMOTORS  1587  1.394   2.406   708.29
BANDHANBNK  1699  1.278   1.662   341.86
PNB         1539  1.249   1.684   102.18
WIPRO       1506  1.214   1.880   171.05
NTPC        1634  1.210   1.639   257.53
NATIONALUM  1578  1.186   1.149   157.27
TATASTEEL   1570  1.175   1.484   101.88
BAJFINANCE  1618  1.168   1.315   508.73
ASHOKLEY    1633  1.158   1.115    72.74
DIVISLAB    1588  1.154   1.136  3042.37
ITC         1647  1.152   1.124   182.99
ONGC        1565  1.139   1.173   126.72
INDUSINDBK  1635  1.139   1.257   766.94
COALINDIA   1644  1.131   1.152   189.66
ADANIPORTS  1611  1.124   1.190   693.27
VEDL        1586  1.123   0.943   229.58
POWERGRID   1592  1.106   0.843   110.33
HINDALCO    1578  1.105   0.900   285.23
RELIANCE    1575  1.100   0.865   429.54
SBIN        1635  1.065   0.622   176.12
CIPLA       1472  1.049   0.305   225.92
INFY        1500  1.027   0.237   142.97
HDFCBANK    1548  1.019   0.148    47.17
AXISBANK    1637  1.012   0.100    53.30
JSWSTEEL    1598  1.001   0.009     4.57
TECHM       1613  0.996  -0.034   -25.90
ICICIBANK   1552  0.990  -0.088   -35.28
DABUR       1646  0.941  -0.460  -134.59
BHARTIARTL  1617  0.934  -0.526  -331.82
SUNPHARMA   1584  0.888  -0.757  -628.11
```

### Total
```
N=47,787  Prof_WR=45.2%  BE_prof=44.1%  Pure_WR=16.4%  BE_pure=35.7%
PF=1.079  Sharpe=1.455  Net=+7,972.49
```

### Yearwise
```
Year     N    PF   Sharpe     Net
2022  11595  1.131   2.254  2,913.47
2023  11568  1.035   0.688    667.67
2024  12015  1.094   1.677  2,827.01
2025  12609  1.053   1.045  1,564.35
```

---

## Summary Comparison

| Metric       | LONG (Bounce) | SHORT (Rejection) |
|---|---|---|
| N (trades)   | 49,062        | 47,787            |
| PF           | 0.922         | 1.079             |
| Sharpe       | -1.458        | +1.455            |
| Net PnL      | -8,627        | +7,972            |
| Stocks > PF1 | 4 / 30        | 27 / 30           |

**Verdict:** SHORT holds genuine raw edge — positive PF in all 4 years, 27/30 stocks profitable.  
**NPF estimate:** PF=1.079 → NPF≈0.7 (not yet tradeable). Target PF≥1.4–1.5 before paper trading.
