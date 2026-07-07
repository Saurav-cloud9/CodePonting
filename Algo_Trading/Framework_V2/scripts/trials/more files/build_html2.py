"""
Build fv2_calculator.html — Panel A vs B calculator for all 30 fv2 stocks.
Stock dropdown + All Stocks aggregate. 1-share mode only.
"""
import json
from pathlib import Path
import pandas as pd

CSV_DIR = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/data/historical/csv/intraday_5min')
OUT     = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_calculator.html')

STOCKS = [
    'ADANIPORTS', 'ASHOKLEY', 'AXISBANK', 'BAJFINANCE', 'BANDHANBNK',
    'BHARTIARTL', 'CIPLA', 'COALINDIA', 'DABUR', 'DIVISLAB',
    'HDFCBANK', 'HINDALCO', 'ICICIBANK', 'INDUSINDBK', 'INFY',
    'ITC', 'JSWSTEEL', 'NATIONALUM', 'NTPC', 'ONGC',
    'PNB', 'POWERGRID', 'RELIANCE', 'SBIN', 'SUNPHARMA',
    'TATAMOTORS', 'TATASTEEL', 'TECHM', 'VEDL', 'WIPRO',
]
SIG_MAP = {'rising': 0, 'flat': 1, 'falling': 2}

# ── Build per-stock trade arrays ───────────────────────────────────────────────
stocks_data = {}   # stock → list of [sig_idx, raw_pnl, win]
all_trades  = []   # aggregate for _ALL_

for stock in STOCKS:
    csv = CSV_DIR / f'{stock}_5min.csv'
    if not csv.exists():
        print(f'  SKIP (not found): {stock}')
        stocks_data[stock] = []
        continue
    df = pd.read_csv(csv)
    t  = df[df['signal_type'].notna()].copy()
    arr = [
        [SIG_MAP[row['signal_type']], round(row['raw_pnl'], 4), int(row['win'])]
        for _, row in t.iterrows()
    ]
    stocks_data[stock] = arr
    all_trades.extend(arr)
    r  = (t['signal_type'] == 'rising').sum()
    fl = (t['signal_type'] == 'flat').sum()
    fa = (t['signal_type'] == 'falling').sum()
    print(f'  {stock:15s} {len(arr):4d} signals  R={r} F={fl} D={fa}')

stocks_data['_ALL_'] = all_trades
print(f'\nTotal signals (all stocks): {len(all_trades):,}')

# Compact JSON
stocks_js = json.dumps(stocks_data, separators=(',', ':'))

