import requests
from datetime import datetime, timedelta
import pytz
import os
import csv
from urllib.parse import urlparse

API_KEY = os.getenv('GNEWS_API_KEY')
assert API_KEY, "⚠️ GNEWS_API_KEY not set as GitHub Secret"

BST = pytz.timezone('Europe/London')
now = datetime.now(BST)

KEYWORDS = ['Palo Alto', 'Palo Alto Networks', 'Unit 42']
spokespeople = ['tim erridge', 'scott mckinnon', 'carla baker', 'anna chung', 'sam rubin']

# Paste your national domains here:
national_domains = {
    "bbc.co.uk", "bloomberg.com", "businessinsider.com", "forbes.com", "ft.com",
    "reuters.com", "news.sky.com", "telegraph.co.uk", "thetimes.com", "independent.co.uk",
    "pa.media", "cityam.com", "irishexaminer.com", "independent.ie", "irishtimes.com",
    "moneyweek.com", "sundaytimes.co.uk", "economist.com", "theguardian.com", "channel5.com",
    "cnet.com", "edition.cnn.com", "cbronline.com", "computerworld.com", "express.co.uk",
    "dailymail.co.uk", "mirror.co.uk", "standard.co.uk", "inews.co.uk", "ibtimes.co.uk",
    "itv.com", "metro.co.uk", "theguardian.com/observer", "thesun.co.uk", "thesundaytimes.co.uk",
    "wsj.com", "businesspost.ie", "newstalk.com", "rte.ie", "thetimes.co.ie", "irishindependent.ie"
}

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

def fetch_articles():
    print("🔍 Fetching articles from GNews...")
    url = "https://gnews.io/api/v4/search"
    params = {
        'q': ' OR '.join(f'"{k}"' for k in KEYWORDS),
        'lang': 'en',
        'from': (now - timedelta(days=30)).strftime('%Y-%m-%d'),
        'max': 100,
        'token': API_KEY
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get('articles', [])

def clean_domain(url):
    try:
        domain = urlparse(url).netloc.lower()
        return domain[4:] if domain.startswith('www.') else domain
    except:
        return ""

def classify_domain(domain):
    return "national" if domain in national_domains else "trade"

def format_article(a):
    dt = datetime.fromisoformat(a['publishedAt'].replace('Z', '+00:00')).astimezone(BST)
    domain = clean_domain(a['url'])
    return {
        'date': dt,
        'domain': domain,
        'pub': a['source']['name'],
        'title': a['title'].strip(),
        'link': a['url'],
        'summary': (a.get('description') or '')[:200]
    }

def build_md_table(title, articles):
    if not articles:
        return f"## {title}\n\n_No articles found._\n\n"
    s = f"## {title}\n\n| Date | Publication | Title | Summary |\n|------|-------------|--------|---------|\n"
    for a in articles:
        s += f"| {a['date'].strftime('%Y-%m-%d %H:%M')} | {a['pub']} | [{a['title']}]({a['link']}) | {a['summary']} |\n"
    return s + "\n"

def write_csv(path, articles):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Publication', 'Title', 'Link', 'Summary'])
        for a in articles:
            writer.writerow([
                a['date'].strftime('%Y-%m-%d %H:%M'), a['pub'], a['title'], a['link'], a['summary']
            ])

def main():
    articles_raw = fetch_articles()

    articles = [format_article(a) for a in articles_raw if a.get('publishedAt')]

    today = now.date()
    today_articles = [a for a in articles if a['date'].date() == today and (
        any(k.lower() in a['title'].lower() for k in KEYWORDS) or
        any(sp in (a['title'] + a['summary']).lower() for sp in spokespeople)
    )]

    national_today = [a for a in today_articles if classify_domain(a['domain']) == "national"]
    trade_today = [a for a in today_articles if classify_domain(a['domain']) == "trade"]

    weekly = [a for a in articles if a['date'].date() >= today - timedelta(days=7)]
    monthly = [a for a in articles if a['date'].date() >= today - timedelta(days=30)]

    md = "# 🔐 Palo Alto Networks Coverage\n\n"
    md += build_md_table("📌 All PANW Mentions Today", today_articles)
    md += build_md_table("📰 National Coverage", national_today)
    md += build_md_table("📘 Trade Coverage", trade_today)

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

    md += TECHNICAL_SUMMARY

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)

    write_csv("summaries/weekly/summary.csv", weekly)
    write_csv("summaries/monthly/summary.csv", monthly)

    print("✅ README.md, weekly and monthly CSVs updated.")


if __name__ == "__main__":
    main()

