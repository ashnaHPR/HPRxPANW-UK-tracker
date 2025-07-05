import os
import requests
from datetime import datetime, timezone
import pytz

# BST timezone for datetime conversions
BST = pytz.timezone('Europe/London')

# Spokespersons list (case insensitive)
spokespersons = ['tim erridge', 'scott mckinnon', 'carla baker', 'anna chung', 'sam rubin']

# National publication titles (case insensitive)
national_titles = [
    'BBC', 'Bloomberg', 'Business Insider', 'Forbes', 'Financial Times', 'Reuters',
    'Sky News', 'The Telegraph', 'The Times', 'The Independent', 'PA Media',
    'City AM', 'Irish Examiner', 'Irish Independent', 'Irish Times', 'MoneyWeek',
    'Sunday Times (Ireland)', 'Economist', 'The Guardian', 'BBC Radio 4', 'BBC Radio 5 Live',
    'Channel 5', 'CNET', 'CNN International', 'Computer Business Review', 'Computerworld UK',
    'Daily Express', 'Daily Mail', 'Daily Mirror', 'Evening Standard', 'The i',
    'International Business Times UK', 'ITV News', 'Metro', 'The Observer', 'The Sun',
    'The Sun on Sunday', 'Sunday Express', 'Sunday Mirror', 'Wall Street Journal',
    'Business Post', 'Newstalk', 'RTÉ News'
]

# National domains (full list from you, cleaned and lowercased)
national_domains = {
    'bbc.co.uk', 'bloomberg.com', 'businessinsider.com', 'forbes.com', 'ft.com',
    'reuters.com', 'news.sky.com', 'telegraph.co.uk', 'thetimes.com', 'independent.co.uk',
    'pa.media', 'cityam.com', 'irishexaminer.com', 'independent.ie', 'irishtechnews.ie',
    'irishtimes.com', 'moneyweek.com', 'sundaytimes.co.uk', 'economist.com',
    'theguardian.com', 'bbc.co.uk', 'channel5.com', 'cnet.com', 'edition.cnn.com',
    'cbronline.com', 'computerworld.com', 'express.co.uk', 'dailymail.co.uk',
    'mirror.co.uk', 'standard.co.uk', 'inews.co.uk', 'ibtimes.co.uk', 'itv.com',
    'metro.co.uk', 'theguardian.com/observer', 'thesun.co.uk', 'thesundaytimes.co.uk',
    'wsj.com', 'businesspost.ie', 'newstalk.com', 'rte.ie', 'thetimes.co.ie',
    'irishindependent.ie'
}

# Full domains list (including trade + national)
all_domains = {
    'bbc.co.uk', 'bloomberg.com', 'businessinsider.com', 'forbes.com', 'ft.com',
    'reuters.com', 'news.sky.com', 'telegraph.co.uk', 'thetimes.com', 'independent.co.uk',
    'pa.media', 'cityam.com', 'computerweekly.com', 'raconteur.net', 'techcrunch.com',
    'theregister.com', 'techradar.com', 'insight.scmagazineuk.com', 'verdict.co.uk',
    'wired.com', 'zdnet.com', 'itpro.com', 'csoonline.com', 'infosecurity-magazine.com',
    'techmonitor.ai', 'capacitymedia.com', 'cybermagazine.com', 'digitalisationworld.com',
    'channelfutures.com', 'accountancyage.com', 'financialresearch.gov', 'businesspost.ie',
    'cio.com', 'directoroffinance.com', 'emeafinance.com', 'finextra.com', 'finance-monthly.com',
    'ffnews.com', 'fintech.global', 'fstech.co.uk', 'gtreview.com', 'government-transformation.com',
    'gpsj.co.uk', 'ifamagazine.com', 'ismg.io', 'insuranceday.com', 'intelligentciso.com',
    'ifre.com', 'irishexaminer.com', 'independent.ie', 'irishtechnews.ie', 'irishtimes.com',
    'techforge.pub', 'digit-software.com', 'intelligentcio.com', 'silicon.co.uk', 'information-age.com',
    'diginomica.com', 'techrepublic.com', 'computing.co.uk', 'thenextweb.com', 'moneyweek.com',
    'politico.eu', 'professionaladviser.com', 'publicfinanceinternational.org', 'publicsectorexecutive.com',
    'publicsectorfocus.com', 'publicsectornetwork.co.uk', 'publicsectordigital.com', 'publicservicemagazine.com',
    'rte.ie', 'spglobal.com', 'structuredcreditinvestor.com', 'thetimes.co.ie', 'techcentral.ie',
    'europeanfinancialreview.com', 'thestack.technology', 'thinkdigitalpartners.com', 'uktech.news',
    'wealthandfinance-intl.com', 'economist.com', 'theguardian.com', 'bbc.co.uk', 'channel5.com',
    'cnet.com', 'edition.cnn.com', 'cbronline.com', 'computerworld.com', 'express.co.uk',
    'dailymail.co.uk', 'mirror.co.uk', 'standard.co.uk', 'inews.co.uk', 'ibtimes.co.uk',
    'itv.com', 'metro.co.uk', 'theguardian.com/observer', 'thesun.co.uk', 'thesundaytimes.co.uk',
    'express.co.uk', 'mirror.co.uk', 'wsj.com', 'healthcare-outlook.com', 'digitalhealth.net',
    'digitalhealthnews.com', 'healthcarebusinessoutlook.com', 'healthtechdigital.com',
    'pathfinderinternational.co.uk', 'housing-technology.com', 'themj.co.uk', 'ukauthority.com',
    'schoolsweek.co.uk', 'insights.talintpartners.com', 'tes.com', 'timeshighereducation.com',
    'ictforeducation.co.uk', 'educationbusinessuk.net', 'researchprofessionalnews.com',
    'telecoms.com', 'lightreading.com', 'totaltele.com', 'telecomtv.com', 'developingtelecoms.com',
    'telecomstechnews.com', 'mobile-magazine.com', 'mobileworldlive.com', 'mobileeurope.co.uk',
    'iot-now.com', 'manufacturingdigital.com', 'themanufacturer.com', 'mpemagazine.co.uk',
    'manufacturingmanagement.co.uk', 'businessandindustrytoday.co.uk', 'industryeurope.com',
    'logisticsbusiness.com', 'logisticsit.com', 'ipesearch.co.uk', 'mfg-outlook.com',
    'manufacturing-today.com', 'ukmfg.tv', 'uk-manufacturing-online.co.uk', 'am-online.com',
    'autoexpress.co.uk', 'auto-retail.co.uk', 'automotivelogisticsmagazine.com',
    'automotivemanufacturingsolutions.com', 'automotiveworld.com',
    'automotivetestingtechnologyinternational.com', 'connectedtechnologysolutions.co.uk',
    'moveelectric.com', 'ciltuk.org.uk', 'evo.co.uk', 'motortrader.com', 'just-auto.com',
    'autofutures.tv', 'motoringresearch.com', 'theengineer.co.uk', 'fiercepharma.com',
    'hsj.co.uk', 'hospitaltimes.co.uk', 'pbiforum.net', 'pharma-iq.com',
    'pharmaceutical-technology.com', 'intelligentcxo.com', 'cxtoday.com', 'cxnetwork.com',
    'cxm.co.uk', 'cxomagazine.com', 'channellife.co.uk', 'channelweb.co.uk', 'it-sp.eu',
    'computerweekly.com/microscope', 'pcr-online.biz', 'pcpro.co.uk', 'channelpro.co.uk',
    'cloudpro.co.uk', 'iteuropa.com', 'siliconrepublic.com', 'irishtechnews.ie', 'techcentral.ie',
    'businesspostgroup.com', 'newstalk.com', 'irishexaminer.com', 'irishtimes.com',
    'independent.ie', 'thetimes.com/world/ireland', 'rte.ie'
}

