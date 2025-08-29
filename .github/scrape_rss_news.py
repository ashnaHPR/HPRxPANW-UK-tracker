import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import time
import os
import csv
from urllib.parse import urlparse

# Load config from config.py in the repo
from config import KEYWORDS, SPOKESPEOPLE, NATIONAL_DOMAINS, ALL_DOMAINS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

now = datetime.utcnow()

def fetch_bing_news(query, interval_hours=24):
    """Fetch Bing News results for a given query and time interval."""
    logger.info(f"Fetching news for query: '{query}' in last {interval_hours} hours")

    base_url = "https://www.bing.com/news/search"
    params = {
        "q": query,
        "qft": f"+filterui:age-lt{interval_hours}h",
        "form": "NWRFSH",
        "sp": "-1",
        "sc": "0-0",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NewsScraper/1.0; +https://github.com/user/repo)"
    }

    response = requests.get(base_url, params=params, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    articles = []
    results = soup.find_all("div", class_="news-card")

    for r in results:
        try:
            title_tag = r.find("a")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            url = title_tag['href']

            source_tag = r.find("div", class_="source")
            if source_tag:
                publication = source_tag.get_text(strip=True)
            else:
                publication = "Unknown"

            snippet_tag = r.find("div", class_="snippet")
            summary = snippet_tag.get_text(strip=True) if snippet_tag else ""

            date_tag = r.find("span", class_="time")
            if date_tag:
                # Bing often shows relative times like '2 hours ago', parse accordingly
                date_str = date_tag.get_text(strip=True)
                published_at = parse_bing_relative_date(date_str)
            else:
                published_at = now

            domain = urlparse(url).netloc.lower().replace("www.", "")

            article = {
                "title": title,
                "url": url,
                "publication": publication,
                "summary": summary,
                "date": published_at,
                "domain": domain,
            }
            articles.append(article)
        except Exception as e:
            logger.warning(f"Failed to parse a news item: {e}")
    logger.info(f"Fetched {len(articles)} articles for query '{query}'")
    return articles

def parse_bing_relative_date(date_str):
    """Parse relative date strings from Bing News like '2 hours ago'."""
    date_str = date_str.lower()
    now_ = datetime.utcnow()
    if "hour" in date_str:
        hours = int(date_str.split()[0])
        return now_ - timedelta(hours=hours)
    elif "minute" in date_str:
        minutes = int(date_str.split()[0])
        return now_ - timedelta(minutes=minutes)
    elif "day" in date_str:
        days = int(date_str.split()[0])
        return now_ - timedelta(days=days)
    else:
        # fallback to now if unrecognized format
        return now_

def filter_articles_by_keywords_and_spokespeople(articles, keywords, spokespeople, allowed_domains=None):
    filtered = []
    keywords_lower = [k.lower() for k in keywords]
    spokespeople_lower = [s.lower() for s in spokespeople]
    for a in articles:
        title_lower = a['title'].lower()
        summary_lower = a['summary'].lower()
        pub_lower = a['publication'].lower()
        if allowed_domains and a['domain'] not in allowed_domains:
            continue
        if any(k in title_lower or k in summary_lower for k in keywords_lower) or \
           any(sp in title_lower or sp in summary_lower for sp in spokespeople_lower) or \
           any(sp in pub_lower for sp in spokespeople_lower):
            filtered.append(a)
    return filtered

def deduplicate_articles(articles):
    seen = set()
    unique = []
    for a in articles:
        key = (a['title'], a['url'])
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique

def classify_domain(domain):
    if domain in NATIONAL_DOMAINS:
        return "national"
    else:
        return "trade"

def format_article(article, now):
    date_str = article['date'].strftime("%Y-%m-%d %H:%M")
    return {
        "date": article['date'],
        "date_str": date_str,
        "publication": article['publication'],
        "title": article['title'],
        "summary": article['summary'],
        "url": article['url'],
        "domain": article['domain']
    }

def build_md_table(title, articles):
    if not articles:
        return f"\n## {title}\n\n_No articles found._\n"
    md = f"\n## {title}\n\n"
    md += "| Date | Publication | Title | Summary |\n"
    md += "| --- | --- | --- | --- |\n"
    for a in articles:
        # Format markdown links properly with the article url
        md += f"| {a['date_str']} | [{a['publication']}]({a['url']}) | [{a['title']}]({a['url']}) | {a['summary']} |\n"
    return md

def write_csv(filepath, articles):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Publication", "Title", "Summary", "URL"])
        for a in articles:
            writer.writerow([a['date'].strftime("%Y-%m-%d %H:%M"), a['publication'], a['title'], a['summary'], a['url']])

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
