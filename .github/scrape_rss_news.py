import os
import csv
import time
import pytz
import requests
from bs4 import BeautifulSoup
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

def fetch_bing_news(query):
    logger.info(f"🔍 Scraping Bing News for: {query}")
    encoded = quote_plus(query)
    url = f"https://www.bing.com/news/search?q={encoded}&qft=sortbydate%3d%221%22&form=YFNR"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NewsScraper/1.0; +https://github.com/yourrepo)"
    }

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        logger.error(f"Failed to fetch Bing News page for query '{query}': HTTP {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for card in soup.select('div.news-card'):
        try:
            link_tag = card.find('a', href=True)
            link = link_tag['href'] if link_tag else ''
            title_tag = card.find('a', class_='title')
            title = title_tag.text.strip() if title_tag else ''
            summary_tag = card.find('div', class_='snippet')
            summary = summary_tag.text.strip() if summary_tag else ''
            source_tag = card.find('div', class_='source')
            pub_name = source_tag.text.strip() if source_tag else ''
            time_tag = card.find('span', class_='source')
            time_text = time_tag.text.strip() if time_tag else ''

            # Bing does not provide relative time in a simple format; skipping detailed parse for now
            publishedAt = now  # fallback to current time

            results.append({
                'publishedAt': publishedAt.isoformat(),
                'title': title,
                'summary': summary[:200],
                'link': link,
                'domain': clean_domain(link),
                'source': {'name': pub_name}
            })
        except Exception as e:
            logger.warning(f"Error parsing an article: {e}")
    logger.info(f"Found {len(results)} articles on page.")
    return results

def write_csv(path, articles):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Publication', 'Title', 'Link', 'Summary'])
        for a in sorted(articles, key=lambda x: x['date'], reverse=True):
            writer.writerow([a['date'].strftime('%Y-%m-%d %H:%M'), a['pub'], a['title'], a['link'], a['summary']])

def main():
    logger.info("🚀 Starting scrape...")

    queries = KEYWORDS + [f'"Palo Alto Networks" AND {sp}' for sp in SPOKESPEOPLE]
    raw_articles = []

    for query in queries:
        raw_articles += fetch_bing_news(query)
        time.sleep(1)  # gentle delay

    logger.info("🔎 Domains before filtering:")
    for a in raw_articles:
        logger.info(f"{clean_domain(a['link'])} → {a['title']}")

    filtered = filter_articles_by_keywords_and_spokespeople(
        raw_articles, KEYWORDS, SPOKESPEOPLE, allowed_domains=None
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
- Scrapes Bing News HTML directly (no RSS, no API keys)
- Each keyword/spokesperson searched independently
- Filters by target domains (currently disabled for testing)
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
