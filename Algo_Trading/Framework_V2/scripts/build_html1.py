"""
Build fv2_signal_viewer.html — candlestick chart viewer for all 30 fv2 stocks.
Reads all 30 stock CSVs, generates per-day candle + signal data, embeds as JS.

Data format per stock:
  "d": ["2022-01-03", ...],
  "c": {"2022-01-03": "o,h,l,c,ma,slope|...", ...},
  "s": {"2022-01-03": [[touch_idx, bounce_idx, entry_idx, slope, "R"/"L"/"F", pnl, win], ...], ...},
  pnl/win: per-signal forward simulation (2.5×ATR14 SL, 4.5×ATR14 target, EOD exit) — all signals covered
  "st": {"total": N, "R": N, "L": N, "F": N}

Signal detection (H1 style — counts all bounce events, not just non-overlapping trades):
  - touch:  low <= ma20
  - bounce: close > ma20 AND vol >= 1.2 * vol_ma20 (at touch or next 3 candles, same day)
  - entry:  candle after bounce (None if bounce is last candle of day)
  - advance: i = bounce_idx + 2 after bounce (skip entry candle); i += 1 if no bounce

⚠️  Output file is large (~80-90 MB). This is expected for 30 stocks of 5-min OHLC data.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────────
CSV_DIR = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/data/historical/csv/intraday_5min')
DS3_DIR = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V1/data/historical/intraday_5min_DS3')
OUT     = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_h1_signal_viewer.html')

STOCKS = [
    'ADANIPORTS', 'ASHOKLEY', 'AXISBANK', 'BAJFINANCE', 'BANDHANBNK',
    'BHARTIARTL', 'CIPLA', 'COALINDIA', 'DABUR', 'DIVISLAB',
    'HDFCBANK', 'HINDALCO', 'ICICIBANK', 'INDUSINDBK', 'INFY',
    'ITC', 'JSWSTEEL', 'NATIONALUM', 'NTPC', 'ONGC',
    'PNB', 'POWERGRID', 'RELIANCE', 'SBIN', 'SUNPHARMA',
    'TATAMOTORS', 'TATASTEEL', 'TECHM', 'VEDL', 'WIPRO',
]

DATE_START = '2022-01-01'
DATE_END   = '2025-12-31'
DEFAULT_STOCK = 'TATAMOTORS'
DEFAULT_DAY   = None  # always open on earliest available date


# ── Signal + candle extraction ─────────────────────────────────────────────────

def build_stock_data(stock: str) -> dict:
    csv = CSV_DIR / f'{stock}_5min.csv'
    df  = pd.read_csv(csv)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)

    # vol_ma20: use DS3 parquet for warmup (full 2015+ history) for DS3 stocks.
    # BAJFINANCE has no pre-2022 parquet — rolling(20) from CSV start (19-candle NaN accepted).
    # If CSV already has vol_ma20 (e.g. TATAMOTORS after backtest export), use it directly.
    if 'vol_ma20' not in df.columns:
        ds3_parquet = DS3_DIR / f'{stock}.parquet'
        if ds3_parquet.exists():
            ds3 = pd.read_parquet(ds3_parquet, columns=['datetime', 'volume'])
            ds3['datetime'] = pd.to_datetime(ds3['datetime'])
            ds3 = ds3.sort_values('datetime').reset_index(drop=True)
            ds3['vol_ma20'] = ds3['volume'].rolling(20).mean()
            ds3 = ds3[ds3['datetime'] >= DATE_START][['datetime', 'vol_ma20']].reset_index(drop=True)
            df = df.merge(ds3, on='datetime', how='left')
        else:
            df['vol_ma20'] = df['volume'].rolling(20).mean()

    # ATR14: True Range rolling mean (global, no per-day reset)
    prev_close = df['close'].shift(1)
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - prev_close).abs(),
        (df['low']  - prev_close).abs(),
    ], axis=1).max(axis=1)
    df['atr14'] = tr.rolling(14).mean()

    # Slope: 5-candle change in MA20 (global context, not per-day)
    df['slope'] = (df['ma20'] - df['ma20'].shift(5)) / df['ma20'] * 100

    # Filter to output range
    mask = (df['datetime'] >= DATE_START) & (df['datetime'] <= DATE_END)
    df = df[mask].reset_index(drop=True)
    df['_date'] = df['datetime'].dt.strftime('%Y-%m-%d')

    dates_list   = sorted(df['_date'].unique().tolist())
    candles_dict = {}
    signals_dict = {}
    stats = {'total': 0, 'R': 0, 'L': 0, 'F': 0}

    for date in dates_list:
        day = df[df['_date'] == date].reset_index(drop=True)
        n   = len(day)

        # ── Candle strings: "o,h,l,c,ma,slope|..." ────────────────────────────
        parts = []
        for _, row in day.iterrows():
            ma_str  = f"{row['ma20']:.2f}"  if pd.notna(row['ma20'])  else ''
            sl_str  = f"{row['slope']:.4f}" if pd.notna(row['slope']) else ''
            atr_str = f"{row['atr14']:.2f}" if pd.notna(row['atr14']) else ''
            vr_str  = f"{row['volume'] / row['vol_ma20']:.2f}" if pd.notna(row['vol_ma20']) and row['vol_ma20'] > 0 else ''
            vol_str = f"{int(row['volume'])}"
            parts.append(
                f"{row['open']:.2f},{row['high']:.2f},{row['low']:.2f},"
                f"{row['close']:.2f},{ma_str},{sl_str},{atr_str},{vr_str},{vol_str}"
            )
        candles_dict[date] = '|'.join(parts)

        # ── Signal detection ───────────────────────────────────────────────────
        day_signals = []
        i = 0
        while i < n:
            row = day.iloc[i]
            if pd.isna(row['ma20']) or pd.isna(row['vol_ma20']) or pd.isna(row['atr14']):
                i += 1
                continue
            if row['low'] > row['ma20']:
                i += 1
                continue

            touch_idx = i
            slope_val = row['slope'] if pd.notna(row['slope']) else 0.0
            cat = 'R' if slope_val > 0.05 else ('F' if slope_val < -0.05 else 'L')

            # Find bounce: close > ma20 AND vol >= 1.2 * vol_ma20
            # (at touch candle or within next 3 candles, same day)
            bounce_idx = None
            for j in range(touch_idx, min(touch_idx + 4, n)):
                b = day.iloc[j]
                if pd.notna(b['ma20']) and b['close'] > b['ma20'] and \
                   pd.notna(b['vol_ma20']) and b['volume'] >= 1.2 * b['vol_ma20']:
                    bounce_idx = j
                    break

            if bounce_idx is not None:
                entry_idx = bounce_idx + 1 if bounce_idx + 1 < n else None
                pnl, win, exit_idx_val, sl_val, tgt_val, exit_reason = None, None, None, None, None, None
                if entry_idx is not None:
                    entry_price = day.iloc[entry_idx]['open']
                    atr_val     = day.iloc[touch_idx]['atr14']
                    if pd.notna(entry_price) and pd.notna(atr_val) and atr_val > 0:
                        sl     = entry_price - 2.5 * atr_val
                        target = entry_price + 4.5 * atr_val
                        exit_price = day.iloc[-1]['close']  # default: EOD
                        exit_reason = 'E'  # E=EOD, T=target, S=SL
                        for ki in range(entry_idx, n):
                            krow = day.iloc[ki]
                            if krow['high'] >= target:
                                exit_price = target; exit_reason = 'T'; break
                            if krow['low'] <= sl:
                                exit_price = sl; exit_reason = 'S'; break
                        pnl          = round(float(exit_price - entry_price), 2)
                        win          = 1 if exit_reason == 'T' else 0
                        exit_idx_val = int(ki)
                        sl_val       = round(float(sl), 2)
                        tgt_val      = round(float(target), 2)
                day_signals.append([
                    touch_idx,
                    bounce_idx,
                    entry_idx,
                    round(float(slope_val), 4),
                    cat,
                    pnl,
                    win,
                    exit_idx_val,   # s[7]
                    sl_val,         # s[8]
                    tgt_val,        # s[9]
                    exit_reason,    # s[10]: 'T'=target, 'S'=SL, 'E'=EOD
                ])
                stats['total'] += 1
                stats[cat] += 1
                i = bounce_idx + 2   # skip past entry candle — entry can't also be next touch
            else:
                i += 1

        if day_signals:
            signals_dict[date] = day_signals

    total_sigs = stats['total']
    r_pct = stats['R'] / total_sigs * 100 if total_sigs else 0
    print(f"  {stock:15s}  days={len(dates_list):4d}  signals={total_sigs:5d}"
          f"  R={stats['R']:4d}({r_pct:.0f}%)  L={stats['L']:4d}  F={stats['F']:4d}")

    return {
        'd':  dates_list,
        'c':  candles_dict,
        's':  signals_dict,
        'st': stats,
    }


# ── Build all stocks ───────────────────────────────────────────────────────────

print('Building H1 data for 30 stocks...')
all_data = {}
for stock in STOCKS:
    csv = CSV_DIR / f'{stock}_5min.csv'
    if not csv.exists():
        print(f'  {stock:15s}  SKIP — CSV not found')
        continue
    all_data[stock] = build_stock_data(stock)

print(f'\nAll stocks processed. Serialising JS data...')
all_data_js = json.dumps(all_data, separators=(',', ':'))
print(f'JS data size: {len(all_data_js)/1e6:.1f} MB')


# ── CSS (preserved exactly from original H1) ──────────────────────────────────

CSS = """@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0f1117;--bg2:#181b25;--bg3:#1e2230;--fg:#c8cdd8;--fg2:#8891a5;--fg3:#555d72;--green:#22c55e;--red:#ef4444;--amber:#f59e0b;--teal:#14b8a6;--blue:#3b82f6;--purple:#a78bfa;--border:#2a2e3d}
body{background:var(--bg);color:var(--fg);font-family:'JetBrains Mono',monospace;font-size:13px;overflow:hidden;height:100vh}
.layout{display:grid;grid-template-columns:1fr 240px;grid-template-rows:48px 1fr;height:100vh}
.topbar{grid-column:1/-1;background:var(--bg2);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 16px;gap:12px;flex-wrap:nowrap}
.topbar h1{font-size:14px;font-weight:500;color:var(--fg);letter-spacing:-0.3px;white-space:nowrap}
.topbar .stock{color:var(--amber);font-weight:700}
.stock-sel{background:var(--bg3);border:1px solid var(--border);color:var(--fg);font-family:inherit;font-size:12px;padding:4px 8px;border-radius:4px;cursor:pointer;outline:none;height:28px}
.stock-sel:focus{border-color:#4a4d68}
.nav-btn{background:var(--bg3);border:1px solid var(--border);color:var(--fg2);padding:4px 10px;border-radius:4px;cursor:pointer;font-family:inherit;font-size:12px;transition:all .15s;white-space:nowrap}
.nav-btn:hover{background:var(--border);color:var(--fg)}
.date-display{color:var(--fg);font-weight:500;min-width:100px;text-align:center}
.jump-wrap{display:flex;align-items:center;gap:4px}
.jump-sel{background:var(--bg3);border:1px solid var(--border);color:var(--fg2);padding:3px 6px;border-radius:4px;cursor:pointer;font-family:inherit;font-size:12px;outline:none}
.jump-sel:hover{background:var(--border);color:var(--fg)}
.toggle-wrap{display:flex;align-items:center;gap:8px;margin-left:auto;flex-shrink:0}
.toggle{position:relative;width:36px;height:20px;background:var(--bg3);border-radius:10px;cursor:pointer;border:1px solid var(--border);transition:all .2s}
.toggle.on{background:#1a3a2a;border-color:var(--green)}
.toggle .knob{position:absolute;top:2px;left:2px;width:14px;height:14px;background:var(--fg3);border-radius:50%;transition:all .2s}
.toggle.on .knob{left:18px;background:var(--green)}
.toggle-label{font-size:11px;color:var(--fg2)}
.chart-area{background:var(--bg);overflow:hidden;position:relative;display:flex;flex-direction:column}
canvas{display:block;width:100%}
#chart{flex:1}
#volCanvas{height:70px;flex-shrink:0;border-top:1px solid var(--border)}
.sidebar{background:var(--bg2);border-left:1px solid var(--border);padding:16px;overflow-y:auto}
.sidebar h2{font-size:11px;font-weight:500;color:var(--fg3);text-transform:uppercase;letter-spacing:1px;margin:0 0 12px}
.stat-row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border)}
.stat-row:last-child{border:none}
.stat-label{color:var(--fg2);font-size:12px}
.stat-val{font-weight:700;font-size:12px}
.stat-val.green{color:var(--green)}
.stat-val.red{color:var(--red)}
.stat-val.amber{color:var(--amber)}
.stat-val.gray{color:var(--fg3)}
.section{margin:0 0 20px}
.legend{margin:16px 0 0}
.legend-item{display:flex;align-items:center;gap:8px;padding:4px 0;font-size:11px;color:var(--fg2)}
.legend-dot{width:10px;height:10px;border-radius:2px}
.signal-list{margin:8px 0 0;max-height:300px;overflow-y:auto}
.signal-item{padding:6px 8px;border-radius:4px;margin:2px 0;font-size:11px;cursor:pointer;transition:background .15s}
.signal-item:hover{background:var(--bg3)}
.signal-item .time{color:var(--fg)}
.sig-detail{margin-top:10px;padding:8px;background:var(--bg3);border-radius:6px;font-size:11px;display:none}
.sig-detail.visible{display:block}
.sig-detail .sd-title{font-size:10px;font-weight:500;color:var(--fg3);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}
.sig-detail .sd-row{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid var(--border)}
.sig-detail .sd-row:last-child{border:none}
.sig-detail .sd-label{color:var(--fg3)}
.sig-detail .sd-val{font-weight:500}
.signal-item .slope{margin-left:auto;font-size:10px}
.signal-item.rising .slope{color:var(--green)}
.signal-item.flat .slope{color:var(--fg3)}
.signal-item.falling .slope{color:var(--red)}
.signal-item.filtered{opacity:0.3}
.signal-item.selected{background:var(--bg3);border-left:2px solid var(--amber);padding-left:6px}
.tooltip{position:absolute;background:var(--bg2);border:1px solid var(--border);border-radius:6px;padding:8px 10px;font-size:11px;pointer-events:none;z-index:10;display:none;min-width:140px}
.tooltip .tt-row{display:flex;justify-content:space-between;gap:12px;padding:1px 0}
.tooltip .tt-label{color:var(--fg3)}
.tooltip .tt-val{color:var(--fg);font-weight:500}
.crosshair-x,.crosshair-y{position:absolute;background:var(--fg3);pointer-events:none;display:none}
.crosshair-x{width:1px;top:0;bottom:0;opacity:0.3}
.crosshair-y{height:1px;left:0;right:0;opacity:0.3}"""


# ── HTML body (topbar with stock dropdown added) ───────────────────────────────

STOCK_OPTIONS = '\n'.join(
    f'<option value="{s}"{"selected" if s == DEFAULT_STOCK else ""}>{s}</option>'
    for s in STOCKS
)

BODY = f"""<div class="layout">
<div class="topbar">
<select class="stock-sel" id="stockSel" onchange="switchStock(this.value)">
{STOCK_OPTIONS}
</select>
<h1><span class="stock" id="stockName">{DEFAULT_STOCK}</span> &middot; 5min &middot; fv2 Signal Viewer</h1>
<button class="nav-btn" onclick="navDay(-1)">&#9664; Prev</button>
<div class="date-display" id="dateDisplay">&mdash;</div>
<div class="jump-wrap">
<select id="jumpYear" class="jump-sel"></select>
<select id="jumpMonth" class="jump-sel"></select>
<select id="jumpDay" class="jump-sel"></select>
<button class="nav-btn" onclick="goToDate()">Go</button>
</div>
<button class="nav-btn" onclick="navDay(1)">Next &#9654;</button>
<div class="toggle-wrap">
<div class="toggle on" id="slopeToggle" onclick="toggleSlope()"><div class="knob"></div></div>
<span class="toggle-label" id="toggleLabel">Gap 1: Slope filter ON</span>
</div>
</div>
<div class="chart-area" id="chartArea">
<canvas id="chart"></canvas>
<canvas id="volCanvas"></canvas>
<div class="tooltip" id="tooltip"></div>
<div class="crosshair-x" id="crossX"></div>
<div class="crosshair-y" id="crossY"></div>
</div>
<div class="sidebar">
<div class="section">
<h2>All signals (<span id="sidebarStock">{DEFAULT_STOCK}</span>)</h2>
<div class="stat-row"><span class="stat-label">Total</span><span class="stat-val" id="statTotal">&mdash;</span></div>
<div class="stat-row"><span class="stat-label">Rising (R)</span><span class="stat-val green" id="statR">&mdash;</span></div>
<div class="stat-row"><span class="stat-label">Flat (L)</span><span class="stat-val gray" id="statL">&mdash;</span></div>
<div class="stat-row"><span class="stat-label">Falling (F)</span><span class="stat-val red" id="statF">&mdash;</span></div>
</div>
<div class="section">
<h2>Today's signals</h2>
<div class="stat-row"><span class="stat-label">Raw</span><span class="stat-val" id="dayRaw">&mdash;</span></div>
<div class="stat-row"><span class="stat-label">After filter</span><span class="stat-val green" id="dayFiltered">&mdash;</span></div>
<div class="stat-row"><span class="stat-label">Removed</span><span class="stat-val red" id="dayRemoved">&mdash;</span></div>
</div>
<div class="section">
<h2>Stats &mdash; <span id="dayStatsCount" style="color:var(--fg2);font-weight:400">0 trades</span></h2>
<div class="stat-row"><span class="stat-label">Win Rate</span><span class="stat-val" id="dayWinRate">&mdash;</span></div>
<div class="stat-row"><span class="stat-label">Avg PnL / Trade</span><span class="stat-val" id="dayAvgPnl">&mdash;</span></div>
<div class="stat-row"><span class="stat-label">Profit Factor</span><span class="stat-val" id="dayPF">&mdash;</span></div>
<div style="border-top:1px solid var(--border);margin:8px 0 4px"></div>
<div class="stat-row"><span class="stat-label" style="color:var(--green);font-size:11px">R &mdash; avg pnl</span><span class="stat-val" id="catR" style="font-size:11px">&mdash;</span></div>
<div class="stat-row"><span class="stat-label" style="color:var(--fg3);font-size:11px">L &mdash; avg pnl</span><span class="stat-val" id="catL" style="font-size:11px">&mdash;</span></div>
<div class="stat-row"><span class="stat-label" style="color:var(--red);font-size:11px">F &mdash; avg pnl</span><span class="stat-val" id="catF" style="font-size:11px">&mdash;</span></div>
</div>
<div class="section">
<h2>Signals</h2>
<div class="signal-list" id="signalList"></div>
<div class="sig-detail" id="sigDetail">
<div class="sd-title">Signal Detail</div>
<div class="sd-row"><span class="sd-label">Outcome</span><span class="sd-val" id="sdOutcome">—</span></div>
<div class="sd-row"><span class="sd-label">PnL</span><span class="sd-val" id="sdPnl">—</span></div>
<div class="sd-row"><span class="sd-label">Exit</span><span class="sd-val" id="sdExit">—</span></div>
<div class="sd-row"><span class="sd-label">Entry</span><span class="sd-val" id="sdEntry">—</span></div>
<div class="sd-row"><span class="sd-label">SL</span><span class="sd-val" id="sdSL">—</span></div>
<div class="sd-row"><span class="sd-label">Target</span><span class="sd-val" id="sdTgt">—</span></div>
<div class="sd-row"><span class="sd-label">Type</span><span class="sd-val" id="sdType">—</span></div>
</div>
</div>
<div class="legend">
<div class="legend-item"><div class="legend-dot" style="background:var(--teal)"></div>MA20 line</div>
<div class="legend-item"><div class="legend-dot" style="background:var(--amber)"></div>Touch candle</div>
<div class="legend-item"><div class="legend-dot" style="background:var(--blue)"></div>Bounce candle</div>
<div class="legend-item"><div class="legend-dot" style="background:var(--green)"></div>Entry (&#9650;)</div>
<div class="legend-item"><div class="legend-dot" style="background:var(--fg3)"></div>Filtered out (dimmed)</div>
</div>
</div>
</div>"""


# ── JS: exact logic from original H1 + multi-stock wrapper ────────────────────

JS = r"""
const ALL_STOCKS_DATA = ALL_STOCKS_DATA_PLACEHOLDER;
let currentStock = 'DEFAULT_STOCK_PLACEHOLDER';
let DATA = ALL_STOCKS_DATA[currentStock];

let currentDateIdx = 0;
let slopeFilterOn = true;
let selectedSig = -1;
let candles = [];
let daySigs = [];
const canvas = document.getElementById('chart');
const ctx = canvas.getContext('2d');
const chartArea = document.getElementById('chartArea');
const tooltip = document.getElementById('tooltip');
const crossX = document.getElementById('crossX');

// ── Event listeners — placed early so browser registers them before parsing large data block ──
chartArea.addEventListener('mousemove', e => {
    const rect = chartArea.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    if (mx < PAD.left || mx > W - PAD.right || my < PAD.top || my > PAD.top + plotH) {
        tooltip.style.display = 'none'; crossX.style.display = 'none'; crossY.style.display = 'none'; return;
    }
    const n = candles.length;
    const cw = plotW / n;
    const idx = Math.floor((mx - PAD.left) / cw);
    if (idx < 0 || idx >= n) return;
    const c = candles[idx];
    crossX.style.display = 'block'; crossX.style.left = (PAD.left + idx * cw + cw/2) + 'px';
    crossY.style.display = 'block'; crossY.style.top = my + 'px';
    let html = '<div class="tt-row"><span class="tt-label">Time</span><span class="tt-val">' + timeLabel(idx) + '</span></div>';
    html += '<div class="tt-row"><span class="tt-label">O</span><span class="tt-val">' + c.o.toFixed(2) + '</span></div>';
    html += '<div class="tt-row"><span class="tt-label">H</span><span class="tt-val">' + c.h.toFixed(2) + '</span></div>';
    html += '<div class="tt-row"><span class="tt-label">L</span><span class="tt-val">' + c.l.toFixed(2) + '</span></div>';
    html += '<div class="tt-row"><span class="tt-label">C</span><span class="tt-val">' + c.c.toFixed(2) + '</span></div>';
    if (c.ma !== null) html += '<div class="tt-row"><span class="tt-label">MA20</span><span class="tt-val" style="color:#14b8a6">' + c.ma.toFixed(2) + '</span></div>';
    if (c.sl !== null) {
        const sColor = c.sl > 0.05 ? '#22c55e' : c.sl < -0.05 ? '#ef4444' : '#555d72';
        html += '<div class="tt-row"><span class="tt-label">Slope</span><span class="tt-val" style="color:' + sColor + '">' + (c.sl > 0 ? '+' : '') + c.sl.toFixed(3) + '%</span></div>';
    }
    if (c.atr !== null) html += '<div class="tt-row"><span class="tt-label">ATR14</span><span class="tt-val" style="color:#888">' + c.atr.toFixed(2) + '</span></div>';
    if (c.vr !== null) { const vrColor = c.vr >= 1.2 ? '#f97316' : '#555d72'; html += '<div class="tt-row"><span class="tt-label">Vol Ratio</span><span class="tt-val" style="color:' + vrColor + '">' + c.vr.toFixed(2) + 'x</span></div>'; }
    html += '<div style="margin-top:5px;padding-top:4px;border-top:1px solid #333;font-size:9px;color:#555">Slope = (MA20[T0] \u2212 MA20[T0\u22125]) / MA20[T0] \xd7 100</div>';
    tooltip.innerHTML = html; tooltip.style.display = 'block';
    let tx = mx + 16; if (tx + 160 > W) tx = mx - 170;
    tooltip.style.left = tx + 'px'; tooltip.style.top = Math.max(PAD.top, my - 40) + 'px';
});

chartArea.addEventListener('mouseleave', () => {
    tooltip.style.display = 'none'; crossX.style.display = 'none'; crossY.style.display = 'none';
});

document.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft') navDay(-1);
    if (e.key === 'ArrowRight') navDay(1);
    if (e.key === 'f' || e.key === 'F') toggleSlope();
});
const crossY = document.getElementById('crossY');

