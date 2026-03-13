"""
scrapers/jpmorgan.py — J.P. Morgan Career Scraper

Utilise l'API Oracle HCM REST (jpmc.fa.oraclecloud.com) qui alimente
le portail campus CX_1001 de JPMorgan Chase.
"""

import random
import requests
from config import USER_AGENTS

BANK_NAME = "J.P. Morgan"

_API_BASE = (
    "https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/"
    "recruitingCEJobRequisitions"
    "?onlyData=true"
    "&expand=requisitionList.workLocation"
)
_BASE_JOB_URL = (
    "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience"
    "/en/sites/CX_1001/job/"
)

# Mots-clés couvrant internships, analyst programs, etc.
_KEYWORDS = ["intern", "analyst", "associate", "summer", "graduate"]


def _fetch(keyword: str, headers: dict) -> list:
    finder = (
        f"findReqs;siteNumber=CX_1001,limit=200,"
        f'keyword="{keyword}",sortBy=POSTING_DATE_DESC'
    )
    url = f"{_API_BASE}&finder={finder}"
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            return []
        return items[0].get("requisitionList", [])
    except Exception:
        return []


def scrape() -> list[dict]:
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept":     "application/json",
        "Referer":    "https://careers.jpmorgan.com/",
    }

    seen_ids: set = set()
    jobs: list[dict] = []

    for kw in _KEYWORDS:
        for r in _fetch(kw, headers):
            job_id = r.get("Id")
            if not job_id or job_id in seen_ids:
                continue
            seen_ids.add(job_id)
            url = f"{_BASE_JOB_URL}{job_id}"
            work_locations = r.get("workLocation", [])
            location = r.get("PrimaryLocation", "")
            if not location and isinstance(work_locations, list) and work_locations:
                location = work_locations[0].get("LocationName", "")
            jobs.append({
                "title":        r.get("Title", "").strip(),
                "bank":         BANK_NAME,
                "location":     location,
                "program_type": r.get("Category", "Campus"),
                "url":          url,
            })
    return jobs
