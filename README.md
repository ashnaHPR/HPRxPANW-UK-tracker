# Palo Alto Networks News Tracker 🛡️

This project tracks the latest news, blog posts, and security advisories from Palo Alto Networks using their public RSS feeds.

## Features

- Automated every 6 hours via GitHub Actions
- Pulls news from:
  - Palo Alto Research Center Blog
  - Security Advisories

## Output

All news is saved in `news.json` in the following format:

```json
[
  {
    "title": "Sample Article",
    "link": "https://...",
    "published": "Date string",
    "source": "Palo Alto Research"
  }
]
