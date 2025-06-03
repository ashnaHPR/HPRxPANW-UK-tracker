# 📰 Daily Palo Alto News Scraper

This repository contains an automated GitHub Actions workflow that scrapes daily news articles related to **Palo Alto** and publishes a summarized digest.

## 🔧 How It Works

- ✅ Uses Python with `newspaper3k`, `BeautifulSoup`, and `OpenAI` (optional for summarization).
- 🕒 Runs daily at 8 AM UTC.
- 📄 Updates `news/paloalto_news.md` with new headlines and summaries.

## 📁 File Structure
