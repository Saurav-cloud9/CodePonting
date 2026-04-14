path = r"c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_h3_chart.html"
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# ── 1. Replace findBestCombos with PF gate + fallback ──────────────────────
OLD_FIND = (
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
    "}"
)
NEW_FIND = (
    "let navCombos   = [];\n"
    "let navIdx      = -1;\n"
    "let navFallback = false;\n"
    "\n"
    "function findBestCombos() {\n"
    "  const base = GRID.filter(r => r.oi < 6 && r.n_te >= 1000)\n"
    "    .map(r => ({ ...r, score: r.pf_te * Math.log(r.n_te) }))\n"
    "    .sort((a, b) => b.score - a.score);\n"
    "  const qualified = base.filter(r => r.pf_te >= 1.0);\n"
    "  navFallback = qualified.length < 5;\n"
    "  navCombos = (navFallback ? base : qualified).slice(0, 10);\n"
    "  navIdx = 0;\n"
    "  checkCluster();\n"
    "  renderNavCard();\n"
    "  navSnapSliders();\n"
    "}"
)
assert OLD_FIND in html, "findBestCombos anchor not found"
html = html.replace(OLD_FIND, NEW_FIND, 1)

# ── 2. Add fallback warning in renderNavCard after card.style.display = 'block' ──
OLD_RENDER = "  card.style.display = 'block';\n  const r = navCombos[navIdx];"
NEW_RENDER = (
    "  card.style.display = 'block';\n"
    "  const fbEl = document.getElementById('nav-fallback-note');\n"
    "  if (fbEl) fbEl.style.display = navFallback ? 'block' : 'none';\n"
    "  const r = navCombos[navIdx];"
)
assert OLD_RENDER in html, "renderNavCard display anchor not found"
html = html.replace(OLD_RENDER, NEW_RENDER, 1)

# ── 3. Add fallback note div inside nav-card header area ─────────────────────
OLD_NAV_HEADER_END = "    <div class=\"nav-stab\" id=\"nav-stability\">\u2014</div>\n  </div>"
NEW_NAV_HEADER_END = (
    "    <div class=\"nav-stab\" id=\"nav-stability\">\u2014</div>\n"
    "    <div id=\"nav-fallback-note\" style=\"display:none;margin-top:6px;padding:5px 10px;"
    "background:rgba(251,191,36,0.12);border:1px solid #fbbf24;border-radius:4px;"
    "font-size:11px;color:#fbbf24\">"
    "\u26a0 No combos above PF 1.0 \u2014 showing best available</div>\n"
    "  </div>"
)
assert OLD_NAV_HEADER_END in html, "nav-card footer anchor not found"
html = html.replace(OLD_NAV_HEADER_END, NEW_NAV_HEADER_END, 1)

# ── 4. resetNavigator: also hide fallback note ────────────────────────────────
OLD_RESET = "  document.getElementById('nav-cluster-banner').style.display = 'none';"
NEW_RESET = (
    "  document.getElementById('nav-cluster-banner').style.display = 'none';\n"
    "  const fbEl2 = document.getElementById('nav-fallback-note');\n"
    "  if (fbEl2) fbEl2.style.display = 'none';\n"
    "  navFallback = false;"
)
assert OLD_RESET in html, "resetNavigator anchor not found"
html = html.replace(OLD_RESET, NEW_RESET, 1)

# ── Verify ────────────────────────────────────────────────────────────────────
checks = [
    "navFallback",
    "qualified.length < 5",
    "nav-fallback-note",
    "No combos above PF 1.0",
    "pf_te >= 1.0",
]
all_ok = True
for c in checks:
    ok = c in html
    print(f"{'OK' if ok else 'MISSING'} {c}")
    if not ok:
        all_ok = False

if all_ok:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\nWritten OK. Size: {len(html):,} bytes")
else:
    print("\nAborted.")