# GNews API key from environment variable
GNEWS_API_KEY = os.getenv('GNEWS_API_KEY')
if not GNEWS_API_KEY:
    raise ValueError("Missing GNEWS_API_KEY environment variable")

def is_today_bst(published_str):
    """Return True if the published date is today (BST)."""
    try:
        dt_utc = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
    except Exception:
        return False
    dt_bst = dt_utc.astimezone(BST)
    now_bst = datetime.now(BST)
    return dt_bst.date() == now_bst.date()

def contains_spokesperson(text):
    """Check if text contains any spokesperson (case insensitive)."""
    if not text:
        return False
    text_lower = text.lower()
    return any(name in text_lower for name in spokespersons)

def classify_article(title, domain):
    domain = domain.lower()
    if domain in national_domains:
        return 'national'
    # Also check title for national publication keywords
    for nat_title in national_titles:
        if nat_title.lower() in title.lower():
            return 'national'
    return 'trade'

def clean_domain(source_name, url):
    # Attempt to extract domain from URL if missing
    if source_name:
        return source_name.lower()
    if url:
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.lower()
        except:
            return ''
    return ''

# Query string for GNews API
query_terms = '"Palo Alto Networks" OR "Palo Alto" OR "Unit 42"'

# Today date ISO format for 'from' param
today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')

url = f"https://gnews.io/api/v4/search?q={query_terms}&lang=en&from={today_date}&max=100&token={GNEWS_API_KEY}"

print(f"Fetching articles from: {url}")

response = requests.get(url)
if response.status_code != 200:
    raise Exception(f"GNews API Error: {response.status_code} {response.text}")

data = response.json()
articles = data.get('articles', [])

print(f"Found {len(articles)} articles from GNews")

national_articles = []
trade_articles = []

for entry in articles:
    title = entry.get('title', '') or ''
    description = entry.get('description', '') or ''
    content = (title + " " + description).lower()
    link = entry.get('url', '')
    published_at = entry.get('publishedAt', '') or ''
    source = entry.get('source', {})
    source_name = source.get('name', '')
    domain = source.get('domain', '') or clean_domain(source_name, link)

    if not is_today_bst(published_at):
        continue

    # Check for topics & spokespeople in content (case-insensitive)
    if any(keyword in content for keyword in ['palo alto', 'unit 42']) or contains_spokesperson(content):

        category = classify_article(title, domain)

        art = {
            'publication': source_name or domain,
            'title': title,
            'link': link,
            'published': datetime.fromisoformat(published_at.replace('Z', '+00:00')).astimezone(BST).strftime('%Y-%m-%d %H:%M:%S %Z'),
            'summary': (description[:200] + '...') if description else '',
        }

        if category == 'national':
            national_articles.append(art)
        else:
            trade_articles.append(art)

# Sort descending by published date/time
national_articles.sort(key=lambda x: x['published'], reverse=True)
trade_articles.sort(key=lambda x: x['published'], reverse=True)

def build_markdown_table(title, articles):
    if not articles:
        return f"## {title}\n\n_No articles found today