const volCanvas = document.getElementById('volCanvas');
const vctx = volCanvas.getContext('2d');
const VOL_PAD = {top: 6, right: 60, bottom: 18, left: 12};
const PAD = {top: 20, right: 60, bottom: 30, left: 12};
let W, H, plotW, plotH, VW, VH, vPlotW, vPlotH;

function resize() {
    const r = window.devicePixelRatio || 1;
    const rect = chartArea.getBoundingClientRect();
    const volRect = volCanvas.getBoundingClientRect();
    canvas.width = rect.width * r;
    canvas.height = (rect.height - volRect.height) * r;
    canvas.style.width = rect.width + 'px';
    ctx.setTransform(r, 0, 0, r, 0, 0);
    volCanvas.width = volRect.width * r;
    volCanvas.height = volRect.height * r;
    volCanvas.style.width = volRect.width + 'px';
    vctx.setTransform(r, 0, 0, r, 0, 0);
    W = rect.width; H = rect.height - volRect.height;
    VW = volRect.width; VH = volRect.height;
    plotW = W - PAD.left - PAD.right;
    plotH = H - PAD.top - PAD.bottom;
    vPlotW = VW - VOL_PAD.left - VOL_PAD.right;
    vPlotH = VH - VOL_PAD.top - VOL_PAD.bottom;
    draw();
}

