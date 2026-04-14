"""
Build fv2_h3_chart.html — H3.1 companion chart view for Gap 1 slope analysis.

Reuses same signal detection as build_html3.py. Computes extended metrics
(PF, WR, N, AvgPnL, CAGR) for all 8×15=120 offset×threshold combos.
Output: tiny HTML (<1 MB + Chart.js CDN).
"""

import json
from pathlib import Path

import pandas as pd

# ── Paths (same as build_html3.py) ────────────────────────────────────────────
CSV_DIR = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/data/historical/csv/intraday_5min')
OUT     = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_h3_chart.html')
H3_OUT  = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_h3_slope_tuner.html')

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
TRAIN_END  = '2023-12-31'
OFFSETS    = [-5, -4, -3, -2, -1, 0, 1, 2]
THRESHOLDS = [round(x * 0.01, 2) for x in range(1, 16)]


# ── Signal extraction (identical to build_html3.py) ────────────────────────────

def build_stock_signals(stock: str, stock_idx: int) -> list:
    csv = CSV_DIR / f'{stock}_5min.csv'
    df  = pd.read_csv(csv)
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df = df.sort_values('datetime').reset_index(drop=True)

    prev_close = df['close'].shift(1)
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - prev_close).abs(),
        (df['low']  - prev_close).abs(),
    ], axis=1).max(axis=1)
    df['atr14'] = tr.rolling(14).mean()
    df['slope'] = (df['ma20'] - df['ma20'].shift(5)) / df['ma20'] * 100

    df['_ds'] = df['datetime'].dt.strftime('%Y-%m-%d')
    mask = (df['_ds'] >= DATE_START) & (df['_ds'] <= DATE_END)
    df = df[mask].reset_index(drop=True)

    signals = []
    for date in sorted(df['_ds'].unique()):
        day = df[df['_ds'] == date].reset_index(drop=True)
        n   = len(day)
        period = 0 if date <= TRAIN_END else 1

        i = 0
        while i < n:
            row = day.iloc[i]
            if pd.isna(row['ma20']) or pd.isna(row['vol_ma20']):
                i += 1; continue
            if row['low'] > row['ma20']:
                i += 1; continue

            touch_idx = i
            slopes = []
            for O in OFFSETS:
                ref = touch_idx + O
                if 0 <= ref < n and pd.notna(day.iloc[ref]['slope']):
                    slopes.append(round(float(day.iloc[ref]['slope']), 4))
                else:
                    slopes.append(None)

            bounce_idx = None
            for j in range(touch_idx, min(touch_idx + 4, n)):
                b = day.iloc[j]
                if (pd.notna(b['ma20']) and b['close'] > b['ma20'] and
                        pd.notna(b['vol_ma20']) and b['volume'] >= 1.2 * b['vol_ma20']):
                    bounce_idx = j; break

            if bounce_idx is not None:
                entry_idx = bounce_idx + 1 if bounce_idx + 1 < n else None
                pnl, win = None, None
                if entry_idx is not None:
                    entry_price = day.iloc[entry_idx]['open']
                    atr_val     = day.iloc[touch_idx]['atr14']
                    if pd.notna(entry_price) and pd.notna(atr_val) and atr_val > 0:
                        sl = entry_price - 2.5 * atr_val
                        target = entry_price + 4.5 * atr_val
                        exit_price = day.iloc[-1]['close']
                        win = 0
                        for ki in range(entry_idx, n):
                            krow = day.iloc[ki]
                            if krow['high'] >= target:
                                exit_price = target; win = 1; break
                            if krow['low'] <= sl:
                                exit_price = sl; break
                        pnl = round(float(exit_price - entry_price), 2)

                signals.append([period] + slopes + [pnl, win, stock_idx])
                i = bounce_idx + 2
            else:
                i += 1

    return signals


# ── Extended grid computation ──────────────────────────────────────────────────

def _cell_stats(sigs, years):
    """Compute all metrics for a filtered signal list."""
    if not sigs:
        return {'pf': None, 'wr': None, 'n': 0, 'avgPnl': None, 'cagr': None}
    wins = sum(1 for s in sigs if s[10] == 1)
    tot  = sum(s[9] for s in sigs)
    gp   = sum(s[9] for s in sigs if s[9] > 0)
    gl   = abs(sum(s[9] for s in sigs if s[9] < 0))
    pf   = round(gp / gl, 4) if gl > 0 else (9.99 if gp > 0 else None)
    feq  = 1_000_000 + tot
    cagr = round((pow(feq / 1_000_000, 1 / years) - 1) * 100, 2) if feq > 0 else None
    return {
        'pf':     pf,
        'wr':     round(wins / len(sigs) * 100, 2),
        'n':      len(sigs),
        'avgPnl': round(tot / len(sigs), 2),
        'cagr':   cagr,
    }


