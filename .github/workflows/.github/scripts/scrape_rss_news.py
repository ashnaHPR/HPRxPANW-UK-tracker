import os
import feedparser
from openai import OpenAI
from datetime import datetime
import re
import traceback
from urllib.parse import urlparse

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

def summarize(text):
    prompt = (
        "Summarize this article in 2-3 sentences for a cybersecurity-focused audience:\n\n"
        f"{text}\n\nSummary:"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error: {e}]"

def clean_html(text):
    return re.sub('<[^<]+?>', '', text)

def extract_source_and_date(entry):
    parsed_url = urlparse(entry.link)
    source = parsed_url.netloc.replace("www.", "")
    pub_date = entry.get("published", "")[:16]
    return f"{source} {pub_date.strip()}"

def fetch_and_summarize():
    os.makedirs("news", exist_ok=True)
    output = [f"_Last updated: {datetime.utcnow().isoformat()} UTC_\n"]
    output.append("| Source | Title | Summary |")
    output.append("|--------|-------|---------|")

    for data in topics.values():
        feed = feedparser.parse(data['url'])
        entries = feed.entries[:5]

        for entry in entries:
            source_date = extract_source_and_date(entry)
            summary_text = clean_html(entry.get('summary', '')) or entry.get('title', '')
            summarized = summarize(summary_text)
            title = entry.title.strip().replace("|", "-")
            link = entry.link.strip()
            output.append(f"| {source_date} | [{title}]({link}) | {summarized} |")

    markdown = "\n".join(output)
    
    # Save to dedicated file
    with open("news/paloalto_news_section.md", "w", encoding="utf-8") as f:
        f.write(markdown)

    # Replace section in README
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    new_readme = re.sub(
        r"(<!-- NEWS_START -->)(.*?)(<!-- NEWS_END -->)",
        f"\\1\n\n{markdown}\n\n\\3",
        readme,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)

if __name__ == "__main__":
    try:
        fetch_and_summarize()
    except Exception as e:
        print("❌ Script failed:")
        print(e)
        traceback.print_exc()
        exit(2)
