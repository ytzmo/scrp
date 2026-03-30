"""
scrapers/euronext.py — Euronext Career Scraper

Utilise le endpoint Workday CXS (hrhub.wd3.myworkdayjobs.com).
Même pattern que bofa.py / morgan_stanley.py.
"""

import random
import requests
from config import USER_AGENTS

BANK_NAME = "Euronext"

_API_URL  = "https://hrhub.wd3.myworkdayjobs.com/wday/cxs/hrhub/Euronext_Career_Page/jobs"
_BASE_URL = "https://hrhub.wd3.myworkdayjobs.com/en-US/Euronext_Career_Page"
_LIMIT    = 20


def _fetch_page(offset: int, session: requests.Session) -> list:
    payload = {
        "appliedFacets": {},
        "limit":         _LIMIT,
        "offset":        offset,
        "searchText":    "",
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
        "Referer":      "https://hrhub.wd3.myworkdayjobs.com/",
    })

    seen_paths: set = set()
    jobs: list[dict] = []

    offset = 0
    while offset < 400:
        postings = _fetch_page(offset, session)
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
