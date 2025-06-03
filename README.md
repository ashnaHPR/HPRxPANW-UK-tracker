# 🛡️ Palo Alto Networks News Bot

A GitHub Action that automatically fetches and summarizes daily cybersecurity news related to **Palo Alto Networks**.

## 🔧 What It Does

- Pulls news from Google News and Unit 42
- Summarizes each article using GPT-4 (OpenAI)
- Outputs to `news/paloalto_news.md` daily

## ⏱️ Schedule

- Runs every day at 12:00 UTC
- Can also be triggered manually from the Actions tab

## 🔐 Setup

1. In your repo, go to `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
2. Add:
