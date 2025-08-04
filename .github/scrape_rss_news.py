import requests
from bs4 import BeautifulSoup
import os
import csv
import time
import pytz
from datetime import datetime, timedelta
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

# ------------------------ Google News scraper -----------------------

def fetch_google_news_html(query):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
    }
    encoded_query = requests.utils.quote(query)
    url = f"https://www.google.com/search?q={encoded_query}&tbm=nws&hl=en-GB"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch Google News page, status code: {response.status_code}")
            return []

        html = response.text

        soup = BeautifulSoup(html, "html.parser")
        articles = []

        containers = soup.select("div.dbsr")

        if not containers:
            logger.info("No Google News articles found for query: " + query)
            return []

        for container in containers:
            a_tag = container.find("a")
            if not a_tag or not a_tag.get("href"):
                continue
            link = a_tag['href']

            title_tag = container.find("div", recursive=True)
            title = title_tag.get_text(strip=True) if title_tag else ""

            snippet_tag = container.find("div", class_="Y3v8qd") or container.find("div", class_="st")
            summary = snippet_tag.get_text(strip=True) if snippet_tag else ""

            dt = datetime.now(BST)

            articles.append({
                'publishedAt': dt.isoformat(),
                'title': title,
                'summary': summary,
                'link': link,
                'domain': clean_domain(link),
                'source': {'name': clean_domain(link)}
            })

        return articles

    except Exception as e:
        logger.error(f"Exception during Google News scraping: {e}")
        return []

# ------------------------ Bing News scraper -----------------------

def fetch_bing_news_html(query):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
    }
    encoded_query = requests.utils.quote(query)
    url = f"https://www.bing.com/news/search?q={encoded_query}&form=QBNH"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch Bing News page, status code: {response.status_code}")
            return []

        html = response.text

        soup = BeautifulSoup(html, "html.parser")
        articles = []

        containers = soup.select("div.news-card")

        if not containers:
            logger.info("No Bing news articles found for query: " + query)
            return []

        for container in containers:
            a_tag = container.find("a")
            if not a_tag or not a_tag.get("href"):
                continue
            link = a_tag['href']

            title = a_tag.get_text(strip=True)

            summary_tag = container.find("div", class_="snippet")
            summary = summary_tag.get_text(strip=True) if summary_tag else ""

            dt = datetime.now(BST)

            articles.append({
                'publishedAt': dt.isoformat(),
                'title': title,
                'summary': summary,
                'link': link,
                'domain': clean_domain(link),
                'source': {'name': clean_domain(link)}
            })

        return articles

    except Exception as e:
        logger.error(f"Exception during Bing News scraping: {e}")
        return []

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

    # Queries: keywords + (Palo Alto Networks AND each spokesperson)
    queries = KEYWORDS + [f'"Palo Alto Networks" AND {sp}' for sp in SPOKESPEOPLE]

    raw_articles = []

    for query in queries:
        logger.info(f"Fetching Google News for query: {query}")
        raw_articles += fetch_google_news_html(query)
        time.sleep(1)  # gentle delay

        logger.info(f"Fetching Bing News for query: {query}")
        raw_articles += fetch_bing_news_html(query)
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
- HTML scrape (Google News & Bing News)
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
