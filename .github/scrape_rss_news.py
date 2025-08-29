import os
import csv
import time
import pytz
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
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
    """
    Parse Bing time strings:
    - Relative times like '17h', '1d', '5m'
    - 'Just now' or empty → now
    - If format looks like an absolute date or unparseable → return old date (e.g. 30 days ago)
    """
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
        # Try parsing absolute date formats (add more formats if needed)
        try:
            parsed_date = datetime.strptime(time_str, '%b %d, %Y')
            return BST.localize(parsed_date)
        except Exception:
            return now_dt - timedelta(days=30)
    except Exception:
        return now_dt - timedelta(days=30)

def extract_real_url(bing_url):
    """
    Extract the real article URL from Bing News redirect URLs.
    If not a redirect, returns the original URL.
    """
    parsed = urlparse(bing_url)
    # Bing news redirect URLs often contain the real URL as a 'url' query param
    if 'bing.com/news/apiclick.aspx' in bing_url or 'bing.com/news/hovercard' in bing_url:
        qs = parse_qs(parsed.query)
        if 'url' in qs:
            return unquote(qs['url'][0])
    return bing_url

def fetch_bing_news(query, interval_hours=None):
    logger.info(f"🔍 Scraping Bing News for: {query} (interval={interval_hours}h)")
    encoded = quote_plus(query)
    url = f"https://www.bing.com/news/search?q={encoded}&setlang=en-US&mkt=en-GB"
    if interval_hours:
        url += f"&qft=interval%3d%22{interval_hours}%22"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NewsScraper/1.0; +https://github.com/yourrepo)"
    }

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        logger.error(f"Failed to fetch Bing News page for query '{query}': HTTP {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    articles = soup.select('div.news-card')
    if not articles:
        articles = soup.select('div.t_s')

    for g in articles:
        try:
            link_tag = g.find('a')
            if not link_tag:
                continue

            raw_link = link_tag.get('data-href') or link_tag.get('href') or ''
            link = extract_real_url(raw_link)

            title = link_tag.text.strip()

            # Get publication name
            source_tag = g.find('div', class_='source')
            pub_name = source_tag.text.strip() if source_tag and source_tag.text.strip() and source_tag.text.strip() != '.' else ''

            # Fallback: use domain from link if publication name missing or invalid
            if not pub_name:
                pub_name = clean_domain(link) or "Unknown"

            summary_tag = g.find('div', class_='snippet')
            summary = summary_tag.text.strip() if summary_tag else ''

            time_tag = g.find('span', class_='time')
            time_text = time_tag.text.strip() if time_tag else ''

            publishedAt = parse_bing_time(time_text)

            # Skip articles older than 7 days
            if (now - publishedAt).days > 7:
                continue

            results.append({
                'date': publishedAt,
                'title': title,
                'summary': summary[:200],
                'link': link,
                'pub': pub_name,
                'domain': clean_domain(link),
            })

            logger.info(f"Article parsed: {title} | {pub_name} | {link}")

        except Exception as e:
            logger.warning(f"Error parsing a Bing article: {e}")

    logger.info(f"✅ Found {len(results)} articles on page.")
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
        all_articles_7d += fetch_bing_news(query, interval_hours=168)  # 7 days * 24 hours
        time.sleep(1)

    logger.info("🔎 Domains before filtering:")
    for a in all_articles_24h:
        logger.info(f"{a['domain']} → {a['title']}")

    # Filter articles by keywords/spokespeople for 24h batch (adjust as you want)
    filtered_24h = filter_articles_by_keywords_and_spokespeople(
        all_articles_24h, KEYWORDS, SPOKESPEOPLE, allowed_domains=None
    )

    formatted_24h = [format_article(a, now) for a in deduplicate_articles(filtered_24h)]

    # Log article dates for debugging
    for a in formatted_24h:
        logger.info(f"Article date: {a['date'].strftime('%Y-%m-%d %H:%M %Z')} - Title: {a['title']}")

    today = now.date()

    # Classification by domain for today articles
    today_articles = [a for a in formatted_24h if a['date'].date() == today]
    national_today = [a for a in today_articles if classify_domain(a['domain']) == "national"]
    trade_today = [a for a in today_articles if classify_domain(a['domain']) == "trade"]

    # Weekly and monthly from 7d articles, dedup + filter
    filtered_7d = filter_articles_by_keywords_and_spokespeople(
        all_articles_7d, KEYWORDS, SPOKESPEOPLE, allowed_domains=None
    )
    formatted_7d = [format_article(a, now) for a in deduplicate_articles(filtered_7d)]
    weekly = [a for a in formatted_7d if a['date'].date() >= today - timedelta(days=7)]
    monthly = [a for a in formatted_7d if a['date'].date() >= today - timedelta(days=30)]

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
