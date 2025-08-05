import tldextract
from datetime import datetime
import pytz
from scripts.config import NATIONAL_DOMAINS

BST = pytz.timezone('Europe/London')

def clean_domain(url):
    try:
        ext = tldextract.extract(url)
        domain = f"{ext.domain}.{ext.suffix}".lower()
        return domain
    except Exception:
        return ""

def classify_domain(domain):
    domain = domain.lower()
    return "national" if domain in NATIONAL_DOMAINS else "trade"

def escape_md(text):
    if not text:
        return ""
    return text.replace("|", "\\|").replace("\n", " ").strip()

def deduplicate_articles(articles):
    seen = set()
    unique = []
    for a in articles:
        key = a.get('link') or a.get('url')
        if key and key not in seen:
            seen.add(key)
            unique.append(a)
    return unique

def format_article(a, fallback_time):
    try:
        dt = datetime.fromisoformat(a['publishedAt'].replace('Z', '+00:00')).astimezone(BST)
    except Exception:
        dt = fallback_time
    url = a.get('link') or a.get('url') or ''
    domain = clean_domain(url)
    summary = a.get('summary') or ''
    return {
        'date': dt,
        'domain': domain,
        'pub': a.get('source', {}).get('name', domain),
        'title': a.get('title', '').strip(),
        'summary': summary.strip(),
        'link': url
    }

def filter_articles_by_keywords_and_spokespeople(articles, keywords, spokespeople, allowed_domains=None):
    keywords_lower = [k.lower() for k in keywords]
    spokespeople_lower = [s.lower() for s in spokespeople]
    filtered = []

    for a in articles:
        domain = clean_domain(a.get('link') or a.get('url') or '')
        if allowed_domains and domain not in allowed_domains:
            continue

        title = a.get('title', '').lower()
        summary = a.get('summary', '').lower()

        if any(k in title for k in keywords_lower) or any(sp in title or sp in summary for sp in spokespeople_lower):
            a['domain'] = domain  # Ensure domain is set
            filtered.append(a)

    return filtered