def compute_grid(signals: list) -> list:
    """Returns flat list of 120 objects (8 offsets × 15 thresholds)."""
    train_sigs = [s for s in signals if s[0] == 0 and s[9] is not None]
    test_sigs  = [s for s in signals if s[0] == 1 and s[9] is not None]

    rows = []
    for oi in range(8):
        for ti, thresh in enumerate(THRESHOLDS):
            tr_f = [s for s in train_sigs if s[1+oi] is not None and s[1+oi] >= thresh]
            te_f = [s for s in test_sigs  if s[1+oi] is not None and s[1+oi] >= thresh]
            tr   = _cell_stats(tr_f, 2.0)
            te   = _cell_stats(te_f, 2.0)
            rows.append({
                'oi': oi, 'ti': ti, 'thresh': thresh,
                'pf_tr':     tr['pf'],     'pf_te':     te['pf'],
                'wr_tr':     tr['wr'],     'wr_te':     te['wr'],
                'n_tr':      tr['n'],      'n_te':      te['n'],
                'avgpnl_tr': tr['avgPnl'], 'avgpnl_te': te['avgPnl'],
                'cagr_tr':   tr['cagr'],   'cagr_te':   te['cagr'],
            })
    return rows


def compute_baseline(signals: list) -> dict:
    def _s(sigs, years):
        sigs = [s for s in sigs if s[9] is not None]
        if not sigs: return {'pf': None, 'wr': None, 'n': 0, 'avgPnl': None, 'cagr': None}
        wins = sum(1 for s in sigs if s[10] == 1)
        tot  = sum(s[9] for s in sigs)
        gp   = sum(s[9] for s in sigs if s[9] > 0)
        gl   = abs(sum(s[9] for s in sigs if s[9] < 0))
        feq  = 1_000_000 + tot
        return {
            'pf':     round(gp/gl, 4) if gl > 0 else None,
            'wr':     round(wins/len(sigs)*100, 2),
            'n':      len(sigs),
            'avgPnl': round(tot/len(sigs), 2),
            'cagr':   round((pow(feq/1_000_000,1/years)-1)*100, 2) if feq > 0 else None,
        }
    return {
        'train': _s([s for s in signals if s[0]==0], 2.0),
        'test':  _s([s for s in signals if s[0]==1], 2.0),
    }


# ── Main ───────────────────────────────────────────────────────────────────────

print('Building H3.1 data for 30 stocks...')
all_signals = []
for idx, stock in enumerate(STOCKS):
    sigs = build_stock_signals(stock, idx)
    all_signals.extend(sigs)
    print(f'  {stock:15s}  signals={len(sigs):5d}')

total = len(all_signals)
print(f'\nTotal: {total:,}  (train={sum(1 for s in all_signals if s[0]==0):,}  test={sum(1 for s in all_signals if s[0]==1):,})')

print('Computing grid (120 combos)...')
grid     = compute_grid(all_signals)
baseline = compute_baseline(all_signals)

grid_js     = json.dumps(grid,     separators=(',', ':'))
baseline_js = json.dumps(baseline, separators=(',', ':'))
print(f'Grid JS: {len(grid_js)/1e3:.1f} KB')


# ── HTML template (raw string — no f-string escaping needed) ──────────────────

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>H3.1 — Gap 1 Chart View</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0f0f0f;--bg2:#1a1a1a;--bg3:#222;--bg4:#2a2a2a;
  --fg:#e8e8e8;--fg2:#b8b8b8;--fg3:#888;--fg4:#555;
  --border:#333;--border2:#444;
  --green:#4ade80;--red:#f87171;--amber:#fbbf24;--teal:#14b8a6;
}
body{background:var(--bg);color:var(--fg);font-family:'Segoe UI',system-ui,sans-serif;font-size:13px;padding:16px 20px}
.titlebar{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px}
h1{font-size:15px;font-weight:600;color:var(--fg2)}
.subtitle{font-size:11px;color:var(--fg3)}
.h3-btn{background:var(--bg3);border:1px solid var(--border2);color:var(--teal);border-radius:5px;padding:5px 12px;font-size:11px;cursor:pointer;text-decoration:none}
.h3-btn:hover{background:var(--bg4)}
.section{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:14px}
.sec-title{font-size:11px;font-weight:700;color:var(--fg3);text-transform:uppercase;letter-spacing:.6px;margin-bottom:12px}

