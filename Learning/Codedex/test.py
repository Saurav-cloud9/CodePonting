import feedparser
from bs4 import BeautifulSoup
import anthropic

feed = feedparser.parse("https://quantocracy.com/feed/")
if len(feed.entries) > 0:
    print("Good")
else:
    print("oops!")