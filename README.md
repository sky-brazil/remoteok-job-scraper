# RemoteOK Job Scraper - Python + Selenium

Production-style web scraping project that collects remote developer jobs from [RemoteOK](https://remoteok.com/remote-dev-jobs) and exports clean, analysis-ready CSV data.

This repository is curated as a professional portfolio sample for clients, recruiters, and teams evaluating practical automation skills.

## Why this project is business-relevant

- Demonstrates end-to-end data extraction workflow design.
- Uses browser automation for JavaScript-heavy pages.
- Produces structured output ready for analytics, BI dashboards, and lead pipelines.
- Includes command-line controls to adapt scope and output quickly.

## Core capabilities

- Selenium-based scraping with configurable headless/headed execution.
- Smart extraction of:
  - Job title
  - Company
  - Location
  - Salary (when available)
  - Canonical job URL
- Multi-page scraping support via CLI (`--pages`).
- Duplicate row handling for cleaner datasets.
- Logging designed for troubleshooting and demo sessions.

## Tech stack

- Python 3
- Selenium WebDriver
- webdriver-manager

## Repository structure

```text
.
├─ remote_jobs_scraper_selenium.py   # Main scraper script
├─ remote_jobs_selenium.csv          # Example generated output
├─ requirements.txt                  # Python dependencies
└─ README.md
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python remote_jobs_scraper_selenium.py --pages 1 --output remote_jobs_selenium.csv
```

## Command-line options

```bash
python remote_jobs_scraper_selenium.py \
  --base-url "https://remoteok.com/remote-dev-jobs" \
  --pages 2 \
  --output "remote_jobs_selenium.csv" \
  --verbose
```

Available flags:

- `--base-url`: starting RemoteOK URL
- `--pages`: number of paginated pages to process
- `--output`: destination CSV path
- `--headed`: run with visible browser window
- `--verbose`: enable debug-level logs

## CSV schema

The generated file includes:

| Column | Description |
|---|---|
| `title` | Job role title |
| `company` | Hiring company name |
| `location` | Location text from listing |
| `salary` | Salary range when present |
| `url` | Direct URL to job listing |

## Professional quality notes

- Clear code structure with focused functions.
- Typed records for predictable data contracts.
- Reusable CLI interface for quick adaptation.
- Practical logging for maintainability and handoff.

---

If you are hiring for Python automation, scraping, or data pipeline work, this project reflects a production-minded approach to reliable data collection.
