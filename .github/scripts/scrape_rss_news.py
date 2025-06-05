import feedparser
from datetime import datetime, timezone
import pytz

# Define BST timezone (+1 hour from UTC)
BST = pytz.timezone('Europe/London')

# Full list of RSS feeds
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

    # Palo Alto-specific feeds
    'Palo Alto Networks': 'https://news.google.com/rss/search?q="Palo+Alto+Networks"&hl=en-US&gl=US&ceid=US:en',
    'Palo Alto Networks Firewalls': 'https://news.google.com/rss/search?q="Palo+Alto+firewall"&hl=en-US&gl=US&ceid=US:en',
    'Palo Alto Networks Research': 'https://unit42.paloaltonetworks.com/feed/',
}

# Spokespersons to check for (lowercase for case-insensitive matching)
spokespersons = ['tim erridge', 'scott mckinnon', 'carla baker', 'anna chung', 'sam rubin']

def is_today_bst(pub_date):
    """Check if the published date is today in BST."""
    if not pub_date:
        return False
    try:
        dt_utc = datetime(*pub_date[:6], tzinfo=timezone.utc)
    except Exception:
        return False
    dt_bst = dt_utc.astimezone(BST)
    now_bst = datetime.now(BST)
    return dt_bst.date() == now_bst.date()

def contains_spokesperson(text):
    """Check if any spokesperson is mentioned in the text (case-insensitive)."""
    if not text:
        return False
    text_lower = text.lower()
    return any(name in text_lower for name in spokespersons)

articles = []

for publication, feed_url in topics.items():
    d = feedparser.parse(feed_url)
    for entry in d.entries:
        if hasattr(entry, 'published_parsed') and is_today_bst(entry.published_parsed):
            # Combine all content fields
            content_parts = []

            if hasattr(entry, 'title'):
                content_parts.append(entry.title)
            if hasattr(entry, 'summary'):
                content_parts.append(entry.summary)
            if hasattr(entry, 'description'):
                content_parts.append(entry.description)
            if hasattr(entry, 'content'):
                content_parts.extend([c.value for c in entry.content if hasattr(c, 'value')])

            full_content = ' '.join(content_parts).lower()

            # Filter: Include only Palo Alto feeds or if spokesperson mentioned
            if publication.startswith('Palo Alto Networks') or contains_spokesperson(full_content):
                articles.append({
                    'publication': publication,
                    'title': entry.title,
                    'link': entry.link,
                    'published': datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).astimezone(BST).strftime('%Y-%m-%d %H:%M:%S %Z'),
                    'summary': entry.get('summary', '')[:200] + '...' if entry.get('summary') else '',
                })

# Sort articles by published date descending
articles.sort(key=lambda x: x['published'], reverse=True)

# Prepare README content
readme_content = "# Today's News Articles\n\n"
if articles:
    readme_content += "| Date (BST) | Publication | Title | Summary |\n"
    readme_content += "|------------|-------------|-------|---------|\n"
    for art in articles:
        readme_content += f"| {art['published']} | {art['publication']} | [{art['title']}]({art['link']}) | {art['summary']} |\n"
else:
    readme_content += "No articles found for today.\n"

# Write to README.md
with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme_content)

print(f"README.md updated with {len(articles)} articles.")
