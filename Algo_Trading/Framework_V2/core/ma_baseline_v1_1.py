import pandas as pd


class MABaselineV1_1:
    """
    v1.1 = v1 (wick-only touch) + Above VWAP + Below EMA100 at touch bar.
    Both filters applied at entry (filter-at-entry, realistic simulation).
    """
    MA_COL   = 'ma20'
    SL_MULT  = 2.5
    TP_MULT = 4.5
    EOD_HOUR = 15
    EMA_SPAN = 100

    @classmethod
    def prepare(cls, df):
        df = df.copy()
        df[f'ema{cls.EMA_SPAN}'] = df['close'].ewm(span=cls.EMA_SPAN, adjust=False).mean()
        df['tp']      = (df['high'] + df['low'] + df['close']) / 3
        df['cum_tpv'] = df.groupby('date').apply(
            lambda g: (g['tp'] * g['volume']).cumsum(), include_groups=False
        ).reset_index(level=0, drop=True)
        df['cum_vol'] = df.groupby('date')['volume'].cumsum()
        df['vwap']    = df['cum_tpv'] / df['cum_vol']
        return df

    def run(self, df):
        ema_col = f'ema{self.EMA_SPAN}'
        trades = []
        i = 0
        while i < len(df):
            row = df.iloc[i]
            if pd.isna(row['ma20']) or pd.isna(row['atr14']) or pd.isna(row[ema_col]):
                i += 1; continue

            above_vwap  = row['close'] >= row['vwap']
            below_ema   = row['close'] <  row[ema_col]

            if (row['low'] <= row['ma20'] and row['open'] > row['ma20']
                    and row['close'] > row['ma20']
                    and above_vwap and below_ema):
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
