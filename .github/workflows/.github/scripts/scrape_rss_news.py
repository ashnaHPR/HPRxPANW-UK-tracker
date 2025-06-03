import os
import feedparser
import re
from datetime import datetime

topics = {
    'Palo Alto Networks': {
        'url': 'https://news.google.com/rss/search?q="Palo+Alto+Networks"&hl=en-US&gl=US&ceid=US:en',
        'desc': 'Latest news and updates about Palo Alto Networks cybersecurity solutions.'
    },
    'Palo Alto Networks Firewalls': {
        'url': 'https://news.google.com/rss/search?q="Palo+Alto+firewall"&hl=en-US&gl=US&ceid=US:en',
        'desc': 'News about Palo Alto Networks firewall products and innovations.'
    },
    'Palo Alto Networks Research': {
        'url': 'https://unit42.paloaltonetworks.com/feed/',
        'desc': 'Threat intelligence and research updates from Palo Alto Networks Unit 42.'
    }
}

def clean_html(text):
    return re.sub('<[^<]+?>', '', text)

def fetch_and_summarize():
    os.makedirs("news", exist_ok=True)
    output = [f"# 📰 Palo Alto Networks News Summary\n\n_Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}_\n"]

    table_header = "| Source | Title | Description |\n|---|---|---|\n"
    output.append(table_header)

    for topic_title, data in topics.items():
        feed = feedparser.parse(data['url'])
        entries = feed.entries[:5]

        if not entries:
            output.append(f"| {topic_title} | _No articles found._ |  |\n")
            continue

        for entry in entries:
            description = clean_html(entry.get('summary', '')) or entry.get('title', '')
            published = entry.get('published', '') or entry.get('updated', '')
            try:
                dt_obj = datetime(*entry.published_parsed[:6])
                published_fmt = dt_obj.strftime("%b %d, %Y")
            except Exception:
                published_fmt = published

            title_md = f"[{entry.title}]({entry.link})"
            output.append(f"| {topic_title} {published_fmt} | {title_md} | {description} |\n")

    with open("news/paloalto_news.md", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    with open("README.md", "w", encoding="utf-8") as f:
        readme_intro = (
            "# Palo Alto Networks Cybersecurity News Tracker\n\n"
            "This README is updated every 6 hours with the latest Palo Alto Networks news.\n\n"
        )
        f.write(readme_intro)
        f.write("\n".join(output))

if __name__ == "__main__":
    fetch_and_summarize()
