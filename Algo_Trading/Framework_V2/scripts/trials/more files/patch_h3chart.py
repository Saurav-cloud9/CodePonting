import re

path = r"c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_h3_chart.html"
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# ── 1. CSS: Add navigator styles after .stability.warn ───────────────────────
NAV_CSS = """
/* ── NAVIGATOR ── */
.nav-btn{background:var(--bg4);border:1px solid var(--border2);color:var(--amber);border-radius:5px;padding:6px 14px;font-size:12px;font-weight:600;cursor:pointer;margin-bottom:10px;display:block}
.nav-btn:hover{background:#333}
.nav-card{background:var(--bg4);border:1px solid var(--amber);border-radius:6px;padding:10px 14px;margin-bottom:10px;display:none}
.nav-header{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.nav-ctrl-btn{background:var(--bg3);border:1px solid var(--border2);color:var(--fg2);border-radius:4px;padding:2px 8px;font-size:12px;cursor:pointer}
.nav-ctrl-btn:disabled{opacity:.35;cursor:default}
.nav-pos{font-size:12px;font-weight:700;color:var(--amber);flex:1;text-align:center}
.nav-reset{background:transparent;border:1px solid var(--border2);color:var(--fg3);border-radius:4px;padding:2px 8px;font-size:11px;cursor:pointer}
.nav-reset:hover{color:var(--fg)}
.nav-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-bottom:6px}
.nav-cell{display:flex;flex-direction:column;gap:2px}
.nav-lbl{font-size:10px;color:var(--fg3)}
.nav-val{font-size:12px;font-weight:700;color:var(--fg)}
.nav-stab{font-size:11px;margin-top:2px}
.nav-stab.g{color:var(--green)}.nav-stab.a{color:var(--amber)}.nav-stab.r{color:var(--red)}
.nav-cluster{background:rgba(74,222,128,0.12);border:1px solid var(--green);border-radius:5px;padding:7px 12px;font-size:11px;color:var(--green);margin-bottom:10px;display:none}"""

OLD_CSS = ".stability.ok{color:var(--green)}.stability.warn{color:var(--amber)}"
assert OLD_CSS in html, "CSS anchor not found"
html = html.replace(OLD_CSS, OLD_CSS + NAV_CSS, 1)

# ── 2. HTML: Add button + nav card between slider-block and readout ──────────
NAV_HTML = (
    "  </div>\n"
    '  <button class="nav-btn" onclick="findBestCombos()">&#9733; Find Best Combo</button>\n'
    '  <div id="nav-cluster-banner" class="nav-cluster"></div>\n'
    '  <div id="nav-card" class="nav-card">\n'
    '    <div class="nav-header">\n'
    '      <button class="nav-ctrl-btn" id="nav-prev" onclick="navStep(-1)" disabled>&#9664;</button>\n'
    '      <span class="nav-pos" id="nav-pos">#1 of 10</span>\n'
    '      <button class="nav-ctrl-btn" id="nav-next" onclick="navStep(1)">&#9654;</button>\n'
    '      <button class="nav-reset" onclick="resetNavigator()">Reset</button>\n'
    '    </div>\n'
    '    <div class="nav-grid">\n'
    '      <div class="nav-cell"><span class="nav-lbl">Offset</span><span class="nav-val" id="nav-offset">\u2014</span></div>\n'
    '      <div class="nav-cell"><span class="nav-lbl">Threshold</span><span class="nav-val" id="nav-thresh">\u2014</span></div>\n'
    '      <div class="nav-cell"><span class="nav-lbl">Test PF</span><span class="nav-val" id="nav-pf-te">\u2014</span></div>\n'
    '      <div class="nav-cell"><span class="nav-lbl">Train PF</span><span class="nav-val" id="nav-pf-tr">\u2014</span></div>\n'
    '      <div class="nav-cell"><span class="nav-lbl">Test N</span><span class="nav-val" id="nav-n-te">\u2014</span></div>\n'
    '      <div class="nav-cell"><span class="nav-lbl">Score</span><span class="nav-val" id="nav-score">\u2014</span></div>\n'
    '    </div>\n'
    '    <div class="nav-stab" id="nav-stability">\u2014</div>\n'
    '  </div>\n'
    '  <div class="readout">'
)

OLD_HTML = "  </div>\n  <div class=\"readout\">"
assert OLD_HTML in html, "HTML readout anchor not found"
html = html.replace(OLD_HTML, NAV_HTML, 1)

# ── 3. Legend filter ──────────────────────────────────────────────────────────
OLD_LEGEND = "      labels: { color: '#888', font: { size: 10 }, boxWidth: 14, padding: 10 }"
NEW_LEGEND = "      labels: { color: '#888', font: { size: 10 }, boxWidth: 14, padding: 10,\n        filter: (item) => item.text !== '' }"
assert OLD_LEGEND in html, "Legend anchor not found"
html = html.replace(OLD_LEGEND, NEW_LEGEND, 1)

