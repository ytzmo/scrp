"""
main.py — Orchestrateur principal du Bank Internship Scraper (Version Serveur Web / Render)
"""

import sys
import time
import subprocess
import random
import os
from datetime import datetime
from flask import Flask

from config import PROGRAM_KEYWORDS, DEPT_KEYWORDS, EXCLUDE_KEYWORDS, SEEN_FILE, LAST_REPORT_FILE
from notifier import send_discord_alert, send_health_report, send_status_report
from storage import save_seen, count_seen

# Import de tous les scrapers
from scrapers import goldman_sachs, jpmorgan, morgan_stanley, bofa, citi
from scrapers import barclays, hsbc, bnp_paribas, societe_generale, credit_agricole
from scrapers import euronext, natixis

# ─────────────────────────────────────────────────────────────
# COULEURS TERMINAL
# ─────────────────────────────────────────────────────────────
BLUE   = "\033[94m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

# ─────────────────────────────────────────────────────────────
# REGISTRE DES SCRAPERS
# ─────────────────────────────────────────────────────────────
SCRAPERS = [
    goldman_sachs,
    jpmorgan,
    morgan_stanley,
    bofa,
    citi,
    barclays,
    hsbc,
    bnp_paribas,
    societe_generale,
    credit_agricole,
    euronext,
    natixis,
]

# ─────────────────────────────────────────────────────────────
# LOGIQUE DE FILTRAGE
# ─────────────────────────────────────────────────────────────

def _matches(title: str) -> bool:
    """
    Retourne True si l'offre passe les 3 filtres :
      1. Correspond à au moins un mot-clé de programme (stage/internship/…)
      2. Correspond à au moins un département Front Office
      3. Ne contient AUCUN mot-clé d'exclusion
    """
    t = title.lower()

    # Filtre 1 — Programme
    if not any(kw in t for kw in PROGRAM_KEYWORDS):
        return False

    # Filtre 2 — Département FO
    if not any(kw in t for kw in DEPT_KEYWORDS):
        return False

    # Filtre 3 — Exclusions
    if any(kw in t for kw in EXCLUDE_KEYWORDS):
        return False

    return True


# ─────────────────────────────────────────────────────────────
# SCRAPING GLOBAL
# ─────────────────────────────────────────────────────────────

def run_all_scrapers() -> list[dict]:
    """
    Lance tous les scrapers et retourne la liste BRUTE (non filtrée)
    de toutes les offres trouvées.
    """
    all_jobs: list[dict] = []
    for scraper in SCRAPERS:
        bank_name = getattr(scraper, "BANK_NAME", scraper.__name__)
        print(f"  {BLUE}>{RESET} {bank_name}...", end=" ", flush=True)
        try:
            jobs = scraper.scrape()
            print(f"{GREEN}{len(jobs)} offres brutes{RESET}")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"{RED}❌ Erreur : {e}{RESET}")
    return all_jobs


def filter_jobs(jobs: list[dict]) -> list[dict]:
    """Applique les filtres de programme + département + exclusions."""
    return [j for j in jobs if _matches(j.get("title", ""))]


# ─────────────────────────────────────────────────────────────
# PHASE 1 — INITIALISATION
# ─────────────────────────────────────────────────────────────

def initialize() -> dict:
    """
    Scrape toutes les banques, filtre, sauvegarde dans offres_existantes.json.
    N'envoie AUCUNE notification Discord.
    Retourne le dict seen (url → job).
    """
    print(f"\n{BOLD}{YELLOW}━━━ INITIALISATION ━━━{RESET}")
    print(f"  Scraping de toutes les banques...\n")

    raw  = run_all_scrapers()
    filtered = filter_jobs(raw)

    print(f"\n  {YELLOW}Filtrage :{RESET} {len(raw)} brutes → {BOLD}{GREEN}{len(filtered)} retenues{RESET}")

    seen: dict = {}
    for job in filtered:
        url = job.get("url", "")
        if url:
            seen[url] = job

    save_seen(seen)
    print(f"\n{GREEN}✅ Initialisation terminée.{RESET} {len(seen)} offres stockées dans offres_existantes.json")
    print(f"{YELLOW}ℹ️  Aucune notification Discord envoyée (première passe).{RESET}\n")
    return seen


# ─────────────────────────────────────────────────────────────
# COMMIT GITHUB ACTIONS (Désactivé pour Render, gardé en archive)
# ─────────────────────────────────────────────────────────────
def push_seen_to_github():
    """
    Commit et push le fichier offres_existantes.json sur GitHub.
    Désactivé par défaut sur Render car le disque local garde la mémoire.
    """
    print(f"\n{BOLD}{YELLOW}━━━ SAUVEGARDE GITHUB (Désactivée) ━━━{RESET}")
    pass


