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
from bs4 import BeautifulSoup
import anthropic

feed = feedparser.parse("https://www.moneycontrol.com/rss/marketreports.xml")

print("=== Quant News Bot ===")
print("Fetching latest market headlines...")
print("Analysing with Claude AI...\n")

client = anthropic.Anthropic()
result = []

for i in feed.entries[:5]:
    attempts = 0
    while attempts < 3:
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=100,
                messages=[
                    {"role":"user","content":f"You are a quant analyst. Given this news headline and summary, in one line state whether this is Bullish / Bearish / Neutral and which strategy type is affected: Trend / Mean-Reversion / Macro {BeautifulSoup(i.title, "html.parser").get_text()} {BeautifulSoup(i.summary, "html.parser").get_text()}"
                    }
                ]
            )

            print("HEADLINE:", BeautifulSoup(i.title, "html.parser").get_text())
            print("ANALYSIS:", response.content[0].text)
            if "Bullish" in response.content[0].text:
                print("Signal: Bullish")
                result.append({"headline": i.title, "signal": "Bullish"})
            elif "Bearish" in response.content[0].text:
                print("Signal: Bearish")
                result.append({"headline": i.title, "signal": "Bearish"})
            else:
                print("Signal: Neutral")
                result.append({"headline": i.title, "signal": "Neutral"})
            print("---")
            print("\n")
            break

        except Exception as e:
            attempts += 1
            print(f"Retrying now. {attempts} attempts done")

x = sum(1 for r in result if r['signal'] == 'Bullish')
y = sum(1 for r in result if r['signal'] == 'Bearish')
z = sum(1 for r in result if r['signal'] == 'Neutral')
print(f"===== Today's Signal Summary: {x} bullish | {y} bearish | {z} neutral =====")






