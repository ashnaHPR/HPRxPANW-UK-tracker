import requests
from datetime import datetime, timezone
import pytz
from urllib.parse import urlparse

# Define BST timezone (+1 hour from UTC)
BST = pytz.timezone('Europe/London')

# API key for GNews API
GNEWS_API_KEY = "d304220708e1b37ac194616353216bf9"

# Keywords to look for in articles (case insensitive)
keywords = ['palo alto', 'palo alto networks', 'unit 42']
spokespersons = ['tim erridge', 'scott mckinnon', 'carla baker', 'anna chung', 'sam rubin']

# All domains you sent
all_domains = [
    "bbc.co.uk","bloomberg.com","businessinsider.com","forbes.com","ft.com","reuters.com",
    "news.sky.com","telegraph.co.uk","thetimes.com","independent.co.uk","pa.media","cityam.com",
    "computerweekly.com","raconteur.net","techcrunch.com","theregister.com","techradar.com",
    "insight.scmagazineuk.com","verdict.co.uk","wired.com","zdnet.com","itpro.com","csoonline.com",
    "infosecurity-magazine.com","techmonitor.ai","capacitymedia.com","cybermagazine.com",
    "digitalisationworld.com","channelfutures.com","accountancyage.com","financialresearch.gov",
    "businesspost.ie","cio.com","directoroffinance.com","emeafinance.com","finextra.com",
    "finance-monthly.com","ffnews.com","fintech.global","fstech.co.uk","gtreview.com",
    "government-transformation.com","gpsj.co.uk","ifamagazine.com","ismg.io","insuranceday.com",
    "intelligentciso.com","ifre.com","irishexaminer.com","independent.ie","irishtechnews.ie",
    "irishtimes.com","techforge.pub","digit-software.com","intelligentcio.com","silicon.co.uk",
    "information-age.com","diginomica.com","techrepublic.com","computing.co.uk","thenextweb.com",
    "moneyweek.com","politico.eu","professionaladviser.com","publicfinanceinternational.org",
    "publicsectorexecutive.com","publicsectorfocus.com","publicsectornetwork.co.uk",
    "publicsectordigital.com","publicservicemagazine.com","rte.ie","spglobal.com",
    "structuredcreditinvestor.com","thetimes.co.ie","techcentral.ie","europeanfinancialreview.com",
    "thestack.technology","thinkdigitalpartners.com","uktech.news","wealthandfinance-intl.com",
    "economist.com","theguardian.com","channel5.com","cnet.com","edition.cnn.com","cbronline.com",
    "computerworld.com","express.co.uk","dailymail.co.uk","mirror.co.uk","standard.co.uk",
    "inews.co.uk","ibtimes.co.uk","itv.com","metro.co.uk","theguardian.com/observer","thesun.co.uk",
    "thesundaytimes.co.uk","wsj.com","healthcare-outlook.com","digitalhealth.net",
    "digitalhealthnews.com","healthcarebusinessoutlook.com","healthtechdigital.com",
    "pathfinderinternational.co.uk","housing-technology.com","themj.co.uk","ukauthority.com",
    "schoolsweek.co.uk","insights.talintpartners.com","tes.com","timeshighereducation.com",
    "ictforeducation.co.uk","educationbusinessuk.net","researchprofessionalnews.com","telecoms.com",
    "lightreading.com","totaltele.com","telecomtv.com","developingtelecoms.com","telecomstechnews.com",
    "mobile-magazine.com","mobileworldlive.com","mobileeurope.co.uk","iot-now.com",
    "manufacturingdigital.com","themanufacturer.com","mpemagazine.co.uk","manufacturingmanagement.co.uk",
    "businessandindustrytoday.co.uk","industryeurope.com","logisticsbusiness.com","logisticsit.com",
    "ipesearch.co.uk","mfg-outlook.com","manufacturing-today.com","ukmfg.tv","uk-manufacturing-online.co.uk",
    "am-online.com","autoexpress.co.uk","auto-retail.co.uk","automotivelogisticsmagazine.com",
    "automotivemanufacturingsolutions.com","automotiveworld.com","automotivetestingtechnologyinternational.com",
    "connectedtechnologysolutions.co.uk","moveelectric.com","ciltuk.org.uk","evo.co.uk",
    "motortrader.com","just-auto.com","autofutures.tv","motoringresearch.com","theengineer.co.uk",
    "fiercepharma.com","hsj.co.uk","hospitaltimes.co.uk","pbiforum.net","pharma-iq.com",
    "pharmaceutical-technology.com","intelligentcxo.com","cxtoday.com","cxnetwork.com",
    "cxm.co.uk","cxomagazine.com","channellife.co.uk","channelweb.co.uk","it-sp.eu",
    "computerweekly.com/microscope","pcr-online.biz","pcpro.co.uk","channelpro.co.uk",
    "cloudpro.co.uk","iteuropa.com","siliconrepublic.com","irishtechnews.ie","techcentral.ie",
    "businesspostgroup.com","newstalk.com","irishexaminer.com","irishtimes.com","independent.ie",
    "thetimes.com/world/ireland","rte.ie"
]

