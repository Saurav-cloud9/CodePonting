# Quant News Bot: Fetches market headlines and analyses them using Claude AI

import feedparser
from bs4 import BeautifulSoup
import anthropic

feeds = {
    1: ("Moneycontrol", "https://www.moneycontrol.com/rss/marketreports.xml"),
    2: ("Quantocracy", "https://quantocracy.com/feed/"),
    3: ("Livemint", "https://www.livemint.com/rss/markets"),
    4: ("Investing.com", "https://in.investing.com/rss/news.rss")
}

while True:        
    print("=== Quant News Bot ===")
    print("Fetching latest market headlines...")
    print("Analysing with Claude AI...\n")

    print("Select a news source:")
    print("1. Moneycontrol")
    print("2. Quantocracy")
    print("3. LiveMint")
    print("4. Investing.com India")

    choice = int(input("Enter 1-4: "))

    feed = feedparser.parse(feeds[choice][1])

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

    again = input("Do you want to try another news bot?(Y/N): ").lower()
    if again == 'y':
        continue
    else:
        break





