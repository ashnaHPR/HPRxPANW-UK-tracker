import requests
from bs4 import BeautifulSoup

def fetch_google_news(query):
    print(f"🔍 Scraping Google News for: {query}")
    encoded_query = query.replace(' ', '+')
    url = f"https://www.google.com/search?q={encoded_query}&tbm=nws&hl=en-GB"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: HTTP {response.status_code}")
        return []

    with open("debug_google_news.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Saved Google News HTML to debug_google_news.html")

    soup = BeautifulSoup(response.text, "html.parser")

    # Update selector based on live page inspection (this is current as of Aug 2025)
    articles = []
    for g in soup.select('div.So6nqc'):
        title_tag = g.select_one('div.mCBkyc')
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        link_tag = g.select_one('a')
        link = link_tag['href'] if link_tag else None
        snippet_tag = g.select_one('div.GI74Re')
        summary = snippet_tag.get_text(strip=True) if snippet_tag else ''
        source_tag = g.select_one('div.CEMjEf span.xQ82C.e8fRJf')
        source = source_tag.get_text(strip=True) if source_tag else ''
        time_tag = g.select_one('time')
        published_time = time_tag['datetime'] if time_tag else ''

        articles.append({
            'title': title,
            'link': link,
            'summary': summary,
            'source': source,
            'published_time': published_time,
        })

    print(f"Found {len(articles)} articles.")
    for i, a in enumerate(articles[:5], 1):
        print(f"{i}. {a['title']} ({a['source']})")
        print(f"   Link: {a['link']}")
        print(f"   Summary: {a['summary']}\n")

    return articles

if __name__ == "__main__":
    fetch_google_news("Palo Alto Networks")
