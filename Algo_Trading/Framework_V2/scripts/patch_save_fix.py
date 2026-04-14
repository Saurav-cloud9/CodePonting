# -*- coding: utf-8 -*-
path = r"c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_h3_chart.html"
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# Locate block by start/end markers
MARK_START = "  if (window.showSaveFilePicker) {"
MARK_END   = "  }\n}\n"

idx_s = html.find(MARK_START)
idx_e = html.find(MARK_END, idx_s) + len(MARK_END)
assert idx_s > 0, "start marker not found"
assert idx_e > len(MARK_END), "end marker not found"

OLD_BLOCK = html[idx_s:idx_e]

NEW_BLOCK = (
    "  if (window.showSaveFilePicker) {\n"
    "    // showSaveFilePicker works for both new and existing files\n"
    "    window.showSaveFilePicker({\n"
    "      suggestedName: 'gap_observations.md',\n"
    "      types: [{ description: 'Markdown', accept: { 'text/markdown': ['.md'] } }],\n"
    "    }).then(async (fh) => {\n"
    "      let existing = '';\n"
    "      try { const f = await fh.getFile(); existing = await f.text(); } catch(e) {}\n"
    "      const writable = await fh.createWritable();\n"
    "      await writable.write(existing + md);\n"
    "      await writable.close();\n"
    "      toast('Saved to gap_observations.md \u2705', true);\n"
    "    }).catch((e) => {\n"
    "      if (e && e.name === 'AbortError') return;\n"
    "      fallbackDownload(md);\n"
    "    });\n"
    "  } else {\n"
    "    fallbackDownload(md);\n"
    "  }\n"
    "}\n"
    "\n"
    "function fallbackDownload(md) {\n"
    "  const blob = new Blob([md], { type: 'text/markdown' });\n"
    "  const url  = URL.createObjectURL(blob);\n"
    "  const a    = document.createElement('a');\n"
    "  a.href = url; a.download = 'gap_observations.md'; a.click();\n"
    "  URL.revokeObjectURL(url);\n"
    "  const t = document.getElementById('toast-h31');\n"
    "  t.textContent = 'Downloaded \u2014 move to Framework_V2/research/';\n"
    "  t.style.background = '#1e3a5f'; t.style.color = '#93c5fd';\n"
    "  t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 4000);\n"
    "}\n"
)

html = html[:idx_s] + NEW_BLOCK + html[idx_e:]

checks = ["showSaveFilePicker", "fallbackDownload", "AbortError"]
all_ok = True
for c in checks:
    ok = c in html
    print(f"{'OK' if ok else 'MISSING'} {c}")
    if not ok: all_ok = False

if all_ok:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Written OK. {len(html):,} bytes")
else:
    print("Aborted.")
