"""
scrapers/bofa.py — Bank of America Career Scraper

Utilise le endpoint Workday CXS (ghr.wd1.myworkdayjobs.com).
"""

import random
import requests
from config import USER_AGENTS

BANK_NAME = "Bank of America"

_API_URL  = "https://ghr.wd1.myworkdayjobs.com/wday/cxs/ghr/Lateral-US/jobs"
_BASE_URL = "https://ghr.wd1.myworkdayjobs.com/en-US/Lateral-US"
_LIMIT    = 20
_KEYWORDS = ["intern", "analyst", "summer", "graduate"]


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
        "User-Agent":   random.choice(USER_AGENTS),
        "Accept":       "application/json",
        "Content-Type": "application/json",
        "Referer":      "https://ghr.wd1.myworkdayjobs.com/",
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
            if len(postings) < _LIMIT:
                break
            offset += _LIMIT

    return jobs
