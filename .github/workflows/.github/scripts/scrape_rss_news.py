import os
import feedparser
import openai
from datetime import datetime

# Load API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

topics = {
    'Palo Alto Networks News': {
        'url': 'https://news.google.com/rss/search?q="Palo+Alto+Networks"&hl=en-US&gl=US&ceid=US:en',
        'desc': 'Latest news and updates about Palo Alto Networks cybersecurity solutions.'
    },
    'Palo Alto Firewalls': {
        'url': 'https://news.google.com/rss/search?q="Palo+Alto+firewall"&hl=en-US&gl=US&ceid=US:en',
        'desc': 'News about Palo Alto Networks firewall products and innovations.'
    },
    'Palo Alto Security Research': {
        'url': 'https://unit42.paloaltonetworks.com/feed/',
        'desc': 'Threat intelligence and research updates from Palo Alto Networks Unit 42.'
    }
}

def summarize(text):
    prompt = (
        "Summarize the following news article in 2-3 sentences:\n\n"
        f"{text}\n\nSummary:"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error summarizing: {e}]"

def clean_html(text):
    import re
    return re.sub('<[^<]+?>', '', text)

def fetch_and_summarize():
    os.makedirs("news", exist_ok=True)
    output = [f"# 📰 Palo Alto Networks News Summary\n\n_Last updated: {datetime.utcnow().isoformat()} UTC_\n"]

    for title, data in topics.items():
        output.append(f"\n## {title}\n{data['desc']}\n")
        feed = feedparser.parse(data['url'])
        entries = feed.entries[:5]

        if not entries:
            output.append("_No articles found._\n")
            continue

        for entry in entries:
            summary = clean_html(entry.get('summary', ''))
            summarized = summarize(summary or entry.get('title', ''))
            output.append(f"- **[{entry.title}]({entry.link})**\n  - {summarized}\n")

    with open("news/paloalto_news.md", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    fetch_and_summarize()