/* ── SLIDERS ── */
.slider-block{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:12px}
.sl-group{flex:1;min-width:160px}
.sl-group label{font-size:11px;color:var(--fg3);display:flex;justify-content:space-between;margin-bottom:4px}
.sl-group label b{color:var(--fg);font-weight:700}
input[type=range]{width:100%;accent-color:var(--teal);cursor:pointer}

/* ── READOUT ── */
.readout{background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:10px 14px}
.readout-title{font-size:12px;font-weight:600;color:var(--fg2);margin-bottom:8px}
.readout-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:6px}
.ro-cell{display:flex;flex-direction:column;gap:2px}
.ro-lbl{font-size:10px;color:var(--fg3)}
.ro-val{font-size:12px;font-weight:700}
.ro-val.g{color:var(--green)}.ro-val.r{color:var(--red)}.ro-val.a{color:var(--amber)}.ro-val.x{color:var(--fg3)}
.stability{font-size:11px;margin-top:4px}
.stability.ok{color:var(--green)}.stability.warn{color:var(--amber)}

/* ── CHARTS ── */
.charts-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.chart-wrap{background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:12px}
.chart-title{font-size:12px;font-weight:600;color:var(--fg2);margin-bottom:8px}
.chart-subtitle{font-size:10px;color:var(--fg3);margin-bottom:10px}
canvas{max-height:320px}

footer{text-align:center;color:var(--fg4);font-size:11px;padding:10px 0}
</style>
</head>
<body>

<div class="titlebar">
  <div>
    <h1>H3.1 — Gap 1: Slope Chart View</h1>
    <div class="subtitle">Train 2022–2023 &nbsp;|&nbsp; Test 2024–2025 &nbsp;|&nbsp; 30 stocks &nbsp;·&nbsp; Click chart points to snap sliders</div>
  </div>
  <a class="h3-btn" href="fv2_h3_slope_tuner.html" target="_blank">← Heatmap View</a>
</div>

<!-- ── SECTION 1: SLIDERS ── -->
<div class="section">
  <div class="sec-title">Section 1 — Controls</div>
  <div class="slider-block">
    <div class="sl-group">
      <label>Offset &nbsp;<b id="lbl-off">T0</b></label>
      <input type="range" id="sl-off" min="0" max="7" value="5" oninput="onSlide()">
    </div>
    <div class="sl-group">
      <label>Min Threshold &nbsp;<b id="lbl-thresh">0.05%</b></label>
      <input type="range" id="sl-thresh" min="0" max="14" value="4" oninput="onSlide()">
    </div>
  </div>
  <div class="readout">
    <div class="readout-title" id="readout-title">Offset: T0  |  Threshold: 0.05%</div>
    <div class="readout-grid">
      <div class="ro-cell"><span class="ro-lbl">Train PF</span><span class="ro-val" id="ro-tr-pf">—</span></div>
      <div class="ro-cell"><span class="ro-lbl">Train WR</span><span class="ro-val" id="ro-tr-wr">—</span></div>
      <div class="ro-cell"><span class="ro-lbl">Train Signals</span><span class="ro-val" id="ro-tr-n">—</span></div>
      <div class="ro-cell"><span class="ro-lbl">Test PF</span><span class="ro-val" id="ro-te-pf">—</span></div>
      <div class="ro-cell"><span class="ro-lbl">Test WR</span><span class="ro-val" id="ro-te-wr">—</span></div>
      <div class="ro-cell"><span class="ro-lbl">Test Signals</span><span class="ro-val" id="ro-te-n">—</span></div>
    </div>
    <div class="stability" id="stability">—</div>
  </div>
</div>

