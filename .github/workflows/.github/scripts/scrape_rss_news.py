import os
import feedparser
import re
from datetime import datetime

# Media feeds
topics = {
    'BBC News': 'https://feeds.bbci.co.uk/news/rss.xml',
    'Bloomberg (UK)': 'https://www.bloomberg.com/feed/podcast/uk.xml',
    'Business Insider': 'https://www.businessinsider.com/rss',
    'Financial Times': 'https://www.ft.com/?format=rss',
    'Forbes': 'https://www.forbes.com/investing/feed2/',
    'Independent': 'https://www.independent.co.uk/news/rss',
    'PA Media': 'https://www.pamediagroup.com/feed/',
    'Reuters': 'http://feeds.reuters.com/reuters/topNews',
    'Sky News': 'https://feeds.skynews.com/feeds/rss/home.xml',
    'The Daily Telegraph': 'https://www.telegraph.co.uk/rss.xml',
    'The Guardian': 'https://www.theguardian.com/uk/rss',
    'The Register': 'https://www.theregister.com/headlines.atom',
    'WIRED': 'https://www.wired.com/feed/rss',
    'ZDNet UK': 'https://www.zdnet.com/news/rss.xml',
    'The Next Web': 'https://thenextweb.com/feed/',
    'The Record': 'https://therecord.media/feed/',
    'CNBC': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',

    'SC Magazine': 'https://www.scmagazine.com/home/feed/rss/',
    'TechCrunch': 'http://feeds.feedburner.com/TechCrunch/',
    'TechRadar Pro': 'https://www.techradar.com/rss',
    'Computer Weekly': 'https://www.computerweekly.com/rss/allarticles.xml',
    'Verdict': 'https://www.verdict.co.uk/feed/',
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
    'Think Digital Partners': 'https://thinkdigitalpartners.com/feed/',

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
    'The Daily Telegraph', 'The Guardian', 'The Register',
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
    for name in spokespersons:
        if name.lower() in text_lower:
            return True
    return False

def contains_palo_alto(text):
    return "palo alto networks" in text.lower()

def fetch_and_generate_news():
    os.makedirs("news", exist_ok=True)
    now_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    last_updated_header = f"# 📰 Palo Alto Networks News from Selected Media\n\n_Last updated: {now_utc}_\n\n"

    table_header = "| Date | Publication | Headline | Summary |\n|---|---|---|---|\n"

    national_entries = []
    trade_entries = []
    palo_alto_entries = []

    for pub_name, feed_url in topics.items():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:20]:
            title = entry.get('title', '')
            summary = clean_html(entry.get('summary', ''))
            combined_text = f"{title} {summary}"

            if contains_palo_alto(combined_text) or contains_spokesperson(combined_text):
                publication_name = pub_name  # keep pub name as is
                if pub_name.startswith('Palo Alto Networks'):
                    palo_alto_entries.append((entry, publication_name))
                elif pub_name in national_outlets:
                    national_entries.append((entry, publication_name))
                elif pub_name in trade_outlets:
                    trade_entries.append((entry, publication_name))
                else:
                    # Uncategorized but mentions PA Networks, add to Palo Alto news for safety
                    palo_alto_entries.append((entry, publication_name))

    def format_entries(entries):
        if not entries:
            return "| N/A | N/A | _No relevant Palo Alto Networks news found._ | |\n"
        rows = []
        for entry, pub in entries:
            description = clean_html(entry.get('summary', '')) or ''
            published = entry.get('published', '') or entry.get('updated', '')
            try:
                dt_obj = datetime(*entry.published_parsed[:6])
                published_fmt = dt_obj.strftime("%b %d, %Y")
            except Exception:
                published_fmt = published or "Unknown date"
            title_md = f"[{entry.title}]({entry.link})"
            rows.append(f"| {published_fmt} | {pub} | {title_md} | {description} |\n")
        return "".join(rows)

    national_md = table_header + format_entries(national_entries)
    trade_md = table_header + format_entries(trade_entries)
    paloalto_md = table_header + format_entries(palo_alto_entries)

    def generate_readme_content(nat_md, trade_md, pa_md, last_updated_header):
        toc = (
            "📋 Table of Contents\n\n"
            "- [National Outlets](#national-outlets)\n"
            "- [Trade Outlets](#trade-outlets)\n"
            "- [Palo Alto Networks News](#palo-alto-networks-news)\n\n"
        )
        national_section = (
            "## National Outlets\n\n"
            "This section covers national media outlets monitored for Palo Alto Networks news.\n\n"
            + nat_md + "\n"
        )
        trade_section = (
            "## Trade Outlets\n\n"
            "This section covers trade and specialist publications monitored for Palo Alto Networks news.\n\n"
            + trade_md + "\n"
        )
        paloalto_section = (
            "## Palo Alto Networks News\n\n"
            + pa_md + "\n"
        )
        return last_updated_header + toc + national_section + trade_section + paloalto_section

    readme_content = generate_readme_content(national_md, trade_md, paloalto_md, last_updated_header)

    # Write news markdown file
    with open("news/paloalto_news.md", "w", encoding="utf-8") as f:
        f.write(last_updated_header)
        f.write("## National Outlets\n\n")
        f.write(national_md)
        f.write("\n## Trade Outlets\n\n")
        f.write(trade_md)
        f.write("\n## Palo Alto Networks News\n\n")
        f.write(paloalto_md)

    # Write README
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)


if __name__ == "__main__":
    fetch_and_generate_news()
