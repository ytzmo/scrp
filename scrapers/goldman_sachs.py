"""
scrapers/goldman_sachs.py — Goldman Sachs Career Scraper

Utilise l'API Oracle HCM REST (hdpc.fa.us2.oraclecloud.com) qui expose
les offres du site Campus Hiring de Goldman Sachs.
Pas de Playwright nécessaire — pure requête HTTP.
"""

import random
import requests
from config import USER_AGENTS

BANK_NAME = "Goldman Sachs"

# Oracle HCM endpoint public
_API_URL = (
    "https://hdpc.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/"
    "recruitingCEJobRequisitions"
    "?onlyData=true"
    "&expand=requisitionList.workLocation"
    "&finder=findReqs;siteNumber=CampusHiring,limit=200,sortBy=POSTING_DATE_DESC"
)
_BASE_JOB_URL = (
    "https://hdpc.fa.us2.oraclecloud.com/hcmUI/CandidateExperience"
    "/en/sites/CampusHiring/job/"
)


def scrape() -> list[dict]:
    """
    Retourne une liste de dicts {title, bank, location, program_type, url}
    sans aucun filtrage — le filtrage est délégué à main.py.
    """
    headers = {
        "User-Agent":  random.choice(USER_AGENTS),
        "Accept":      "application/json",
        "Referer":     "https://higher.gs.com/",
    }
    try:
        resp = requests.get(_API_URL, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return []
        requisitions = items[0].get("requisitionList", [])
    except Exception as e:
        print(f"[{BANK_NAME}] ❌ {e}")
        return []

    jobs = []
    for r in requisitions:
        job_id = r.get("Id")
        if not job_id:
            continue
        url = f"{_BASE_JOB_URL}{job_id}"
        location = r.get("PrimaryLocation", "")
        if not location:
            work_locations = r.get("workLocation", [])
            if isinstance(work_locations, list) and work_locations:
                location = work_locations[0].get("LocationName", "")
        jobs.append({
            "title":        r.get("Title", "").strip(),
            "bank":         BANK_NAME,
            "location":     location,
            "program_type": r.get("Category", "Campus"),
            "url":          url,
        })
    return jobs