# ── Styles ─────────────────────────────────────────────────────────────────────
CSS = """
:root {
  --bg:     #0f1117;
  --panel:  #1a1d2e;
  --card:   #20243a;
  --border: #2a2d40;
  --text:   #e1e4e8;
  --muted:  #8b92a5;
  --green:  #00d4a0;
  --red:    #ff5f5f;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: 'JetBrains Mono', Consolas, monospace;
  min-height: 100vh;
  font-size: 14px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 28px;
  border-bottom: 1px solid var(--border);
  background: #12151f;
  flex-wrap: wrap;
  gap: 12px;
}
.header-left  { display: flex; flex-direction: column; gap: 4px; }
.header-title { font-size: 17px; font-weight: 700; }
.header-meta  { font-size: 12px; color: var(--muted); }
.stock-select-wrap { display: flex; align-items: center; gap: 10px; }
.stock-select-wrap label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
#stock-select {
  background: var(--card);
  border: 1px solid var(--border);
  color: var(--text);
  font-family: inherit;
  font-size: 13px;
  padding: 7px 12px;
  border-radius: 6px;
  cursor: pointer;
  outline: none;
  min-width: 160px;
}
#stock-select:focus { border-color: #4a4d68; }
.main { padding: 24px 28px; display: flex; flex-direction: column; gap: 22px; }

/* Panels */
.panels { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
}
.panel-title    { font-size: 13px; font-weight: 700; margin-bottom: 4px; }
.panel-subtitle { font-size: 11px; color: var(--muted); margin-bottom: 16px; }
.metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.metric-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 16px;
  position: relative;
  cursor: default;
}
.metric-card:hover .tooltip { display: block; }
.metric-label {
  font-size: 10px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-bottom: 8px;
}
.metric-value { font-size: 20px; font-weight: 700; color: var(--text); line-height: 1.2; }
.metric-value.green { color: var(--green); }
.metric-value.red   { color: var(--red); }
.tooltip {
  display: none;
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  background: #282c42;
  border: 1px solid #3a3d55;
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 11px;
  color: var(--muted);
  line-height: 1.6;
  z-index: 20;
  width: 240px;
  white-space: normal;
  pointer-events: none;
}

/* Delta Bar */
.delta-label {
  font-size: 11px;
  color: var(--muted);
  margin-bottom: 10px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.delta-bar { display: flex; gap: 10px; flex-wrap: wrap; }
.pill {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  min-width: 80px;
}
.pill.green   { background: rgba(0,212,160,0.10); border: 1px solid rgba(0,212,160,0.30); color: var(--green); }
.pill.red     { background: rgba(255,95,95,0.10);  border: 1px solid rgba(255,95,95,0.30);  color: var(--red); }
.pill.neutral { background: rgba(139,146,165,0.10); border: 1px solid rgba(139,146,165,0.25); color: var(--muted); }
.pill-name { font-size: 9px; opacity: 0.65; font-weight: 400; text-transform: uppercase; letter-spacing: 0.4px; }

/* Breakdown Table */
.table-section {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
}
.table-title { font-size: 13px; font-weight: 700; margin-bottom: 14px; }
table { width: 100%; border-collapse: collapse; }
th {
  font-size: 10px;
  color: var(--muted);
  text-align: left;
  padding: 8px 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
}
td { padding: 11px 14px; font-size: 13px; border-bottom: 1px solid var(--border); }
tr:last-child td { border-bottom: none; }
tr.rising  td { background: rgba(0,212,160,0.04); }
tr.flat    td { background: transparent; }
tr.falling td { background: rgba(255,95,95,0.04); }
tr.rising  td:first-child { border-left: 3px solid var(--green); }
tr.flat    td:first-child { border-left: 3px solid var(--muted); }
tr.falling td:first-child { border-left: 3px solid var(--red); }

/* Footer */
.footer {
  text-align: center;
  font-size: 11px;
  color: var(--muted);
  padding: 16px 28px;
  border-top: 1px solid var(--border);
  line-height: 2;
}
"""

