def fetch_and_generate_news():
    now_utc = datetime.utcnow()
    now_str = now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')
    cutoff = now_utc - timedelta(days=1)

    header = f"# 📰 Palo Alto Networks News from Selected Media\n\n" \
             f"![Last Updated](https://img.shields.io/badge/Last%20Updated-{now_utc.strftime('%Y--%m--%d_%H%M')}--UTC-blue)\n\n"

    table_header = "| Date | Publication | Headline | Summary |\n|---|---|---|---|\n"

    national_rows = []
    trade_rows = []
    paloalto_rows = []
    spokesperson_rows = {person: [] for person in spokespersons}

    for pub_name, feed_url in topics.items():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            published = entry.get('published', '') or entry.get('updated', '')
            try:
                published_dt = datetime(*entry.published_parsed[:6])
            except:
                continue

            if published_dt < cutoff:
                continue

            title = clean_html(entry.get('title', 'No Title'))
            summary = clean_html(entry.get('summary', '')) if 'summary' in entry else ''
            content = ''
            if 'content' in entry and isinstance(entry['content'], list):
                content = clean_html(entry['content'][0].get('value', ''))

            full_text = f"{title} {summary} {content}"
            link = entry.get('link', '#')

            row = f"| {published_dt.strftime('%Y-%m-%d')} | {pub_name} | [{title}]({link}) | {summary[:200]}... |\n"

            for person in spokespersons:
                if person.lower() in full_text.lower():
                    spokesperson_rows[person].append(row)

            if contains_palo_alto(full_text):
                paloalto_rows.append(row)
            elif pub_name in national_outlets:
                national_rows.append(row)
            elif pub_name in trade_outlets:
                trade_rows.append(row)

    result = header

    if paloalto_rows:
        result += "## 🔍 Palo Alto Networks Mentions\n" + table_header + "".join(paloalto_rows) + "\n"

    if any(spokesperson_rows.values()):
        result += "## 🧑‍💼 Spokesperson Mentions\n"
        for person, rows in spokesperson_rows.items():
            if rows:
                result += f"### {person}\n" + table_header + "".join(rows) + "\n"

    if national_rows:
        result += "## 🗞️ National Media Coverage\n" + table_header + "".join(national_rows) + "\n"

    if trade_rows:
        result += "## 🛠️ Trade Media Coverage\n" + table_header + "".join(trade_rows) + "\n"

    return result
