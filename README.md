# DealDigger

🔎 **DealDigger** is a web app for comparing product prices between Blinkit and Zepto.

## Features

✅ Search for any product  
✅ Scrape real-time data from Blinkit and Zepto  
✅ Display matched products side by side  
✅ Highlight which platform has cheaper price  
✅ Expandable sections to show all scraped products from each platform

## Tech Stack

- Python
- Selenium
- Streamlit
- TheFuzz (fuzzy string matching)

## How to Run Locally

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Run the app**

```bash
streamlit run app.py
```

## Notes

- Scraping depends on current website structures and may need updates if sites change.
- Default location for scraping is set to Delhi.
