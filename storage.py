"""
storage.py — Persistance des offres vues dans offres_existantes.json.

Format du fichier : dict {url: {title, bank, location, program_type, url}}
La clé est l'URL absolue → sert d'ID unique anti-doublon.
"""

import json
import os
from config import SEEN_FILE


def load_seen() -> dict:
    """Charge les offres déjà connues depuis le fichier JSON.
    Retourne un dict vide si le fichier n'existe pas ou est corrompu.
    """
    if not os.path.exists(SEEN_FILE):
        return {}
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_seen(seen: dict) -> None:
    """Sauvegarde le dict des offres vues dans le fichier JSON."""
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(seen, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"[storage] ❌ Impossible d'écrire {SEEN_FILE}: {e}")


def count_seen(seen: dict, bank: str | None = None) -> int:
    """Compte le nombre d'offres stockées, globalement ou pour une banque."""
    if bank is None:
        return len(seen)
    return sum(1 for v in seen.values() if v.get("bank") == bank)
