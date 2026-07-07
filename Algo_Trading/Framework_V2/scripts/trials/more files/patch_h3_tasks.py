"""
Patch script — Tasks 1-4
  T1: Update scoring in H3.1 (stability_factor, fallback=0.96)
  T2: Remove save button from H3
  T3+4: Add save button + saveObs() to H3.1
"""

PATH_H3    = r"c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_h3_slope_tuner.html"
PATH_H31   = r"c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_h3_chart.html"

# ═══════════════════════════════════════════════════════════════════
# TASK 1 — Update scoring in H3.1
# ═══════════════════════════════════════════════════════════════════
with open(PATH_H31, 'r', encoding='utf-8') as f:
    h31 = f.read()

# 1a. Update findBestCombos: stability_factor in score + fallback=0.96
OLD_FIND = (
    "  const base = GRID.filter(r => r.oi < 6 && r.n_te >= 1000)\n"
    "    .map(r => ({ ...r, score: r.pf_te * Math.log(r.n_te) }))\n"
    "    .sort((a, b) => b.score - a.score);\n"
    "  const qualified = base.filter(r => r.pf_te >= 1.0);\n"
    "  navFallback = qualified.length < 5;\n"
    "  navCombos = (navFallback ? base : qualified).slice(0, 10);"
)
NEW_FIND = (
    "  const scoreFn = r => {\n"
    "    const sf = Math.max(0, 1 - Math.abs(r.pf_tr - r.pf_te) / 0.1);\n"
    "    return r.pf_te * Math.log(r.n_te) * sf;\n"
    "  };\n"
    "  const base = GRID.filter(r => r.oi < 6 && r.n_te >= 1000)\n"
    "    .map(r => ({ ...r, score: scoreFn(r) }))\n"
    "    .sort((a, b) => b.score - a.score);\n"
    "  const qualified = base.filter(r => r.pf_te >= 1.0);\n"
    "  const fallback96 = base.filter(r => r.pf_te >= 0.96);\n"
    "  navFallback = qualified.length < 5;\n"
    "  navCombos = (navFallback ? fallback96 : qualified).slice(0, 10);"
)
assert OLD_FIND in h31, "T1: findBestCombos anchor not found"
h31 = h31.replace(OLD_FIND, NEW_FIND, 1)

# ═══════════════════════════════════════════════════════════════════
# TASK 2 — Remove save button from H3
# ═══════════════════════════════════════════════════════════════════
with open(PATH_H3, 'r', encoding='utf-8') as f:
    h3 = f.read()

OLD_H3_BTN = (
    '\n<button class="exp-btn" onclick="exportObs()">Save Observation to gap_observations.md</button>\n'
    '<div class="toast" id="toast">Copied to clipboard — paste into gap_observations.md</div>\n'
)
assert OLD_H3_BTN in h3, "T2: H3 export button not found"
h3 = h3.replace(OLD_H3_BTN, '\n', 1)

# Also remove the exportObs() function from H3
OLD_H3_FN_END = "  }).catch(()=>prompt('Copy this observation:',text));\n}\n"
idx_fn    = h3.find("\nfunction exportObs() {")
idx_end   = h3.find(OLD_H3_FN_END)
if idx_fn > 0 and idx_end > 0:
    # walk back to find the comment line before function
    block_start = h3.rfind('\n', 0, idx_fn)  # one newline before
    h3 = h3[:block_start] + '\n' + h3[idx_end + len(OLD_H3_FN_END):]
    print("T2: exportObs() removed from H3")
else:
    print("T2: exportObs() fn not found — skipping fn removal")

# ═══════════════════════════════════════════════════════════════════
# TASKS 3+4 — Add save button + saveObs() to H3.1
# ═══════════════════════════════════════════════════════════════════

# 3a. Add toast CSS + save button CSS to H3.1 styles
OLD_CSS_END = ".nav-cluster{background:rgba(74,222,128,0.12);border:1px solid var(--green);border-radius:5px;padding:7px 12px;font-size:11px;color:var(--green);margin-bottom:10px;display:none}"
NEW_CSS_END = (
    OLD_CSS_END + "\n"
    ".save-obs-btn{display:block;margin:10px 0 0;background:var(--bg3);border:1px solid var(--border2);"
    "color:var(--fg2);border-radius:6px;padding:7px 22px;cursor:pointer;font-size:12px;width:100%}\n"
    ".save-obs-btn:hover{background:var(--bg4)}\n"
    ".toast-h31{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#14532d;"
    "color:#bbf7d0;border-radius:6px;padding:7px 20px;font-size:12px;font-weight:600;"
    "opacity:0;transition:opacity .3s;pointer-events:none;z-index:99}\n"
    ".toast-h31.show{opacity:1}"
)
assert OLD_CSS_END in h31, "T3: CSS anchor not found"
h31 = h31.replace(OLD_CSS_END, NEW_CSS_END, 1)

