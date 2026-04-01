"""
scrapers/bnp_paribas.py — BNP Paribas Career Scraper

Scrape la page dédiée CIB stages/internships sur group.bnpparibas.
Pagine automatiquement toutes les pages pour récupérer l'intégralité
des offres.

group.bnpparibas est protégé par Akamai qui bloque les IPs datacenter.
curl_cffi avec impersonation TLS fonctionne depuis une IP résidentielle.
Depuis GitHub Actions, on route le trafic via Tor (SOCKS5 proxy sur
127.0.0.1:9050) pour obtenir une IP non-datacenter.
"""

import os
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

# Impersonations à tester dans l'ordre
_BROWSERS = ["safari15_3", "chrome110", "chrome116", "safari17_0"]

# Proxy Tor SOCKS5 (démarré par GitHub Actions)
_TOR_PROXY = os.environ.get("TOR_PROXY", "")


# ─────────────────────────────────────────────
# PARSING HTML
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
# SCRAPING AVEC curl_cffi (+ proxy optionnel)
# ─────────────────────────────────────────────

def _scrape_with_browser(browser_id: str, proxy: str = "") -> list[dict]:
    """
    Scrape toutes les pages en utilisant une impersonation TLS donnée.
    Si proxy est fourni (ex: socks5://127.0.0.1:9050), route via ce proxy.
    Retourne [] si la première page échoue.
    """
    from curl_cffi import requests as curl_req

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept":     "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer":    "https://group.bnpparibas/emploi-carriere/",
        "Cache-Control": "no-cache",
        "Connection":    "keep-alive",
    }

    kwargs = {
        "headers":     headers,
        "impersonate": browser_id,
        "timeout":     45,
    }
    if proxy:
        kwargs["proxy"] = proxy

    all_results: list[dict] = []
    seen_urls: set[str] = set()
    max_page = 1

    for page in range(1, _MAX_PAGES + 1):
        url = _PAGE_URL if page == 1 else f"{_PAGE_URL}?page={page}"
        resp = curl_req.get(url, **kwargs)

        if resp.status_code != 200:
            if page == 1:
                via = f" via proxy {proxy}" if proxy else ""
                print(f"  [BNP] {browser_id}{via}: HTTP {resp.status_code}")
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
# POINT D'ENTRÉE
# ─────────────────────────────────────────────

def scrape() -> list[dict]:
    # ── Étape 1 : essai direct (marche depuis IP résidentielle) ──
    for browser_id in _BROWSERS:
        try:
            results = _scrape_with_browser(browser_id)
            if results:
                return results
        except Exception as e:
            print(f"  [BNP] {browser_id} direct: {e}")
            continue

    # ── Étape 2 : essai via proxy Tor (si disponible) ──
    if _TOR_PROXY:
        print(f"  [BNP] Essai via Tor ({_TOR_PROXY})...")
        for browser_id in _BROWSERS:
            try:
                results = _scrape_with_browser(browser_id, proxy=_TOR_PROXY)
                if results:
                    print(f"  [BNP] ✅ Succès via Tor avec {browser_id}")
                    return results
            except Exception as e:
                print(f"  [BNP] {browser_id} via Tor: {e}")
                continue

    print("  [BNP] ⚠️ Toutes les méthodes ont échoué")
    return []
