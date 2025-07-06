import requests
from datetime import datetime, timezone
import pytz

# BST timezone
BST = pytz.timezone('Europe/London')

# Your GNews API key from GitHub secrets or local testing
API_KEY = "d304220708e1b37ac194616353216bf9"  # Replace with your secret or env var in production

# Domains list (you gave me a lot, here they all are)
all_domains = [
    "bbc.co.uk", "bloomberg.com", "businessinsider.com", "forbes.com", "ft.com",
    "reuters.com", "news.sky.com", "telegraph.co.uk", "thetimes.com", "independent.co.uk",
    "pa.media", "cityam.com", "computerweekly.com", "raconteur.net", "techcrunch.com",
    "theregister.com", "techradar.com", "insight.scmagazineuk.com", "verdict.co.uk",
    "wired.com", "zdnet.com", "itpro.com", "csoonline.com", "infosecurity-magazine.com",
    "techmonitor.ai", "capacitymedia.com", "cybermagazine.com", "digitalisationworld.com",
    "channelfutures.com", "accountancyage.com", "financialresearch.gov", "businesspost.ie",
    "cio.com", "directoroffinance.com", "emeafinance.com", "finextra.com", "finance-monthly.com",
    "ffnews.com", "fintech.global", "fstech.co.uk", "gtreview.com", "government-transformation.com",
    "gpsj.co.uk", "ifamagazine.com", "ismg.io", "insuranceday.com", "intelligentciso.com",
    "ifre.com", "irishexaminer.com", "independent.ie", "irishtechnews.ie", "irishtimes.com",
    "techforge.pub", "digit-software.com", "intelligentcio.com", "silicon.co.uk", "information-age.com",
    "diginomica.com", "techrepublic.com", "computing.co.uk", "thenextweb.com", "moneyweek.com",
    "politico.eu", "professionaladviser.com", "publicfinanceinternational.org", "publicsectorexecutive.com",
    "publicsectorfocus.com", "publicsectornetwork.co.uk", "publicsectordigital.com", "publicservicemagazine.com",
    "rte.ie", "spglobal.com", "structuredcreditinvestor.com", "thetimes.co.ie", "techcentral.ie",
    "europeanfinancialreview.com", "thestack.technology", "thinkdigitalpartners.com", "uktech.news",
    "wealthandfinance-intl.com", "economist.com", "theguardian.com", "channel5.com", "cnet.com",
    "edition.cnn.com", "cbronline.com", "computerworld.com", "express.co.uk", "dailymail.co.uk",
    "mirror.co.uk", "standard.co.uk", "inews.co.uk", "ibtimes.co.uk", "itv.com", "metro.co.uk",
    "theguardian.com/observer", "thesun.co.uk", "thesundaytimes.co.uk", "wsj.com", "healthcare-outlook.com",
    "digitalhealth.net", "digitalhealthnews.com", "healthcarebusinessoutlook.com", "healthtechdigital.com",
    "pathfinderinternational.co.uk", "housing-technology.com", "themj.co.uk", "ukauthority.com",
    "schoolsweek.co.uk", "insights.talintpartners.com", "tes.com", "timeshighereducation.com",
    "ictforeducation.co.uk", "educationbusinessuk.net", "researchprofessionalnews.com", "telecoms.com",
    "lightreading.com", "totaltele.com", "telecomtv.com", "developingtelecoms.com", "telecomstechnews.com",
    "mobile-magazine.com", "mobileworldlive.com", "mobileeurope.co.uk", "iot-now.com", "manufacturingdigital.com",
    "themanufacturer.com", "mpemagazine.co.uk", "manufacturingmanagement.co.uk", "businessandindustrytoday.co.uk",
    "industryeurope.com", "logisticsbusiness.com", "logisticsit.com", "ipesearch.co.uk", "mfg-outlook.com",
    "manufacturing-today.com", "ukmfg.tv", "uk-manufacturing-online.co.uk", "am-online.com", "autoexpress.co.uk",
    "auto-retail.co.uk", "automotivelogisticsmagazine.com", "automotivemanufacturingsolutions.com",
    "automotiveworld.com", "automotivetestingtechnologyinternational.com", "connectedtechnologysolutions.co.uk",
    "moveelectric.com", "ciltuk.org.uk", "evo.co.uk", "motortrader.com", "just-auto.com", "autofutures.tv",
    "motoringresearch.com", "theengineer.co.uk", "fiercepharma.com", "hsj.co.uk", "hospitaltimes.co.uk",
    "pbiforum.net", "pharma-iq.com", "pharmaceutical-technology.com", "intelligentcxo.com", "cxtoday.com",
    "cxnetwork.com", "cxm.co.uk", "cxomagazine.com", "channellife.co.uk", "channelweb.co.uk", "it-sp.eu",
    "computerweekly.com/microscope", "pcr-online.biz", "pcpro.co.uk", "channelpro.co.uk", "cloudpro.co.uk",
    "iteuropa.com", "siliconrepublic.com", "irishtechnews.ie", "techcentral.ie", "businesspostgroup.com",
    "newstalk.com", "irishexaminer.com", "irishtimes.com", "independent.ie", "thetimes.com/world/ireland",
    "rte.ie"
]