# ─────────────────────────────────────────────────────────────
# RAPPORT 3H
# ─────────────────────────────────────────────────────────────

def check_and_send_3h_report(seen_count: int):
    """
    Vérifie le dernier envoi du rapport 3h dans last_report.txt.
    Si > 3 heures se sont écoulées, envoie le rapport et met à jour le fichier.
    """
    import os
    import time
    
    now = time.time()
    last_sent = 0.0
    
    if os.path.exists(LAST_REPORT_FILE):
        try:
            with open(LAST_REPORT_FILE, "r", encoding="utf-8") as f:
                last_sent = float(f.read().strip())
        except ValueError:
            pass
            
    # 3 heures = 3 * 3600 secondes = 10800
    if now - last_sent >= 10800:
        send_status_report(seen_count)
        try:
            with open(LAST_REPORT_FILE, "w", encoding="utf-8") as f:
                f.write(str(now))
        except OSError as e:
            print(f"[main] ❌ Impossible de sauvegarder {LAST_REPORT_FILE}: {e}")

# ─────────────────────────────────────────────────────────────
# PHASE 2 — REFRESH
# ─────────────────────────────────────────────────────────────

def refresh(seen: dict) -> dict:
    """
    Re-scrape toutes les banques, détecte les nouvelles offres,
    envoie une alerte Discord par nouvelle offre, met à jour le JSON.
    Retourne le dict seen mis à jour.
    """
    now_time = datetime.now().strftime("%H:%M:%S")
    print(f"\n{BOLD}{BLUE}━━━ REFRESH [{now_time}] ━━━{RESET}")

    raw      = run_all_scrapers()
    filtered = filter_jobs(raw)

    new_jobs: list[dict] = []
    for job in filtered:
        url = job.get("url", "")
        if url and url not in seen:
            new_jobs.append(job)
            seen[url] = job

    if new_jobs:
        save_seen(seen)
        print(f"\n{GREEN}🔔 {len(new_jobs)} NOUVELLE(S) OFFRE(S) ! Envoi Discord...{RESET}")
        for job in new_jobs:
            bank  = job.get("bank", "?")
            title = job.get("title", "?")
            print(f"    {GREEN}+{RESET} [{bank}] {title}")
            ok = send_discord_alert(job)
            if not ok:
                print(f"      {RED}(Discord KO){RESET}")
            time.sleep(1.2)  # Anti-rate-limit Discord
    else:
        print(f"\n{BLUE}  → Scan terminé. Rien de nouveau.{RESET}")

    # Heartbeat Discord quotidien (8h du matin)
    if datetime.now().hour == 8 and not getattr(refresh, "_health_sent_today", False):
        send_health_report(count_seen(seen))
        refresh._health_sent_today = True
    elif datetime.now().hour != 8:
        refresh._health_sent_today = False

    # Rapport d'état toutes les 3h
    try:
        check_and_send_3h_report(count_seen(seen))
    except Exception as e:
        print(f"[main] ❌ Erreur lors du rapport 3h : {e}")

    return seen


# ─────────────────────────────────────────────────────────────
# POINT D'ENTRÉE WEB (RENDER + CRON-JOB)
# ─────────────────────────────────────────────────────────────

app = Flask(__name__)

@app.route('/')
def home():
    """Page d'accueil pour indiquer à Render que l'app est en vie."""
    return "✅ Bank Sniper est en ligne et écoute !"

@app.route('/scan')
def trigger_scan():
    """URL appelée par cron-job.org toutes les X minutes."""
    from storage import load_seen
    
    # 1. Charger les offres existantes
    seen = load_seen()
    
    # Si le dictionnaire est vide (premier lancement ou redémarrage du serveur), 
    # on peut initialiser discrètement ou laisser refresh s'en charger.
    # Ici, on laisse refresh faire son travail normal.
    
    try:
        # 2. Lancer le scan (la fonction sauvegarde automatiquement le JSON)
        seen = refresh(seen)
        
        return f"Scan terminé avec succès. {len(seen)} offres en base.", 200
        
    except Exception as e:
        print(f"❌ Erreur lors du scan : {e}")
        return f"Erreur lors du scan : {e}", 500

if __name__ == "__main__":
    print(f"{BOLD}{'━'*50}{RESET}")
    print(f"{BOLD}  🏦 Bank Sniper — Lancement du Serveur Web{RESET}")
    print(f"{BOLD}{'━'*50}{RESET}")
    
    # Render attribue dynamiquement un port via la variable d'environnement PORT
    port = int(os.environ.get('PORT', 10000))
    # Lancement du serveur
    app.run(host='0.0.0.0', port=port)
