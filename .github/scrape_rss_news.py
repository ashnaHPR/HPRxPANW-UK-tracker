import os
import csv
import time
import pytz
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlparse, parse_qs
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

def parse_bing_time(time_str: str) -> datetime:
    time_str = time_str.lower().strip()
    now_dt = datetime.now(BST)

    try:
        if time_str in ('just now', ''):
            return now_dt
        if time_str.endswith('h'):
            hours = int(time_str[:-1])
            return now_dt - timedelta(hours=hours)
        if time_str.endswith('d'):
            days = int(time_str[:-1])
            return now_dt - timedelta(days=days)
        if time_str.endswith('m'):
            mins = int(time_str[:-1])
            return now_dt - timedelta(minutes=mins)
        if time_str.endswith('y'):
            years = int(time_str[:-1])
            return now_dt - timedelta(days=years * 365)

        # Try parsing absolute formats
        for fmt in ['%b %d, %Y', '%B %d, %Y']:
            try:
                parsed_date = datetime.strptime(time_str, fmt)
                return BST.localize(parsed_date)
            except:
                continue

        logger.warning(f"Unrecognized time format: '{time_str}'")
        return now_dt - timedelta(days=30)

    except Exception as e:
        logger.warning(f"Failed to parse time: '{time_str}' - {e}")
        return now_dt - timedelta(days=30)

def extract_real_link(href: str) -> str:
    if not href:
        return ''
    if href.startswith('/'):
        return f"https://www.bing.com{href}"
    if 'bing.com/news/url' in href:
        # Bing redirects through a query param
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        return qs.get('url', [href])[0]
    return href

def fetch_bing_news(query, interval_hours=None):
    logger.info(f"🔍 Scraping Bing News for: {query} (interval={interval_hours}h)")
    encoded = quote_plus(query)
    url = f"https://www.bing.com/news/search?q={encoded}&setlang=en-US&mkt=en-GB"
    if interval_hours:
        url += f"&qft=interval%3d%22{interval_hours}%22"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        logger.error(f"Failed to fetch Bing News page for query '{query}': HTTP {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    articles = soup.select('div.news-card') or soup.select('div.t_s')
    if not articles:
        logger.warning("No articles found using known selectors.")
        return []

    for g in articles:
        try:
            link_tag = g.find('a')
            link = extract_real_link(link_tag.get('href', '')) if link_tag else ''
            title = link_tag.text.strip() if link_tag else ''

            summary_tag = g.find('div', class_='snippet') or g.find('div.snippet')
            summary = summary_tag.text.strip() if summary_tag else ''

            # More robust pub name detection
            pub_name = ''
            for selector in ['div.source', 'div.source span', 'span.source']:
                el = g.select_one(selector)
                if el and el.text.strip() not in ('', '.'):
                    pub_name = el.text.strip()
                    break
            if not pub_name:
                pub_name = "Unknown"

            time_tag = g.find('span', class_='time')
            time_text = time_tag.text.strip() if time_tag else ''
            publishedAt = parse_bing_time(time_text)

            if (now - publishedAt).days > 7:
                continue

            domain = clean_domain(link)

            results.append({
                'date': publishedAt,
                'title': title,
                'summary': summary[:200],
                'link': link,
                'pub': pub_name,
                'domain': domain,
            })

        except Exception as e:
            logger.warning(f"Error parsing a Bing article: {e}")
            # logger.debug(g.prettify())  # Uncomment for full HTML debug

    logger.info(f"✅ Found {len(results)} articles.")
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

    all_articles_1h = []
    all_articles_24h = []
    all_articles_7d = []

    for query in queries:
        all_articles_1h += fetch_bing_news(query, interval_hours=1)
        time.sleep(1)
        all_articles_24h += fetch_bing_news(query, interval_hours=24)
        time.sleep(1)
        all_articles_7d += fetch_bing_news(query, interval_hours=168)
        time.sleep(1)

    # Filter and deduplicate 24h articles
    filtered_24h = filter_articles_by_keywords_and_spokespeople(
        all_articles_24h, KEYWORDS, SPOKESPEOPLE, allowed_domains=None
    )
    formatted_24h = [format_article(a, now) for a in deduplicate_articles(filtered_24h)]

    today = now.date()
    today_articles = [a for a in formatted_24h if a['date'].date() == today]
    national_today = [a for a in today_articles if classify_domain(a['domain']) == "national"]
    trade_today = [a for a in today_articles if classify_domain(a['domain']) == "trade"]

    # Filter and deduplicate 7d articles
    filtered_7d = filter_articles_by_keywords_and_spokespeople(
        all_articles_7d, KEYWORDS, SPOKESPEOPLE, allowed_domains=None
    )
    formatted_7d = [format_article(a, now) for a in deduplicate_articles(filtered_7d)]
    weekly = [a for a in formatted_7d if a['date'].date() >= today - timedelta(days=7)]
    monthly = [a for a in formatted_7d if a['date'].date() >= today - timedelta(days=30)]

    # Markdown content
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
- Filters by target domains (disabled now)
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
