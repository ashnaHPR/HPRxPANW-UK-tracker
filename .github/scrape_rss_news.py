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


def fetch_google_news(query):
    logger.info(f"🔍 Scraping Google News for: {query}")
    encoded = quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}&tbm=nws&hl=en-GB"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NewsScraper/1.0; +https://github.com/yourrepo)"
    }

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        logger.error(f"Failed to fetch Google News page for query '{query}': HTTP {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    # Updated selectors based on current Google News HTML structure
    for g in soup.select('div.NiLAwe.y6IFtc.R7GTQ.keNKEd.j7vNaf.nID9nc'):
        try:
            link_tag = g.find('a')
            link = link_tag['href'] if link_tag else ''
            title_tag = g.find('h3')
            title = title_tag.text.strip() if title_tag else ''
            snippet_tag = g.find('div', class_='GI74Re nDgy9d')
            summary = snippet_tag.text.strip() if snippet_tag else ''
            source_time_tag = g.find('div', class_='QmrVtf RD0gLb Kybdz')
            pub_name = ''
            time_text = ''
            if source_time_tag:
                spans = source_time_tag.find_all('span')
                if spans:
                    pub_name = spans[0].text.strip()
                    if len(spans) > 1:
                        time_text = spans[1].text.strip()

            publishedAt = parse_relative_time(time_text)

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


def parse_relative_time(time_str):
    """
    Convert relative times like '2 hours ago', '1 day ago' to datetime in BST
    """
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(BST)
    if 'hour' in time_str:
        try:
            hours = int(time_str.split()[0])
            return now_utc - timedelta(hours=hours)
        except Exception:
            return now_utc
    elif 'minute' in time_str:
        try:
            minutes = int(time_str.split()[0])
            return now_utc - timedelta(minutes=minutes)
        except Exception:
            return now_utc
    elif 'day' in time_str:
        try:
            days = int(time_str.split()[0])
            return now_utc - timedelta(days=days)
        except Exception:
            return now_utc
    else:
        # fallback to now if unknown format or empty
        return now_utc


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
        raw_articles += fetch_google_news(query)
        time.sleep(1)  # gentle delay

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
- Scrapes Google News HTML directly (no RSS, no API keys)
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
