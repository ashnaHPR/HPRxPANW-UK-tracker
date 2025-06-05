import os
import feedparser
import re
from datetime import datetime, timedelta

# Media feeds
topics = {
    # (Same as yours)
}

spokespersons = [
    "Anna Chung", "Carla Baker", "Scott McKinnon", "Tim Erridge"
]

national_outlets = [
    # (Same as yours)
]

trade_outlets = [
    # (Same as yours)
]

def clean_html(text):
    """Remove HTML tags from text."""
    return re.sub('<[^<]+?>', '', text).strip()

def contains_spokesperson(text):
    return any(name.lower() in text.lower() for name in spokespersons)

def contains_palo_alto(text):
    return "palo alto networks" in text.lower()

def fetch_and_generate_news():
    now_utc = datetime.utcnow()
    now_str = now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')
    cutoff = now_utc - timedelta(days=1)

    print(f"Fetching news feeds at {now_str} (cutoff {cutoff.strftime('%Y-%m-%d %H:%M:%S')})")

    header = f"# 📰 Palo Alto Networks News from Selected Media\n\n_Last updated: {now_str}_\n\n"
    table_header = "| Date | Publication | Headline | Summary |\n|---|---|---|---|\n"

    national_rows, trade_rows, paloalto_rows = [], [], []

    for pub_name, feed_url in topics.items():
        print(f"\nParsing feed: {pub_name}")
        feed = feedparser.parse(feed_url)
        print(f"  Found {len(feed.entries)} entries")

        for entry in feed.entries:
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])
            else:
                continue

            if published < cutoff:
                continue

            text_content = ' '.join([
                clean_html(getattr(entry, 'title', '')),
                clean_html(getattr(entry, 'summary', '')),
                *[clean_html(c.value) for c in getattr(entry, 'content', []) if hasattr(c, 'value')]
            ])

            if not (contains_palo_alto(text_content) or contains_spokesperson(text_content)):
                continue

            headline = clean_html(getattr(entry, 'title', 'No title'))
            summary = clean_html(getattr(entry, 'summary', ''))
            date_str = published.strftime('%Y-%m-%d')
            pub_display = pub_name.replace('|', '\\|')

            row = f"| {date_str} | {pub_display} | [{headline}]({entry.link}) | {summary} |"

            if pub_name in national_outlets:
                national_rows.append(row)
            elif pub_name in trade_outlets:
                trade_rows.append(row)
            else:
                paloalto_rows.append(row)

    content = header

    if national_rows:
        content += "## National Media\n\n" + table_header + "\n".join(sorted(national_rows, reverse=True)) + "\n\n"
    else:
        content += "## National Media\n\n_No recent articles found._\n\n"

    if trade_rows:
        content += "## Trade Media\n\n" + table_header + "\n".join(sorted(trade_rows, reverse=True)) + "\n\n"
    else:
        content += "## Trade Media\n\n_No recent articles found._\n\n"

    if paloalto_rows:
        content += "## Palo Alto Specific News\n\n" + table_header + "\n".join(sorted(paloalto_rows, reverse=True)) + "\n\n"
    else:
        content += "## Palo Alto Specific News\n\n_No recent articles found._\n\n"

    # ✅ Always ensure the README has a change (even if no new articles)
    content += f"\n<!-- Auto-update timestamp: {now_str} -->\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ README.md updated with {len(national_rows) + len(trade_rows) + len(paloalto_rows)} articles.")

if __name__ == "__main__":
    fetch_and_generate_news()
