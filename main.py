"""
main.py — Orchestrateur principal du Bank Internship Scraper

Logique :
  1. INITIALISATION : scrape toutes les banques, stocke les offres dans
     offres_existantes.json, N'envoie PAS de notification Discord.
  2. BOUCLE (toutes les 5 min) : re-scrape, compare, envoie une alerte
     Discord uniquement pour les nouvelles offres.

Usage :
  python3 main.py             → boucle infinie (mode production)
  python3 main.py --init-only → initialise puis quitte (mode test)
  python3 main.py --test-notif → envoie une fausse offre sur Discord pour tester l'embed
"""

import sys
import time
import subprocess
import random
from datetime import datetime

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
# COMMIT GITHUB ACTIONS
# ─────────────────────────────────────────────────────────────
def push_seen_to_github():
    """
    Commit et push le fichier offres_existantes.json sur GitHub
    pour sauvegarder l'état entre chaque lancement du Cron.
    """
    print(f"\n{BOLD}{YELLOW}━━━ SAUVEGARDE GITHUB ━━━{RESET}")
    try:
        # Configurer l'utilisateur Git pour le commit
        subprocess.run(["git", "config", "--global", "user.name", "GitHub Actions Bot"], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"], check=True, stdout=subprocess.DEVNULL)
        
        # Ajouter les fichiers d'état
        subprocess.run(["git", "add", SEEN_FILE, LAST_REPORT_FILE], check=True)
        
        # Vérifier s'il y a des changements à commit
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if SEEN_FILE in status.stdout or LAST_REPORT_FILE in status.stdout:
            # Créer le commit
            subprocess.run(["git", "commit", "-m", "Auto-update: offres_existantes.json et last_report.txt"], check=True)
            # Pousser sur le dépôt
            subprocess.run(["git", "push"], check=True)
            print(f"{GREEN}✅ Fichiers d'état sauvegardés et poussés sur GitHub avec succès.{RESET}")
        else:
            print(f"{BLUE}  → Aucun changement dans les fichiers d'état, pas de commit nécessaire.{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{RED}❌ Erreur lors du push GitHub : {e}{RESET}")
    except Exception as e:
        print(f"{RED}❌ Erreur inattendue lors de la sauvegarde : {e}{RESET}")


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
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n{BOLD}{BLUE}━━━ REFRESH [{now}] ━━━{RESET}")

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
# POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────

def _test_notification():
    """Envoie une fausse offre sur Discord pour valider l'embed."""
    fake_job = {
        "title":        "Summer Analyst — Global Markets (Equities)",
        "bank":         "Goldman Sachs",
        "location":     "New York, NY",
        "program_type": "Summer Internship",
        "url":          "https://higher.gs.com/careers/",
    }
    print("Envoi d'une notification de test Discord...")
    ok = send_discord_alert(fake_job)
    print("✅ Succès !" if ok else "❌ Échec — vérifiez votre DISCORD_WEBHOOK_OFFERS dans config.py")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--test-notif" in args:
        _test_notification()
        sys.exit(0)

    init_only = "--init-only" in args

    print(f"{BOLD}{'━'*50}{RESET}")
    print(f"{BOLD}  🏦 Bank Sniper — Front Office Internship Alert{RESET}")
    print(f"{BOLD}{'━'*50}{RESET}")
    print(f"  Mode : Run Unique (GitHub Actions Cron)")
    print()

    # Charger la mémoire existante
    from storage import load_seen
    seen = load_seen()

    if init_only:
        seen = initialize()
        push_seen_to_github()
        sys.exit(0)

    # Lancement unique
    try:
        seen = refresh(seen)
        push_seen_to_github()
    except Exception as e:
        print(f"{RED}❌ Erreur inattendue : {e}{RESET}")
        sys.exit(1)