JS = """
// STOCKS_DATA: {stock: [[sig_idx, raw_pnl, win], ...], _ALL_: [...]}
// sig_idx: 0=rising, 1=flat, 2=falling
const STOCKS_DATA = STOCKS_DATA_PLACEHOLDER;

const SIG_NAMES = ['Rising', 'Flat', 'Falling'];
const SIG_CLS   = ['rising', 'flat', 'falling'];

function computeMetrics(trades, cap=1000000) {
  if (!trades.length) return {count:0, winRate:0, avgPnl:0, cagr:-100, maxDd:-100, pf:0};
  const pnls = trades.map(t => t[1]);
  let eq = cap, peak = cap, maxDd = 0;
  for (const p of pnls) {
    eq += p;
    if (eq > peak) peak = eq;
    const dd = (eq - peak) / peak * 100;
    if (dd < maxDd) maxDd = dd;
  }
  const finalEq = cap + pnls.reduce((a,b) => a+b, 0);
  const cagr = finalEq > 0
    ? (Math.pow(finalEq / cap, 0.25) - 1) * 100
    : (finalEq / cap - 1) * 100;
  const gp = pnls.filter(p => p > 0).reduce((a,b) => a+b, 0);
  const gl = Math.abs(pnls.filter(p => p < 0).reduce((a,b) => a+b, 0));
  const pf = gl > 0 ? gp / gl : 999;
  const winCount = trades.filter(t => t[2] === 1).length;
  return {
    count:   trades.length,
    winRate: winCount / trades.length * 100,
    avgPnl:  pnls.reduce((a,b) => a+b, 0) / trades.length,
    cagr:    cagr,
    maxDd:   maxDd,
    pf:      pf
  };
}

function fmtPnl(v)  { return (v >= 0 ? 'Rs +' : 'Rs -') + Math.abs(v).toFixed(2); }
function fmtCagr(v) { return (v >= 0 ? '+' : '') + v.toFixed(2) + '%'; }
function fmtWr(v)   { return v.toFixed(1) + '%'; }
function fmtPf(v)   { return v.toFixed(2); }
function fmtCnt(v)  { return v.toLocaleString('en-IN'); }
function fmtDd(v)   { return v.toFixed(2) + '%'; }

function cardColor(key, bVal, aVal) {
  if (key === 'count') return '';
  return bVal > aVal ? 'green' : 'red';
}
function pillCls(key, delta) {
  if (key === 'count') return 'neutral';
  return delta > 0 ? 'green' : 'red';
}
function fmtDelta(key, v) {
  if (key === 'winRate') return (v>=0?'+':'')+v.toFixed(1)+'%';
  if (key === 'cagr' || key === 'maxDd') return (v>=0?'+':'')+v.toFixed(2)+'%';
  if (key === 'avgPnl') { const r = v.toFixed(2); return (v>=0?'Rs +':'Rs -')+Math.abs(r); }
  if (key === 'pf') return (v>=0?'+':'')+v.toFixed(2);
  return (v>=0?'+':'')+v.toLocaleString('en-IN');
}

const METRIC_DEFS = [
  { key:'count',   label:'Signal Count',   fmt:fmtCnt,  tip:'Total trade entries triggered by signal logic' },
  { key:'winRate', label:'Win Rate',        fmt:fmtWr,   tip:'Trades where exit_reason == target &divide; total &times; 100' },
  { key:'avgPnl',  label:'Avg PnL / Trade', fmt:fmtPnl,  tip:'Mean Rs PnL per trade (1-share: price points &times; 1).' },
  { key:'cagr',    label:'CAGR (4yr)',      fmt:fmtCagr, tip:'Annualised return: (final_equity &divide; 10L)<sup>0.25</sup> &minus; 1. Non-compounding.' },
  { key:'maxDd',   label:'Max Drawdown',    fmt:fmtDd,   tip:'Peak-to-trough on equity curve as % of peak. More negative = worse.' },
  { key:'pf',      label:'Profit Factor',   fmt:fmtPf,   tip:'Gross profit &divide; gross loss. &gt;1.0 = positive edge.' },
];
const DELTA_LABELS = {count:'Signals',winRate:'Win Rate',avgPnl:'Avg PnL',cagr:'CAGR',maxDd:'Max DD',pf:'Prof. Factor'};

function renderPanel(gridId, m, refM, isBPanel) {
  const grid = document.getElementById(gridId);
  grid.innerHTML = METRIC_DEFS.map(d => {
    const v   = m[d.key];
    const cls = isBPanel ? cardColor(d.key, v, refM[d.key]) : '';
    return `<div class="metric-card">
      <div class="metric-label">${d.label}</div>
      <div class="metric-value ${cls}">${d.fmt(v)}</div>
      <div class="tooltip">${d.tip}</div>
    </div>`;
  }).join('');
}

function renderDeltaBar(pa, pb) {
  const bar = document.getElementById('delta-bar');
  bar.innerHTML = METRIC_DEFS.map(d => {
    const delta = pb[d.key] - pa[d.key];
    const cls   = pillCls(d.key, delta);
    return `<div class="pill ${cls}">
      <span>${fmtDelta(d.key, delta)}</span>
      <span class="pill-name">${DELTA_LABELS[d.key]}</span>
    </div>`;
  }).join('');
}

function renderBreakdown(trades) {
  const tbody = document.getElementById('bk-tbody');
  tbody.innerHTML = [0,1,2].map(si => {
    const sub = trades.filter(t => t[0] === si);
    const m   = computeMetrics(sub);
    return `<tr class="${SIG_CLS[si]}">
      <td>${SIG_NAMES[si]}</td>
      <td>${fmtCnt(m.count)}</td>
      <td>${fmtWr(m.winRate)}</td>
      <td>${fmtPnl(m.avgPnl)}</td>
    </tr>`;
  }).join('');
}

function getCurrentTrades() {
  const sel = document.getElementById('stock-select').value;
  return STOCKS_DATA[sel] || [];
}

function renderAll() {
  const trades  = getCurrentTrades();
  const rising  = trades.filter(t => t[0] === 0);
  const pa = computeMetrics(trades);
  const pb = computeMetrics(rising);
  renderPanel('pa-grid', pa, pa, false);
  renderPanel('pb-grid', pb, pa, true);
  renderDeltaBar(pa, pb);
  renderBreakdown(trades);
  // Update meta line
  const sel = document.getElementById('stock-select').value;
  document.getElementById('header-meta').textContent =
    (sel === '_ALL_' ? 'All 30 Stocks' : sel) + '  \\u00b7  2022\\u20132025';
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('stock-select').addEventListener('change', renderAll);
  renderAll();
});
"""

