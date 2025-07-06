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
        'pub': a.get('source', {}).get('name', domain),
        'title': a.get('title', '').strip(),
        'summary': a.get('summary', '').strip(),
        'link': url
    }

def filter_articles_by_keywords_and_spokespeople(articles, keywords, spokespeople, allowed_domains):
    keywords_lower = [k.lower() for k in keywords]
    spokespeople_lower = [s.lower() for s in spokespeople]
    filtered = []
    for a in articles:
        domain = clean_domain(a.get('link') or a.get('url') or '')
        if domain not in allowed_domains:
            continue
        title = a.get('title', '').lower()
        summary = a.get('summary', '').lower()
        # Check if any keyword in title
        if any(k in title for k in keywords_lower):
            filtered.append(a)
            continue
        # Check if any spoke in title or summary
        if any(sp in title or sp in summary for sp in spokespeople_lower):
            filtered.append(a)
            continue
    return filtered
