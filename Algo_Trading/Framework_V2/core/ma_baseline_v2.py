import pandas as pd


class MABaselineV2:
    """
    v2 = Bare SHORT baseline — mirror of v0.
    Touch:  high >= MA20 (any bar touching MA20 from below)
    Search: MAX_TB_GAP bars for rejection bar where close < MA20
    Entry:  SHORT at next bar open after rejection bar
    SL:     entry + SL_MULT  * ATR14  (above entry)
    TP:    entry - TP_MULT * ATR14  (below entry)
    PnL:    entry - exit_px  (positive = profit for short)
    """
    SL_MULT    = 2.5
    TP_MULT   = 4.5
    MAX_TB_GAP = 3
    EOD_HOUR   = 15

    def run(self, df):
        trades = []
        i = 0
        while i < len(df):
            row = df.iloc[i]
            if pd.isna(row['ma20']) or pd.isna(row['atr14']):
                i += 1; continue
            if row['high'] >= row['ma20']:
                if row['hour'] >= self.EOD_HOUR:
                    i += 1; continue
                touch_date = row['date']
                atr = row['atr14']
                rejection_bar = None
                for j in range(i, i + self.MAX_TB_GAP + 1):
                    if j >= len(df): break
                    b = df.iloc[j]
                    if b['date'] != touch_date: break
                    if b['hour'] >= self.EOD_HOUR: break
                    if b['close'] < b['ma20']:
                        rejection_bar = b; break
                if rejection_bar is None:
                    i += 1; continue
                entry_idx = j + 1
                if entry_idx >= len(df): i += 1; continue
                entry_bar = df.iloc[entry_idx]
                if entry_bar['date'] != touch_date:
                    i += 1; continue
                entry = entry_bar['open']
                sl  = entry + self.SL_MULT  * atr
                tp = entry - self.TP_MULT * atr
                for k in range(entry_idx, len(df)):
                    k_bar = df.iloc[k]
                    if k_bar['hour'] >= self.EOD_HOUR or k_bar['date'] != touch_date:
                        pnl = entry - k_bar['open']
                        outcome = 'EOD+' if pnl > 0 else 'EOD-'; break
                    if k_bar['low']  <= tp:
                        pnl = entry - tp; outcome = 'W'; break
                    if k_bar['high'] >= sl:
                        pnl = entry - sl;  outcome = 'L'; break
                trades.append({'pnl': pnl, 'outcome': outcome, 'exit_dt': k_bar['datetime']})
                i = k + 1
            else:
                i += 1
        return trades