function parseDay(dateStr) {
    const raw = DATA.c[dateStr];
    if (!raw) return [];
    return raw.split('|').map(s => {
        const p = s.split(',');
        return {o: +p[0], h: +p[1], l: +p[2], c: +p[3], ma: p[4] ? +p[4] : null, sl: p[5] ? +p[5] : null, atr: p[6] ? +p[6] : null, vr: p[7] ? +p[7] : null, vol: p[8] ? +p[8] : null};
    });
}

function loadDay(idx) {
    currentDateIdx = Math.max(0, Math.min(idx, DATA.d.length - 1));
    const date = DATA.d[currentDateIdx];
    candles = parseDay(date);
    daySigs = DATA.s[date] || [];
    selectedSig = -1;
    document.getElementById('dateDisplay').textContent = date;
    updateSidebar();
    draw();
}

function navDay(delta) { loadDay(currentDateIdx + delta); syncJumpSelects(DATA.d[currentDateIdx]); }

function initJumpSelects() {
    const dates = DATA.d;
    const years = [...new Set(dates.map(d => d.slice(0,4)))].sort();
    const ySel = document.getElementById('jumpYear');
    const mSel = document.getElementById('jumpMonth');
    const dSel = document.getElementById('jumpDay');
    ySel.innerHTML = '';
    years.forEach(y => { const o = document.createElement('option'); o.value = y; o.textContent = y; ySel.appendChild(o); });
    function updateMonths() {
        const y = ySel.value;
        const months = [...new Set(dates.filter(d => d.slice(0,4)===y).map(d => d.slice(5,7)))].sort();
        mSel.innerHTML = '';
        months.forEach(m => { const o = document.createElement('option'); o.value = m; o.textContent = m; mSel.appendChild(o); });
        updateDays();
    }
    function updateDays() {
        const y = ySel.value; const m = mSel.value;
        const days = dates.filter(d => d.slice(0,4)===y && d.slice(5,7)===m).map(d => d.slice(8,10)).sort();
        dSel.innerHTML = '';
        days.forEach(day => { const o = document.createElement('option'); o.value = day; o.textContent = day; dSel.appendChild(o); });
    }
    ySel.addEventListener('change', updateMonths);
    mSel.addEventListener('change', updateDays);
    const cur = DATA.d[0];
    ySel.value = cur.slice(0,4); updateMonths();
    mSel.value = cur.slice(5,7); updateDays();
    dSel.value = cur.slice(8,10);
}

