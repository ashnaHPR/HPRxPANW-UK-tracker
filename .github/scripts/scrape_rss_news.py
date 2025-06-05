import feedparser
import re
from datetime import datetime, timedelta

topics = {
    'BBC News': 'https://feeds.bbci.co.uk/news/rss.xml',
    'Bloomberg (UK)': 'https://www.bloomberg.com/feed/podcast/uk.xml',
    'Business Insider': 'https://www.businessinsider.com/rss',
    'Financial Times': 'https://www.ft.com/?format=rss',
    'Forbes': 'https://www.forbes.com/investing/feed2/',
    'Independent': 'https://www.independent.co.uk/news/rss',
    'PA Media': 'https://www.pamediagroup.com/feed/',
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

spokespersons = [
    "Anna Chung",
    "Carla Baker",
    "Scott McKinnon",
    "Tim Erridge"
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

palo_alto_sources = [
    'Palo Alto Networks',
    'Palo Alto Networks Firewalls',
    'Palo Alto Networks Research',
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

    print(f"Fetching news feeds at {now_str} (cutoff {cutoff.strftime('%Y-%m-%d %H:%M:%S')})")

    header = f"# 📰 Palo Alto Networks News from Selected Media\n\n_Last updated: {now_str}_\n\n"
    table_header = "| Date | Publication | Headline | Summary |\n|---|---|---|---|\n"

    national_rows = []
    trade_rows = []
    paloalto_rows = []

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

            text_content = " ".join([
                clean_html(getattr(entry, 'title', '')),
                clean_html(getattr(entry, 'summary', '')),
                *[clean_html(c.value) for c in getattr(entry, 'content', []) if hasattr(c, 'value')]
            ])

            if not (contains_palo_alto(text_content) or contains_spokesperson(text_content)):
                continue

            headline = clean_html(getattr(entry, 'title', 'No title'))
            summary = clean_html(getattr(entry, 'summary', ''))
            date_str = published.strftime('%b %d, %Y')
            pub_display = pub_name.replace('|', '\\|')

            row = f"| {date_str} | {pub_display} | [{headline}]({entry.link}) | {summary} |"

            if pub_name in national_outlets:
                national_rows.append(row)
            elif pub_name in trade_outlets:
                trade_rows.append(row)
            elif pub_name in palo_alto_sources:
                paloalto_rows.append(row)
            else:
                # Optional: classify unknown sources as trade media or skip
                trade_rows.append(row)

    content = header

    # Proper blank lines for markdown rendering
    if national_rows:
        content += "## National Media\n\n" + table_header + "\n".join(sorted(national_rows, reverse=True)) + "\n\n"
    else:
        content += "## National Media\n\n_No relevant news found._\n\n"

    if trade_rows:
        content += "## Trade Media\n\n" + table_header + "\n".join(sorted(trade_rows, reverse=True)) + "\n\n"
    else:
        content += "## Trade Media\n\n_No relevant news found._\n\n"

    if paloalto_rows:
        content += "## Palo Alto Specific News\n\n" + table_header + "\n".join(sorted(paloalto_rows, reverse=True)) + "\n\n"
    else:
        content += "## Palo Alto Specific News\n\n_No relevant news found._\n\n"

    # Always add timestamp comment so Git sees changes every run
    content += f"\n<!-- Auto-update timestamp: {now_str} -->\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ README.md updated with {len(national_rows) + len(trade_rows) + len(paloalto_rows)} articles.")

if __name__ == "__main__":
    fetch_and_generate_news()
