"""
scrapers/bnp_paribas.py — BNP Paribas Career Scraper

BNP expose un endpoint Drupal AJAX sur group.bnpparibas qui retourne
du HTML encapsulé dans du JSON.  curl_cffi impersonne Safari pour
passer le TLS fingerprinting.
On scrape directement la page dédiée CIB (type=28 = stages/internships).
"""

import random
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_req
from config import USER_AGENTS

BANK_NAME  = "BNP Paribas"
_BASE      = "https://group.bnpparibas"

# URL de la page listant les stages CIB de BNP Paribas
_PAGE_URL  = (
    f"{_BASE}/emploi-carriere/toutes-offres-emploi/"
    "stage/bnp-paribas-corporate-institutional-banking"
)

# Endpoint AJAX alternatif (JSON wrapping HTML) — utilisé en fallback
_AJAX_URL  = (
    f"{_BASE}/en/careers/all-job-offers"
    "?json=1&form[q]=analyst&form[type][]=28"
)


def _parse_articles(html: str) -> list[dict]:
    soup     = BeautifulSoup(html, "html.parser")
    articles = soup.find_all("article", class_=lambda c: c and "card-offer" in c)
    results  = []
    for art in articles:
        a_tag = art.find("a", class_="card-link") or art.find("a")
        if not a_tag:
            continue
        href  = a_tag.get("href", "")
        url   = href if href.startswith("http") else f"{_BASE}{href}"
        h3    = art.find("h3")
        title = h3.get_text(strip=True) if h3 else a_tag.get_text(strip=True)
        # Localisation éventuelle
        loc_tag  = art.find(class_=lambda c: c and "location" in c.lower()) if art else None
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
        "Referer":    "https://group.bnpparibas/",
    }
    # Essai 1 : page HTML directe
    try:
        resp = curl_req.get(
            _PAGE_URL, headers=headers, impersonate="safari15_3", timeout=30
        )
        if resp.status_code == 200:
            results = _parse_articles(resp.text)
            if results:
                return results
    except Exception:
        pass

    # Essai 2 : endpoint AJAX (JSON wrapping HTML)
    try:
        ajax_headers = {**headers, "X-Requested-With": "XMLHttpRequest"}
        resp = curl_req.get(
            _AJAX_URL, headers=ajax_headers, impersonate="safari15_3", timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            html_fragment = data.get("html", "")
            return _parse_articles(html_fragment)
    except Exception:
        pass

    return []
