"""
Build fv2_h3_slope_tuner.html — Gap 1: slope offset + threshold tuner.

Reads all 30 stock CSVs, detects all bounce signals (H1 universe, no position guard),
computes slope at 8 offsets (T-5 to T+2) per signal, embeds compact JSON.

Signal row: [period, s_t-5..s_t+2 (8 values), pnl, win, stock_idx]
  Indices:    0       1..8                       9    10   11
  period:     0=train(2022-2023)  1=test(2024-2025)

Target output: <5 MB embedded data, <10 MB total HTML.
"""

import json
from pathlib import Path

import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────────
CSV_DIR = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/data/historical/csv/intraday_5min')
OUT     = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_h3_slope_tuner.html')
RES_DIR = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/research')

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
OFFSETS    = [-5, -4, -3, -2, -1, 0, 1, 2]    # T-5 → T+2
THRESHOLDS = [round(x * 0.01, 2) for x in range(1, 16)]  # 0.01 → 0.15


# ── Signal extraction ──────────────────────────────────────────────────────────

def build_stock_signals(stock: str, stock_idx: int) -> list:
    csv = CSV_DIR / f'{stock}_5min.csv'
    df  = pd.read_csv(csv)
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df = df.sort_values('datetime').reset_index(drop=True)

    # ATR14 (true range rolling mean, global — not per-day reset)
    prev_close = df['close'].shift(1)
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - prev_close).abs(),
        (df['low']  - prev_close).abs(),
    ], axis=1).max(axis=1)
    df['atr14'] = tr.rolling(14).mean()

    # Slope: 5-candle MA20 change (global)
    df['slope'] = (df['ma20'] - df['ma20'].shift(5)) / df['ma20'] * 100

    # Filter to output range
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
                i += 1
                continue
            if row['low'] > row['ma20']:
                i += 1
                continue

            touch_idx = i

            # Slopes at 8 offsets (T-5 to T+2), within-day bounds only
            slopes = []
            for O in OFFSETS:
                ref = touch_idx + O
                if 0 <= ref < n and pd.notna(day.iloc[ref]['slope']):
                    slopes.append(round(float(day.iloc[ref]['slope']), 4))
                else:
                    slopes.append(None)

            # Find bounce: close > MA20 AND vol >= 1.2×vol_ma20, within 3 candles
            bounce_idx = None
            for j in range(touch_idx, min(touch_idx + 4, n)):
                b = day.iloc[j]
                if (pd.notna(b['ma20']) and b['close'] > b['ma20'] and
                        pd.notna(b['vol_ma20']) and b['volume'] >= 1.2 * b['vol_ma20']):
                    bounce_idx = j
                    break

            if bounce_idx is not None:
                entry_idx = bounce_idx + 1 if bounce_idx + 1 < n else None
                pnl, win = None, None
                if entry_idx is not None:
                    entry_price = day.iloc[entry_idx]['open']
                    atr_val     = day.iloc[touch_idx]['atr14']
                    if pd.notna(entry_price) and pd.notna(atr_val) and atr_val > 0:
                        sl     = entry_price - 2.5 * atr_val
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

                # [period, s0..s7, pnl, win, stock_idx]
                signals.append([period] + slopes + [pnl, win, stock_idx])
                i = bounce_idx + 2
            else:
                i += 1

    return signals


# ── Heatmap precompute ─────────────────────────────────────────────────────────

def compute_heatmap(signals: list) -> dict:
    """Precompute PF + count for 8×15 grid, per period."""
    result = {}
    for period_key, period_val in [('train', 0), ('test', 1)]:
        psigs = [s for s in signals if s[0] == period_val and s[9] is not None]
        pf_grid    = []  # [offset_idx][thresh_idx]
        count_grid = []
        for oi in range(8):
            col_pf, col_cnt = [], []
            for thresh in THRESHOLDS:
                fs = [s for s in psigs if s[1 + oi] is not None and s[1 + oi] >= thresh]
                if not fs:
                    col_pf.append(None); col_cnt.append(0); continue
                gp = sum(s[9] for s in fs if s[9] > 0)
                gl = abs(sum(s[9] for s in fs if s[9] < 0))
                col_pf.append(round(gp / gl, 4) if gl > 0 else (9.99 if gp > 0 else None))
                col_cnt.append(len(fs))
            pf_grid.append(col_pf)
            count_grid.append(col_cnt)
        result[period_key] = {'pf': pf_grid, 'count': count_grid}
    return result


