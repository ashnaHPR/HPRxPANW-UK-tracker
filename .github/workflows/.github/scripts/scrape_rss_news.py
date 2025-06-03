import os
import feedparser
import re
from datetime import datetime
from openai import OpenAI
import traceback

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

topics = {
    'Palo Alto Networks': {
        'url': 'https://news.google.com/rss/search?q="Palo+Alto+Networks"&hl=en-US&gl=US&ceid=US:en',
        'desc': 'Latest news and updates about Palo Alto Networks cybersecurity solutions.'
    },
    'Palo Alto Networks Firewalls': {
        'url': 'https://news.google.com/rss/search?q="Palo+Alto+firewall"&hl=en-US&gl=US&ceid=US:en',
        'desc': 'News about Palo Alto Networks firewall products and innovations.'
    },
    'Palo Alto Networks Research': {
        'url': 'https://unit42.paloaltonetworks.com/feed/',
        'desc': 'Threat intelligence and research updates from Palo Alto Networks Unit 42.'
    }
}

def clean_html(text):
    return re.sub('<[^<]+?>', '', text)

def summarize(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Summarize this for a cybersecurity-focused audience:\n\n{text}"}],
            max_tokens=200,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error: {e}]"

def format_table(rows):
    table = "| Source | Title | Summary |\n|--------|-------|---------|\n"
    for row in rows:
        table += f"| {row['source']} | [{row['title']}]({row['link']}) | {row['summary']} |\n"
    return table

def fetch_news():
    os.makedirs("news", exist_ok=True)
    news_rows = []

    for title, data in topics.items():
        feed = feedparser.parse(data['url'])
        for entry in feed.entries[:5]:
            summary_text = clean_html(entry.get('summary', entry.title))
            summarized = summarize(summary_text)
            news_rows.append({
                'source': entry.get('source', {}).get('title', 'Unknown'),
                'title': entry.title,
                'link': entry.link,
                'summary': summarized
            })

    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    table_md = f"# 📰 Palo Alto Networks News Summary\n\n_Last updated: {timestamp}_\n\n"
    table_md += format_table(news_rows)

    with open("news/paloalto_news.md", "w", encoding="utf-8") as f:
        f.write(table_md)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(table_md)

if __name__ == "__main__":
    try:
        fetch_news()
    except Exception as e:
        print("❌ Script failed with an error:")
        print(e)
        traceback.print_exc()
        exit(2)