<!-- ── SECTION 2: CHARTS ── -->
<div class="section">
  <div class="sec-title">Section 2 — Charts</div>
  <div class="charts-grid">
    <div class="chart-wrap">
      <div class="chart-title">Chart A — Threshold Slice</div>
      <div class="chart-subtitle" id="chartA-sub">PF across thresholds (offset locked at T0)</div>
      <canvas id="chartA"></canvas>
    </div>
    <div class="chart-wrap">
      <div class="chart-title">Chart B — Offset Slice</div>
      <div class="chart-subtitle" id="chartB-sub">PF across offsets (threshold locked at 0.05%)</div>
      <canvas id="chartB"></canvas>
    </div>
  </div>
</div>

<footer>
  H3.1 — Gap 1 chart view &nbsp;·&nbsp; 30 stocks &nbsp;·&nbsp; 1-share mode<br>
  Train: 2022–2023 &nbsp;|&nbsp; Test: 2024–2025 &nbsp;·&nbsp; No position guard
</footer>

<script>
// ── EMBEDDED DATA ─────────────────────────────────────────────────────────────
const GRID     = __GRID__;
const BASELINE = __BASELINE__;

const OFF_LABELS   = ['T-5','T-4','T-3','T-2','T-1','T0','T+1','T+2'];
const THRESH_VALS  = [0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.10,0.11,0.12,0.13,0.14,0.15];
const THRESH_LBLS  = THRESH_VALS.map(v => v.toFixed(2)+'%');

// Lookup: grid[oi][ti] → row
const gridLookup = {};
GRID.forEach(r => { gridLookup[r.oi + '_' + r.ti] = r; });
function g(oi, ti) { return gridLookup[oi + '_' + ti] || null; }

// ── STATE ─────────────────────────────────────────────────────────────────────
let selOff   = 5;   // T0
let selThresh = 4;  // 0.05%

// ── CHART COLOURS ─────────────────────────────────────────────────────────────
const C_TRAIN  = '#4ade80';
const C_TEST   = '#14b8a6';
const C_COUNT  = 'rgba(120,120,120,0.25)';
const C_BASE   = 'rgba(255,255,255,0.25)';
const C_AMBER  = 'rgba(251,191,36,0.45)';

const chartDefaults = {
  animation: false,
  responsive: true,
  maintainAspectRatio: true,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: {
      labels: { color: '#888', font: { size: 10 }, boxWidth: 14, padding: 10 }
    },
    tooltip: {
      backgroundColor: '#1a1a1a',
      borderColor: '#444',
      borderWidth: 1,
      titleColor: '#b8b8b8',
      bodyColor: '#e8e8e8',
      padding: 8,
    }
  },
  scales: {
    x:      { ticks: { color: '#888', font: { size: 10 } }, grid: { color: '#2a2a2a' } },
    yLeft:  { type:'linear', position:'left',  min:0.75, max:1.25,
              ticks: { color: '#888', font: { size: 10 } }, grid: { color: '#2a2a2a' } },
    yRight: { type:'linear', position:'right', min:0,
              ticks: { color: '#555', font: { size: 9 } }, grid: { drawOnChartArea: false } },
  }
};

// ── CUSTOM PLUGINS ────────────────────────────────────────────────────────────

// Vertical crosshair line at selected index
const vlinePl = {
  id: 'vline',
  afterDraw(chart, args, opts) {
    if (opts.idx === undefined || opts.idx === null) return;
    const { ctx, chartArea, scales } = chart;
    const x = scales.x.getPixelForValue(opts.idx);
    ctx.save();
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = 'rgba(255,255,255,0.55)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(x, chartArea.top);
    ctx.lineTo(x, chartArea.bottom);
    ctx.stroke();
    ctx.restore();
  }
};

// Lookahead shading for Chart B (T+1 = idx 6, T+2 = idx 7)
const lookaheadPl = {
  id: 'lookahead',
  afterDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const x6 = scales.x.getPixelForValue(6);
    const x7 = scales.x.getPixelForValue(7);
    const bw  = (x7 - x6);
    const xStart = x6 - bw / 2;
    ctx.save();
    ctx.fillStyle = 'rgba(239,68,68,0.09)';
    ctx.fillRect(xStart, chartArea.top, chartArea.right - xStart, chartArea.bottom - chartArea.top);
    ctx.fillStyle = 'rgba(239,68,68,0.55)';
    ctx.font = '9px sans-serif';
    ctx.fillText('\u26A0 lookahead', xStart + 4, chartArea.top + 13);
    ctx.restore();
  }
};

