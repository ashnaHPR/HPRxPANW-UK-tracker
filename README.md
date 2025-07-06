# 🔐 Palo Alto Networks Coverage

## 📌 All PANW Mentions Today

_No articles found._

## 📰 National Coverage

_No articles found._

## 📘 Trade Coverage

_No articles found._


---

## Technical Summary

This repository hosts an automated news coverage tracker for Palo Alto Networks, implemented in Python and integrated with GitHub Actions for continuous operation.

The system queries the GNews API every 4 hours to pull the latest articles containing Palo Alto Networks-related keywords and mentions of specific spokespeople. Articles are filtered to ensure timeliness based on BST timezone, and source classification is performed via a comprehensive domain mapping strategy that segments outlets into national and trade media categories.

Results are formatted into Markdown tables with clickable headlines, publication timestamps, and article summaries, then committed back to the repository's `README.md`. This creates a continuously updated, version-controlled media monitoring dashboard accessible to stakeholders at any time.

Key technical highlights include:

- Robust timezone-aware data filtering  
- Domain-driven source classification for granular insights  
- Automated CI/CD pipeline with GitHub Actions for scheduled updates  
- Modular design allowing easy extension with new keywords or sources  

This setup provides an efficient, scalable, and transparent solution for real-time media intelligence tailored to Palo Alto Networks’ coverage needs.
