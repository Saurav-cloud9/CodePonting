import pandas as pd


class MABaselineV3:
    """
    v3 = SHORT wick-only — mirror of v1.
    Signal: high >= MA20, open < MA20, close < MA20 (single bar rejection)
    Entry: SHORT at next bar open
    SL:    entry + SL_MULT  * ATR14  (above entry)
    TP:   entry - TP_MULT * ATR14  (below entry)
    PnL:   entry - exit_px  (positive = profit for short)
    """
    SL_MULT  = 2.0
    TP_MULT = 3.5
    EOD_HOUR = 15

    def run(self, df):
        hours  = df['hour'].values
        dates  = df['date'].values
        highs  = df['high'].values
        opens  = df['open'].values
        closes = df['close'].values
        lows   = df['low'].values
        ma20s  = df['ma20'].values
        atrs   = df['atr14'].values

        trades = []
        i = 0
        while i < len(df):
            if pd.isna(ma20s[i]) or pd.isna(atrs[i]):
                i += 1; continue
            if hours[i] >= self.EOD_HOUR:
                i += 1; continue

            if highs[i] >= ma20s[i] and opens[i] < ma20s[i] and closes[i] < ma20s[i]:
                signal_date = dates[i]
                atr = atrs[i]
                entry_idx = i + 1
                if entry_idx >= len(df):
                    i += 1; continue
                if dates[entry_idx] != signal_date:
                    i += 1; continue

                entry = opens[entry_idx]
                sl  = entry + self.SL_MULT  * atr
                tp = entry - self.TP_MULT * atr

                for k in range(entry_idx, len(df)):
                    if hours[k] >= self.EOD_HOUR or dates[k] != signal_date:
                        pnl = entry - opens[k]
                        outcome = 'EOD+' if pnl > 0 else 'EOD-'; break
                    if lows[k]  <= tp:
                        pnl = entry - tp; outcome = 'W'; break
                    if highs[k] >= sl:
                        pnl = entry - sl;  outcome = 'L'; break

                trades.append({'pnl': pnl, 'outcome': outcome, 'exit_dt': df.iloc[k]['datetime']})
                i = k + 1
            else:
                i += 1
        return trades
