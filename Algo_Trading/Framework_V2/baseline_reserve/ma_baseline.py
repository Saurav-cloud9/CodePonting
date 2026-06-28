import pandas as pd


class MABaseline:
    MA_COL     = 'ma20'
    SL_MULT    = 2.5
    TGT_MULT   = 4.5
    MAX_TB_GAP = 3
    EOD_HOUR   = 15

    def run(self, df):
        trades = []
        i = 0
        while i < len(df):
            row = df.iloc[i]
            if pd.isna(row['ma20']) or pd.isna(row['atr14']):
                i += 1; continue
            if row['low'] <= row['ma20']:
                if row['hour'] >= self.EOD_HOUR:
                    i += 1; continue
                touch_date = row['date']
                atr = row['atr14']
                bounce_bar = None
                for j in range(i, i + self.MAX_TB_GAP + 1):
                    if j >= len(df): break
                    b = df.iloc[j]
                    if b['date'] != touch_date: break
                    if b['hour'] >= self.EOD_HOUR: break
                    if b['close'] > b['ma20']:
                        bounce_bar = b; break
                if bounce_bar is None:
                    i += 1; continue
                entry_idx = j + 1
                if entry_idx >= len(df): i += 1; continue
                entry_bar = df.iloc[entry_idx]
                if entry_bar['date'] != touch_date:
                    i += 1; continue
                entry = entry_bar['open']
                sl  = entry - self.SL_MULT  * atr
                tgt = entry + self.TGT_MULT * atr
                for k in range(entry_idx, len(df)):
                    k_bar = df.iloc[k]
                    if k_bar['hour'] >= self.EOD_HOUR:
                        pnl = k_bar['open'] - entry
                        outcome = 'EOD+' if pnl > 0 else 'EOD-'; break
                    if k_bar['high'] >= tgt:
                        pnl = tgt - entry; outcome = 'W'; break
                    if k_bar['low']  <= sl:
                        pnl = sl  - entry; outcome = 'L'; break
                trades.append({'pnl': pnl, 'outcome': outcome, 'exit_dt': k_bar['datetime']})
                i = k + 1
            else:
                i += 1
        return trades