function goToDate() {
    const y = document.getElementById('jumpYear').value;
    const m = document.getElementById('jumpMonth').value;
    const d = document.getElementById('jumpDay').value;
    const target = y + '-' + m + '-' + d;
    let idx = DATA.d.indexOf(target);
    if (idx === -1) { let best = -1, bestDiff = Infinity; DATA.d.forEach((dt, i) => { const diff = Math.abs(new Date(dt) - new Date(target)); if (diff < bestDiff) { bestDiff = diff; best = i; } }); idx = best; }
    if (idx !== -1) { loadDay(idx); syncJumpSelects(DATA.d[idx]); }
}

function syncJumpSelects(date) {
    const ySel = document.getElementById('jumpYear');
    const mSel = document.getElementById('jumpMonth');
    const dSel = document.getElementById('jumpDay');
    const dates = DATA.d;
    ySel.value = date.slice(0,4);
    const months = [...new Set(dates.filter(d => d.slice(0,4)===date.slice(0,4)).map(d => d.slice(5,7)))].sort();
    mSel.innerHTML = ''; months.forEach(m => { const o = document.createElement('option'); o.value = m; o.textContent = m; mSel.appendChild(o); });
    mSel.value = date.slice(5,7);
    const days = dates.filter(d => d.slice(0,4)===date.slice(0,4) && d.slice(5,7)===date.slice(5,7)).map(d => d.slice(8,10)).sort();
    dSel.innerHTML = ''; days.forEach(day => { const o = document.createElement('option'); o.value = day; o.textContent = day; dSel.appendChild(o); });
    dSel.value = date.slice(8,10);
}