# ── 4 & 5. Add nav dot datasets to BOTH charts ────────────────────────────────
NAV_DOT_DS = (
    "        { type:'line', label:'', data:[], showLine:false, borderColor:'#f97316', backgroundColor:'#f97316',\n"
    "          pointRadius:9, pointHoverRadius:11, pointStyle:'circle', yAxisID:'yLeft', order:0 },\n"
    "        { type:'line', label:'', data:[], showLine:false, borderColor:'#f97316', backgroundColor:'transparent',\n"
    "          pointRadius:5, pointHoverRadius:7, pointStyle:'circle', yAxisID:'yLeft', order:0 },\n"
)

# Chart A anchor (ends with vline: { idx: selThresh })
OLD_DS_A = (
    "        refLine(0.95, C_AMBER, 'PF = 0.95'),\n"
    "      ]\n"
    "    },\n"
    "    options: Object.assign({}, chartDefaults, {\n"
    "      plugins: Object.assign({}, chartDefaults.plugins, {\n"
    "        vline: { idx: selThresh },"
)
NEW_DS_A = (
    "        refLine(0.95, C_AMBER, 'PF = 0.95'),\n"
    + NAV_DOT_DS +
    "      ]\n"
    "    },\n"
    "    options: Object.assign({}, chartDefaults, {\n"
    "      plugins: Object.assign({}, chartDefaults.plugins, {\n"
    "        vline: { idx: selThresh },"
)
assert OLD_DS_A in html, "ChartA dataset anchor not found"
html = html.replace(OLD_DS_A, NEW_DS_A, 1)

# Chart B anchor (ends with vline: { idx: selOff })
OLD_DS_B = (
    "        refLine(0.95, C_AMBER, 'PF = 0.95'),\n"
    "      ]\n"
    "    },\n"
    "    options: Object.assign({}, chartDefaults, {\n"
    "      plugins: Object.assign({}, chartDefaults.plugins, {\n"
    "        vline: { idx: selOff },"
)
NEW_DS_B = (
    "        refLine(0.95, C_AMBER, 'PF = 0.95'),\n"
    + NAV_DOT_DS +
    "      ]\n"
    "    },\n"
    "    options: Object.assign({}, chartDefaults, {\n"
    "      plugins: Object.assign({}, chartDefaults.plugins, {\n"
    "        vline: { idx: selOff },"
)
assert OLD_DS_B in html, "ChartB dataset anchor not found"
html = html.replace(OLD_DS_B, NEW_DS_B, 1)

