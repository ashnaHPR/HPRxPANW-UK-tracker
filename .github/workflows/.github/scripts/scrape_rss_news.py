import os
import feedparser
import openai
from datetime import datetime
import re
import traceback

openai.api_key = os.getenv("OPENAI_API_KEY")

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

def summarize(text):
    prompt = (
        "Summarize this article in 2-3 sentences for a cybersecurity-focused audience:\n\n"
        f"{text}\n\nSummary:"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error in summarization: {e}]"

def clean_html(text):
    return re.sub('<[^<]+?>', '', text)

def fetch_and_summarize():
    os.makedirs("news", exist_ok=True)
    output = [f"# 📰 Palo Alto Networks News Summary\n\n_Last updated: {datetime.utcnow().isoformat()} UTC_\n"]

    for title, data in topics.items():
        print(f"Fetching RSS feed for topic: '{title}' from URL: {data['url']}")
        output.append(f"\n## {title}\n{data['desc']}\n")
        feed = feedparser.parse(data['url'])
        entries = feed.entries[:5]

        if not entries:
            print(f"No articles found for topic: {title}")
            output.append("_No articles found._\n")
            continue

        for entry in entries:
            summary_text = clean_html(entry.get('summary', '')) or entry.get('title', '')
            print(f"Summarizing article: {entry.title}")
            summarized = summarize(summary_text)
            print(f"Summary for '{entry.title}': {summarized}")
            output.append(f"- **[{entry.title}]({entry.link})**\n  - {summarized}\n")

    with open("news/paloalto_news.md", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    print("News summary file written successfully.")

if __name__ == "__main__":
    try:
        print("Starting fetch_and_summarize()")
        fetch_and_summarize()
        print("fetch_and_summarize() completed successfully")
    except Exception as e:
        print("❌ Script failed with an error:")
        print(e)
        traceback.print_exc()
        exit(2)