def compute_baseline(signals: list) -> dict:
    """Baseline stats (all periods combined + per period)."""
    def _stats(sigs, years):
        sigs = [s for s in sigs if s[9] is not None]
        if not sigs:
            return {'pf': None, 'wr': None, 'avgPnl': None, 'count': 0, 'cagr': None}
        wins = sum(1 for s in sigs if s[10] == 1)
        total = sum(s[9] for s in sigs)
        gp = sum(s[9] for s in sigs if s[9] > 0)
        gl = abs(sum(s[9] for s in sigs if s[9] < 0))
        pf = round(gp / gl, 4) if gl > 0 else (9.99 if gp > 0 else None)
        final_eq = 1_000_000 + total
        cagr = round((pow(final_eq / 1_000_000, 1 / years) - 1) * 100, 2) if final_eq > 0 else None
        return {
            'pf': pf,
            'wr': round(wins / len(sigs) * 100, 2),
            'avgPnl': round(total / len(sigs), 2),
            'count': len(sigs),
            'cagr': cagr,
        }
    return {
        'all':   _stats(signals, 4),
        'train': _stats([s for s in signals if s[0] == 0], 2),
        'test':  _stats([s for s in signals if s[0] == 1], 2),
    }


# ── Main ───────────────────────────────────────────────────────────────────────

print('Building H3 data for 30 stocks...')
all_signals = []
for idx, stock in enumerate(STOCKS):
    sigs = build_stock_signals(stock, idx)
    all_signals.extend(sigs)
    print(f'  {stock:15s}  signals={len(sigs):5d}')

total = len(all_signals)
train_n = sum(1 for s in all_signals if s[0] == 0)
test_n  = sum(1 for s in all_signals if s[0] == 1)
print(f'\nTotal signals: {total:,}  (train={train_n:,}  test={test_n:,})')

print('Precomputing heatmap...')
heatmap_data = compute_heatmap(all_signals)
baseline     = compute_baseline(all_signals)
print(f"All  PF={baseline['all']['pf']}   count={baseline['all']['count']:,}")
print(f"Train PF={baseline['train']['pf']}  count={baseline['train']['count']:,}")
print(f"Test  PF={baseline['test']['pf']}   count={baseline['test']['count']:,}")

print('Serialising...')
stocks_js   = json.dumps(STOCKS)
heatmap_js  = json.dumps(heatmap_data, separators=(',', ':'))
baseline_js = json.dumps(baseline,     separators=(',', ':'))
signals_js  = json.dumps(all_signals,  separators=(',', ':'))
print(f'  Signals JS size: {len(signals_js)/1e6:.1f} MB')


# ── HTML ───────────────────────────────────────────────────────────────────────

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>H3 — Gap 1 Slope Tuner</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0f0f0f;--bg2:#1a1a1a;--bg3:#222;--bg4:#2a2a2a;--bg5:#2f2f2f;
  --fg:#e8e8e8;--fg2:#b8b8b8;--fg3:#888;--fg4:#555;
  --border:#333;--border2:#444;
  --green:#4ade80;--red:#f87171;--amber:#fbbf24;--teal:#14b8a6;
  --blue:#60a5fa;
}}
body{{background:var(--bg);color:var(--fg);font-family:'Segoe UI',system-ui,sans-serif;font-size:13px;line-height:1.4;padding:16px 20px}}
h1{{font-size:15px;font-weight:600;color:var(--fg2);margin-bottom:14px}}
.section{{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:14px}}
.sec-title{{font-size:11px;font-weight:700;color:var(--fg3);text-transform:uppercase;letter-spacing:.6px;margin-bottom:14px}}

