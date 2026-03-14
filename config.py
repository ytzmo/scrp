"""
config.py — Configuration centrale du scraper.
Modifiez DISCORD_WEBHOOK_URL avec votre URL avant de lancer le script.
"""

import os

# ─────────────────────────────────────────────
# DISCORD
# ─────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK", "")
# Avatar optionnel affiché par le bot Discord
DISCORD_AVATAR_URL = "https://i.imgur.com/4M34hi2.png"
DISCORD_BOT_NAME   = "Bank Sniper 🏦"

# ─────────────────────────────────────────────
# FICHIER DE PERSISTANCE
# ─────────────────────────────────────────────
SEEN_FILE = "offres_existantes.json"
LAST_REPORT_FILE = "last_report.txt"

# ─────────────────────────────────────────────
# TIMING
# ─────────────────────────────────────────────
REFRESH_INTERVAL_SEC = 300   # 5 minutes

# ─────────────────────────────────────────────
# FILTRES — Programmes / Types de postes (au moins un doit matcher)
# ─────────────────────────────────────────────
PROGRAM_KEYWORDS = [
    "stage",
    "intern",
    "internship",
    "off-cycle",
    "off cycle",
    "summer analyst",
    "summer associate",
    "graduate",
    "analyst program",
    "trainee",
    "césure",
    "cesure",
    "fin d'études",
    "fin d etudes",
]

# ─────────────────────────────────────────────
# FILTRES — Départements Front Office (au moins un doit matcher)
# ─────────────────────────────────────────────
DEPT_KEYWORDS = [
    "sales",
    "trading",
    "markets",
    "market",
    "equities",
    "equity",
    "fixed income",
    "fi ",
    "quantitative",
    "quant",
    "structuring",
    "derivatives",
    "rates",
    "credit",
    " fx",
    "foreign exchange",
    "capital markets",
    "investment banking",
    " ibd",
    "financing",
    "securitization",
    "flow",
    "prime",
    "exo",
    "exotic",
    "research",           # sell-side research = FO
    "global banking",
    "global markets",
    "cib",
    "ib ",
]

# ─────────────────────────────────────────────
# FILTRES — Exclusions strictes (si l'un d'eux est dans le titre → rejeté)
# ─────────────────────────────────────────────
EXCLUDE_KEYWORDS = [
    "risk",
    "compliance",
    "operations",
    " ops",
    "human resource",
    " hr ",
    "information technology",
    " it ",
    "middle office",
    "back office",
    "legal",
    "audit",
    "controller",
    "finance d'entreprise",
    "procurement",
    "transformation",
    "data governance",
    "cybersecurity",
    "infrastructure",
    "network",
    "software engineer",
    "developer",
    "développeur",
]

# ─────────────────────────────────────────────
# USER-AGENT POOL (rotation aléatoire)
# ─────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36",
]
