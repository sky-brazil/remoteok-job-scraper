"""RemoteOK job scraper with a portfolio-ready CLI interface."""

from __future__ import annotations

import argparse
import csv
import logging
import time
from pathlib import Path
from typing import List, TypedDict
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

LOGGER = logging.getLogger(__name__)
JOB_ROW_SELECTOR = "tr.job, tr[data-id][data-href]"
DEFAULT_BASE_URL = "https://remoteok.com/remote-dev-jobs"


class JobRecord(TypedDict):
    title: str
    company: str
    location: str
    salary: str
    url: str


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def create_driver(headless: bool = True) -> webdriver.Chrome:
    """Create and return a configured Chrome WebDriver instance."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )

    return webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options,
    )


def _safe_text(row, selector: str) -> str:
    try:
        return row.find_element(By.CSS_SELECTOR, selector).text.strip()
    except NoSuchElementException:
        return ""


def scrape_remoteok(driver: webdriver.Chrome, url: str, wait_seconds: int = 15) -> List[JobRecord]:
    """Scrape one RemoteOK page and return normalized job records."""
    driver.get(url)

    wait = WebDriverWait(driver, wait_seconds)
    try:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr.job, tr[data-id]")))
    except TimeoutException:
        LOGGER.warning("No job rows loaded for URL: %s", url)
        return []

    time.sleep(1.5)
    rows = driver.find_elements(By.CSS_SELECTOR, JOB_ROW_SELECTOR)
    LOGGER.debug("Rows detected on page: %s", len(rows))

    jobs: List[JobRecord] = []
    for row in rows:
        row_classes = row.get_attribute("class") or ""
        if "closed" in row_classes or "expand" in row_classes:
            continue

        data_href = row.get_attribute("data-href") or row.get_attribute("data-url") or ""
        job_url = urljoin("https://remoteok.com", data_href) if data_href else ""

        title = _safe_text(
            row,
            "td.company.position.company_and_position h2[itemprop='title'], h2[itemprop='title']",
        )
        company = _safe_text(
            row,
            "td.company.position.company_and_position h3[itemprop='name'], h3[itemprop='name']",
        )
        location = _safe_text(row, "div.location")
        salary = _safe_text(row, "div.salary")

        if not title and not company:
            continue

        jobs.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "url": job_url,
            }
        )

    LOGGER.info("Collected %s jobs from %s", len(jobs), url)
    return jobs


def deduplicate_jobs(jobs: List[JobRecord]) -> List[JobRecord]:
    """Keep first occurrence of each unique URL/title/company tuple."""
    seen = set()
    unique_jobs: List[JobRecord] = []

    for job in jobs:
        signature = (job["url"], job["title"], job["company"])
        if signature in seen:
            continue
        seen.add(signature)
        unique_jobs.append(job)

    if len(unique_jobs) != len(jobs):
        LOGGER.info("Removed %s duplicate rows.", len(jobs) - len(unique_jobs))
    return unique_jobs


def scrape_multiple_pages(
    driver: webdriver.Chrome,
    base_url: str,
    pages: int = 1,
    sleep_seconds: float = 1.5,
) -> List[JobRecord]:
    all_jobs: List[JobRecord] = []

    for page in range(1, pages + 1):
        page_url = base_url if page == 1 else f"{base_url}?pg={page}"
        LOGGER.info("Scraping page %s/%s: %s", page, pages, page_url)

        jobs = scrape_remoteok(driver, page_url)
        all_jobs.extend(jobs)

        if page < pages:
            time.sleep(sleep_seconds)

    return deduplicate_jobs(all_jobs)


def save_to_csv(jobs: List[JobRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["title", "company", "location", "salary", "url"]

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(jobs)

    LOGGER.info("Saved %s jobs to %s", len(jobs), output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape remote developer jobs from RemoteOK and export CSV."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="RemoteOK URL to scrape (default: remote developer feed).",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Number of pages to scrape using ?pg= pagination (default: 1).",
    )
    parser.add_argument(
        "--output",
        default="remote_jobs_selenium.csv",
        help="Output CSV path (default: remote_jobs_selenium.csv).",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run with visible browser instead of headless mode.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging for troubleshooting.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(verbose=args.verbose)

    if args.pages < 1:
        raise ValueError("--pages must be at least 1.")

    output_path = Path(args.output).resolve()
    driver = create_driver(headless=not args.headed)

    try:
        jobs = scrape_multiple_pages(driver, base_url=args.base_url, pages=args.pages)
        save_to_csv(jobs, output_path)
    finally:
        driver.quit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
