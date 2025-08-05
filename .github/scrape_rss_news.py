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


def parse_bing_time(time_str: str) -> datetime:
    now = datetime.now(BST)
    time_str = time_str.lower().strip()

    try:
        if 'hour' in time_str or 'hr' in time_str:
            hours = int(''.join(filter(str.isdigit, time_str)))
            return now - timedelta(hours=hours)

        elif 'min' in time_str:
            mins = int(''.join(filter(str.isdigit, time_str)))
            return now - timedelta(minutes=mins)

        elif 'day' in time_str:
            days = int(''.join(filter(str.isdigit, time_str)))
            return now - timedelta(days=days)

        else:
            for fmt in ['%b %d, %Y', '%d %b %Y', '%b %d']:
                try:
                    dt = datetime.strptime(time_str, fmt)
                    if '%Y' not in fmt:
                        dt = dt.replace(year=now.year)
                    return BST.localize(dt)
                except ValueError:
                    continue
            return now
    except Exception:
        return now


def fetch_bing_news(query):
    logger.info(f"🔍 Scraping Bing News for: {query}")
    encoded = quote_plus(query)
    url = f"https://www.bing.com/news/search?q={encoded}&setlang=en-US&mkt=en-GB"
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
            link = link_tag['href'] if link_tag else ''
            title = link_tag.text.strip() if link_tag else ''
            summary_tag = g.find('div', class_='snippet')
            summary = summary_tag.text.strip() if summary_tag else ''
            source_tag = g.find('div', class_='source')
            pub_name = source_tag.text.strip() if source_tag else ''
            time_tag = g.find('span', class_='time')
            time_text = time_tag.text.strip() if time_tag else ''

            logger.info(f"⏱️ Raw time text: '{time_text}' — Title: {title}")

            if not time_text:
                logger.info(f"⏭️ Skipping (no time found): {title}")
                continue

            publishedAt = parse_bing_time(time_text)

            if publishedAt > now + timedelta(hours=1):
                logger.warning(f"⏳ Skipping (future date): {title} @ {publishedAt}")
                continue

            results.append({
                'publishedAt': publishedAt.isoformat(),
                'title': title,
                'summary': summary[:200],
                'link': link,
                'domain': clean_domain(link),
                'source': {'name': pub_name}
            })
        except Exception as e:
            logger.warning(f"⚠️ Error parsing a Bing article: {e}")

    logger.info(f"✅ Found {len(results)} articles on page.")
    return results


def is_article_in_target_range(article_dt: datetime) -> bool:
    today = datetime.now(BST).date()
    weekday = today.weekday()

    if weekday == 0:  # Monday
        friday = today - timedelta(days=3)
        return friday <= article_dt.date() <= today
    else:
        return article_dt.date() == today


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
        time.sleep(1)

    logger.info("🔎 Domains before filtering:")
    for a in raw_articles:
        logger.info(f"{clean_domain(a['link'])} → {a['title']}")

    filtered = filter_articles_by_keywords_and_spokespeople(
        raw_articles, KEYWORDS, SPOKESPEOPLE, allowed_domains=None
    )

    formatted = [format_article(a, now) for a in deduplicate_articles(filtered)]

    for a in formatted:
        logger.info(f"🗞️ Article date: {a['date'].strftime('%Y-%m-%d %H:%M %Z')} - Title: {a['title']}")

    filtered_date = [a for a in formatted if is_article_in_target_range(a['date'])]

    today = now.date()

    today_articles = [a for a in filtered_date if a['date'].date() == today]
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
