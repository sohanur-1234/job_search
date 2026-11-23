# RA Circular Notifier

Automated Research Assistant (RA) and research opportunity monitoring pipeline for Bangladeshi universities, labs, research institutes, and LinkedIn posts.

## Folder Structure

```text
ra-job-notifier/
├── .github/
│   └── workflows/
│       └── scraper.yml
├── scraper.py
├── requirements.txt
├── seen_links.json
├── opportunities.json
└── README.md
```

## Setup Instructions

1. Push the contents of the `ra-job-notifier/` folder to a GitHub repository.
2. Go to **Settings > Secrets and variables > Actions** in your repository and add these secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `GOOGLE_API_KEY`
   - `GOOGLE_CSE_ID`
   - `GEMINI_API_KEY`
3. Open the **Actions** tab and trigger **RA Circular Notifier** via **Run workflow** to test.
