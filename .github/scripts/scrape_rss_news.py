import os
import feedparser
import re
from datetime import datetime, timedelta

# Your topics, spokespersons, outlets (keep your original lists here)...

topics = {
    'BBC News': 'https://feeds.bbci.co.uk/news/rss.xml',
    # ... all your other feeds ...
    'Palo Alto Networks': 'https://news.google.com/rss/search?q="Palo+Alto+Networks"&hl=en-US&gl=US&ceid=US:en',
    'Palo Alto Networks Firewalls': 'https://news.google.com/rss/search?q="Palo+Alto+firewall"&hl=en-US&gl=US&ceid=US:en',
    'Palo Alto Networks Research': 'https://unit42.paloaltonetworks.com/feed/',
}

spokespersons = [
    "Anna Chung", "Carla Baker", "Scott McKinnon", "Tim Erridge"
]

national_outlets = [
    'BBC News', 'Bloomberg (UK)', 'Business Insider', 'Financial Times',
    'Forbes', 'Independent', 'PA Media', 'Reuters', 'Sky News',
    'The Daily Telegraph', 'The Guardian', 'The Times', 'The Register',
    'WIRED', 'ZDNet UK', 'The Next Web', 'The Record', 'CNBC'
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
    return "palo alto networks" in text.lower()

def fetch_and_generate_news():
    now_utc = datetime.utcnow()
    now_str = now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')
    cutoff = now_utc - timedelta(days=1)

    header = f"# 📰 Palo Alto Networks News from Selected Media\n\n_Last updated: {now_str}_\n\n"
    table_header = "| Date | Publication | Headline | Summary |\n|---|---|---|---|\n"

    national_rows = []
    trade_rows = []
    paloalto_rows = []

    for pub_name, feed_url in topics.items():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            published = None
            if 'published_parsed' in entry and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif 'updated_parsed' in entry and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])
            else:
                continue
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

            if not (contains_palo_alto(text_content) or contains_spokesperson(text_content)):
                continue

            headline = clean_html(entry.title) if 'title' in entry else "No title"
            summary = clean_html(entry.summary) if 'summary' in entry else ""
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

    # Write README.md no matter what
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

    print(f"README.md updated with {len(national_rows) + len(trade_rows) + len(paloalto_rows)} articles.")

if __name__ == "__main__":
    fetch_and_generate_news()
