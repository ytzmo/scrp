"""
scrapers/credit_agricole.py — Crédit Agricole CIB Career Scraper

CACIB utilise groupecreditagricole.jobs (ASP.NET server-rendered).
L'URL est pré-filtrée :
  - métier = Marchés / Finance (170466)
  - contrat = Stage (579)
  - marque = CACIB (124-4)

Un simple requests + BeautifulSoup suffit car la page est rendue côté serveur.
"""

import random
import requests
from bs4 import BeautifulSoup
from config import USER_AGENTS

BANK_NAME  = "Crédit Agricole"
_BASE_URL  = "https://groupecreditagricole.jobs"

# URL ciblée : stages CIB
_PAGE_URL  = (
    f"{_BASE_URL}/fr/nos-offres/"
    "metiers/170466/contrats/579/marques/124-4/"
)


def _parse_page(html: str) -> list[dict]:
    soup     = BeautifulSoup(html, "html.parser")
    articles = soup.find_all("article", class_=lambda c: c and "card" in c and "offer" in c)
    results  = []
    for art in articles:
        title_tag = art.find("h3", class_=lambda c: c and "title" in c)
        if title_tag:
            a_tag = title_tag.find("a")
        else:
            a_tag = art.find("a")
        if not a_tag:
            continue
        href  = a_tag.get("href", "")
        url   = href if href.startswith("http") else f"{_BASE_URL}{href}"
        title = a_tag.get_text(strip=True)
        loc_tag  = art.find("li", class_=lambda c: c and "location" in c)
        location = loc_tag.get_text(strip=True) if loc_tag else "France"
        results.append({
            "title":        title,
            "bank":         BANK_NAME,
            "location":     location,
            "program_type": "Stage / Internship",
            "url":          url,
        })
    return results


def scrape() -> list[dict]:
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept":     "text/html,application/xhtml+xml",
        "Referer":    _BASE_URL,
    }
    session = requests.Session()
    session.headers.update(headers)

    results:    list[dict] = []
    seen_urls:  set        = set()
    page_num    = 1

    while True:
        url = f"{_PAGE_URL}?page={page_num}" if page_num > 1 else _PAGE_URL
        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
        except Exception:
            break

        jobs = _parse_page(resp.text)
        if not jobs:
            break

        added = 0
        for job in jobs:
            if job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                results.append(job)
                added += 1

        # Arrêt si aucune nouvelle offre (page vide ou doublon de pagination)
        if added == 0:
            break
        page_num += 1

    return results