function toggleSlope() {
    slopeFilterOn = !slopeFilterOn;
    const el = document.getElementById('slopeToggle');
    el.classList.toggle('on', slopeFilterOn);
    document.getElementById('toggleLabel').textContent = 'Gap 1: Slope filter ' + (slopeFilterOn ? 'ON' : 'OFF');
    updateSidebar();
    draw();
}

function updateSidebar() {
    document.getElementById('statTotal').textContent = DATA.st.total;
    document.getElementById('statR').textContent = DATA.st.R;
    document.getElementById('statL').textContent = DATA.st.L;
    document.getElementById('statF').textContent = DATA.st.F;

    const raw = daySigs.length;
    const rising = daySigs.filter(s => s[4] === 'R').length;
    const removed = raw - rising;
    document.getElementById('dayRaw').textContent = raw;
    document.getElementById('dayFiltered').textContent = slopeFilterOn ? rising : raw;
    document.getElementById('dayRemoved').textContent = slopeFilterOn ? removed : 0;

    const visibleSigs = slopeFilterOn ? daySigs.filter(s => s[4] === 'R') : daySigs;
    const sigsWithPnl = visibleSigs.filter(s => s[5] !== null && s[5] !== undefined);
    const wrEl = document.getElementById('dayWinRate');
    const apEl = document.getElementById('dayAvgPnl');
    const pfEl = document.getElementById('dayPF');
    const cntEl = document.getElementById('dayStatsCount');
    const n = sigsWithPnl.length;
    cntEl.textContent = n + (n === 1 ? ' trade' : ' trades');
    if (n > 0) {
        const wins = sigsWithPnl.filter(s => s[6] === 1);
        const wr = (wins.length / n * 100).toFixed(1) + '%';
        const avgPnl = sigsWithPnl.reduce((a, s) => a + s[5], 0) / n;
        const posSum = sigsWithPnl.filter(s => s[5] > 0).reduce((a, s) => a + s[5], 0);
        const negSum = Math.abs(sigsWithPnl.filter(s => s[5] < 0).reduce((a, s) => a + s[5], 0));
        const pf = negSum > 0 ? (posSum / negSum).toFixed(2) : (posSum > 0 ? 'N/A' : '0.00');
        wrEl.textContent = wr;
        wrEl.className = 'stat-val ' + (wins.length / n >= 0.5 ? 'green' : 'red');
        apEl.textContent = 'Rs ' + (avgPnl >= 0 ? '+' : '') + avgPnl.toFixed(2);
        apEl.className = 'stat-val ' + (avgPnl >= 0 ? 'green' : 'red');
        pfEl.textContent = pf;
        pfEl.className = 'stat-val ' + (pf === 'N/A' ? 'gray' : parseFloat(pf) >= 1 ? 'green' : 'red');
    } else {
        wrEl.textContent = '—'; wrEl.className = 'stat-val gray';
        apEl.textContent = '—'; apEl.className = 'stat-val gray';
        pfEl.textContent = '—'; pfEl.className = 'stat-val gray';
    }

    // Per-category breakdown — always uses ALL daySigs (not toggle-filtered)
    ['R', 'L', 'F'].forEach(cat => {
        const id = cat === 'R' ? 'catR' : cat === 'L' ? 'catL' : 'catF';
        const el = document.getElementById(id);
        const catSigs = daySigs.filter(s => s[4] === cat && s[5] !== null && s[5] !== undefined);
        if (catSigs.length === 0) {
            el.textContent = '—'; el.className = 'stat-val gray';
        } else {
            const avg = catSigs.reduce((a, s) => a + s[5], 0) / catSigs.length;
            el.textContent = 'Rs ' + (avg >= 0 ? '+' : '') + avg.toFixed(2) + ' (' + catSigs.length + ')';
            el.className = 'stat-val ' + (avg >= 0 ? 'green' : 'red');
        }
    });

    const list = document.getElementById('signalList');
    list.innerHTML = '';
    daySigs.forEach((s, i) => {
        const ti = s[0], slope = s[3], cat = s[4];
        const time = candles[ti] ? timeLabel(ti) : '??';
        const catName = cat === 'R' ? 'rising' : cat === 'F' ? 'falling' : 'flat';
        const isSelected = (i === selectedSig);
        let cls = 'signal-item ' + catName;
        if (isSelected) {
            cls += ' selected';
        } else if (selectedSig >= 0) {
            cls += ' filtered';               // another signal is selected — dim this one
        } else if (slopeFilterOn && cat !== 'R') {
            cls += ' filtered';               // slope filter active
        }
        const div = document.createElement('div');
        div.className = cls;
        div.innerHTML = '<span class="time">#' + (i+1) + ' ' + time + '</span><span class="slope">' + (slope > 0 ? '+' : '') + slope.toFixed(3) + '%</span>';
        div.onclick = () => { selectedSig = (selectedSig === i) ? -1 : i; updateSidebar(); draw(); };
        list.appendChild(div);
    });

    // Signal detail panel
    const detail = document.getElementById('sigDetail');
    if (selectedSig >= 0 && selectedSig < daySigs.length) {
        const s = daySigs[selectedSig];
        const pnl = s[5], win = s[6], sl = s[8], tgt = s[9], cat = s[4], er = s[10];
        const entryIdx = s[2];
        const entryPrice = (entryIdx !== null && candles[entryIdx]) ? candles[entryIdx].o : null;
        const outcomeEl = document.getElementById('sdOutcome');
        const pnlEl = document.getElementById('sdPnl');
        const exitLabel = er === 'T' ? 'TARGET HIT' : er === 'S' ? 'SL HIT' : 'EOD';
        const isWin = er === 'T';
        const isLoss = er === 'S';
        const isEOD = er === 'E';
        outcomeEl.textContent = isWin ? 'WIN' : isLoss ? 'SL HIT' : (pnl > 0 ? 'EOD +' : pnl < 0 ? 'EOD -' : 'EOD');
        outcomeEl.className = 'sd-val ' + (isWin ? 'green' : isLoss ? 'red' : isEOD && pnl > 0 ? 'green' : isEOD && pnl < 0 ? 'red' : 'gray');
        pnlEl.textContent = pnl !== null ? 'Rs ' + (pnl >= 0 ? '+' : '') + pnl.toFixed(2) : '—';
        pnlEl.className = 'sd-val ' + (pnl > 0 ? 'green' : pnl < 0 ? 'red' : '');
        document.getElementById('sdExit').textContent = exitLabel;
        document.getElementById('sdEntry').textContent = entryPrice !== null ? entryPrice.toFixed(2) : '—';
        document.getElementById('sdSL').textContent = sl !== null ? sl.toFixed(2) : '—';
        document.getElementById('sdTgt').textContent = tgt !== null ? tgt.toFixed(2) : '—';
        document.getElementById('sdType').textContent = cat === 'R' ? 'Rising' : cat === 'F' ? 'Falling' : 'Flat';
        detail.classList.add('visible');
    } else {
        detail.classList.remove('visible');
    }
}