// ── BUILD CHART A (Threshold Slice) ──────────────────────────────────────────
function makeChartA() {
  const ctx = document.getElementById('chartA').getContext('2d');

  const refLine = (val, color, label) => ({
    type: 'line', label, data: THRESH_VALS.map(() => val),
    borderColor: color, borderDash: [4, 4], borderWidth: 1,
    pointRadius: 0, yAxisID: 'yLeft', order: 10
  });

  return new Chart(ctx, {
    data: {
      labels: THRESH_LBLS,
      datasets: [
        { type:'line', label:'Train PF', data:[], borderColor:C_TRAIN, backgroundColor:'transparent',
          borderWidth:2, pointRadius:3, pointHoverRadius:5, yAxisID:'yLeft', order:1 },
        { type:'line', label:'Test PF',  data:[], borderColor:C_TEST,  backgroundColor:'transparent',
          borderDash:[5,3], borderWidth:2, pointRadius:3, pointHoverRadius:5, yAxisID:'yLeft', order:2 },
        { type:'bar',  label:'Signals (train)', data:[], backgroundColor:C_COUNT, yAxisID:'yRight', order:5 },
        refLine(1.0,  C_BASE,  'PF = 1.0'),
        refLine(0.95, C_AMBER, 'PF = 0.95'),
      ]
    },
    options: Object.assign({}, chartDefaults, {
      plugins: Object.assign({}, chartDefaults.plugins, {
        vline: { idx: selThresh },
        tooltip: Object.assign({}, chartDefaults.plugins.tooltip, {
          callbacks: {
            label: function(ctx) {
              if (ctx.datasetIndex > 2) return null;
              const oi = selOff, ti = ctx.dataIndex;
              const row = g(oi, ti);
              if (!row) return ctx.dataset.label + ': —';
              if (ctx.datasetIndex === 0)
                return 'Train: PF ' + (row.pf_tr ? row.pf_tr.toFixed(2) : '—') +
                       '  WR ' + (row.wr_tr ? row.wr_tr.toFixed(1) + '%' : '—') +
                       '  N ' + row.n_tr.toLocaleString() +
                       '  Avg ' + (row.avgpnl_tr !== null ? (row.avgpnl_tr >= 0 ? '+' : '') + row.avgpnl_tr.toFixed(2) : '—');
              if (ctx.datasetIndex === 1)
                return 'Test:  PF ' + (row.pf_te ? row.pf_te.toFixed(2) : '—') +
                       '  WR ' + (row.wr_te ? row.wr_te.toFixed(1) + '%' : '—') +
                       '  N ' + row.n_te.toLocaleString() +
                       '  Avg ' + (row.avgpnl_te !== null ? (row.avgpnl_te >= 0 ? '+' : '') + row.avgpnl_te.toFixed(2) : '—');
              return 'Signals: ' + row.n_tr.toLocaleString();
            }
          }
        })
      }),
      onClick(evt, elems, chart) {
        if (!elems.length) return;
        const ti = elems[0].index;
        selThresh = ti;
        document.getElementById('sl-thresh').value = ti;
        syncAll();
      }
    }),
    plugins: [vlinePl]
  });
}

