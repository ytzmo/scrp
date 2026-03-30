"""
scrapers/natixis.py — Natixis Career Scraper

Utilise l'API WordPress BPCE sur recrutement.natixis.com.
Endpoint : POST /app/wp-json/bpce/v1/search/jobs
Retourne un JSON avec data.items contenant titre, lien, localisation, etc.
"""

import random
import requests
from config import USER_AGENTS

BANK_NAME = "Natixis"

_API_URL  = "https://recrutement.natixis.com/app/wp-json/bpce/v1/search/jobs"
_BASE_URL = "https://recrutement.natixis.com"
_PAGE_SIZE = 20


def _fetch_page(offset: int, session: requests.Session) -> tuple[list, int]:
    """Retourne (items, total) pour la page courante."""
    payload = {
        "lang":               "en",
        "keyword":            "",
        "tax_sector":         "",
        "tax_contract":       "",
        "tax_place":          "",
        "tax_job":            "",
        "tax_experience":     "",
        "tax_degree":         "",
        "tax_brands":         "",
        "tax_department":     "",
        "tax_city":           "",
        "tax_country":        "",
        "tax_channel":        "",
        "jobcode":            "",
        "tax_community_job":  "",
        "external":           False,
        "userID":             "",
        "from":               offset,
        "size":               _PAGE_SIZE,
        "map_mode":           "gmap",
    }
    try:
        resp = session.post(_API_URL, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        items = data.get("items", [])
        total = data.get("total", 0)
        return items, total
    except Exception:
        return [], 0


def scrape() -> list[dict]:
    session = requests.Session()
    session.headers.update({
        "User-Agent":   random.choice(USER_AGENTS),
        "Accept":       "application/json",
        "Content-Type": "application/json",
        "Referer":      "https://recrutement.natixis.com/en/our-job-offers",
    })

    seen_urls: set = set()
    jobs: list[dict] = []

    offset = 0
    while True:
        items, total = _fetch_page(offset, session)
        if not items:
            break

        for item in items:
            title = item.get("title", "").strip()
            # Lien relatif ou absolu
            link_obj = item.get("link", {})
            href = link_obj.get("url", "") if isinstance(link_obj, dict) else ""
            if not href:
                continue
            url = href if href.startswith("http") else f"{_BASE_URL}{href}"
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Localisation
            location = item.get("localisation", "")
            if not location:
                locs = item.get("localisations", [])
                if locs and isinstance(locs, list):
                    location = locs[0].get("city", "France")

            # Type de contrat
            contracts = item.get("contract", [])
            program_type = contracts[0] if contracts else ""

            jobs.append({
                "title":        title,
                "bank":         BANK_NAME,
                "location":     location,
                "program_type": program_type,
                "url":          url,
            })

        offset += _PAGE_SIZE
        if offset >= total:
            break

    return jobs
