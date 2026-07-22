The fix for fv2

**Measure:** slope = (MA20[touch] - MA20[touch - 5]) / MA20[touch] x 100  
**Threshold:** rising > +0.05% | flat = +/-0.05% | falling < -0.05%  
**Lookback:** 5 candles = 25 minutes of MA direction  
**Rule:** fv2 only enters when slope > +0.05% — everything else is skipped