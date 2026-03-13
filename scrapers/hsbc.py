"""
scrapers/hsbc.py — HSBC Career Scraper

HSBC utilise la plateforme Eightfold.ai (portal.careers.hsbc.com).
L'API JSON native /api/apply/v2/jobs est accessible avec curl_cffi
pour contourner le TLS fingerprinting.
"""

import random
from curl_cffi import requests as curl_req
from config import USER_AGENTS

BANK_NAME = "HSBC"

_API_URL  = "https://portal.careers.hsbc.com/api/apply/v2/jobs"
_JOB_BASE = "https://portal.careers.hsbc.com/careers"
_LIMIT    = 50

_PARAMS_BASE = {
    "domain":   "hsbc.com",
    "sort_by":  "newest",
    "from":     0,
    "num_jobs": _LIMIT,
}
_KEYWORDS = ["intern", "internship", "analyst", "summer", "graduate"]


def _fetch(keyword: str, offset: int) -> list:
    params = {**_PARAMS_BASE, "query": keyword, "from": offset}
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept":     "application/json",
        "Referer":    "https://portal.careers.hsbc.com/",
    }
    try:
        resp = curl_req.get(
            _API_URL,
            params=params,
            headers=headers,
            impersonate="chrome110",
            timeout=25,
        )
        resp.raise_for_status()
        return resp.json().get("positions", [])
    except Exception:
        return []


def scrape() -> list[dict]:
    seen_ids: set = set()
    jobs: list[dict] = []

    for kw in _KEYWORDS:
        offset = 0
        while True:
            positions = _fetch(kw, offset)
            if not positions:
                break
            for pos in positions:
                pid = pos.get("id", "")
                if not pid or pid in seen_ids:
                    continue
                seen_ids.add(pid)
                url = pos.get("canonicalPositionUrl", "") or f"{_JOB_BASE}?pid={pid}"
                jobs.append({
                    "title":        pos.get("name", "").strip(),
                    "bank":         BANK_NAME,
                    "location":     pos.get("location", ""),
                    "program_type": pos.get("type", ""),
                    "url":          url,
                })
            if len(positions) < _LIMIT:
                break
            offset += _LIMIT

    return jobs