function timeLabel(idx) {
    const h = 9 + Math.floor((15 + idx * 5) / 60);
    const m = (15 + idx * 5) % 60;
    return String(h).padStart(2,'0') + ':' + String(m).padStart(2,'0');
}

function draw() {
    if (!candles.length) return;
    ctx.clearRect(0, 0, W, H);
    drawVol();

    let lo = Infinity, hi = -Infinity;
    candles.forEach(c => { if (c.l < lo) lo = c.l; if (c.h > hi) hi = c.h; if (c.ma && c.ma < lo) lo = c.ma; if (c.ma && c.ma > hi) hi = c.ma; });
    const margin = (hi - lo) * 0.08;
    lo -= margin; hi += margin;

    const n = candles.length;
    const cw = plotW / n;
    const bw = Math.max(2, cw * 0.6);

    function x(i) { return PAD.left + i * cw + cw / 2; }
    function y(v) { return PAD.top + plotH * (1 - (v - lo) / (hi - lo)); }

    ctx.strokeStyle = '#1e2230'; ctx.lineWidth = 0.5;
    const steps = 6;
    for (let i = 0; i <= steps; i++) {
        const gy = PAD.top + plotH * i / steps;
        ctx.beginPath(); ctx.moveTo(PAD.left, gy); ctx.lineTo(W - PAD.right, gy); ctx.stroke();
        const val = hi - (hi - lo) * i / steps;
        ctx.fillStyle = '#555d72'; ctx.font = '10px "JetBrains Mono"';
        ctx.textAlign = 'left'; ctx.fillText(val.toFixed(1), W - PAD.right + 6, gy + 3);
    }

    ctx.fillStyle = '#555d72'; ctx.font = '10px "JetBrains Mono"'; ctx.textAlign = 'center';
    const interval = Math.max(1, Math.floor(n / 8));
    for (let i = 0; i < n; i += interval) { ctx.fillText(timeLabel(i), x(i), H - 8); }

    const sigSet = {};
    daySigs.forEach((s, idx) => {
        const show = selectedSig >= 0 ? (idx === selectedSig) : (!slopeFilterOn || s[4] === 'R');
        sigSet[s[0]] = {type: 'touch', show, cat: s[4]};
        sigSet[s[1]] = {type: s[1] === s[0] ? 'touch_bounce' : 'bounce', show, cat: s[4]};
        if (s[2] !== null) sigSet[s[2]] = {type: 'entry', show, cat: s[4]};
    });

    ctx.beginPath(); ctx.strokeStyle = '#14b8a6'; ctx.lineWidth = 1.5;
    let started = false;
    candles.forEach((c, i) => {
        if (c.ma !== null) {
            if (!started) { ctx.moveTo(x(i), y(c.ma)); started = true; }
            else ctx.lineTo(x(i), y(c.ma));
        }
    });
    ctx.stroke();

    candles.forEach((c, i) => {
        const cx = x(i);
        const isGreen = c.c >= c.o;
        let fillColor = isGreen ? '#22c55e' : '#ef4444';
        let alpha = 1;
        const sig = sigSet[i];
        if (sig && !sig.show) alpha = 0.15;
        ctx.globalAlpha = alpha;

        ctx.strokeStyle = fillColor; ctx.lineWidth = 0.8;
        ctx.beginPath(); ctx.moveTo(cx, y(c.h)); ctx.lineTo(cx, y(c.l)); ctx.stroke();

        const top = y(Math.max(c.o, c.c));
        const bot = y(Math.min(c.o, c.c));
        const bodyH = Math.max(1, bot - top);
        ctx.fillStyle = fillColor;
        ctx.fillRect(cx - bw/2, top, bw, bodyH);

        if (sig && sig.show) {
            if (sig.type === 'touch') {
                ctx.strokeStyle = '#f59e0b'; ctx.lineWidth = 2;
                ctx.strokeRect(cx - bw/2 - 2, top - 2, bw + 4, bodyH + 4);
            } else if (sig.type === 'bounce') {
                ctx.strokeStyle = '#3b82f6'; ctx.lineWidth = 2;
                ctx.strokeRect(cx - bw/2 - 2, top - 2, bw + 4, bodyH + 4);
            } else if (sig.type === 'touch_bounce') {
                ctx.strokeStyle = '#3b82f6'; ctx.lineWidth = 2.5;
                ctx.strokeRect(cx - bw/2 - 4, top - 4, bw + 8, bodyH + 8);
                ctx.strokeStyle = '#f59e0b'; ctx.lineWidth = 2;
                ctx.strokeRect(cx - bw/2 - 1, top - 1, bw + 2, bodyH + 2);
            } else if (sig.type === 'entry') {
                ctx.fillStyle = '#22c55e';
                ctx.beginPath();
                ctx.moveTo(cx, y(c.l) + 8);
                ctx.lineTo(cx - 5, y(c.l) + 16);
                ctx.lineTo(cx + 5, y(c.l) + 16);
                ctx.closePath();
                ctx.fill();
            }
        }
        ctx.globalAlpha = 1;
    });

    candles.forEach((c, i) => {
        if (c.sl !== null) {
            let col;
            if (c.sl > 0.05) col = 'rgba(34,197,94,0.04)';
            else if (c.sl < -0.05) col = 'rgba(239,68,68,0.04)';
            else col = 'rgba(85,93,114,0.03)';
            ctx.fillStyle = col;
            ctx.fillRect(x(i) - cw/2, PAD.top, cw, plotH);
        }
    });

    // ── Selected signal overlay ────────────────────────────────────────────────
    if (selectedSig >= 0 && selectedSig < daySigs.length) {
        const s = daySigs[selectedSig];
        const entryIdx = s[2], exitIdx = s[7], slPrice = s[8], tgtPrice = s[9];
        if (entryIdx !== null && exitIdx !== null && slPrice !== null) {
            // Entry→exit window highlight (behind lines)
            const xL = x(entryIdx) - cw / 2;
            const xR = x(exitIdx)  + cw / 2;
            ctx.fillStyle = 'rgba(59,130,246,0.07)';
            ctx.fillRect(xL, PAD.top, xR - xL, plotH);

            ctx.save();
            ctx.font = '10px "JetBrains Mono"';

            // SL line — dashed red
            ctx.setLineDash([4, 3]);
            ctx.strokeStyle = 'rgba(239,68,68,0.7)'; ctx.lineWidth = 1;
            ctx.beginPath(); ctx.moveTo(PAD.left, y(slPrice)); ctx.lineTo(W - PAD.right, y(slPrice)); ctx.stroke();
            ctx.setLineDash([]);
            ctx.fillStyle = '#ef4444'; ctx.textAlign = 'left';
            ctx.fillText('SL ' + slPrice.toFixed(1), PAD.left + 4, y(slPrice) - 3);

            // Target line — dashed green
            ctx.setLineDash([4, 3]);
            ctx.strokeStyle = 'rgba(34,197,94,0.7)'; ctx.lineWidth = 1;
            ctx.beginPath(); ctx.moveTo(PAD.left, y(tgtPrice)); ctx.lineTo(W - PAD.right, y(tgtPrice)); ctx.stroke();
            ctx.setLineDash([]);
            ctx.fillStyle = '#22c55e'; ctx.textAlign = 'left';
            ctx.fillText('TGT ' + tgtPrice.toFixed(1), PAD.left + 4, y(tgtPrice) - 3);

            ctx.restore();
        }
    }
}

