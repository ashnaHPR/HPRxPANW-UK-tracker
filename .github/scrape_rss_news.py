import requests
import feedparser
import os
import csv
import time
import pytz
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from scripts.config import NATIONAL_DOMAINS
from scripts.utils import clean_domain, classify_domain, escape_md, deduplicate_articles, format_article
from scripts.logger import logging

BST = pytz.timezone('Europe/London')
now = datetime.now(BST)

# Define separate RSS search streams with their queries
SEARCH_STREAMS = {
    "panw": ['"Palo Alto Networks"', '"Unit 42"'],
    "uk": ['"Palo Alto Networks" AND UK'],
    "tim_erridge": ['"Palo Alto Networks" AND Tim Erridge'],
    "sam_rubin": ['"Palo Alto Networks" AND Sam Rubin'],
    "carla_baker": ['"Palo Alto Networks" AND Carla Baker'],
    "scott_mckinnon": ['"Palo Alto Networks" AND Scott Mckinnon'],
}

def fetch_google_rss_for_query(query_terms):
    query = quote_plus(' OR '.join(query_terms))
    url = f"https://news.google.com/rss/search?q={query}&hl=en-GB&gl=GB&ceid=GB:en"
    logging.info(f"Fetching Google RSS for query: {query_terms}")
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        if not hasattr(entry, 'published'):
            continue
        try:
            dt = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc).astimezone(BST)
        except Exception:
            continue
        articles.append({
            'publishedAt': dt.isoformat(),
            'title': entry.title,
            'summary': entry.get('summary', '')[:200],
            'link': entry.link,
            'domain': clean_domain(entry.link),
            'source': {'name': clean_domain(entry.link)}
        })
    return articles

def fetch_bing_rss_for_query(query_terms):
    query = quote_plus(' OR '.join(query_terms))
    url = f"https://www.bing.com/news/search?q={query}&format=rss"
    logging.info(f"Fetching Bing RSS for query: {query_terms}")
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

def main():
    all_articles = []

    for stream_name, keywords in SEARCH_STREAMS.items():
        google_articles = fetch_google_rss_for_query(keywords)
        bing_articles = fetch_bing_rss_for_query(keywords)
        all_articles.extend(google_articles)
        all_articles.extend(bing_articles)

    formatted = [format_article(a, now) for a in deduplicate_articles(all_articles) if a.get('publishedAt')]
    today = now.date()

    from scripts.config import KEYWORDS, SPOKESPEOPLE  # if not already imported

    today_articles = [
        a for a in formatted if a['date'].date() == today and (
            any(k.lower() in a['title'].lower() for k in KEYWORDS) or
            any(sp in (a['title'] + a['summary']).lower() for sp in SPOKESPEOPLE)
        )
    ]
    national_today = [a for a in today_articles if classify_domain(a['domain']) == "national"]
    trade_today = [a for a in today_articles if classify_domain(a['domain']) == "trade"]
    weekly = [a for a in formatted if a['date'].date() >= today - timedelta(days=7)]
    monthly = [a for a in formatted if a['date'].date() >= today - timedelta(days=30)]

    md = f"# 🔐 Palo Alto Networks Coverage\n\n_Last updated: {now.strftime('%Y-%m-%d %H:%M %Z')}_\n\n"
    md += build_md_table("📌 All PANW Mentions Today", today_articles)
    md += build_md_table("📰 National Coverage", national_today)
    md += build_md_table("📘 Trade Coverage", trade_today)

    md += """
---

## Technical Summary

This automated tracker monitors media mentions of Palo Alto Networks using Python.

### Features:
- Pulls news every 4 hours from Google News RSS + Bing News RSS
- Filters for keywords & named spokespeople
- Classifies by publication type (national or trade)
- Updates `README.md` with markdown tables
- Outputs weekly/monthly CSVs
- Fully timezone-aware (BST)
- GitHub Actions-powered for CI/CD

📌 Keywords: `{}`  
🧑‍💼 Spokespeople tracked: `{}`  
📰 National domains: `{}`

""".format(', '.join(KEYWORDS), ', '.join(SPOKESPEOPLE), len(NATIONAL_DOMAINS))

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)

    write_csv("summaries/weekly/summary.csv", weekly)
    write_csv("summaries/monthly/summary.csv", monthly)
    logging.info("✅ Updated README.md and CSVs.")

if __name__ == "__main__":
    main()
