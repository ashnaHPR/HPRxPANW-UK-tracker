import os
import feedparser
import re
from datetime import datetime

# List of media feeds including Palo Alto focused and general media
topics = {
    'BBC News': 'https://feeds.bbci.co.uk/news/rss.xml',
    'Bloomberg (UK)': 'https://www.bloomberg.com/feed/podcast/uk.xml',
    'Business Insider': 'https://www.businessinsider.com/rss',
    'Financial Times': 'https://www.ft.com/?format=rss',
    'Forbes': 'https://www.forbes.com/investing/feed2/',
    'Independent': 'https://www.independent.co.uk/news/rss',
    'Reuters': 'http://feeds.reuters.com/reuters/topNews',
    'SC Magazine': 'https://www.scmagazine.com/home/feed/rss/',
    'Sky News': 'https://feeds.skynews.com/feeds/rss/home.xml',
    'TechCrunch': 'http://feeds.feedburner.com/TechCrunch/',
    'The Daily Telegraph': 'https://www.telegraph.co.uk/rss.xml',
    'The Guardian': 'https://www.theguardian.com/uk/rss',
    'The Register': 'https://www.theregister.com/headlines.atom',
    'TechRadar Pro': 'https://www.techradar.com/rss',
    'Computer Weekly': 'https://www.computerweekly.com/rss/allarticles.xml',
    'Verdict': 'https://www.verdict.co.uk/feed/',
    'WIRED': 'https://www.wired.com/feed/rss',
    'ZDNet UK': 'https://www.zdnet.com/news/rss.xml',
    'The Stack': 'https://thestack.technology/feed/',
    'Tech Monitor': 'https://techmonitor.ai/feed/',
    'IT Pro': 'https://www.itpro.co.uk/rss',
    'Tech Forge': 'https://techforge.co/feed/',
    'Digit': 'https://www.digit.in/rss',
    'Intelligent CIO Europe': 'https://www.intelligentcio.com/feed/',
    'Digitalisation World': 'https://www.digitalisationworld.com/rss.xml',
    'Silicon UK': 'https://silicon.uk/feed/',
    'UKTN': 'https://uktoday.news/feed/',
    'Information Age': 'https://www.information-age.com/feed/',
    'Diginomica': 'https://diginomica.com/feed/',
    'TechRepublic': 'https://www.techrepublic.com/rssfeeds/articles/',
    'Computing': 'https://www.computing.co.uk/rss',
    'The Next Web': 'https://thenextweb.com/feed/',
    'The Record': 'https://therecord.media/feed/',
    
    # Palo Alto specific feeds
    'Palo Alto Networks': 'https://news.google.com/rss/search?q="Palo+Alto+Networks"&hl=en-US&gl=US&ceid=US:en',
    'Palo Alto Networks Firewalls': 'https://news.google.com/rss/search?q="Palo+Alto+firewall"&hl=en-US&gl=US&ceid=US:en',
    'Palo Alto Networks Research': 'https://unit42.paloaltonetworks.com/feed/',
}

spokespersons = [
    "Anna Chung",
    "Carla Baker",
    "Scott McKinnon",
    "Tim Erridge"
]

def clean_html(text):
    """Remove HTML tags from text."""
    return re.sub('<[^<]+?>', '', text).strip()

def contains_spokesperson(text):
    text_lower = text.lower()
    for name in spokespersons:
        if name.lower() in text_lower:
            return True
    return False

def contains_palo_alto(text):
    return "palo alto networks" in text.lower()

def fetch_and_generate_news():
    os.makedirs("news", exist_ok=True)
    now_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    header = f"# 📰 Palo Alto Networks News from Selected Media\n\n_Last updated: {now_utc}_\n\n"
    table_header = "| Publication + Date | Headline | Summary |\n|---|---|---|\n"

    output = [header, table_header]

    for pub_name, feed_url in topics.items():
        feed = feedparser.parse(feed_url)
        filtered_entries = []

        for entry in feed.entries[:20]:  # check up to 20 recent articles
            title = entry.get('title', '')
            summary = clean_html(entry.get('summary', ''))
            combined_text = f"{title} {summary}"

            # Filtering rules:
            # For Palo Alto-specific feeds: filter by spokespersons only
            if 'Palo Alto Networks' in pub_name:
                if contains_spokesperson(combined_text):
                    filtered_entries.append(entry)
            else:
                # For general media: filter if mentions Palo Alto Networks or spokespersons
                if contains_palo_alto(combined_text) or contains_spokesperson(combined_text):
                    filtered_entries.append(entry)

        if not filtered_entries:
            output.append(f"| {pub_name} | _No relevant Palo Alto news found._ | |\n")
            continue

        for entry in filtered_entries:
            description = clean_html(entry.get('summary', '')) or ''
            published = entry.get('published', '') or entry.get('updated', '')
            try:
                dt_obj = datetime(*entry.published_parsed[:6])
                published_fmt = dt_obj.strftime("%b %d, %Y")
            except Exception:
                published_fmt = published or "Unknown date"

            title_md = f"[{entry.title}]({entry.link})"
            output.append(f"| {pub_name} {published_fmt} | {title_md} | {description} |\n")

    # Write news markdown
    with open("news/paloalto_news.md", "w", encoding="utf-8") as f:
        f.write("".join(output))

    # Write README.md with the same content (plus intro)
    readme_intro = (
        "# Palo Alto Networks Cybersecurity News Filtered by Media and Spokespersons\n\n"
        "This README is updated every 6 hours with the latest Palo Alto Networks news mentioning key spokespersons or from selected media.\n\n"
    )
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_intro)
        f.write("".join(output))


if __name__ == "__main__":
    fetch_and_generate_news()
