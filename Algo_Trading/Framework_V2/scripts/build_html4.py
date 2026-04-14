"""
Build fv2_h4_pullback.html — Gap 2+3: Pullback Quality + Candles Above tuner.

Signal row: [period, ca, pb, sd, tbp, sctb, bw, pnl, win, si]
  0: period  (0=train 2022-2023, 1=test 2024-2025)
  1: ca      candles_above  (int, 0-20)
  2: pb      pullback_bars  (int, 0-20)
  3: sd      shoot_depth    (float, ATR units)
  4: tbp     touch_body_pct (float, %)
  5: sctb    same_candle_tb (0/1)
  6: bw      bounce_window  (0-3, T+N)
  7: pnl     raw_pnl
  8: win     0/1
  9: si      stock_idx

Heatmap axes (threshold-based):
  X: candles_above >= x  (x = 0..10)
  Y: pullback_bars  >= y  (y = 1..15)
  Same-candle bypass: sctb=1 signals skip pullback_bars gate
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────────
CSV_DIR = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/data/historical/csv/intraday_5min')
OUT     = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_h4_pullback.html')

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


# ── Metric computation ─────────────────────────────────────────────────────────

def candles_above(day, touch_idx):
    """Count candles before touch where low > MA20. Max 20, same day only."""
    count = 0
    for i in range(touch_idx - 1, max(touch_idx - 21, -1), -1):
        r = day.iloc[i]
        if pd.isna(r['ma20']):
            break
        if r['low'] > r['ma20']:
            count += 1
        else:
            break
    return count


def pullback_bars(day, touch_idx, day_start_idx=0):
    """Bars from swing high (max high in last 20 candles) to touch."""
    lo = max(touch_idx - 20, day_start_idx)
    if lo >= touch_idx:
        return 0
    window = day.iloc[lo:touch_idx]
    if window.empty:
        return 0
    swing_high_pos = window['high'].idxmax()
    return touch_idx - (swing_high_pos - day.index[0])


def shoot_depth(row, atr):
    """(MA20 - low) / ATR14. 0 if low >= MA20."""
    if pd.isna(atr) or atr <= 0:
        return 0.0
    depth = row['ma20'] - row['low']
    return max(0.0, round(float(depth / atr), 4))


def touch_body_pct(row):
    """abs(close - open) / (high - low) * 100. 0 if high == low."""
    rng = row['high'] - row['low']
    if rng <= 0:
        return 0.0
    return round(abs(row['close'] - row['open']) / rng * 100, 2)


# ── Signal extraction ──────────────────────────────────────────────────────────

def build_stock_signals(stock: str, stock_idx: int) -> list:
    csv = CSV_DIR / f'{stock}_5min.csv'
    df  = pd.read_csv(csv)
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df = df.sort_values('datetime').reset_index(drop=True)

    # ATR14 (global, no per-day reset)
    prev_close = df['close'].shift(1)
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - prev_close).abs(),
        (df['low']  - prev_close).abs(),
    ], axis=1).max(axis=1)
    df['atr14'] = tr.rolling(14).mean()

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
            atr_val   = row['atr14']

            # Compute H4 metrics
            ca   = candles_above(day, touch_idx)
            pb   = pullback_bars(day, touch_idx)
            sd   = shoot_depth(row, atr_val)
            tbp  = touch_body_pct(row)

            # Find bounce (T+0 to T+3, same day)
            bounce_idx = None
            for j in range(touch_idx, min(touch_idx + 4, n)):
                b = day.iloc[j]
                if (pd.notna(b['ma20']) and b['close'] > b['ma20'] and
                        pd.notna(b['vol_ma20']) and b['volume'] >= 1.2 * b['vol_ma20']):
                    bounce_idx = j
                    break

            if bounce_idx is not None:
                sctb = 1 if bounce_idx == touch_idx else 0
                bw   = bounce_idx - touch_idx  # 0–3

                entry_idx = bounce_idx + 1 if bounce_idx + 1 < n else None
                pnl, win = None, None
                if entry_idx is not None:
                    entry_price = day.iloc[entry_idx]['open']
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

                signals.append([period, ca, pb, sd, tbp, sctb, bw, pnl, win, stock_idx])
                i = bounce_idx + 2
            else:
                i += 1

    return signals


# ── Baseline stats ─────────────────────────────────────────────────────────────

def compute_baseline(signals: list) -> dict:
    def _stats(sigs, years):
        sigs = [s for s in sigs if s[7] is not None]
        if not sigs:
            return {'pf': None, 'wr': None, 'avgPnl': None, 'count': 0, 'cagr': None}
        wins  = sum(1 for s in sigs if s[8] == 1)
        total = sum(s[7] for s in sigs)
        gp    = sum(s[7] for s in sigs if s[7] > 0)
        gl    = abs(sum(s[7] for s in sigs if s[7] < 0))
        pf    = round(gp / gl, 4) if gl > 0 else (9.99 if gp > 0 else None)
        feq   = 1_000_000 + total
        cagr  = round((pow(feq / 1_000_000, 1 / years) - 1) * 100, 2) if feq > 0 else None
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

print('Building H4 data for 30 stocks...')
all_signals = []
for idx, stock in enumerate(STOCKS):
    sigs = build_stock_signals(stock, idx)
    all_signals.extend(sigs)
    print(f'  {stock:15s}  signals={len(sigs):5d}')

total   = len(all_signals)
train_n = sum(1 for s in all_signals if s[0] == 0)
test_n  = sum(1 for s in all_signals if s[0] == 1)
print(f'\nTotal signals: {total:,}  (train={train_n:,}  test={test_n:,})')

print('Computing baseline...')
baseline = compute_baseline(all_signals)
print(f"All  PF={baseline['all']['pf']}  count={baseline['all']['count']:,}")
print(f"Train PF={baseline['train']['pf']}  count={baseline['train']['count']:,}")
print(f"Test  PF={baseline['test']['pf']}  count={baseline['test']['count']:,}")

print('Serialising...')
stocks_js   = json.dumps(STOCKS)
baseline_js = json.dumps(baseline, separators=(',', ':'))
signals_js  = json.dumps(all_signals, separators=(',', ':'))
print(f'  Signals JS: {len(signals_js)/1e6:.1f} MB')


# ── HTML ───────────────────────────────────────────────────────────────────────

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>H4 — Gap 2+3 Pullback Tuner</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0f0f0f;--bg2:#1a1a1a;--bg3:#222;--bg4:#2a2a2a;--bg5:#2f2f2f;
  --fg:#e8e8e8;--fg2:#b8b8b8;--fg3:#888;--fg4:#555;
  --border:#333;--border2:#444;
  --green:#4ade80;--red:#f87171;--amber:#fbbf24;--teal:#14b8a6;--blue:#60a5fa;
}}
body{{background:var(--bg);color:var(--fg);font-family:'Segoe UI',system-ui,sans-serif;font-size:13px;line-height:1.4;padding:16px 20px}}
h1{{font-size:15px;font-weight:600;color:var(--fg2);margin-bottom:14px}}
.section{{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:14px}}
.sec-title{{font-size:11px;font-weight:700;color:var(--fg3);text-transform:uppercase;letter-spacing:.6px;margin-bottom:14px}}

/* ── FILTERS ── */
.filters{{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:14px;align-items:flex-end}}
.flt-group{{display:flex;flex-direction:column;gap:4px}}
.flt-label{{font-size:10px;color:var(--fg3);font-weight:600;text-transform:uppercase;letter-spacing:.4px}}
.flt-group select{{background:var(--bg3);border:1px solid var(--border2);color:var(--fg);padding:4px 8px;border-radius:4px;font-size:12px;cursor:pointer;outline:none}}
.flt-group select:focus{{border-color:var(--teal)}}

/* ── HEATMAP ── */
.hm-wrapper{{display:flex;gap:28px;overflow-x:auto;padding-bottom:4px}}
.hm-panel{{flex:1;min-width:0}}
.hm-panel-title{{font-size:12px;font-weight:600;color:var(--fg2);text-align:center;margin-bottom:8px}}
.hm-body{{display:flex;gap:4px}}
.hm-yaxis{{display:flex;flex-direction:column;padding-top:22px}}
.hm-yaxis span{{height:28px;display:flex;align-items:center;justify-content:flex-end;font-size:9px;color:var(--fg3);padding-right:4px;white-space:nowrap}}
.hm-inner{{display:flex;flex-direction:column;gap:0}}
.hm-xaxis{{display:flex;margin-bottom:2px}}
.hm-xaxis span{{width:48px;text-align:center;font-size:9px;color:var(--fg3);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.hm-row{{display:flex}}
.cell{{width:48px;height:28px;display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;border:1px solid transparent;position:relative;transition:filter .1s}}
.cell:hover{{filter:brightness(1.3);z-index:2}}
.cell.sel{{border:2px solid #fff!important;z-index:3}}
.cell .pv{{font-size:10px;font-weight:700;line-height:1.1}}
.cell .sc{{font-size:8px;opacity:.6;line-height:1.1}}
.c0{{background:#1c0a0a;color:#888}}
.c1{{background:#4a0c0c;color:#fca5a5}}
.c2{{background:#4a2500;color:#fcd34d}}
.c3{{background:#0a2e14;color:#6ee7a0}}
.c4{{background:#14532d;color:#4ade80}}
.c5{{background:#166534;color:#bbf7d0;box-shadow:inset 0 0 0 1px #22c55e}}

/* ── STATS DUAL ── */
.stats-dual{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:10px}}
.sp{{background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:11px}}
.sp-title{{font-size:11px;font-weight:700;color:var(--fg3);margin-bottom:8px}}
.sr{{display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid var(--bg4)}}
.sr:last-child{{border:none}}
.sl{{font-size:11px;color:var(--fg3)}}
.sv{{font-size:12px;font-weight:700}}
.sv.g{{color:var(--green)}}.sv.r{{color:var(--red)}}.sv.a{{color:var(--amber)}}.sv.x{{color:var(--fg3)}}

/* ── SELECTED CELL INFO ── */
.cell-info{{background:var(--bg4);border:1px solid var(--border2);border-radius:5px;padding:7px 12px;font-size:11px;color:var(--fg2);margin-bottom:12px;display:flex;gap:20px;flex-wrap:wrap}}
.ci-item span{{color:var(--fg3);margin-right:4px}}

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

/* ── TOP 10 NAV ── */
.top10-bar{{display:flex;gap:8px;align-items:center;margin-bottom:10px;flex-wrap:wrap}}
.t10-btn{{background:var(--bg3);border:1px solid var(--border2);color:var(--fg2);padding:4px 14px;border-radius:4px;cursor:pointer;font-size:12px}}
.t10-btn:hover{{background:var(--bg4)}}
.t10-lbl{{font-size:12px;color:var(--fg3)}}
.t10-card{{background:var(--bg3);border:1px solid var(--border2);border-radius:6px;padding:10px 14px;font-size:11px;color:var(--fg2)}}
.t10-card strong{{color:var(--fg);font-size:13px}}

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
<h1>H4 — Gap 2+3: Pullback Quality Tuner &nbsp;·&nbsp; candles_above × pullback_bars</h1>

<!-- ── SECTION 0: FILTERS ── -->
<div class="section">
  <div class="sec-title">Filters — recomputes heatmap on change</div>
  <div class="filters">
    <div class="flt-group">
      <span class="flt-label">Shoot Depth</span>
      <select id="flt-sd" onchange="onFilter()">
        <option value="any">Any</option>
        <option value="0.2">≤ 0.2 ATR</option>
        <option value="0.3">≤ 0.3 ATR</option>
        <option value="0.5">≤ 0.5 ATR</option>
        <option value="0.8">≤ 0.8 ATR</option>
      </select>
    </div>
    <div class="flt-group">
      <span class="flt-label">Touch Body %</span>
      <select id="flt-tbp" onchange="onFilter()">
        <option value="any">Any</option>
        <option value="20">≤ 20%</option>
        <option value="30">≤ 30%</option>
        <option value="50">≤ 50%</option>
      </select>
    </div>
    <div class="flt-group">
      <span class="flt-label">Same Candle</span>
      <select id="flt-sctb" onchange="onFilter()">
        <option value="all">All</option>
        <option value="same">Same candle only</option>
        <option value="sep">Separate only</option>
      </select>
    </div>
    <div class="flt-group">
      <span class="flt-label">Bounce Window</span>
      <select id="flt-bw" onchange="onFilter()">
        <option value="any">Any</option>
        <option value="0">T+0 only</option>
        <option value="1">≤ T+1</option>
        <option value="2">≤ T+2</option>
        <option value="3">≤ T+3</option>
      </select>
    </div>
    <div class="flt-group">
      <span class="flt-label">Min Signals / Cell</span>
      <select id="flt-minsig" onchange="onFilter()">
        <option value="0">Any</option>
        <option value="30">≥ 30</option>
        <option value="50">≥ 50</option>
        <option value="100">≥ 100</option>
        <option value="200">≥ 200</option>
        <option value="500">≥ 500</option>
        <option value="1000">≥ 1000</option>
      </select>
    </div>
  </div>
  <div class="warn" id="warn-flt"></div>
</div>

<!-- ── SECTION 1: HEATMAP ── -->
<div class="section">
  <div class="sec-title">Section 1 — Profit Factor Heatmap &nbsp;·&nbsp; X = candles_above ≥ · Y = pullback_bars ≥ &nbsp;·&nbsp; Click cell to inspect</div>
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

<!-- ── SECTION 2: FINE-TUNE ── -->
<div class="section">
  <div class="sec-title">Section 2 — Selected Cell Stats</div>
  <div class="cell-info" id="cell-info">
    <span><span>Selected:</span> none — click a heatmap cell</span>
  </div>
  <div class="warn" id="warn-cell"></div>
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

<!-- ── SECTION 3: TOP 10 + COMPARISON ── -->
<div class="section">
  <div class="sec-title">Section 3 — Top 10 Combos</div>
  <div class="top10-bar">
    <button class="t10-btn" onclick="findTop10()">Find Best Combos</button>
    <button class="t10-btn" onclick="navTop10(-1)">◀</button>
    <span class="t10-lbl" id="t10-lbl">—</span>
    <button class="t10-btn" onclick="navTop10(1)">▶</button>
  </div>
  <div class="t10-card" id="t10-card" style="display:none"></div>
</div>

<!-- ── SECTION 4: COMPARISON + STOCK TABLE ── -->
<div class="section">
  <div class="sec-title">Section 4 — Panel A vs B Comparison</div>
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
      <div class="cp-title">Panel B — Selected cell (all periods)</div>
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
<div class="toast" id="toast">Copied — paste into gap_observations.md</div>

<footer>H4 — Gap 2+3 tuner &nbsp;·&nbsp; 30 stocks &nbsp;·&nbsp; 2022–2025 &nbsp;·&nbsp; 1-share mode<br>
Train: 2022–2023 &nbsp;|&nbsp; Test: 2024–2025 &nbsp;·&nbsp; No position guard</footer>

<script>
// ── DATA ───────────────────────────────────────────────────────────────────────
const STOCKS   = {stocks_js};
const baseline = {baseline_js};
const allSigs  = {signals_js};
// sig indices: 0=period,1=ca,2=pb,3=sd,4=tbp,5=sctb,6=bw,7=pnl,8=win,9=si

const CA_MAX = 10;  // X axis: 0..10
const PB_MAX = 15;  // Y axis: 1..15
const CA_LABELS = Array.from({{length: CA_MAX+1}}, (_,i) => 'ca≥'+i);
const PB_LABELS = Array.from({{length: PB_MAX}}, (_,i) => 'pb≥'+(i+1));

// ── STATE ─────────────────────────────────────────────────────────────────────
let selCA = -1, selPB = -1;  // selected cell (-1 = none)
let filteredSigs = [];
let top10list = [];
let top10idx  = 0;

// Precompute per-stock baseline PF
const basePF = STOCKS.map((_, si) => {{
  const ss = allSigs.filter(s => s[9]===si && s[7]!==null);
  if (!ss.length) return null;
  const gp = ss.filter(s=>s[7]>0).reduce((a,s)=>a+s[7],0);
  const gl = Math.abs(ss.filter(s=>s[7]<0).reduce((a,s)=>a+s[7],0));
  return gl>0 ? gp/gl : (gp>0?9.99:0);
}});

// ── FILTER ────────────────────────────────────────────────────────────────────
function getFilters() {{
  return {{
    sd:     document.getElementById('flt-sd').value,
    tbp:    document.getElementById('flt-tbp').value,
    sctb:   document.getElementById('flt-sctb').value,
    bw:     document.getElementById('flt-bw').value,
    minsig: +document.getElementById('flt-minsig').value,
  }};
}}

function passesSig(s, f) {{
  if (s[7] === null) return false;
  if (f.sd  !== 'any' && s[3] > +f.sd)  return false;
  if (f.tbp !== 'any' && s[4] > +f.tbp) return false;
  if (f.sctb === 'same' && s[5] !== 1)  return false;
  if (f.sctb === 'sep'  && s[5] !== 0)  return false;
  if (f.bw   !== 'any' && s[6] > +f.bw) return false;
  return true;
}}

function onFilter() {{
  const f = getFilters();
  filteredSigs = allSigs.filter(s => passesSig(s, f));
  const w = document.getElementById('warn-flt');
  if (filteredSigs.length < 500) {{
    w.style.display='block'; w.className='warn red';
    w.textContent='⚠ Only '+filteredSigs.length+' signals after filters — results unreliable';
  }} else {{
    w.style.display='none';
  }}
  rebuildHeatmap();
  if (selCA >= 0) updateS2(); else clearS2();
  updateS4();
  top10list = []; top10idx = 0;
  document.getElementById('t10-lbl').textContent = '—';
  document.getElementById('t10-card').style.display = 'none';
}}

// ── HEATMAP ───────────────────────────────────────────────────────────────────
function pfClass(pf) {{
  if (pf===null) return 'c0';
  if (pf < 0.90) return 'c1';
  if (pf < 0.95) return 'c2';
  if (pf < 1.00) return 'c3';
  if (pf <= 1.10) return 'c4';
  return 'c5';
}}

function computeHeatmapGrids() {{
  // Returns {{train: {{pf,cnt}}, test: {{pf,cnt}}}}
  const minSig = +document.getElementById('flt-minsig').value;
  const sctbMode = document.getElementById('flt-sctb').value;
  const result = {{}};
  for (const [key, period] of [['train',0],['test',1]]) {{
    const psigs = filteredSigs.filter(s => s[0]===period);
    // Accumulators [ca_idx][pb_idx]
    const gp  = Array.from({{length:CA_MAX+1}},()=>new Float64Array(PB_MAX));
    const gl  = Array.from({{length:CA_MAX+1}},()=>new Float64Array(PB_MAX));
    const cnt = Array.from({{length:CA_MAX+1}},()=>new Int32Array(PB_MAX));
    for (const s of psigs) {{
      const ca   = Math.min(s[1], CA_MAX);
      const pb   = s[2];
      const sctb = s[5];
      const pnl  = s[7];
      // Cell (xi, yi): signal qualifies if ca >= xi AND (sctb=1 OR pb >= yi+1)
      const yMax = sctb ? PB_MAX-1 : Math.min(pb-1, PB_MAX-1); // yi index cap
      for (let xi=0; xi<=ca; xi++) {{
        for (let yi=0; yi<=yMax; yi++) {{
          cnt[xi][yi]++;
          if (pnl>0) gp[xi][yi]+=pnl; else gl[xi][yi]-=pnl;
        }}
      }}
    }}
    const pfGrid = [], cntGrid = [];
    for (let xi=0; xi<=CA_MAX; xi++) {{
      const pfRow=[], cntRow=[];
      for (let yi=0; yi<PB_MAX; yi++) {{
        const c = cnt[xi][yi];
        if (c < Math.max(minSig, 1)) {{ pfRow.push(null); cntRow.push(c); continue; }}
        const g=gp[xi][yi], l=gl[xi][yi];
        pfRow.push(l>0 ? g/l : (g>0?9.99:0));
        cntRow.push(c);
      }}
      pfGrid.push(pfRow); cntGrid.push(cntRow);
    }}
    result[key] = {{pf:pfGrid, cnt:cntGrid}};
  }}
  return result;
}}

function buildHeatmapDOM(gridId, yaxisId, xaxisId, data, period) {{
  // Y-axis (top=pb≥15, bottom=pb≥1)
  const ya = document.getElementById(yaxisId);
  ya.innerHTML = '';
  for (let yi=PB_MAX-1; yi>=0; yi--) {{
    const s=document.createElement('span'); s.textContent='pb≥'+(yi+1); ya.appendChild(s);
  }}
  // X-axis
  const xa = document.getElementById(xaxisId);
  xa.innerHTML = '';
  for (let xi=0; xi<=CA_MAX; xi++) {{
    const s=document.createElement('span'); s.textContent='ca≥'+xi; xa.appendChild(s);
  }}
  // Grid rows (top=high pb, bottom=low pb)
  const grid = document.getElementById(gridId);
  grid.innerHTML = '';
  for (let yi=PB_MAX-1; yi>=0; yi--) {{
    const row=document.createElement('div'); row.className='hm-row';
    for (let xi=0; xi<=CA_MAX; xi++) {{
      const pf  = data.pf[xi][yi];
      const c   = data.cnt[xi][yi];
      const cell=document.createElement('div');
      cell.className='cell '+pfClass(pf)+(xi===selCA&&(yi+1)===selPB?' sel':'');
      cell.dataset.xi=xi; cell.dataset.yi=yi+1;
      cell.innerHTML=
        '<span class="pv">'+(pf!==null?(pf>=9?'N/A':pf.toFixed(2)):'—')+'</span>'+
        '<span class="sc">'+(c>0?c.toLocaleString():'—')+'</span>';
      cell.onclick=()=>onCell(xi, yi+1);
      row.appendChild(cell);
    }}
    grid.appendChild(row);
  }}
}}

let hmData = null;
function rebuildHeatmap() {{
  hmData = computeHeatmapGrids();
  buildHeatmapDOM('hm-train','yaxis-train','xaxis-train', hmData.train, 0);
  buildHeatmapDOM('hm-test', 'yaxis-test', 'xaxis-test',  hmData.test,  1);
}}

function highlightCells() {{
  document.querySelectorAll('.cell').forEach(c => {{
    c.classList.toggle('sel', +c.dataset.xi===selCA && +c.dataset.yi===selPB);
  }});
}}

function onCell(xi, yi) {{
  selCA=xi; selPB=yi;
  highlightCells();
  updateS2();
  updateS4();
}}

// ── STATS HELPERS ─────────────────────────────────────────────────────────────
function cellSigs(period, xi, yi) {{
  // signals in filteredSigs matching cell (xi,yi) for given period
  return filteredSigs.filter(s => {{
    if (period>=0 && s[0]!==period) return false;
    const ca=Math.min(s[1],CA_MAX), pb=s[2], sctb=s[5];
    if (ca < xi) return false;
    if (sctb===0 && pb < yi) return false;
    return true;
  }});
}}

function calcStats(sigs, years) {{
  if (!sigs.length) return {{pf:'—',wr:'—',avg:'—',cnt:0,cagr:'—',pfn:null}};
  const wins=sigs.filter(s=>s[8]===1).length;
  const tot=sigs.reduce((a,s)=>a+s[7],0);
  const gp=sigs.filter(s=>s[7]>0).reduce((a,s)=>a+s[7],0);
  const gl=Math.abs(sigs.filter(s=>s[7]<0).reduce((a,s)=>a+s[7],0));
  const pfn=gl>0?gp/gl:(gp>0?9.99:0);
  const pf=gl>0?pfn.toFixed(2):(gp>0?'N/A':'0.00');
  const feq=1000000+tot;
  const cagr=feq>0?((Math.pow(feq/1000000,1/years)-1)*100).toFixed(2)+'%':'—';
  return {{pf,wr:(wins/sigs.length*100).toFixed(1)+'%',avg:(tot/sigs.length>=0?'+':'')+( tot/sigs.length).toFixed(2),cnt:sigs.length,cagr,pfn}};
}}

// ── SECTION 2 ─────────────────────────────────────────────────────────────────
function fill(id,val,cls){{const e=document.getElementById(id);e.textContent=val;e.className='sv '+(cls||'x');}}
function pfFill(id,val,pfn){{const e=document.getElementById(id);e.textContent=val;e.className='sv '+(pfn===null?'x':pfn>=1.0?'g':pfn>=0.95?'a':'r');}}
function numFill(id,val){{const e=document.getElementById(id);e.textContent=val;const n=parseFloat(val);e.className='sv '+(isNaN(n)?'x':n>0?'g':n<0?'r':'x');}}

function updateS2() {{
  if (selCA<0) return;
  const tr=calcStats(cellSigs(0,selCA,selPB),2);
  const te=calcStats(cellSigs(1,selCA,selPB),2);
  pfFill('tr-pf',tr.pf,tr.pfn); fill('tr-wr',tr.wr); numFill('tr-avg',tr.avg);
  fill('tr-cnt',tr.cnt.toLocaleString()); numFill('tr-cagr',tr.cagr);
  pfFill('te-pf',te.pf,te.pfn); fill('te-wr',te.wr); numFill('te-avg',te.avg);
  fill('te-cnt',te.cnt.toLocaleString()); numFill('te-cagr',te.cagr);

  const ci=document.getElementById('cell-info');
  ci.innerHTML=`<span><span>Cell:</span> ca≥${{selCA}} &nbsp;·&nbsp; pb≥${{selPB}}</span>`+
    `<span><span>Train:</span> PF=${{tr.pf}} (${{tr.cnt}} sigs)</span>`+
    `<span><span>Test:</span> PF=${{te.pf}} (${{te.cnt}} sigs)</span>`;

  const stable=(tr.pfn!==null&&te.pfn!==null)?Math.abs(tr.pfn-te.pfn)<=0.10:null;
  const wc=document.getElementById('warn-cell');
  const tot=tr.cnt+te.cnt;
  const msgs=[];
  if (tot<200) msgs.push('⚠ Very low sample ('+tot+') — unreliable');
  else if (tot<500) msgs.push('⚠ Low sample ('+tot+') — interpret with caution');
  if (stable===false) msgs.push('⚠ Train/test gap > 0.10 PF — possible overfit');
  if (msgs.length) {{wc.style.display='block';wc.className='warn '+(tot<200?'red':'amber');wc.textContent=msgs.join('  ·  ');}}
  else wc.style.display='none';
}}

function clearS2() {{
  ['tr-pf','tr-wr','tr-avg','tr-cnt','tr-cagr','te-pf','te-wr','te-avg','te-cnt','te-cagr']
    .forEach(id=>{{const e=document.getElementById(id);e.textContent='—';e.className='sv x';}});
  document.getElementById('warn-cell').style.display='none';
}}

// ── SECTION 3: TOP 10 ─────────────────────────────────────────────────────────
function scoreComb(xi, yi) {{
  const tr=calcStats(cellSigs(0,xi,yi),2);
  const te=calcStats(cellSigs(1,xi,yi),2);
  if (tr.pfn===null||te.pfn===null||tr.cnt<30||te.cnt<30) return null;
  const stability=Math.abs(tr.pfn-te.pfn);
  const score=te.pfn*Math.log(te.cnt+1)*(stability<=0.10?1.0:stability<=0.20?0.80:0.60);
  return {{xi,yi,tr,te,score,stability}};
}}

function findTop10() {{
  const candidates=[];
  for (let xi=0; xi<=CA_MAX; xi++) {{
    for (let yi=1; yi<=PB_MAX; yi++) {{
      const r=scoreComb(xi,yi);
      if (r) candidates.push(r);
    }}
  }}
  candidates.sort((a,b)=>b.score-a.score);
  top10list=candidates.slice(0,10);
  top10idx=0;
  showTop10();
}}

function showTop10() {{
  if (!top10list.length) return;
  const r=top10list[top10idx];
  document.getElementById('t10-lbl').textContent=`${{top10idx+1}} / ${{top10list.length}}`;
  document.getElementById('t10-card').style.display='block';
  document.getElementById('t10-card').innerHTML=
    `<strong>ca≥${{r.xi}} &nbsp;·&nbsp; pb≥${{r.yi}}</strong> &nbsp; Score: ${{r.score.toFixed(3)}}<br>`+
    `Train PF: ${{r.tr.pf}} (${{r.tr.cnt}} sigs, WR ${{r.tr.wr}}, CAGR ${{r.tr.cagr}})<br>`+
    `Test  PF: ${{r.te.pf}} (${{r.te.cnt}} sigs, WR ${{r.te.wr}}, CAGR ${{r.te.cagr}})<br>`+
    `Train/Test stability: ${{r.stability<=0.10?'✅ stable (≤0.10)':r.stability<=0.20?'⚠ marginal':'❌ unstable'}}`;
  selCA=r.xi; selPB=r.yi;
  highlightCells(); updateS2(); updateS4();
}}

function navTop10(d) {{
  if (!top10list.length) return;
  top10idx=(top10idx+d+top10list.length)%top10list.length;
  showTop10();
}}

// ── SECTION 4: COMPARISON + STOCK TABLE ───────────────────────────────────────
function updateS4() {{
  const bl=baseline.all;
  const apf=bl.pf?bl.pf.toFixed(2):'—';
  pfFill('a-pf',apf,bl.pf);
  fill('a-wr',bl.wr?bl.wr.toFixed(1)+'%':'—');
  const aavg=bl.avgPnl!==null?(bl.avgPnl>=0?'+':'')+bl.avgPnl.toFixed(2):'—';
  numFill('a-avg',aavg);
  fill('a-cnt',bl.count.toLocaleString());
  const acagr=bl.cagr!==null?(bl.cagr>=0?'+':'')+bl.cagr.toFixed(2)+'%':'—';
  numFill('a-cagr',acagr);

  const bst = selCA>=0 ? calcStats(cellSigs(-1,selCA,selPB),4) : {{pf:'—',wr:'—',avg:'—',cnt:0,cagr:'—',pfn:null}};
  pfFill('b-pf',bst.pf,bst.pfn); fill('b-wr',bst.wr); numFill('b-avg',bst.avg);
  fill('b-cnt',bst.cnt.toLocaleString()); numFill('b-cagr',bst.cagr);

  // Delta column
  const dc=document.getElementById('delta-col');
  const metrics=[
    {{lbl:'PF',  a:bl.pf,      b:bst.pfn}},
    {{lbl:'WR',  a:bl.wr,      b:bst.cnt>0?parseFloat(bst.wr):null}},
    {{lbl:'AvgP',a:bl.avgPnl,  b:bst.cnt>0?parseFloat(bst.avg):null}},
    {{lbl:'CAGR',a:bl.cagr,    b:bst.cnt>0?parseFloat(bst.cagr):null}},
  ];
  dc.innerHTML='';
  metrics.forEach(m=>{{
    const diff=(m.a!==null&&m.b!==null)?m.b-m.a:null;
    const cls=diff===null?'x':diff>0.001?'g':diff<-0.001?'r':'x';
    const arrow=diff===null?'—':diff>0.001?'▲':diff<-0.001?'▼':'≈';
    dc.innerHTML+=`<div class="di"><span class="dlbl">${{m.lbl}}</span><span class="dval ${{cls}}">${{arrow}}</span></div>`;
  }});

  // Per-stock table
  if (selCA<0) {{ document.getElementById('stk-tbody').innerHTML=''; return; }}
  const rows=STOCKS.map((stock,si)=>{{
    const ss=cellSigs(-1,selCA,selPB).filter(s=>s[9]===si);
    if (!ss.length) return {{stock,si,cnt:0,wr:'—',pf:'—',pfn:null}};
    const wins=ss.filter(s=>s[8]===1).length;
    const gp=ss.filter(s=>s[7]>0).reduce((a,s)=>a+s[7],0);
    const gl=Math.abs(ss.filter(s=>s[7]<0).reduce((a,s)=>a+s[7],0));
    const pfn=gl>0?gp/gl:(gp>0?9.99:0);
    const pf=gl>0?pfn.toFixed(2):(gp>0?'N/A':'0.00');
    return {{stock,si,cnt:ss.length,wr:(wins/ss.length*100).toFixed(1)+'%',pf,pfn}};
  }}).sort((a,b)=>(b.pfn??-1)-(a.pfn??-1));

  const tbody=document.getElementById('stk-tbody');
  tbody.innerHTML='';
  rows.forEach(r=>{{
    const bpf=basePF[r.si];
    let badge='';
    if (r.pfn!==null&&bpf!==null){{
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
  if (selCA<0) {{ alert('Select a cell first'); return; }}
  const tr=calcStats(cellSigs(0,selCA,selPB),2);
  const te=calcStats(cellSigs(1,selCA,selPB),2);
  const stable=(tr.pfn!==null&&te.pfn!==null)?Math.abs(tr.pfn-te.pfn)<=0.10?'Y':'N':'?';
  const f=getFilters();
  const now=new Date().toISOString().slice(0,10);
  const text=[
    '## Gap 2+3 — Pullback Quality',
    'Date: '+now,
    `Best combo: candles_above ≥ ${{selCA}}, pullback_bars ≥ ${{selPB}}`,
    `Filters: shoot_depth=${{f.sd}} | touch_body_pct=${{f.tbp}} | same_candle=${{f.sctb}} | bounce_window=${{f.bw}}`,
    `Train PF: ${{tr.pf}} (${{tr.cnt}} signals) | Test PF: ${{te.pf}} (${{te.cnt}} signals)`,
    `Stable (train/test within ±0.10)?: ${{stable}}`,
    `Notes: WR Train=${{tr.wr}} Test=${{te.wr}} · AvgPnL Train=${{tr.avg}} Test=${{te.avg}} · CAGR Train=${{tr.cagr}} Test=${{te.cagr}}`,
    `Interaction note: rate_of_descent = shoot_depth / pullback_bars → log for Optuna, not a column`,
  ].join('\\n');
  navigator.clipboard.writeText(text).then(()=>{{
    const t=document.getElementById('toast');
    t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),2500);
  }});
}}

// ── INIT ──────────────────────────────────────────────────────────────────────
onFilter();
updateS4();
</script>
</body>
</html>"""

print('Writing HTML...')
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(HTML, encoding='utf-8')
size_mb = OUT.stat().st_size / 1e6
print(f'Saved: {OUT}')
print(f'Size : {size_mb:.1f} MB')