// ── BUILD CHART B (Offset Slice) ─────────────────────────────────────────────
function makeChartB() {
  const ctx = document.getElementById('chartB').getContext('2d');

  const refLine = (val, color, label) => ({
    type: 'line', label, data: OFF_LABELS.map(() => val),
    borderColor: color, borderDash: [4, 4], borderWidth: 1,
    pointRadius: 0, yAxisID: 'yLeft', order: 10
  });

  return new Chart(ctx, {
    data: {
      labels: OFF_LABELS,
      datasets: [
        { type:'line', label:'Train PF', data:[], borderColor:C_TRAIN, backgroundColor:'transparent',
          borderWidth:2, pointRadius:3, pointHoverRadius:5, yAxisID:'yLeft', order:1 },
        { type:'line', label:'Test PF',  data:[], borderColor:C_TEST,  backgroundColor:'transparent',
          borderDash:[5,3], borderWidth:2, pointRadius:3, pointHoverRadius:5, yAxisID:'yLeft', order:2 },
        { type:'bar',  label:'Signals (train)', data:[], backgroundColor:C_COUNT, yAxisID:'yRight', order:5 },
        refLine(1.0,  C_BASE,  'PF = 1.0'),
        refLine(0.95, C_AMBER, 'PF = 0.95'),
      ]
    },
    options: Object.assign({}, chartDefaults, {
      plugins: Object.assign({}, chartDefaults.plugins, {
        vline: { idx: selOff },
        tooltip: Object.assign({}, chartDefaults.plugins.tooltip, {
          callbacks: {
            label: function(ctx) {
              if (ctx.datasetIndex > 2) return null;
              const oi = ctx.dataIndex, ti = selThresh;
              const row = g(oi, ti);
              if (!row) return ctx.dataset.label + ': —';
              if (ctx.datasetIndex === 0)
                return 'Train: PF ' + (row.pf_tr ? row.pf_tr.toFixed(2) : '—') +
                       '  WR ' + (row.wr_tr ? row.wr_tr.toFixed(1) + '%' : '—') +
                       '  N ' + row.n_tr.toLocaleString() +
                       '  Avg ' + (row.avgpnl_tr !== null ? (row.avgpnl_tr >= 0 ? '+' : '') + row.avgpnl_tr.toFixed(2) : '—');
              if (ctx.datasetIndex === 1)
                return 'Test:  PF ' + (row.pf_te ? row.pf_te.toFixed(2) : '—') +
                       '  WR ' + (row.wr_te ? row.wr_te.toFixed(1) + '%' : '—') +
                       '  N ' + row.n_te.toLocaleString() +
                       '  Avg ' + (row.avgpnl_te !== null ? (row.avgpnl_te >= 0 ? '+' : '') + row.avgpnl_te.toFixed(2) : '—');
              return 'Signals: ' + row.n_tr.toLocaleString();
            }
          }
        })
      }),
      onClick(evt, elems, chart) {
        if (!elems.length) return;
        const oi = elems[0].index;
        selOff = oi;
        document.getElementById('sl-off').value = oi;
        syncAll();
      }
    }),
    plugins: [vlinePl, lookaheadPl]
  });
}

// ── UPDATE FUNCTIONS ──────────────────────────────────────────────────────────

function updateReadout() {
  const row = g(selOff, selThresh);
  document.getElementById('readout-title').textContent =
    'Offset: ' + OFF_LABELS[selOff] + '  |  Threshold: ' + THRESH_VALS[selThresh].toFixed(2) + '%';

  function fillRo(id, val, higherGood) {
    const el = document.getElementById(id);
    el.textContent = val !== null && val !== undefined ? val : '—';
    const n = parseFloat(val);
    if (isNaN(n)) { el.className = 'ro-val x'; return; }
    el.className = 'ro-val ' + (higherGood ? (n >= 1.0 ? 'g' : n >= 0.95 ? 'a' : 'r') :
                                             (n > 0 ? 'g' : n < 0 ? 'r' : 'x'));
  }

  if (!row) {
    ['ro-tr-pf','ro-tr-wr','ro-tr-n','ro-te-pf','ro-te-wr','ro-te-n'].forEach(id => {
      document.getElementById(id).textContent = '—';
    });
    document.getElementById('stability').textContent = '—';
    document.getElementById('stability').className = 'stability';
    return;
  }

  document.getElementById('ro-tr-pf').textContent = row.pf_tr ? row.pf_tr.toFixed(2) : '—';
  document.getElementById('ro-tr-wr').textContent = row.wr_tr ? row.wr_tr.toFixed(1) + '%' : '—';
  document.getElementById('ro-tr-n').textContent  = row.n_tr.toLocaleString();
  document.getElementById('ro-te-pf').textContent = row.pf_te ? row.pf_te.toFixed(2) : '—';
  document.getElementById('ro-te-wr').textContent = row.wr_te ? row.wr_te.toFixed(1) + '%' : '—';
  document.getElementById('ro-te-n').textContent  = row.n_te.toLocaleString();

  const pfTr = row.pf_tr, pfTe = row.pf_te;
  ['ro-tr-pf','ro-te-pf'].forEach(id => {
    const el = document.getElementById(id), n = parseFloat(el.textContent);
    el.className = 'ro-val ' + (!isNaN(n) ? n >= 1.0 ? 'g' : n >= 0.95 ? 'a' : 'r' : 'x');
  });

  const stEl = document.getElementById('stability');
  if (pfTr !== null && pfTe !== null) {
    const delta = Math.abs(pfTr - pfTe);
    const deltaPF = (pfTe - pfTr >= 0 ? '+' : '') + (pfTe - pfTr).toFixed(3);
    if (delta < 0.05) {
      stEl.textContent = '\u2705 Stable  |  \u0394PF = ' + deltaPF + '  (train/test within \xB10.05)';
      stEl.className = 'stability ok';
    } else {
      stEl.textContent = '\u26A0\uFE0F Unstable  |  \u0394PF = ' + deltaPF + '  (train/test gap > 0.05)';
      stEl.className = 'stability warn';
    }
  } else {
    stEl.textContent = '—';
    stEl.className = 'stability';
  }
}

