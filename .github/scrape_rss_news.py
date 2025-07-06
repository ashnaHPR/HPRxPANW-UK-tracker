import requests
import feedparser
import os
import csv
import time
import pytz
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from scripts.config import KEYWORDS, SPOKESPEOPLE, NATIONAL_DOMAINS, ALL_DOMAINS
from scripts.utils import (
    clean_domain, classify_domain, escape_md, deduplicate_articles, format_article,
    filter_articles_by_keywords_and_spokespeople
)
from scripts.logger import logging

API_KEY = os.getenv("GNEWS_API_KEY")
assert API_KEY, "⚠️ GNEWS_API_KEY not set as GitHub Secret"

BST = pytz.timezone('Europe/London')
now = datetime.now(BST)

def fetch_articles():
    logging.info("🔍 Fetching GNews articles...")
    url = "https://gnews.io/api/v4/search"
    params = {
        'q': ' OR '.join(f'"{k}"' for k in KEYWORDS),
        'lang': 'en',
        'from': (now - timedelta(days=30)).strftime('%Y-%m-%d'),
        'max': 100,
        'token': API_KEY
    }

    for attempt in range(3):
        resp = requests.get(url, params=params)
        if resp.status_code == 429:
            logging.warning("⏳ Rate limited by GNews. Retrying...")
            time.sleep(60 * (attempt + 1))
            continue
        try:
            resp.raise_for_status()
            return resp.json().get('articles', [])
        except Exception as e:
            logging.error(f"GNews API error: {e}")
            return []
    return []

def fetch_google_rss():
    logging.info("🔍 Fetching Google RSS articles...")
    query = quote_plus(' OR '.join(f'"{k}"' for k in KEYWORDS))
    url = f"https://news.google.com/rss/search?q={query}&hl=en-GB&gl=GB&ceid=GB:en"
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

def write_csv(path, articles):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Publication', 'Title', 'Link', 'Summary'])
        for a in sorted(articles, key=lambda x: x['date'], reverse=True):
            writer.writerow([a['date'].strftime('%Y-%m-%d %H:%M'), a['pub'], a['title'], a['link'], a['summary']])

def main():
    raw = fetch_articles() + fetch_google_rss()

    allowed_domains = set(NATIONAL_DOMAINS).union(set(ALL_DOMAINS))

    # Filter raw articles by keywords, spokespeople, and domains
    filtered_raw = filter_articles_by_keywords_and_spokespeople(raw, KEYWORDS, SPOKESPEOPLE, allowed_domains)

    # Deduplicate then format
    formatted = [format_article(a, now) for a in deduplicate_articles(filtered_raw) if a.get('publishedAt')]

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

    md += """
---

## Technical Summary

This automated tracker monitors media mentions of Palo Alto Networks using Python.

### Features:
- Pulls news every 4 hours from GNews API + Google News RSS
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

    with open("RE