function switchStock(stock) {
    currentStock = stock;
    DATA = ALL_STOCKS_DATA[stock];
    document.getElementById('stockName').textContent = stock;
    document.getElementById('sidebarStock').textContent = stock;
    document.getElementById('stockSel').value = stock;
    initJumpSelects();
    loadDay(findDemoDay());
}

function drawVol() {
    if (!candles.length || !vPlotW) return;
    vctx.clearRect(0, 0, VW, VH);
    const n = candles.length;
    const cw = vPlotW / n;
    const maxVol = Math.max(...candles.map(c => c.vol || 0));
    if (maxVol === 0) return;
    const vx = i => VOL_PAD.left + i * cw + cw / 2;

    // Build signal sets for colouring
    const touchSet = new Set(), bounceSet = new Set();
    daySigs.forEach(s => { touchSet.add(s[0]); bounceSet.add(s[1]); });

    candles.forEach((c, i) => {
        if (!c.vol) return;
        const barH = (c.vol / maxVol) * vPlotH;
        const bx = VOL_PAD.left + i * cw + 1;
        const by = VOL_PAD.top + vPlotH - barH;
        const bw = Math.max(1, cw - 2);
        // Colour: orange=high VR, teal=bounce, red/green=candle direction, gray=normal
        let col;
        if (bounceSet.has(i) || touchSet.has(i)) col = c.vr && c.vr >= 1.2 ? '#f97316' : '#14b8a6';
        else if (c.vr && c.vr >= 1.2) col = 'rgba(249,115,22,0.7)';
        else col = c.c >= c.o ? 'rgba(34,197,94,0.4)' : 'rgba(239,68,68,0.4)';
        vctx.fillStyle = col;
        vctx.fillRect(bx, by, bw, barH);
    });

    // Y-axis max label
    vctx.fillStyle = '#555d72';
    vctx.font = '9px "JetBrains Mono"';
    vctx.textAlign = 'left';
    vctx.fillText((maxVol / 1000).toFixed(0) + 'K', VOL_PAD.left + vPlotW + 2, VOL_PAD.top + 8);
    vctx.textAlign = 'left';
}

function findDemoDay() {
    return 0;  // always open on earliest date in dataset
}

window.addEventListener('resize', resize);
resize();
loadDay(findDemoDay());
initJumpSelects();
syncJumpSelects(DATA.d[currentDateIdx]);
"""

js_final = (JS
    .replace('ALL_STOCKS_DATA_PLACEHOLDER', all_data_js)
    .replace('DEFAULT_STOCK_PLACEHOLDER', DEFAULT_STOCK)
)

# ── Assemble and write HTML ────────────────────────────────────────────────────

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>fv2 Signal Viewer</title>
<style>
{CSS}
</style>
</head>
<body>
{BODY}
<script>
{js_final}
</script>
</body>
</html>"""

print('Writing HTML...')
OUT.write_text(HTML, encoding='utf-8')
size_mb = OUT.stat().st_size / 1e6
print(f'Saved: {OUT}')
print(f'Size : {size_mb:.1f} MB')
if size_mb > 50:
    print(f'Note : Large file ({size_mb:.0f} MB) — browser may take 5-15s to parse on first load.')