function updateChartA() {
  // Threshold slice: X = thresholds, offset locked
  const trPF = [], tePF = [], counts = [];
  for (let ti = 0; ti < 15; ti++) {
    const row = g(selOff, ti);
    trPF.push(row && row.pf_tr ? row.pf_tr : null);
    tePF.push(row && row.pf_te ? row.pf_te : null);
    counts.push(row ? row.n_tr : 0);
  }
  chartA.data.datasets[0].data = trPF;
  chartA.data.datasets[1].data = tePF;
  chartA.data.datasets[2].data = counts;
  chartA.options.plugins.vline.idx = selThresh;
  document.getElementById('chartA-sub').textContent =
    'PF across thresholds (offset locked at ' + OFF_LABELS[selOff] + ')';
  chartA.update('none');
}

function updateChartB() {
  // Offset slice: X = offsets, threshold locked
  const trPF = [], tePF = [], counts = [];
  for (let oi = 0; oi < 8; oi++) {
    const row = g(oi, selThresh);
    trPF.push(row && row.pf_tr ? row.pf_tr : null);
    tePF.push(row && row.pf_te ? row.pf_te : null);
    counts.push(row ? row.n_tr : 0);
  }
  chartB.data.datasets[0].data = trPF;
  chartB.data.datasets[1].data = tePF;
  chartB.data.datasets[2].data = counts;
  chartB.options.plugins.vline.idx = selOff;
  document.getElementById('chartB-sub').textContent =
    'PF across offsets (threshold locked at ' + THRESH_VALS[selThresh].toFixed(2) + '%)';
  chartB.update('none');
}

function syncAll() {
  selOff    = +document.getElementById('sl-off').value;
  selThresh = +document.getElementById('sl-thresh').value;
  document.getElementById('lbl-off').textContent    = OFF_LABELS[selOff];
  document.getElementById('lbl-thresh').textContent = THRESH_VALS[selThresh].toFixed(2) + '%';
  updateReadout();
  updateChartA();
  updateChartB();
}

function onSlide() { syncAll(); }

// ── INIT ──────────────────────────────────────────────────────────────────────
Chart.defaults.color = '#888';
const chartA = makeChartA();
const chartB = makeChartB();
syncAll();
</script>
</body>
</html>
"""

HTML = TEMPLATE.replace('__GRID__', grid_js).replace('__BASELINE__', baseline_js)


# ── Add "Open Chart View →" button to existing H3 HTML ────────────────────────
if H3_OUT.exists():
    h3_html = H3_OUT.read_text(encoding='utf-8')
    if 'fv2_h3_chart.html' not in h3_html:
        btn = '<a href="fv2_h3_chart.html" target="_blank" style="margin-left:auto;background:#222;border:1px solid #444;color:#14b8a6;border-radius:5px;padding:5px 12px;font-size:11px;text-decoration:none;white-space:nowrap">Open Chart View \u2192</a>'
        h3_html = h3_html.replace('<h1>H3 \u2014 Gap 1: Slope Offset + Threshold Tuner</h1>',
                                   '<div style="display:flex;align-items:center;gap:12px"><h1>H3 \u2014 Gap 1: Slope Offset + Threshold Tuner</h1>' + btn + '</div>')
        H3_OUT.write_text(h3_html, encoding='utf-8')
        print('\nAdded "Open Chart View" button to H3.')
    else:
        print('\nH3 already has chart button.')


# ── Write H3.1 ─────────────────────────────────────────────────────────────────
OUT.write_text(HTML, encoding='utf-8')
size_mb = OUT.stat().st_size / 1e6
print(f'Saved : {OUT}')
print(f'Size  : {size_mb:.2f} MB')
if size_mb > 1.0:
    print(f'Note  : Larger than 1 MB target — Chart.js CDN loaded separately, so file is fine.')