# 3b. Add save button HTML after nav-card closing div (before readout)
OLD_BEFORE_READOUT = "  <div class=\"readout\">"
NEW_BEFORE_READOUT = (
    '  <button class="save-obs-btn" onclick="saveObs()">&#128190; Save Gap 1 Observations to gap_observations.md</button>\n'
    '  <div class="toast-h31" id="toast-h31"></div>\n'
    '  <div class="readout">'
)
assert OLD_BEFORE_READOUT in h31, "T3: readout anchor not found"
h31 = h31.replace(OLD_BEFORE_READOUT, NEW_BEFORE_READOUT, 1)

# 3c. Add saveObs() function before syncAll
SAVE_OBS_FN = (
    "// \u2500\u2500 SAVE OBSERVATION \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
    "function saveObs() {\n"
    "  if (!navCombos.length) {\n"
    "    alert('Please run \\u201cFind Best Combo\\u201d first to generate Top 10 before saving.');\n"
    "    return;\n"
    "  }\n"
    "  const now = new Date().toISOString().slice(0, 10);\n"
    "  const clusterEl = document.getElementById('nav-cluster-banner');\n"
    "  const clusterTxt = clusterEl && clusterEl.style.display !== 'none'\n"
    "    ? clusterEl.textContent.trim()\n"
    "    : 'No strong cluster detected — results scattered across offsets/thresholds.';\n"
    "  const best = navCombos[0];\n"
    "  const sfFn = r => Math.max(0, 1 - Math.abs(r.pf_tr - r.pf_te) / 0.1).toFixed(2);\n"
    "  const dpf  = r => (r.pf_te >= r.pf_tr ? '+' : '') + (r.pf_te - r.pf_tr).toFixed(3);\n"
    "  const stab = r => Math.abs(r.pf_te - r.pf_tr) < 0.03 ? 'Stable'\n"
    "                  : Math.abs(r.pf_te - r.pf_tr) < 0.07 ? 'Marginal' : 'Unstable';\n"
    "\n"
    "  const rows = navCombos.map((r, i) =>\n"
    "    '| ' + [i+1, OFF_LABELS[r.oi], r.thresh.toFixed(2)+'%',\n"
    "      r.pf_tr.toFixed(3), r.pf_te.toFixed(3),\n"
    "      r.n_te.toLocaleString(), dpf(r), stab(r), r.score.toFixed(3)\n"
    "    ].join(' | ') + ' |'\n"
    "  ).join('\\n');\n"
    "\n"
    "  const fallbackNote = navFallback\n"
    "    ? 'Fallback mode active — no combos above PF 1.0; showing best above PF 0.96'\n"
    "    : 'Primary mode — all combos pass PF_test \\u2265 1.0';\n"
    "\n"
    "  const md = [\n"
    "    '',\n"
    "    '## Gap 1 \\u2014 Slope Offset + Threshold',\n"
    "    'Date: ' + now,\n"
    "    'Scoring: PF_test \\u00d7 log(signals) \\u00d7 stability_factor',\n"
    "    'Min PF filter: 1.0 (fallback 0.96) \\u2014 ' + fallbackNote,\n"
    "    '',\n"
    "    '### Top 10 Combos',\n"
    "    '| Rank | Offset | Threshold | PF_train | PF_test | Signals | \\u0394PF | Stable | Score |',\n"
    "    '|------|--------|-----------|----------|---------|---------|-----|--------|-------|',\n"
    "    rows,\n"
    "    '',\n"
    "    '### Cluster Check',\n"
    "    clusterTxt,\n"
    "    '',\n"
    "    '### Key Observations',\n"
    "    '- Best combo: Offset ' + OFF_LABELS[best.oi] + ', Threshold ' + best.thresh.toFixed(2) + '% (PF_test ' + best.pf_te.toFixed(3) + ', N=' + best.n_te.toLocaleString() + ')',\n"
    "    '- Train vs Test regime note: test period (2024\\u20132025) shows cleaner trending conditions vs 2022\\u20132023 chop',\n"
    "    '- Gap 1 alone: PF > 1.0 requires high threshold \\u2192 low signals',\n"
    "    '- Parameters NOT locked \\u2014 awaiting Gaps 2\\u20135 + joint Optuna',\n"
    "    '',\n"
    "    '### Next Step',\n"
    "    'H4 \\u2014 Gap 2: Pullback quality (depth + structure)',\n"
    "    '',\n"
    "  ].join('\\n');\n"
    "\n"
    "  const toast = (msg, ok) => {\n"
    "    const t = document.getElementById('toast-h31');\n"
    "    t.textContent = msg;\n"
    "    t.style.background = ok ? '#14532d' : '#7f1d1d';\n"
    "    t.style.color = ok ? '#bbf7d0' : '#fca5a5';\n"
    "    t.classList.add('show');\n"
    "    setTimeout(() => t.classList.remove('show'), 3500);\n"
    "  };\n"
    "\n"
    "  if (window.showSaveFilePicker) {\n"
    "    // Try File System Access API (read existing + append)\n"
    "    window.showOpenFilePicker({\n"
    "      suggestedName: 'gap_observations.md',\n"
    "      types: [{ description: 'Markdown', accept: { 'text/markdown': ['.md'] } }],\n"
    "      multiple: false\n"
    "    }).then(async ([fh]) => {\n"
    "      const file = await fh.getFile();\n"
    "      const existing = await file.text();\n"
    "      const writable = await fh.createWritable();\n"
    "      await writable.write(existing + md);\n"
    "      await writable.close();\n"
    "      toast('Saved to gap_observations.md \\u2705', true);\n"
    "    }).catch(() => {\n"
    "      // User cancelled or error — fall back to clipboard\n"
    "      navigator.clipboard.writeText(md).then(() =>\n"
    "        toast('Copied to clipboard \\u2014 paste into gap_observations.md', true)\n"
    "      ).catch(() => { prompt('Copy this observation:', md); });\n"
    "    });\n"
    "  } else {\n"
    "    navigator.clipboard.writeText(md).then(() =>\n"
    "      toast('Copied to clipboard \\u2014 paste into gap_observations.md', true)\n"
    "    ).catch(() => { prompt('Copy this observation:', md); });\n"
    "  }\n"
    "}\n"
    "\n"
)

