import os
import feedparser
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+

topics = {
    # ... all your other feeds ...
    'IT Pro': 'https://www.itpro.com/uk/feeds/articletype/news',
    # ... rest of your feeds ...
}

spokespersons = [
    "Anna Chung",
    "Carla Baker",
    "Scott McKinnon",
    "Tim Erridge",
    "Sam Rubin"
]

national_outlets = [
    'BBC News', 'Bloomberg (UK)', 'Business Insider', 'Financial Times',
    'Forbes', 'Independent', 'PA Media', 'Reuters', 'Sky News',
    'The Daily Telegraph', 'The Guardian', 'The Times', 'The Register',
    'WIRED', 'ZDNet UK', 'The Next Web', 'The Record', 'CNBC', 'IT Pro'
]

trade_outlets = [
    'SC Magazine', 'TechCrunch', 'TechRadar Pro', 'Computer Weekly',
    'Verdict', 'The Stack', 'Tech Monitor', 'IT Pro', 'Tech Forge',
    'Digit', 'Intelligent CIO Europe', 'Digitalisation World',
    'Silicon UK', 'UKTN', 'Information Age', 'Diginomica',
    'TechRepublic', 'Computing', 'Think Digital Partners'
]

def clean_html(text):
    return re.sub('<[^<]+?>', '', text).strip()

def contains_spokesperson(text):
    text_lower = text.lower()
    return any(name.lower() in text_lower for name in spokespersons)

def contains_palo_alto(text):
    # Match exact "palo alto networks" phrase (case insensitive)
    return "palo alto networks" in text.lower()

def fetch_and_generate_news():
    # Use BST timezone for datetime filtering
    bst = ZoneInfo('Europe/London')
    now_bst = datetime.now(bst)
    now_str = now_bst.strftime('%Y-%m-%d %H:%M:%S %Z')
    cutoff = now_bst - timedelta(days=1)

    print(f"Fetching news feeds at {now_str} (cutoff {cutoff.strftime('%Y-%m-%d %H:%M:%S %Z')})")

    header = f"# 📰 Palo Alto Networks News from Selected Media\n\n_Last updated: {now_str}_\n\n"
    table_header = "| Date | Publication | Headline | Summary |\n|---|---|---|---|\n"

    national_rows = []
    trade_rows = []
    paloalto_rows = []

    for pub_name, feed_url in topics.items():
        print(f"\nParsing feed from: {pub_name} ({feed_url})")
        feed = feedparser.parse(feed_url)
        print(f"  Found {len(feed.entries)} entries")

        for entry in feed.entries:
            # Get publish date with timezone awareness
            published = None
            if 'published_parsed' in entry and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=ZoneInfo('UTC')).astimezone(bst)
            elif 'updated_parsed' in entry and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=ZoneInfo('UTC')).astimezone(bst)
            else:
                print("  Skipping entry with no date")
                continue

            # Debug print to check article dates and titles for IT Pro or others
            if pub_name == "IT Pro":
                print(f"  IT Pro Article: {entry.title}")
                print(f"    Published (BST): {published}")

            # Filter to last 24 hours in BST
            if published < cutoff:
                continue

            text_content = ""
            if 'title' in entry:
                text_content += entry.title + " "
            if 'summary' in entry:
                text_content += clean_html(entry.summary) + " "
            if 'content' in entry and len(entry.content) > 0:
                for c in entry.content:
                    text_content += clean_html(c.value) + " "

            # Check if article mentions "Palo Alto Networks" or a spokesperson
            if not (contains_palo_alto(text_content) or contains_spokesperson(text_content)):
                continue

            headline = clean_html(entry.title) if 'title' in entry else "No title"
            summary = clean_html(entry.summary) if 'summary' in entry else ""

            date_str = published.strftime('%Y-%m-%d')
            pub_display = pub_name.replace('|', '\\|')

            print(f"  Including article: {headline[:60]}... ({date_str})")

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
        content += "## National Media\n\nNo recent articles found.\n\n"

    if trade_rows:
        content += "## Trade Media\n\n" + table_header + "\n".join(sorted(trade_rows, reverse=True)) + "\n\n"
    else:
        content += "## Trade Media\n\nNo recent articles found.\n\n"

    if paloalto_rows:
        content += "## Palo Alto Specific News\n\n" + table_header + "\n".join(sorted(paloalto_rows, reverse=True)) + "\n\n"
    else:
        content += "## Palo Alto Specific News\n\nNo recent articles found.\n\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

    total = len(national_rows) + len(trade_rows) + len(paloalto_rows)
    print(f"\nREADME.md updated with {total} articles.")

if __name__ == "__main__":
    fetch_and_generate_news()
