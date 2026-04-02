"""
notifier.py — Envoi d'alertes Discord via Webhook.

Chaque nouvelle offre génère un embed riche avec :
  • Titre du poste
  • Banque
  • Localisation
  • Type de programme
  • Lien direct (cliquable)
"""

import requests
from config import DISCORD_WEBHOOK_OFFERS, DISCORD_WEBHOOK_REPORTS, DISCORD_AVATAR_URL, DISCORD_BOT_NAME

# Couleurs Discord par banque (optionnel, pour le côté esthétique)
BANK_COLORS = {
    "Goldman Sachs":    0x1A73E8,  # bleu
    "J.P. Morgan":      0x003087,  # bleu marine
    "Morgan Stanley":   0x0033A0,  # bleu profond
    "Bank of America":  0xE31837,  # rouge
    "Citi":             0x003B70,  # bleu Citi
    "Barclays":         0x00AEEF,  # bleu ciel
    "HSBC":             0xDB0011,  # rouge HSBC
    "BNP Paribas":      0x00965E,  # vert BNP
    "Société Générale": 0xE2000F,  # rouge SG
    "Crédit Agricole":  0x027E45,  # vert CA
    "Euronext":         0x0B1E5E,  # bleu marine Euronext
    "Natixis":          0xE6007E,  # magenta Natixis
}
DEFAULT_COLOR = 0x5865F2  # violet Discord


def send_discord_alert(job: dict) -> bool:
    """
    Envoie un embed Discord pour une nouvelle offre.

    Args:
        job: dict avec les clés 'title', 'bank', 'location', 'program_type', 'url'

    Returns:
        True si l'envoi a réussi, False sinon.
    """
    color  = BANK_COLORS.get(job.get("bank", ""), DEFAULT_COLOR)
    title  = job.get("title", "Offre sans titre")
    bank   = job.get("bank", "Banque inconnue")
    loc    = job.get("location", "Localisation non précisée")
    prog   = job.get("program_type", "—")
    url    = job.get("url", "")

    embed = {
        "title": f"🔔 Nouvelle Offre — {bank}",
        "description": (
            f"**📌 Poste :** {title}\n"
            f"**🏦 Banque :** {bank}\n"
            f"**📍 Localisation :** {loc}\n"
            f"**🎓 Programme :** {prog}\n"
            f"**🔗 Lien :** [Postuler ici]({url})"
        ),
        "color": color,
        "url": url,
        "footer": {"text": "Bank Sniper • Front Office Only"},
    }

    payload = {
        "username":   DISCORD_BOT_NAME,
        "avatar_url": DISCORD_AVATAR_URL,
        "embeds":     [embed],
    }

    try:
        resp = requests.post(
            DISCORD_WEBHOOK_OFFERS,
            json=payload,
            timeout=10,
        )
        # Discord renvoie 204 No Content en cas de succès
        if resp.status_code in (200, 204):
            return True
        else:
            # ICI on force l'affichage de l'erreur envoyée par Discord !
            print(f"[notifier] ❌ Rejeté par Discord (Code {resp.status_code}) : {resp.text}")
            print(f"[notifier] 🔍 Payload envoyé : {payload}")
            return False
    except requests.RequestException as e:
        print(f"[notifier] ❌ Erreur réseau Discord : {e}")
        return False

def send_health_report(total_jobs: int) -> None:
    """Envoie un heartbeat Discord quotidien confirmant que le bot tourne."""
    embed = {
        "title": "✅ Bank Sniper — Système Opérationnel",
        "description": (
            f"Le bot tourne correctement.\n"
            f"**Offres en base :** {total_jobs}\n"
            f"**Refresh :** toutes les 5 minutes"
        ),
        "color": 0x57F287,  # vert succès
    }
    payload = {
        "username":   DISCORD_BOT_NAME,
        "avatar_url": DISCORD_AVATAR_URL,
        "embeds":     [embed],
    }
    try:
        # ✅ CORRECTION : on assigne à "resp"
        resp = requests.post(DISCORD_WEBHOOK_REPORTS, json=payload, timeout=10)
        if resp.status_code in (200, 204):
            return True
        else:
            print(f"[notifier] ❌ Rejeté par Discord (Code {resp.status_code}) : {resp.text}")
            print(f"[notifier] 🔍 Payload envoyé : {payload}")
            return False
    except requests.RequestException as e:
        print(f"[notifier] ❌ Erreur réseau Discord : {e}")
        return False


def send_status_report(total_jobs: int) -> None:
    """Envoie un rapport d'état confirmant que le bot tourne (toutes les 3h)."""
    embed = {
        "title": "⏱️ Bank Sniper — Rapport de routine (3h)",
        "description": (
            f"Le scraper tourne toujours.\n"
            f"**Offres en base :** {total_jobs}"
        ),
        "color": 0x3498DB,  # bleu clair
    }
    payload = {
        "username":   DISCORD_BOT_NAME,
        "avatar_url": DISCORD_AVATAR_URL,
        "embeds":     [embed],
    }
    try:
        # ✅ CORRECTION : on assigne à "resp"
        resp = requests.post(DISCORD_WEBHOOK_REPORTS, json=payload, timeout=10)
        if resp.status_code in (200, 204):
            return True
        else:
            print(f"[notifier] ❌ Rejeté par Discord (Code {resp.status_code}) : {resp.text}")
            print(f"[notifier] 🔍 Payload envoyé : {payload}")
            return False
    except requests.RequestException as e:
        print(f"[notifier] ❌ Erreur réseau Discord : {e}")
        return False