/* ── HEATMAP ── */
.hm-wrapper{{display:flex;gap:28px;overflow-x:auto;padding-bottom:4px}}
.hm-panel{{flex:1;min-width:0}}
.hm-panel-title{{font-size:12px;font-weight:600;color:var(--fg2);text-align:center;margin-bottom:8px}}
.hm-body{{display:flex;gap:4px}}
.hm-yaxis{{display:flex;flex-direction:column;padding-top:22px}}
.hm-yaxis span{{height:30px;display:flex;align-items:center;justify-content:flex-end;font-size:9px;color:var(--fg3);padding-right:4px;white-space:nowrap}}
.hm-inner{{display:flex;flex-direction:column;gap:0}}
.hm-xaxis{{display:flex;margin-bottom:2px}}
.hm-xaxis span{{width:64px;text-align:center;font-size:10px;color:var(--fg3)}}
.hm-xaxis span.la{{color:#f59e0b;font-weight:600}}
.hm-row{{display:flex}}
.cell{{width:64px;height:30px;display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;border:1px solid transparent;position:relative;transition:filter .1s}}
.cell:hover{{filter:brightness(1.3);z-index:2}}
.cell.sel{{border:2px solid #fff!important;z-index:3}}
.cell .pv{{font-size:10px;font-weight:700;line-height:1.1}}
.cell .sc{{font-size:8.5px;opacity:.6;line-height:1.1}}
.cell.la-cell::after{{content:'';position:absolute;inset:0;background:repeating-linear-gradient(45deg,rgba(0,0,0,.25) 0,rgba(0,0,0,.25) 3px,transparent 3px,transparent 7px);pointer-events:none}}
/* PF colour bands */
.c0{{background:#1c0a0a;color:#888}}        /* no signal */
.c1{{background:#4a0c0c;color:#fca5a5}}     /* PF < 0.90 */
.c2{{background:#4a2500;color:#fcd34d}}     /* 0.90–0.95 */
.c3{{background:#0a2e14;color:#6ee7a0}}     /* 0.95–1.00 */
.c4{{background:#14532d;color:#4ade80}}     /* 1.00–1.10 */
.c5{{background:#166534;color:#bbf7d0;box-shadow:inset 0 0 0 1px #22c55e}}  /* >1.10 */

/* ── SLIDERS ── */
.slider-block{{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:10px}}
.sl-group{{flex:1;min-width:160px}}
.sl-group label{{font-size:11px;color:var(--fg3);display:flex;justify-content:space-between;margin-bottom:4px}}
.sl-group label b{{color:var(--fg);font-weight:700}}
input[type=range]{{width:100%;accent-color:var(--teal);cursor:pointer}}
.max-row{{display:flex;align-items:center;gap:10px;margin-bottom:12px;font-size:11px;color:var(--fg3)}}
.tog{{cursor:pointer;border:1px solid var(--border2);border-radius:4px;padding:2px 9px;font-size:11px;background:var(--bg4);color:var(--fg3);transition:all .15s}}
.tog.on{{background:var(--teal);color:#000;border-color:var(--teal);font-weight:600}}

/* ── STATS DUAL ── */
.stats-dual{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:10px}}
.sp{{background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:11px}}
.sp-title{{font-size:11px;font-weight:700;color:var(--fg3);margin-bottom:8px}}
.sr{{display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid var(--bg4)}}
.sr:last-child{{border:none}}
.sl{{font-size:11px;color:var(--fg3)}}
.sv{{font-size:12px;font-weight:700}}
.sv.g{{color:var(--green)}}.sv.r{{color:var(--red)}}.sv.a{{color:var(--amber)}}.sv.x{{color:var(--fg3)}}

/* ── WARNING ── */
.warn{{display:none;border-radius:4px;padding:6px 12px;font-size:11px;margin-bottom:10px}}
.warn.amber{{background:#3a1f00;border:1px solid #78350f;color:#fde68a}}
.warn.red{{background:#3a0505;border:1px solid #7f1d1d;color:#fca5a5}}

/* ── COMPARISON ── */
.comp-grid{{display:grid;grid-template-columns:1fr 80px 1fr;gap:12px;align-items:start;margin-bottom:14px}}
.cp{{background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:11px}}
.cp-title{{font-size:11px;font-weight:700;color:var(--fg3);margin-bottom:8px}}
.delta-col{{display:flex;flex-direction:column;gap:8px;padding-top:30px;align-items:center}}
.di{{display:flex;flex-direction:column;align-items:center;gap:2px}}
.di .dlbl{{font-size:9px;color:var(--fg3)}}
.di .dval{{font-size:11px;font-weight:700}}
.di .dval.g{{color:var(--green)}}.di .dval.r{{color:var(--red)}}.di .dval.x{{color:var(--fg3)}}

/* ── STOCK TABLE ── */
.tbl{{width:100%;border-collapse:collapse;font-size:11px}}
.tbl th{{background:var(--bg4);color:var(--fg3);text-align:left;padding:5px 8px;border-bottom:1px solid var(--border2);font-weight:700;white-space:nowrap}}
.tbl td{{padding:4px 8px;border-bottom:1px solid var(--bg3);white-space:nowrap}}
.tbl tr:hover td{{background:var(--bg3)}}
.badge{{display:inline-block;font-size:9px;padding:1px 5px;border-radius:3px;font-weight:700}}
.badge.up{{background:#14532d;color:#4ade80}}
.badge.dn{{background:#4a0c0c;color:#fca5a5}}
.badge.eq{{background:var(--bg4);color:var(--fg3)}}

/* ── EXPORT ── */
.exp-btn{{display:block;margin:0 auto 14px;background:var(--bg3);border:1px solid var(--border2);color:var(--fg2);border-radius:6px;padding:7px 22px;cursor:pointer;font-size:12px}}
.exp-btn:hover{{background:var(--bg4)}}
.toast{{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#14532d;color:#bbf7d0;border-radius:6px;padding:7px 20px;font-size:12px;font-weight:600;opacity:0;transition:opacity .3s;pointer-events:none;z-index:99}}
.toast.show{{opacity:1}}

footer{{text-align:center;color:var(--fg4);font-size:11px;padding:10px 0}}
</style>
</head>
<body>
<h1>H3 — Gap 1: Slope Offset + Threshold Tuner</h1>

<!-- ── SECTION 1 ── -->
<div class="section">
  <div class="sec-title">Section 1 — Profit Factor Heatmap &nbsp;·&nbsp; Click cell to update sliders</div>
  <div class="hm-wrapper">
    <div class="hm-panel">
      <div class="hm-panel-title">Train &nbsp;·&nbsp; 2022–2023</div>
      <div class="hm-body">
        <div class="hm-yaxis" id="yaxis-train"></div>
        <div class="hm-inner">
          <div class="hm-xaxis" id="xaxis-train"></div>
          <div id="hm-train"></div>
        </div>
      </div>
    </div>
    <div class="hm-panel">
      <div class="hm-panel-title">Test &nbsp;·&nbsp; 2024–2025</div>
      <div class="hm-body">
        <div class="hm-yaxis" id="yaxis-test"></div>
        <div class="hm-inner">
          <div class="hm-xaxis" id="xaxis-test"></div>
          <div id="hm-test"></div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ── SECTION 2 ── -->
<div class="section">
  <div class="sec-title">Section 2 — Fine-tune</div>
  <div class="slider-block">
    <div class="sl-group">
      <label>Offset &nbsp;<b id="lbl-off">T0</b></label>
      <input type="range" id="sl-off" min="0" max="7" value="5" oninput="onSlide()">
    </div>
    <div class="sl-group">
      <label>Min Threshold &nbsp;<b id="lbl-min">0.05%</b></label>
      <input type="range" id="sl-min" min="0" max="14" value="4" oninput="onSlide()">
    </div>
  </div>
  <div class="max-row">
    <span>Max Threshold:</span>
    <button class="tog" id="max-tog" onclick="toggleMax()">OFF</button>
    <div class="sl-group" id="max-sg" style="display:none;flex:1;max-width:220px">
      <label>Max &nbsp;<b id="lbl-max">0.15%</b></label>
      <input type="range" id="sl-max" min="0" max="14" value="14" oninput="onSlide()">
    </div>
  </div>
  <div class="warn" id="warn"></div>
  <div class="stats-dual">
    <div class="sp">
      <div class="sp-title">Train &nbsp;·&nbsp; 2022–2023</div>
      <div class="sr"><span class="sl">PF</span><span class="sv" id="tr-pf">—</span></div>
      <div class="sr"><span class="sl">Win Rate</span><span class="sv" id="tr-wr">—</span></div>
      <div class="sr"><span class="sl">Avg PnL</span><span class="sv" id="tr-avg">—</span></div>
      <div class="sr"><span class="sl">Signals</span><span class="sv" id="tr-cnt">—</span></div>
      <div class="sr"><span class="sl">CAGR</span><span class="sv" id="tr-cagr">—</span></div>
    </div>
    <div class="sp">
      <div class="sp-title">Test &nbsp;·&nbsp; 2024–2025</div>
      <div class="sr"><span class="sl">PF</span><span class="sv" id="te-pf">—</span></div>
      <div class="sr"><span class="sl">Win Rate</span><span class="sv" id="te-wr">—</span></div>
      <div class="sr"><span class="sl">Avg PnL</span><span class="sv" id="te-avg">—</span></div>
      <div class="sr"><span class="sl">Signals</span><span class="sv" id="te-cnt">—</span></div>
      <div class="sr"><span class="sl">CAGR</span><span class="sv" id="te-cagr">—</span></div>
    </div>
  </div>
</div>

<!-- ── SECTION 3 ── -->
<div class="section">
  <div class="sec-title">Section 3 — Comparison Panel</div>
  <div class="comp-grid">
    <div class="cp">
      <div class="cp-title">Panel A — All signals (baseline)</div>
      <div class="sr"><span class="sl">PF</span><span class="sv" id="a-pf">—</span></div>
      <div class="sr"><span class="sl">Win Rate</span><span class="sv" id="a-wr">—</span></div>
      <div class="sr"><span class="sl">Avg PnL</span><span class="sv" id="a-avg">—</span></div>
      <div class="sr"><span class="sl">Signals</span><span class="sv" id="a-cnt">—</span></div>
      <div class="sr"><span class="sl">CAGR (4yr)</span><span class="sv" id="a-cagr">—</span></div>
    </div>
    <div class="delta-col" id="delta-col"></div>
    <div class="cp">
      <div class="cp-title">Panel B — Current filter</div>
      <div class="sr"><span class="sl">PF</span><span class="sv" id="b-pf">—</span></div>
      <div class="sr"><span class="sl">Win Rate</span><span class="sv" id="b-wr">—</span></div>
      <div class="sr"><span class="sl">Avg PnL</span><span class="sv" id="b-avg">—</span></div>
      <div class="sr"><span class="sl">Signals</span><span class="sv" id="b-cnt">—</span></div>
      <div class="sr"><span class="sl">CAGR (4yr)</span><span class="sv" id="b-cagr">—</span></div>
    </div>
  </div>

  <table class="tbl">
    <thead>
      <tr>
        <th>Stock</th><th>Signals (B)</th><th>WR (B)</th><th>PF (B)</th><th>vs Baseline</th>
      </tr>
    </thead>
    <tbody id="stk-tbody"></tbody>
  </table>
</div>

<button class="exp-btn" onclick="exportObs()">Save Observation to gap_observations.md</button>
<div class="toast" id="toast">Copied to clipboard — paste into gap_observations.md</div>

<footer>H3 — Gap 1 tuner &nbsp;·&nbsp; 30 stocks &nbsp;·&nbsp; 2022–2025 &nbsp;·&nbsp; 1-share mode<br>
Train: 2022–2023 &nbsp;|&nbsp; Test: 2024–2025 &nbsp;·&nbsp; No position guard</footer>

<script>
// ── EMBEDDED DATA ──────────────────────────────────────────────────────────────
const STOCKS      = {stocks_js};
const THRESH      = [0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.10,0.11,0.12,0.13,0.14,0.15];
const OFF_LABELS  = ['T-5','T-4','T-3','T-2','T-1','T0','T+1','T+2'];
const hmData      = {heatmap_js};
const baseline    = {baseline_js};
const allSigs     = {signals_js};

// ── STATE ─────────────────────────────────────────────────────────────────────
let selOff = 5;   // default T0
let selMin = 4;   // index → 0.05%
let selMax = 14;  // index → 0.15%
let maxOn  = false;

// ── PRECOMPUTE per-stock baseline PF (all signals, no filter) ─────────────────
const basePF = STOCKS.map((_, si) => {{
  const ss = allSigs.filter(s => s[11] === si && s[9] !== null);
  if (!ss.length) return null;
  const gp = ss.filter(s=>s[9]>0).reduce((a,s)=>a+s[9],0);
  const gl = Math.abs(ss.filter(s=>s[9]<0).reduce((a,s)=>a+s[9],0));
  return gl > 0 ? gp/gl : (gp>0 ? 9.99 : 0);
}});

// ── HEATMAP ───────────────────────────────────────────────────────────────────
function pfClass(pf) {{
  if (pf===null||pf===undefined) return 'c0';
  if (pf < 0.90) return 'c1';
  if (pf < 0.95) return 'c2';
  if (pf < 1.00) return 'c3';
  if (pf <= 1.10) return 'c4';
  return 'c5';
}}

function buildHeatmap(gridId, yaxisId, xaxisId, period) {{
  const data = hmData[period];

  // Y-axis (top=0.15%, bottom=0.01%)
  const ya = document.getElementById(yaxisId);
  ya.innerHTML = '';
  for (let ti=14; ti>=0; ti--) {{
    const s = document.createElement('span');
    s.textContent = THRESH[ti].toFixed(2)+'%';
    ya.appendChild(s);
  }}

  // X-axis
  const xa = document.getElementById(xaxisId);
  xa.innerHTML = '';
  OFF_LABELS.forEach((lbl, oi) => {{
    const s = document.createElement('span');
    s.textContent = lbl;
    if (oi===7) s.className='la';
    xa.appendChild(s);
  }});

  // Grid rows
  const grid = document.getElementById(gridId);
  grid.innerHTML = '';
  for (let ti=14; ti>=0; ti--) {{
    const row = document.createElement('div');
    row.className = 'hm-row';
    for (let oi=0; oi<8; oi++) {{
      const pf  = data.pf[oi][ti];
      const cnt = data.count[oi][ti];
      const cell = document.createElement('div');
      cell.className = 'cell ' + pfClass(pf) + (oi===7?' la-cell':'');
      cell.dataset.oi = oi; cell.dataset.ti = ti;
      cell.innerHTML =
        '<span class="pv">'+(pf!==null&&pf!==undefined ? (pf>=9?'N/A':pf.toFixed(2)) : '—')+'</span>'+
        '<span class="sc">'+(cnt>0 ? cnt.toLocaleString() : '—')+'</span>';
      cell.onclick = () => onCell(oi, ti);
      row.appendChild(cell);
    }}
    grid.appendChild(row);
  }}
}}

function highlightCells() {{
  document.querySelectorAll('.cell').forEach(c => {{
    c.classList.toggle('sel',
      parseInt(c.dataset.oi)===selOff && parseInt(c.dataset.ti)===selMin);
  }});
}}

function onCell(oi, ti) {{
  selOff = oi; selMin = ti;
  document.getElementById('sl-off').value = oi;
  document.getElementById('sl-min').value = ti;
  maxOn = false;
  document.getElementById('max-tog').textContent = 'OFF';
  document.getElementById('max-tog').classList.remove('on');
  document.getElementById('max-sg').style.display = 'none';
  syncLabels(); highlightCells(); updateS2(); updateS3();
}}

// ── SLIDERS ───────────────────────────────────────────────────────────────────
function syncLabels() {{
  selOff = +document.getElementById('sl-off').value;
  selMin = +document.getElementById('sl-min').value;
  selMax = +document.getElementById('sl-max').value;
  document.getElementById('lbl-off').textContent = OFF_LABELS[selOff];
  document.getElementById('lbl-min').textContent = THRESH[selMin].toFixed(2)+'%';
  document.getElementById('lbl-max').textContent = THRESH[selMax].toFixed(2)+'%';
}}
function onSlide() {{ syncLabels(); highlightCells(); updateS2(); updateS3(); }}
function toggleMax() {{
  maxOn = !maxOn;
  const b=document.getElementById('max-tog');
  b.textContent=maxOn?'ON':'OFF'; b.classList.toggle('on',maxOn);
  document.getElementById('max-sg').style.display=maxOn?'flex':'none';
  updateS2(); updateS3();
}}

// ── STATS ─────────────────────────────────────────────────────────────────────
function stats(period, oi, minT, maxT, years) {{
  const ss = allSigs.filter(s => {{
    if (period>=0 && s[0]!==period) return false;
    const sl=s[1+oi];
    if (sl===null||sl===undefined||sl<minT) return false;
    if (maxT!==null && sl>maxT) return false;
    return s[9]!==null && s[9]!==undefined;
  }});
  if (!ss.length) return {{pf:'—',wr:'—',avg:'—',cnt:0,cagr:'—',pfn:null}};
  const wins = ss.filter(s=>s[10]===1).length;
  const tot  = ss.reduce((a,s)=>a+s[9],0);
  const gp   = ss.filter(s=>s[9]>0).reduce((a,s)=>a+s[9],0);
  const gl   = Math.abs(ss.filter(s=>s[9]<0).reduce((a,s)=>a+s[9],0));
  const pfn  = gl>0 ? gp/gl : (gp>0?9.99:0);
  const pf   = gl>0 ? pfn.toFixed(2) : (gp>0?'N/A':'0.00');
  const avg  = (tot/ss.length).toFixed(2);
  const feq  = 1000000+tot;
  const cagr = feq>0 ? ((Math.pow(feq/1000000,1/years)-1)*100).toFixed(2)+'%' : '—';
  return {{pf, wr:(wins/ss.length*100).toFixed(1)+'%', avg:(+avg>=0?'+':'')+avg,
           cnt:ss.length, cagr, pfn}};
}}

function fill(id, val, cls) {{
  const el=document.getElementById(id);
  el.textContent=val; el.className='sv '+(cls||'x');
}}
function pfFill(id, val, pfn) {{
  const el=document.getElementById(id);
  el.textContent=val;
  const n=pfn;
  el.className='sv '+(n===null?'x':n>=1.0?'g':n>=0.95?'a':'r');
}}
function numFill(id, val) {{
  const el=document.getElementById(id);
  el.textContent=val;
  const n=parseFloat(val);
  el.className='sv '+(isNaN(n)?'x':n>0?'g':n<0?'r':'x');
}}

// ── SECTION 2 ─────────────────────────────────────────────────────────────────
function updateS2() {{
  const minT = THRESH[selMin];
  const maxT = maxOn ? THRESH[selMax] : null;
  const tr   = stats(0, selOff, minT, maxT, 2);
  const te   = stats(1, selOff, minT, maxT, 2);

  pfFill('tr-pf',  tr.pf,  tr.pfn);  fill('tr-wr',  tr.wr);
  numFill('tr-avg', tr.avg); fill('tr-cnt', tr.cnt.toLocaleString());
  numFill('tr-cagr', tr.cagr);

  pfFill('te-pf',  te.pf,  te.pfn);  fill('te-wr',  te.wr);
  numFill('te-avg', te.avg); fill('te-cnt', te.cnt.toLocaleString());
  numFill('te-cagr', te.cagr);

  // Warnings
  const warn = document.getElementById('warn');
  const total = tr.cnt + te.cnt;
  const msgs = [];
  if (selOff===7) msgs.push('⚠ T+2 uses future data — analysis only, not tradeable');
  if (total < 500)  msgs.push('⚠ Insufficient sample ('+total+' signals) — do not use for decisions');
  else if (total < 2000) msgs.push('⚠ Low sample ('+total+' signals) — interpret with caution');
  if (msgs.length) {{
    warn.style.display='block';
    warn.className='warn '+(total<500?'red':'amber');
    warn.textContent=msgs.join('  ·  ');
  }} else {{
    warn.style.display='none';
  }}
}}

// ── SECTION 3 ─────────────────────────────────────────────────────────────────
function updateS3() {{
  const minT = THRESH[selMin];
  const maxT = maxOn ? THRESH[selMax] : null;
  const bl   = baseline.all;

  // Panel A (baseline)
  const apf = bl.pf ? bl.pf.toFixed(2) : '—';
  pfFill('a-pf', apf, bl.pf);
  fill('a-wr',   bl.wr ? bl.wr.toFixed(1)+'%' : '—');
  const aavg = bl.avgPnl!==null ? (bl.avgPnl>=0?'+':'')+bl.avgPnl.toFixed(2) : '—';
  numFill('a-avg', aavg);
  fill('a-cnt',  bl.count.toLocaleString());
  const acagr = bl.cagr!==null ? (bl.cagr>=0?'+':'')+bl.cagr.toFixed(2)+'%' : '—';
  numFill('a-cagr', acagr);

  // Panel B (filtered, all periods combined, 4yr)
  const bst = stats(-1, selOff, minT, maxT, 4);
  pfFill('b-pf',   bst.pf,  bst.pfn);
  fill('b-wr',     bst.wr);
  numFill('b-avg', bst.avg);
  fill('b-cnt',    bst.cnt.toLocaleString());
  numFill('b-cagr', bst.cagr);

  // Delta column
  const dc = document.getElementById('delta-col');
  const metrics = [
    {{lbl:'PF',  a:bl.pf,       b:bst.pfn,  fmt:v=>v!==null?v.toFixed(2):'—'}},
    {{lbl:'WR',  a:bl.wr,       b:bst.cnt>0?parseFloat(bst.wr):null, fmt:v=>v!==null?v.toFixed(1)+'%':'—'}},
    {{lbl:'AvgP',a:bl.avgPnl,   b:bst.cnt>0?parseFloat(bst.avg):null, fmt:v=>v!==null?(v>=0?'+':'')+v.toFixed(2):'—'}},
    {{lbl:'CAGR',a:bl.cagr,     b:bst.cnt>0?parseFloat(bst.cagr):null, fmt:v=>v!==null?(v>=0?'+':'')+v.toFixed(2)+'%':'—'}},
  ];
  dc.innerHTML='';
  metrics.forEach(m => {{
    const diff = (m.a!==null&&m.b!==null) ? m.b-m.a : null;
    const cls  = diff===null?'x':diff>0.001?'g':diff<-0.001?'r':'x';
    const arrow= diff===null?'—':diff>0.001?'▲':diff<-0.001?'▼':'≈';
    dc.innerHTML += `<div class="di"><span class="dlbl">${{m.lbl}}</span><span class="dval ${{cls}}">${{arrow}}</span></div>`;
  }});

  // Per-stock table
  const tbody = document.getElementById('stk-tbody');
  tbody.innerHTML='';
  const rows = STOCKS.map((stock, si) => {{
    const ss = allSigs.filter(s => {{
      if (s[11]!==si) return false;
      const sl=s[1+selOff];
      if (sl===null||sl===undefined||sl<minT) return false;
      if (maxT!==null && sl>maxT) return false;
      return s[9]!==null;
    }});
    if (!ss.length) return {{stock,si,cnt:0,wr:'—',pf:'—',pfn:null}};
    const wins=ss.filter(s=>s[10]===1).length;
    const gp=ss.filter(s=>s[9]>0).reduce((a,s)=>a+s[9],0);
    const gl=Math.abs(ss.filter(s=>s[9]<0).reduce((a,s)=>a+s[9],0));
    const pfn=gl>0?gp/gl:(gp>0?9.99:0);
    const pf=gl>0?pfn.toFixed(2):(gp>0?'N/A':'0.00');
    return {{stock,si,cnt:ss.length,wr:(wins/ss.length*100).toFixed(1)+'%',pf,pfn}};
  }}).sort((a,b)=>(b.pfn??-1)-(a.pfn??-1));

  rows.forEach(r => {{
    const bpf = basePF[r.si];
    let badge='';
    if (r.pfn!==null && bpf!==null) {{
      const d=r.pfn-bpf;
      badge=d>0.02?'<span class="badge up">▲ better</span>':
            d<-0.02?'<span class="badge dn">▼ worse</span>':
            '<span class="badge eq">≈ same</span>';
    }}
    tbody.innerHTML+=`<tr><td>${{r.stock}}</td><td>${{r.cnt.toLocaleString()}}</td><td>${{r.wr}}</td><td>${{r.pf}}</td><td>${{badge}}</td></tr>`;
  }});
}}

// ── EXPORT ────────────────────────────────────────────────────────────────────
function exportObs() {{
  const minT=THRESH[selMin], maxT=maxOn?THRESH[selMax]:null;
  const tr=stats(0,selOff,minT,maxT,2), te=stats(1,selOff,minT,maxT,2);
  const trpfn=tr.pfn, tepfn=te.pfn;
  const stable=(trpfn!==null&&tepfn!==null)?Math.abs(trpfn-tepfn)<=0.10?'Y':'N':'?';
  const now=new Date().toISOString().slice(0,10);
  const maxStr=maxOn?' — '+THRESH[selMax].toFixed(2)+'%':'(no max)';
  const text=[
    '## Gap 1 — Slope Offset + Threshold',
    'Date: '+now,
    'Best combo: offset='+OFF_LABELS[selOff]+', min_threshold='+minT.toFixed(2)+'%, max='+maxStr,
    'Train PF: '+tr.pf+' | Test PF: '+te.pf,
    'Stable (train/test within ±0.10)?: '+stable,
    'Signal count: Train='+tr.cnt.toLocaleString()+' · Test='+te.cnt.toLocaleString(),
    'Notes: WR Train='+tr.wr+' Test='+te.wr+' · AvgPnL Train='+tr.avg+' Test='+te.avg+' · CAGR Train='+tr.cagr+' Test='+te.cagr,
  ].join('\\n');
  navigator.clipboard.writeText(text).then(()=>{{
    const t=document.getElementById('toast');
    t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),3000);
  }}).catch(()=>prompt('Copy this observation:',text));
}}

// ── INIT ──────────────────────────────────────────────────────────────────────
buildHeatmap('hm-train','yaxis-train','xaxis-train','train');
buildHeatmap('hm-test', 'yaxis-test', 'xaxis-test', 'test');
highlightCells();
updateS2();
updateS3();
</script>
</body>
</html>
"""

# ── Write ──────────────────────────────────────────────────────────────────────
OUT.write_text(HTML, encoding='utf-8')
size_mb = OUT.stat().st_size / 1e6
print(f'\nSaved : {OUT}')
print(f'Size  : {size_mb:.1f} MB')
