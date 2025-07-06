# scripts/utils.py

import tldextract
from datetime import datetime
import pytz
from scripts.config import NATIONAL_DOMAINS

BST = pytz.timezone('Europe/London')

def clean_domain(url):
    try:
        ext = tldextract.extract(url)
        return f"{ext.domain}.{ext.suffix}".lower()
    except Exception:
        return ""

def classify_domain(domain):
    return "national" if domain in NATIONAL_DOMAINS else "trade"

def escape_md(text):
    return text.replace("|", "\\|").replace("\n", " ").strip()

def deduplicate_articles(articles):
    seen = set()
    unique = []
    for a in articles:
        key = a.get('url') or a.get('link')
        if key and key not in seen:
            seen.add(key)
            unique.append(a)
    return unique

def format_article(a, fallback_time):
    try:
        dt = datetime.fromisoformat(a['publishedAt'].replace('Z', '+00:00')).astimezone(BST)
    except Exception:
        dt = fallback_time
    url = a.get('url') or a.get('link') or ''
    domain = clean_domain(url)
    return {
        'date': dt,
        'domain': domain,
        'pub': a.get('

