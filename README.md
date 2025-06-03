# 🛡️ Palo Alto Networks News Bot

This GitHub Action automatically fetches and summarizes daily news related to Palo Alto Networks, including:

- 📰 General company news
- 🔥 Firewall technology updates
- 🧠 Threat intelligence from Unit 42

## ⏱️ Schedule

- Runs **daily at 12:00 UTC**
- Outputs to [`news/paloalto_news.md`](news/paloalto_news.md)

## 💡 Features

- Pulls from curated RSS feeds (Google News + Unit 42)
- Uses OpenAI GPT-4 for clean, concise summaries
- Keeps your repo updated with the latest in cybersecurity trends

## 🔐 Setup

1. Go to **Repository Settings → Secrets** and add:
