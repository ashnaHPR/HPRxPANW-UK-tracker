import os
import feedparser
import re
from datetime import datetime, timedelta

# Media feeds
topics = {
    'BBC News': 'https://feeds.bbci.co.uk/news/rss.xml',
    'Bloomberg (UK)': 'https://www.bloomberg.com/feed/podcast/uk.xml',
    'Business Insider': 'https://www.businessinsider.com/rss',
    'Financial Times': 'https://www.ft.com/?format=rss',
    'Forbes': 'https://www.forbes.com/investing/feed2/',
    'Independent': 'https://www.independent.co.uk/news/rss',
    'PA Media': 'https://www.pamediagroup.com/feed/',  # example feed, replace if needed
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
    'CNBC': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',

    # Palo Alto specific feeds
    'Palo Alto Networks': 'https://news.google.com/rss/search?q="Palo+Alto+Networks"&hl=en-US&gl=US&ceid=US:en',
    'Palo Alto Networks Firewalls': 'https://news.google.com/rss/search?q="Palo+Alto+firewall"&hl=en-US&gl=US&ceid=US:en',
    'Palo Alto Networks Research': 'https://unit42.paloaltonetworks.com/feed/',
}

national_outlets = [
    'BBC News', 'Bloomberg (UK)', 'Business Insider', 'Financial Times',
    'Forbes', 'Independent', 'PA Media', 'Reuters', 'Sky News',
    'The Daily Telegraph', 'The Guardian', 'The Register',
    'WIRED', 'ZDNet UK', 'The Next Web', 'The Record', 'CNBC'
]

trade_outlets = [
    'SC Magazine', 'TechCrunch', 'TechRadar Pro', 'Computer Weekly',
    'Verdict', 'The Stack', 'Tech Monitor', 'IT Pro', 'Tech Forge',
    'Digit', 'Intelligent CIO Europe', 'Digitalisation World',
    'Silicon UK', 'UKTN', 'Information Age', 'Diginomica',
    'TechRepublic', 'Computing'
]

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
    now_utc = datetime.utcnow()
    now_utc_str = now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')

    table_header = "| Date | Publication | Headline | Summary |\n|---|---|---|---|\n"

    output_national = [f"## National Outlets\n\n{table_header}"]
    output_trade = [f"## Trade Outlets\n\n{table_header}"]
    output_other = [f"## Other News\n\n{table_header}"]

    for pub_name, feed_url in topics.items():
        feed = feedparser.parse(feed_url)
        filtered_entries = []

        for entry in feed.entries[:20]:  # check up to 20 recent articles
            # Skip if published_parsed missing
            if not hasattr(entry, 'published_parsed'):
                continue

            published_dt = datetime(*entry.published_parsed[:6])
            if (now_utc - published_dt) > timedelta(days=1):
                # Older than 24 hours, skip
                continue

            title = entry.get('title', '')
            summary = clean_html(entry.get('summary', ''))
            combined_text = f"{title} {summary}"

            # Include entries mentioning Palo Alto Networks or spokespersons
            if contains_palo_alto(combined_text) or contains_spokesperson(combined_text):
                filtered_entries.append(entry)

        if not filtered_entries:
            line = f"| N/A | {pub_name} | _No relevant Palo Alto news found in last 24 hours._ | |\n"
            if pub_name in national_outlets:
                output_national.append(line)
            elif pub_name in trade_outlets:
                output_trade.append(line)
            else:
                output_other.append(line)
            continue

        for entry in filtered_entries:
            description = clean_html(entry.get('summary', '')) or ''
            try:
                dt_obj = datetime(*entry.published_parsed[:6])
                published_fmt = dt_obj.strftime("%b %d, %Y")
            except Exception:
                published_fmt = "Unknown date"

            title_md = f"[{entry.title}]({entry.link})"
            line = f"| {published_fmt} | {pub_name} | {title_md} | {description} |\n"

            if pub_name in national_outlets:
                output_national.append(line)
            elif pub_name in trade_outlets:
                output_trade.append(line)
            else:
                output_other.append(line)

    # Compose full README content with header and last updated timestamp
    header = f"# 📰 Palo Alto Networks News from Selected Media\n\n_Last updated: {now_utc_str}_\n\n"

    readme_content = (
        header +
        "\n".join(output_national) + "\n\n" +
        "\n".join(output_trade) + "\n\n" +
        "\n".join(output_other) + "\n"
    )

    # Write README.md file
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)


if __name__ == "__main__":
    fetch_and_generate_news()
