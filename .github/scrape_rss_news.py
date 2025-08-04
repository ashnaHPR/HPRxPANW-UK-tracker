import feedparser
import os
import csv
import time
import pytz
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from scripts.config import KEYWORDS, SPOKESPEOPLE, NATIONAL_DOMAINS
from scripts.utils import (
    clean_domain, classify_domain, escape_md,
    deduplicate_articles, format_article,
    filter_articles_by_keywords_and_spokespeople
)
from scripts.logger import logger

BST = pytz.timezone('Europe/London')
now = datetime.now(BST)

# --------------------- Markdown builder ----------------------

def build_md_table(title, articles):
    if not articles:
        return f"## {title}\n\n_No articles found._\n\n"
    s = f"## {title}\n\n| Date | Publication | Title | Summary |\n|------|-------------|--------|---------|\n"
    for a in sorted(articles, key=lambda x: x['date'], reverse=True):
        s += (
            f"| {a['date'].strftime('%Y-%m-%d %H:%M')} "
            f"| {escape_md(a['pub'])} "
            f"| [{escape_md(a['title'])}]({a['link']}) "
            f"| {escape_md(a['summary'])} |\n"
        )
    return s + "\n"

# ------------------------ RSS Functions -----------------------

def fetch_google_rss(query):
    logger.info(f"🔍 Google News RSS for: {query}")
    encoded = quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-GB&gl=GB&ceid=GB:en"
    return parse_rss(url)

def fetch_bing_rss(query):
    logger.info(f"🔍 Bing News RSS for: {query}")
    encoded = quote_plus(query)
    url = f"https://www.bing.com/news/search?q={encoded}&format=rss"
    return parse_rss(url)

def parse_rss(url):
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        try:
            dt = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc).astimezone(BST)
        except Exception:
            dt = now
        articles.append({
            'publishedAt': dt.isoformat(),
            'title': entry.title,
            'summary': entry.get('summary', '')[:200],
            'link': entry.link,
            'domain': clean_domain(entry.link),
            'source': {'name': clean_domain(entry.link)}
        })
    return articles

# -------------------------- Helpers ---------------------------

def write_csv(path, articles):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Publication', 'Title', 'Link', 'Summary'])
        for a in sorted(articles, key=lambda x: x['date'], reverse=True):
            writer.writerow([a['date'].strftime('%Y-%m-%d %H:%M'), a['pub'], a['title'], a['link'], a['summary']])

# -------------------------- Main ------------------------------

def main():
    logger.info("🚀 Starting scrape...")

    queries = KEYWORDS + [f'"Palo Alto Networks" AND {sp}' for sp in SPOKESPEOPLE]
    raw_articles = []

    for query in queries:
        raw_articles += fetch_google_rss(query)
        time.sleep(1)  # polite delay between requests
        raw_articles += fetch_bing_rss(query)
        time.sleep(1)

    filtered = filter_articles_by_keywords_and_spokespeople(
        raw_articles, KEYWORDS, SPOKESPEOPLE, NATIONAL_DOMAINS
    )

    formatted = [format_article(a, now) for a in deduplicate_articles(filtered)]
    today = now.date()

    today_articles = [a for a in formatted if a['date'].date() == today]
    national_today = [a for a in today_articles if classify_domain(a['domain']) == "national"]
    trade_today = [a for a in today_articles if classify_domain(a['domain']) == "trade"]
    weekly = [a for a in formatted if a['date'].date() >= today - timedelta(days=7)]
    monthly = [a for a in formatted if a['date'].date() >= today - timedelta(days=30)]

    md = f"# 🔐 Palo Alto Networks Coverage\n\n_Last updated: {now.strftime('%Y-%m-%d %H:%M %Z')}_\n\n"
    md += build_md_table("📌 All PANW Mentions Today", today_articles)
    md += build_md_table("📰 National Coverage", national_today)
    md += build_md_table("📘 Trade Coverage", trade_today)

    md += f"""
---

## Technical Summary

This GitHub Action fetches UK coverage of Palo Alto Networks every 4 hours.

**Features:**
- RSS only (Google News & Bing News)
- Each keyword/spokesperson searched independently
- Filters by target domains
- Classifies into _national_ or _trade_
- Markdown + weekly/monthly CSV

📌 Keywords: `{', '.join(KEYWORDS)}`  
🧑‍💼 Spokespeople tracked: `{', '.join(SPOKESPEOPLE)}`  
📰 National domains: `{len(NATIONAL_DOMAINS)}` sources tracked

"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)

    write_csv("summaries/weekly/summary.csv", weekly)
    write_csv("summaries/monthly/summary.csv", monthly)

    logger.info("✅ Scrape complete. README + CSVs updated.")

if __name__ == "__main__":
    main()
