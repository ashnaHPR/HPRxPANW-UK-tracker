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
        return f"[Error in summarization: {e}]"

def fetch_and_summarize():
    os.makedirs("news", exist_ok=True)
    output = [f"# 📰 Palo Alto Networks News Summary\n\n_Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}_\n"]

    table_header = "| Source | Title | Summary |\n|---|---|---|\n"
    output.append(table_header)

    for title, data in topics.items():
        feed = feedparser.parse(data['url'])
        entries = feed.entries[:5]

        if not entries:
            output.append(f"| {title} | _No articles found._ |  |\n")
            continue

        for entry in entries:
            summary_text = clean_html(entry.get('summary', '')) or entry.get('title', '')
            summarized = summarize(summary_text)
            # Format date if available
            published = entry.get('published', '') or entry.get('updated', '')
            # Some feeds have dates like 'Tue, 02 Jun 2025 10:00:00 GMT' - convert to YYYY-MM-DD if possible
            try:
                dt_obj = datetime(*entry.published_parsed[:6])
                published_fmt = dt_obj.strftime("%b %d, %Y")
            except Exception:
                published_fmt = published

            title_md = f"[{entry.title}]({entry.link})"
            # Append markdown table row
            output.append(f"| {title} {published_fmt} | {title_md} | {summarized} |\n")

    with open("news/paloalto_news.md", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    # Also update README.md with the same news summary
    with open("README.md", "w", encoding="utf-8") as f:
        readme_intro = (
            "# Palo Alto Networks Cybersecurity News Tracker\n\n"
            "This README is updated every 6 hours with the latest Palo Alto Networks news summarized by GPT-4.\n\n"
        )
        f.write(readme_intro)
        f.write("\n".join(output))

if __name__ == "__main__":
    try:
        fetch_and_summarize()
    except Exception as e:
        print("❌ Script failed with an error:")
        print(e)
        traceback.print_exc()
        exit(1)