OLD_SYNCALL = "function updateReadout() {"
assert OLD_SYNCALL in h31, "T4: updateReadout anchor not found"
h31 = h31.replace(OLD_SYNCALL, SAVE_OBS_FN + OLD_SYNCALL, 1)

# ═══════════════════════════════════════════════════════════════════
# Verify + Write
# ═══════════════════════════════════════════════════════════════════
checks_h31 = [
    "scoreFn",
    "stability_factor" not in h31 and "sf = Math.max" in h31,  # new formula present
    "fallback96",
    "pf_te >= 0.96",
    "saveObs",
    "toast-h31",
    "Save Gap 1 Observations",
    "gap_observations.md",
    "showOpenFilePicker",
    "Top 10 Combos",
]
checks_h3 = [
    "exportObs" not in h3,  # removed
    "Save Observation to gap_observations.md" not in h3,  # removed
]

print("H3.1 checks:")
tokens = ["scoreFn", "fallback96", "pf_te >= 0.96", "saveObs", "toast-h31",
          "Save Gap 1 Observations", "showOpenFilePicker", "Top 10 Combos",
          "sf = Math.max"]
all_ok = True
for t in tokens:
    ok = t in h31
    print(f"  {'OK' if ok else 'MISSING'} {t}")
    if not ok: all_ok = False

print("H3 checks:")
for label, ok in [("exportObs removed", "exportObs" not in h3),
                  ("button removed", "Save Observation to gap_observations.md" not in h3)]:
    print(f"  {'OK' if ok else 'STILL PRESENT'} {label}")
    if not ok: all_ok = False

if all_ok:
    with open(PATH_H31, 'w', encoding='utf-8') as f:
        f.write(h31)
    with open(PATH_H3, 'w', encoding='utf-8') as f:
        f.write(h3)
    print(f"\nH3.1 written: {len(h31):,} bytes")
    print(f"H3   written: {len(h3):,} bytes")
else:
    print("\nAborted — checks failed, files not written")
