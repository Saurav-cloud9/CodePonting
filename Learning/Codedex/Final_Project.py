# ─── Quant News Bot — Core Elements ───

# 1. 📡 Data Source
#    RSS feed (Moneycontrol / Economic Times Markets)

# 2. 🔍 Parser
#    Extract headline + summary from feed

# 3. 🧠 AI Layer
#    Send to Claude API → get quant-relevant summary
#    "Does this affect trend/mean-reversion/macro?"

# 4. 🖨️ Output
#    Clean terminal print → headline + quant impact

# 5. ⏱️ Scheduler (optional)
#    Run every morning before market open

# ─── That's the full project. ───
# 5 elements. Each = one Python concept practiced.
# Simple. Useful. Submittable. 🎯

import feedparser
feed = feedparser.parse("https://www.moneycontrol.com/rss/marketreports.xml")

print(feed.status)      # should be 200
print(len(feed.entries)) # should be > 0

print(feed.entries[0].title)
print(feed.entries[0].summary)

for i in feed.entries[:5]:
    print(i.title)
    print(i.summary)