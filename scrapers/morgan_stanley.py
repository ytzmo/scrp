"""
scrapers/morgan_stanley.py — Morgan Stanley Career Scraper

Utilise le endpoint Workday CXS (ms.wd5.myworkdayjobs.com/External).
L'API JSON native évite tout Playwright.
"""

import random
import requests
from config import USER_AGENTS

BANK_NAME = "Morgan Stanley"

_API_URL  = "https://ms.wd5.myworkdayjobs.com/wday/cxs/ms/External/jobs"
_BASE_URL = "https://ms.wd5.myworkdayjobs.com/en-US/External"
_HEADERS_EXTRA = {
    "Accept":       "application/json",
    "Content-Type": "application/json",
    "Referer":      "https://ms.wd5.myworkdayjobs.com/External",
}
_KEYWORDS = ["intern", "analyst", "summer", "graduate"]
_LIMIT    = 20


def _fetch_page(keyword: str, offset: int, session: requests.Session) -> list:
    payload = {
        "searchText":    keyword,
        "appliedFacets": {},
        "limit":         _LIMIT,
        "offset":        offset,
    }
    try:
        resp = session.post(_API_URL, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json().get("jobPostings", [])
    except Exception:
        return []


def scrape() -> list[dict]:
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        **_HEADERS_EXTRA,
    })

    seen_paths: set = set()
    jobs: list[dict] = []

    for kw in _KEYWORDS:
        offset = 0
        while offset < 400:
            postings = _fetch_page(kw, offset, session)
            if not postings:
                break
            for p in postings:
                path = p.get("externalPath", "")
                if not path or path in seen_paths:
                    continue
                seen_paths.add(path)
                url = f"{_BASE_URL}{path}"
                jobs.append({
                    "title":        p.get("title", "").strip(),
                    "bank":         BANK_NAME,
                    "location":     p.get("locationsText", ""),
                    "program_type": p.get("jobPostingType", ""),
                    "url":          url,
                })
            # Workday renvoie exactement `limit` résultats si d'autres existent
            if len(postings) < _LIMIT:
                break
            offset += _LIMIT

    return jobs