# ── 6. JS navigator functions before syncAll ─────────────────────────────────
NAV_JS = (
    "// \u2500\u2500 NAVIGATOR \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
    "let navCombos = [];\n"
    "let navIdx    = -1;\n"
    "\n"
    "function findBestCombos() {\n"
    "  navCombos = GRID\n"
    "    .filter(r => r.oi < 6 && r.n_te >= 1000)\n"
    "    .map(r => ({ ...r, score: r.pf_te * Math.log(r.n_te) }))\n"
    "    .sort((a, b) => b.score - a.score)\n"
    "    .slice(0, 10);\n"
    "  navIdx = 0;\n"
    "  checkCluster();\n"
    "  renderNavCard();\n"
    "  navSnapSliders();\n"
    "}\n"
    "\n"
    "function navStep(dir) {\n"
    "  const next = navIdx + dir;\n"
    "  if (next < 0 || next >= navCombos.length) return;\n"
    "  navIdx = next;\n"
    "  renderNavCard();\n"
    "  navSnapSliders();\n"
    "}\n"
    "\n"
    "function navSnapSliders() {\n"
    "  const r = navCombos[navIdx];\n"
    "  document.getElementById('sl-off').value    = r.oi;\n"
    "  document.getElementById('sl-thresh').value = r.ti;\n"
    "  syncAll();\n"
    "}\n"
    "\n"
    "function renderNavCard() {\n"
    "  const card = document.getElementById('nav-card');\n"
    "  if (!navCombos.length) { card.style.display = 'none'; return; }\n"
    "  card.style.display = 'block';\n"
    "  const r = navCombos[navIdx];\n"
    "  document.getElementById('nav-pos').textContent     = '#' + (navIdx + 1) + ' of ' + navCombos.length;\n"
    "  document.getElementById('nav-offset').textContent  = OFF_LABELS[r.oi];\n"
    "  document.getElementById('nav-thresh').textContent  = r.thresh.toFixed(2) + '%';\n"
    "  document.getElementById('nav-pf-te').textContent   = r.pf_te.toFixed(3);\n"
    "  document.getElementById('nav-pf-tr').textContent   = r.pf_tr.toFixed(3);\n"
    "  document.getElementById('nav-n-te').textContent    = r.n_te.toLocaleString();\n"
    "  document.getElementById('nav-score').textContent   = r.score.toFixed(3);\n"
    "  const delta = Math.abs(r.pf_te - r.pf_tr);\n"
    "  const stEl  = document.getElementById('nav-stability');\n"
    "  if (delta < 0.03)      { stEl.textContent = '\\u25CF Stable (|\\u0394PF| < 0.03)';        stEl.className = 'nav-stab g'; }\n"
    "  else if (delta < 0.07) { stEl.textContent = '\\u25CF Marginal (|\\u0394PF| < 0.07)';      stEl.className = 'nav-stab a'; }\n"
    "  else                   { stEl.textContent = '\\u25CF Unstable (|\\u0394PF| \\u2265 0.07)'; stEl.className = 'nav-stab r'; }\n"
    "  document.getElementById('nav-prev').disabled = (navIdx === 0);\n"
    "  document.getElementById('nav-next').disabled = (navIdx === navCombos.length - 1);\n"
    "  updateNavDots();\n"
    "}\n"
    "\n"
    "function resetNavigator() {\n"
    "  navCombos = [];\n"
    "  navIdx    = -1;\n"
    "  document.getElementById('nav-card').style.display = 'none';\n"
    "  document.getElementById('nav-cluster-banner').style.display = 'none';\n"
    "  [chartA, chartB].forEach(ch => {\n"
    "    ch.data.datasets[5].data = [];\n"
    "    ch.data.datasets[6].data = [];\n"
    "    ch.update('none');\n"
    "  });\n"
    "}\n"
    "\n"
    "function checkCluster() {\n"
    "  const banner = document.getElementById('nav-cluster-banner');\n"
    "  if (navCombos.length < 7) { banner.style.display = 'none'; return; }\n"
    "  const top    = navCombos[0];\n"
    "  const nearby = navCombos.filter(r =>\n"
    "    Math.abs(r.oi - top.oi) <= 1 && Math.abs(r.thresh - top.thresh) <= 0.02\n"
    "  );\n"
    "  if (nearby.length >= 7) {\n"
    "    banner.style.display = 'block';\n"
    "    banner.textContent = '\\u2605 Cluster: ' + nearby.length + '/10 combos within \\xB11 offset & \\xB10.02% of best (' +\n"
    "      OFF_LABELS[top.oi] + ', ' + top.thresh.toFixed(2) + '%)';\n"
    "  } else {\n"
    "    banner.style.display = 'none';\n"
    "  }\n"
    "}\n"
    "\n"
    "function updateNavDots() {\n"
    "  if (!navCombos.length) return;\n"
    "  const curr   = navCombos[navIdx];\n"
    "  const others = navCombos.filter((_, i) => i !== navIdx);\n"
    "\n"
    "  const currA   = Array(15).fill(null);\n"
    "  const othersA = Array(15).fill(null);\n"
    "  currA[curr.ti] = curr.pf_te;\n"
    "  others.forEach(r => { if (othersA[r.ti] === null) othersA[r.ti] = r.pf_te; });\n"
    "\n"
    "  const currB   = Array(8).fill(null);\n"
    "  const othersB = Array(8).fill(null);\n"
    "  currB[curr.oi] = curr.pf_te;\n"
    "  others.forEach(r => { if (othersB[r.oi] === null) othersB[r.oi] = r.pf_te; });\n"
    "\n"
    "  chartA.data.datasets[5].data = currA;\n"
    "  chartA.data.datasets[6].data = othersA;\n"
    "  chartB.data.datasets[5].data = currB;\n"
    "  chartB.data.datasets[6].data = othersB;\n"
    "  chartA.update('none');\n"
    "  chartB.update('none');\n"
    "}\n"
    "\n"
)

OLD_SYNCALL = "function syncAll() {"
assert OLD_SYNCALL in html, "syncAll anchor not found"
html = html.replace(OLD_SYNCALL, NAV_JS + OLD_SYNCALL, 1)

# ── Verify ────────────────────────────────────────────────────────────────────
checks = [
    ("nav-cluster-banner", 2),
    ("findBestCombos", 2),
    ("navStep", 2),
    ("navSnapSliders", 2),
    ("renderNavCard", 3),
    ("resetNavigator", 2),
    ("checkCluster", 2),
    ("updateNavDots", 2),
    ("nav-card", 4),
    ("nav-btn", 2),
    ("datasets[5]", 3),
    ("datasets[6]", 3),
    ("filter: (item)", 1),
]
all_ok = True
for token, expected_min in checks:
    count = html.count(token)
    ok = count >= expected_min
    print(f"{'OK' if ok else 'FAIL'} [{count}x] {token}")
    if not ok:
        all_ok = False

if all_ok:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\nWritten OK. Size: {len(html):,} bytes ({len(html)//1024} KB)")
else:
    print("\nAborted — some checks failed, file not written")
