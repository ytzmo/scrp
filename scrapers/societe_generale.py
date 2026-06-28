"""
scrapers/societe_generale.py — Société Générale Career Scraper

SG utilise un site Algolia-powered (careers.societegenerale.com).
On passe par Playwright (headless Chromium) pour laisser le JS se charger
puis on extrait les cartes d'offres directement depuis le DOM rendu.
Utiliser un proxy sur le vps sinon le scraping ne marchera ps.

"""

import random
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from config import USER_AGENTS

BANK_NAME = "Société Générale"
_BASE_URL = "https://careers.societegenerale.com"

# URL pré-filtrée : type=INTERNSHIP, fonction=Markets & Finance (KJ697)
_SEARCH_URL = (
    f"{_BASE_URL}/rechercher"
    "?refinementList[jobType][0]=INTERNSHIP"
    "&refinementList[jobFunction][0]=KJ697"
)
_SEARCH_URL_STAGE = (
    f"{_BASE_URL}/rechercher"
    "?refinementList[jobType][0]=INTERNSHIP"
)


def _extract_cards(page) -> list[dict]:
    jobs = []
    # Les URL des offres SG contiennent toujours /offres-d-emploi/ ou /job-offers/
    links = page.locator("a[href*='/offres-d-emploi/'], a[href*='/job-offers/']").all()

    for a_tag in links:
        try:
            href  = a_tag.get_attribute("href") or ""
            url   = href if href.startswith("http") else f"{_BASE_URL}{href}"
            title = a_tag.inner_text().strip()

            if not title or not url or url == _BASE_URL:
                continue

            # On remonte l'arbre pour trouver la localisation (souvent dans le parent bloc)
            parent_text = a_tag.locator("xpath=../..").inner_text()
            parts = [p.strip() for p in parent_text.split('\n') if p.strip()]
            
            # En général : [Date, Titre, Contrat, Localisation, ...]
            location = "France"
            if len(parts) >= 4:
                location = parts[3]

            jobs.append({
                "title":        title,
                "bank":         BANK_NAME,
                "location":     location,
                "program_type": "Stage / Internship",
                "url":          url,
            })
        except Exception:
            continue
    return jobs


def scrape() -> list[dict]:
    ua = random.choice(USER_AGENTS)
    results: list[dict] = []
    seen_urls: set = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(user_agent=ua)
        page    = ctx.new_page()

        for search_url in [_SEARCH_URL, _SEARCH_URL_STAGE]:
            try:
                page.goto(search_url, wait_until="networkidle", timeout=45_000)
                # Attendre que les cartes apparaissent
                page.wait_for_timeout(3000)
            except PWTimeout:
                pass
            except Exception:
                continue

            for job in _extract_cards(page):
                if job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    results.append(job)

        browser.close()

    return results
