"""
scrapers/bnp_paribas.py — BNP Paribas Career Scraper

Scrape la page dédiée CIB stages/internships sur group.bnpparibas.
Pagine automatiquement toutes les pages pour récupérer l'intégralité
des offres.

Stratégie :
  1. curl_cffi (rapide) — fonctionne depuis une IP résidentielle.
  2. Playwright (fallback) — contourne la protection anti-bot depuis
     les IPs datacenter (GitHub Actions).
"""

import random
import time
from bs4 import BeautifulSoup
from config import USER_AGENTS

BANK_NAME  = "BNP Paribas"
_BASE      = "https://group.bnpparibas"

# URL de la page listant les stages CIB de BNP Paribas
_PAGE_URL  = (
    f"{_BASE}/emploi-carriere/toutes-offres-emploi/"
    "stage/bnp-paribas-corporate-institutional-banking"
)

_MAX_PAGES = 30  # Garde-fou : ne jamais dépasser 30 pages


# ─────────────────────────────────────────────
# PARSING HTML (commun aux deux stratégies)
# ─────────────────────────────────────────────

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


def _get_max_page(html: str) -> int:
    """Extrait le numéro de la dernière page depuis la pagination HTML."""
    soup = BeautifulSoup(html, "html.parser")
    pag  = soup.find(class_="pagination")
    if not pag:
        return 1
    links = pag.find_all("a", attrs={"data-to": True})
    if not links:
        return 1
    return max(int(a["data-to"]) for a in links)


# ─────────────────────────────────────────────
# STRATÉGIE 1 : curl_cffi (rapide, IP rési)
# ─────────────────────────────────────────────

def _scrape_curl() -> list[dict]:
    from curl_cffi import requests as curl_req

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept":     "text/html,application/xhtml+xml",
        "Referer":    "https://group.bnpparibas/",
    }

    all_results: list[dict] = []
    seen_urls: set[str] = set()
    max_page = 1

    for page in range(1, _MAX_PAGES + 1):
        url = _PAGE_URL if page == 1 else f"{_PAGE_URL}?page={page}"
        resp = curl_req.get(
            url, headers=headers, impersonate="safari15_3", timeout=30
        )
        if resp.status_code != 200:
            break

        if page == 1:
            max_page = min(_get_max_page(resp.text), _MAX_PAGES)

        articles = _parse_articles(resp.text)
        if not articles:
            break

        for art in articles:
            if art["url"] not in seen_urls:
                seen_urls.add(art["url"])
                all_results.append(art)

        if page >= max_page:
            break
        time.sleep(random.uniform(0.5, 1.2))

    return all_results


# ─────────────────────────────────────────────
# STRATÉGIE 2 : Playwright (fallback datacenter)
# ─────────────────────────────────────────────

def _scrape_playwright() -> list[dict]:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    ua = random.choice(USER_AGENTS)
    all_results: list[dict] = []
    seen_urls: set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(user_agent=ua)
        page    = ctx.new_page()

        max_page = 1

        for page_num in range(1, _MAX_PAGES + 1):
            url = _PAGE_URL if page_num == 1 else f"{_PAGE_URL}?page={page_num}"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                # Attendre que les cartes d'offres se chargent
                page.wait_for_selector("article.card-offer", timeout=10_000)
            except PWTimeout:
                break
            except Exception:
                break

            html = page.content()

            if page_num == 1:
                max_page = min(_get_max_page(html), _MAX_PAGES)

            articles = _parse_articles(html)
            if not articles:
                break

            for art in articles:
                if art["url"] not in seen_urls:
                    seen_urls.add(art["url"])
                    all_results.append(art)

            if page_num >= max_page:
                break
            time.sleep(random.uniform(0.8, 1.5))

        browser.close()

    return all_results


# ─────────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────────

def scrape() -> list[dict]:
    # Essai 1 : curl_cffi (rapide, marche en local / IP résidentielle)
    try:
        results = _scrape_curl()
        if results:
            return results
    except Exception as e:
        print(f"  [BNP] curl_cffi échoué ({e}), fallback Playwright...")

    # Essai 2 : Playwright (contourne l'anti-bot datacenter)
    try:
        results = _scrape_playwright()
        if results:
            return results
    except Exception as e:
        print(f"  [BNP] Playwright échoué ({e})")

    return []
