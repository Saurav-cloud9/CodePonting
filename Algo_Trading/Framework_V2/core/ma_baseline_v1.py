import pandas as pd


class MABaselineV1:
    """
    v1 change vs baseline: touch requires body above MA20 (wick-only touch).
    Excludes body-touch, body-cross, and gap-down touch types.
    """
    MA_COL   = 'ma20'
    SL_MULT  = 2.5
    TP_MULT = 4.5
    EOD_HOUR = 15

    def run(self, df):
        trades = []
        i = 0
        while i < len(df):
            row = df.iloc[i]
            if pd.isna(row['ma20']) or pd.isna(row['atr14']):
                i += 1; continue
            if row['low'] <= row['ma20'] and row['open'] > row['ma20'] and row['close'] > row['ma20']:
                if row['hour'] >= self.EOD_HOUR:
                    i += 1; continue
                touch_date = row['date']
                atr = row['atr14']
                entry_idx = i + 1
                if entry_idx >= len(df): i += 1; continue
                entry_bar = df.iloc[entry_idx]
                if entry_bar['date'] != touch_date:
                    i += 1; continue
                entry = entry_bar['open']
                sl  = entry - self.SL_MULT  * atr
                tp = entry + self.TP_MULT * atr
                for k in range(entry_idx, len(df)):
                    k_bar = df.iloc[k]
                    if k_bar['hour'] >= self.EOD_HOUR:
                        pnl = k_bar['open'] - entry
                        outcome = 'EOD+' if pnl > 0 else 'EOD-'; break
                    if k_bar['high'] >= tp:
                        pnl = tp - entry; outcome = 'W'; break
                    if k_bar['low']  <= sl:
                        pnl = sl  - entry; outcome = 'L'; break
                trades.append({'pnl': pnl, 'outcome': outcome, 'exit_dt': k_bar['datetime']})
                i = k + 1
            else:
                i += 1
        return trades
