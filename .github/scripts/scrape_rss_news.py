import feedparser
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo  # Python 3.9+

# Media feeds
topics = {
    'BBC News': 'https://feeds.bbci.co.uk/news/rss.xml',
    'Bloomberg (UK)': 'https://www.bloomberg.com/feed/podcast/uk.xml',
    'Business Insider': 'https://www.insider.co.uk/?service=rss',
    'Financial Times': 'https://www.ft.com/?format=rss',
    'Forbes': 'https://www.forbes.com/investing/feed2/',
    'Independent': 'https://www.independent.co.uk/news/rss',
    'PA Media': 'https://api.pa.web.scotcourts.gov.uk/web/rss/NewsArticles',
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
    'IT Pro': 'https://www.itpro.com/uk/feeds/articletype/news',
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
    "Tim Erridge",
    "Sam Rubin"
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
    """Remove HTML tags from text."""
    return re.sub('<[^<]+?>', '', text).strip()

def contains_spokesperson(text):
    text_lower = text.lower()
    return any(name.lower() in text_lower for name in spokespersons)

def contains_palo_alto(text):
    # Exact phrase "palo alto networks" case insensitive
    return "palo alto networks" in text.lower()

def fetch_and_generate_news():
    bst = ZoneInfo("Europe/London")

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
            published = None
            if 'published_parsed' in entry and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).astimezone(bst)
            elif 'updated_parsed' in entry and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc).astimezone(bst)
            else:
                print("  Skipping entry with no date")
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

            # Filter for Palo Alto Networks or spokesperson mentions
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

    print(f"\nREADME.md updated with {len(national_rows) + len(trade_rows) + len(paloalto_rows)} articles.")

if __name__ == "__main__":
    fetch_and_generate_news()
