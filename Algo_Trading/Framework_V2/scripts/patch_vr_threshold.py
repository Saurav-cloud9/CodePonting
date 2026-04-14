path = r"c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_signal_viewer.html"
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

OLD = "vrColor = c.vr >= 1.5 ? '#f97316' : c.vr >= 1.0 ? '#888' : '#555d72';"
NEW = "vrColor = c.vr >= 1.2 ? '#f97316' : '#555d72';"

assert OLD in html, "anchor not found"
html = html.replace(OLD, NEW, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Done. 1.2x threshold applied.")
