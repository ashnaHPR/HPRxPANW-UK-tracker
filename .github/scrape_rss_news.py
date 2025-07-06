import sys
import os
import requests
import feedparser
import csv
import time
import pytz
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus

# Add scripts directory to Python path to import your modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from config import KEYWORDS, SPOKESPEOPLE, national_domains as NATIONAL_DOMAINS
from utils import clean_domain, classify_domain, escape_md, deduplicate_articles, format_article

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
            'lin
