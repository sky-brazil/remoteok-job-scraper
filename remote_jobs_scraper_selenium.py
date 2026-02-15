import csv
import time
from typing import List, Dict
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def create_driver(headless: bool = True) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    # user-agent "de navegador normal"
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options,
    )
    return driver


def scrape_remoteok(driver: webdriver.Chrome, url: str) -> List[Dict]:
    driver.get(url)

    wait = WebDriverWait(driver, 15)
    wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "tr.job, tr[data-id]")
        )
    )

    time.sleep(2)

    jobs: List[Dict] = []

    # cada vaga é um <tr> com class job e data-id
    rows = driver.find_elements(By.CSS_SELECTOR, "tr.job, tr[data-id][data-href]")

    print(f"DEBUG: encontrei {len(rows)} linhas de vaga na página")

    for row in rows:
        row_classes = row.get_attribute("class") or ""
        if "closed" in row_classes or "expand" in row_classes:
            # ignora linha de expansão / descrição, etc.
            continue

        # monta URL a partir do data-href
        data_href = row.get_attribute("data-href") or row.get_attribute("data-url") or ""
        if data_href and data_href.startswith("/"):
            job_url = "https://remoteok.com" + data_href
        else:
            job_url = ""

        title = ""
        company = ""
        location = ""
        salary = ""

        try:
            title_el = row.find_element(
                By.CSS_SELECTOR,
                "td.company.position.company_and_position h2[itemprop='title'], h2[itemprop='title']",
            )
            title = title_el.text.strip()
        except Exception:
            pass

        try:
            company_el = row.find_element(
                By.CSS_SELECTOR,
                "td.company.position.company_and_position h3[itemprop='name'], h3[itemprop='name']",
            )
            company = company_el.text.strip()
        except Exception:
            pass

        try:
            loc_el = row.find_element(By.CSS_SELECTOR, "div.location")
            location = loc_el.text.strip()
        except Exception:
            pass

        try:
            salary_el = row.find_element(By.CSS_SELECTOR, "div.salary")
            salary = salary_el.text.strip()
        except Exception:
            pass

        # se não tiver pelo menos título e empresa, não vale como vaga
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

    print(f"DEBUG: jobs extraídos = {len(jobs)}")
    return jobs


def scrape_multiple_pages(
    driver: webdriver.Chrome,
    base_url: str,
    pages: int = 1,
    sleep_seconds: int = 2,
) -> List[Dict]:
    all_jobs: List[Dict] = []

    for page in range(1, pages + 1):
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}?pg={page}"

        print(f"Scraping página {page}: {url}")
        jobs = scrape_remoteok(driver, url)
        print(f"Encontradas {len(jobs)} vagas nesta página.")
        all_jobs.extend(jobs)

        time.sleep(sleep_seconds)

    return all_jobs


def save_to_csv(jobs: List[Dict], filename: str = "remote_jobs_selenium.csv") -> None:
    if not jobs:
        print("Nenhuma vaga encontrada.")
        return

    # sempre salvar na mesma pasta deste arquivo .py
    script_dir = Path(__file__).parent.resolve()
    out_path = script_dir / filename

    print("Salvando CSV em:", out_path)

    fieldnames = ["title", "company", "location", "salary", "url"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(jobs)

    print(f"Salvo {len(jobs)} vagas em {out_path}")


def main():
    base_url = "https://remoteok.com/remote-dev-jobs"  # ajuste o filtro que quiser
    pages_to_scrape = 1  # pode mudar pra 2, 3...

    driver = create_driver(headless=True)

    try:
        jobs = scrape_multiple_pages(driver, base_url, pages=pages_to_scrape)
        save_to_csv(jobs, "remote_jobs_selenium.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