# National domains based on your national titles list:
national_domains = {
    "bbc.co.uk","bloomberg.com","businessinsider.com","forbes.com","ft.com","reuters.com",
    "news.sky.com","telegraph.co.uk","thetimes.com","independent.co.uk","pa.media","cityam.com",
    "irishexaminer.com","independent.ie","irishtimes.com","moneyweek.com","thesundaytimes.co.uk",
    "economist.com","theguardian.com","channel5.com","cnet.com","edition.cnn.com","cbronline.com",
    "computerworld.com","express.co.uk","dailymail.co.uk","mirror.co.uk","standard.co.uk",
    "inews.co.uk","ibtimes.co.uk","itv.com","metro.co.uk","theguardian.com","thesun.co.uk",
    "wsj.com","businesspost.ie","newstalk.com","rte.ie"
}

trade_domains = set(all_domains) - national_domains

def extract_domain(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return ""

def contains_any(text, lst):
    if not text:
        return False
    text = text.lower()
    return any(item.lower() in text for item in lst)

def fetch_articles():
    url = f"https://gnews.io/api/v4/search?q=palo+alto+OR+palo+alto+networks+OR+unit+42&lang=en&max=100&token={GNEWS_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch articles: {response.status_code}")
        return []
    data = response.json()
    return data.get("articles", [])

def main():
    import pytz
    from datetime import datetime, timezone

    BST = pytz.timezone("Europe/London")
    now_bst = datetime.now(BST).date()

    panw_articles = []
    national_articles = []
    trade_articles = []

    articles = fetch_articles()

    for art in articles:
        pub_date_raw = art.get("publishedAt")
        if not pub_date_raw:
            continue
        try:
            dt_utc = datetime.fromisoformat(pub_date_raw.rstrip("Z")).replace(tzinfo=timezone.utc)
            dt_bst = dt_utc.astimezone(BST)
        except Exception:
            continue

        if dt_bst.date() != now_bst:
            continue

        full_text = " ".join([
            art.get("title", ""),
            art.get("description", ""),
            art.get("content", "")
        ]).lower()

        domain = extract_domain(art.get("url", ""))

        # Check PANW keywords
        if contains_any(full_text, keywords):
            panw_articles.append({
                "published": dt_bst.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "publication": domain,
                "title": art.get("title", ""),
                "link": art.get("url", ""),
                "summary": (art.get("description") or "")[:200] + "..."
            })
            continue

        # Check spokespeople for nationals/trades
        if contains_any(full_text, spokespersons):
            if domain in national_domains:
                national_articles.append({
                    "published": dt_bst.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "publication": domain,
                    "title": art.get("title", ""),
                    "link": art.get("url", ""),
                    "summary": (art.get("description") or "")[:200] + "..."
                })
            elif domain in trade_domains:
                trade_articles.append({
                    "published": dt_bst.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "publication": domain,
                    "title": art.get("title", ""),
                    "link": art.get("url", ""),
                    "summary": (art.get("description") or "")[:200] + "..."
                })

    def build_md_table(title, articles):
        if not articles:
            return f"## {title}\n\n_No articles found._\n\n"
        md = f"## {title}\n\n"
        md += "| Date (BST) | Publication | Title | Summary |\n"
        md += "|---|---|---|---|\n"
        for a in articles:
            md += f"| {a['published']} | {a['publication']} | [{a['title']}]({a['link']}) | {a['summary']} |\n"
        md += "\n"
        return md

    panw_articles.sort(key=lambda x: x['published'], reverse=True)
    national_articles.sort(key=lambda x: x['published'], reverse=True)
    trade_articles.sort(key=lambda x: x['published'], reverse=True)

    content = "# Today's Palo Alto Networks News\n\n"
    content += build_md_table("📌 Palo Alto Networks Mentions", panw_articles)
    content += "---\n\n"
    content += build_md_table("📰 National Media Mentions (Spokespersons)", national_articles)
    content += "---\n\n"
    content += build_md_table("📘 Trade Media Mentions (Spokespersons)", trade_articles)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated README.md with {len(panw_articles) + len(national_articles) + len(trade_articles)} articles.")

if __name__ == "__main__":
    main()