STOCKS_OPT = '\n'.join(
    f'<option value="{s}">{"All 30 Stocks" if s == "_ALL_" else s}</option>'
    for s in (['_ALL_'] + STOCKS)
)

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>fv2 Signal Calculator</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <div class="header-title">fv2 Signal Calculator</div>
    <div class="header-meta" id="header-meta">All 30 Stocks &nbsp;&middot;&nbsp; 2022&ndash;2025</div>
  </div>
  <div class="stock-select-wrap">
    <label>Stock</label>
    <select id="stock-select">
{STOCKS_OPT}
    </select>
  </div>
</div>

<div class="main">

  <div class="panels">
    <div class="panel">
      <div class="panel-title">Panel A &mdash; All Signals</div>
      <div class="panel-subtitle">No filter applied</div>
      <div class="metric-grid" id="pa-grid"></div>
    </div>
    <div class="panel">
      <div class="panel-title">Panel B &mdash; Rising MA Only</div>
      <div class="panel-subtitle">Slope &gt; +0.05% &nbsp;&middot;&nbsp; <em>in-sample &middot; not validated OOS</em></div>
      <div class="metric-grid" id="pb-grid"></div>
    </div>
  </div>

  <div>
    <div class="delta-label">Panel B vs Panel A &mdash; delta</div>
    <div class="delta-bar" id="delta-bar"></div>
  </div>

  <div class="table-section">
    <div class="table-title">Breakdown by Slope Type</div>
    <table>
      <thead>
        <tr>
          <th>Slope</th>
          <th>Signals</th>
          <th>Win Rate</th>
          <th>Avg PnL / Trade</th>
        </tr>
      </thead>
      <tbody id="bk-tbody"></tbody>
    </table>
  </div>

</div>

<div class="footer">
  2022&ndash;2025 &nbsp;&middot;&nbsp; SL=A &nbsp;&middot;&nbsp;
  slippage: 1-tick entry + SL exit &nbsp;&middot;&nbsp; charges not included<br>
  1-Share Mode: PnL = price points &times; 1 share &nbsp;&middot;&nbsp; no position sizing applied
</div>

<script>
{JS.replace('STOCKS_DATA_PLACEHOLDER', stocks_js)}
</script>
</body>
</html>"""

OUT.write_text(HTML, encoding='utf-8')
print(f"\nSaved : {OUT}")
print(f"Size  : {OUT.stat().st_size:,} bytes")