# National publication titles you gave (case insensitive)
national_titles = [
    "BBC", "Bloomberg", "Business Insider", "Forbes", "Financial Times", "Reuters",
    "Sky News", "The Telegraph", "The Times", "The Independent", "PA Media", "City AM",
    "Irish Examiner", "Irish Independent", "Irish Times", "MoneyWeek", "Sunday Times (Ireland)",
    "Economist", "The Guardian", "BBC Radio 4", "BBC Radio 5 Live", "Channel 5", "CNET",
    "CNN International", "Computer Business Review", "Computerworld UK", "Daily Express",
    "Daily Mail", "Daily Mirror", "Evening Standard", "The i", "International Business Times UK",
    "ITV News", "Metro", "The Observer", "The Sun", "The Sun on Sunday", "Sunday Express",
    "Sunday Mirror", "Wall Street Journal", "Business Post", "Newstalk", "RTÉ News"
]

# Spokespersons list
spokespersons = ['tim erridge', 'scott mckinnon', 'carla baker', 'anna chung', 'sam rubin']

def is_today_bst(published_str):
    """Check if the published date (string ISO format) is today BST"""
    try:
        dt_utc = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
    except Exception:
        return False
    dt_bst = dt_utc.astimezone(BST)
    now_bst = datetime.now(BST)
    return dt_bst.date() == now_bst.date()

def contains_spokesperson(text):
    if not text:
        return False
    text_lower = text.lower()
    return any(sp in text_lower for sp in spokespersons)

def classify_article(publication_title, domain):
    # Check if domain in national domain list
    domain = domain.lower()
    is_national_domain = any(domain.endswith(nd) for nd in all_domains)
    is_national_title = any(nt.lower() in publication_title.lower() for nt in national_titles)

    if is_national_domain or is_national_title:
        return "national"
    else:
        return "trade"

def fetch_articles():
    panw_articles = []
    national_articles = []
    trade_articles = []

    # Keywords to search for in GNews API
    query_keywords = ['Palo Alto', 'Palo Alto Networks', 'Unit 42']

    # Max articles per request to avoid quota issues
    max_articles = 100

    # GNews API endpoint
    base_url = "https://gnews.io/api/v4/search"

    for keyword in query_keywords:
        params = {
            'q': keyword,
            'lang': 'en',
            'max': max_articles,
            'token': API_KEY,
            'in': 'title,description',
            'sortby': 'publishedAt'
        }

        resp = requests.get(base_url, params=params)
        if resp.status_code != 200:
            print(f"Error fetching articles for {keyword}: {resp.status_code}")
            continue
        data = resp.json()
        if 'articles' not in data:
            print(f"No articles found for {keyword}")
            continue

        for article in data['articles']:
            pub_date_str = article.get('publishedAt')
            if not pub_date_str or not is_today_bst(pub_date_str):
                continue

            # Check if article contains any spokesperson
            combined_text = (article.get('title','') + ' ' + article.get('description','')).lower()
            if not (contains_spokesperson(combined_text) or
                    any(kw.lower() in combined_text for kw in query_keywords)):
                continue

            # Extract domain from URL
            url = article.get('url', '')
            domain = ''
            try:
                domain = url.split('/')[2]
            except Exception:
                domain = ''

            classification = classify_article(article.get('source', {}).get('name', ''), domain)

            article_data = {
                'publication': article.get('source', {}).get('name', ''),
                'title': article.get('title', '').replace('\n',' ').strip(),
                'link': url,
                'published': pub_date_str,
                'summary': article.get('description', '').replace('\n',' ').strip()
            }

            if classification == 'national':
                national_articles.append(article_data)
            else:
                trade_articles.append(article_data)

            panw_articles.append(article_data)

    return national_articles, trade_articles, panw_articles

def build_markdown_table(title, articles):
    if not articles:
        return f"## {title}\n\n_No articles found today._\n"
    md = f"## {title}\n\n"
    md += "| Publication | Title | Published | Summary |\n"
    md += "|-------------|-------|-----------|---------|\n"
    for art in articles:
        md += f"| {art['publication']} | [{art['title']}]({art['link']}) | {art['published']} | {art['summary']} |\n"
    md += "\n"
    return md

def main():
    national_articles, trade_articles, panw_articles = fetch_articles()

    content = "# Palo Alto Networks News Update\n\n"
    content += f"_Last updated: {datetime.now(BST).strftime('%Y-%m-%d %H:%M:%S %Z')}_\n\n"

    content += build_markdown_table("National Publications", national_articles)
    content += build_markdown_table("Trade Publications", trade_articles)
    content += build_markdown_table("All PANW Articles", panw_articles)

    TECHNICAL_SUMMARY = """
---

## Technical Summary

This repository hosts an automated news coverage tracker for Palo Alto Networks, implemented in Python and integrated with GitHub Actions for continuous operation.

The system queries the GNews API every 4 hours to pull the latest articles containing Palo Alto Networks-related keywords and mentions of specific spokespeople. Articles are filtered to ensure timeliness based on BST timezone, and source classification is performed via a comprehensive domain mapping strategy that segments outlets into national and trade media categories.

Results are formatted into Markdown tables with clickable headlines, publication timestamps, and article summaries, then committed back to the repository's `README.md`. This creates a continuously updated, version-controlled media monitoring dashboard accessible to stakeholders at any time.

Key technical highlights include:

- Robust timezone-aware data filtering  
- Domain-driven source classification for granular insights  
- Automated CI/CD pipeline with GitHub Actions for scheduled updates  
- Modular design allowing easy extension with new keywords or sources  

This setup provides an efficient, scalable, and transparent solution for real-time media intelligence tailored to Palo Alto Networks’ coverage needs.
"""

    content += TECHNICAL_SUMMARY

    with open("README.md", "w", encoding='utf-8') as f:
        f.write(content)

