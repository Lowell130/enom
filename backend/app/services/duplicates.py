"""Riconoscimento dei vini doppi (stessa cantina) con confronto tollerante dei nomi.

Il confronto e' deterministico (niente IA): normalizza i nomi togliendo accenti,
punteggiatura, sigle di denominazione e annate, poi considera doppioni:
  - nomi normalizzati identici                           -> "exact"
  - un nome contenuto nell'altro, se la parte comune contiene un nome proprio
    (es. "Colle del Limone" e "Colle del Limone – Falanghina del Molise") -> "similar"
  - nomi molto simili (refusi, parole in piu'/in meno)   -> "similar"
Due vini che differiscono per la menzione "Riserva" (o per tipologia, se nota)
non sono mai considerati doppioni.
"""
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List, Optional, Tuple

SIMILARITY_THRESHOLD = 0.86

# parole che non distinguono un vino dall'altro
_NOISE_WORDS = {
    "doc", "docg", "dop", "igt", "igp", "vino", "vini", "d", "di", "del", "della", "dei", "delle", "degli",
    "de", "il", "lo", "la", "le", "i", "gli", "l", "e", "ed", "sa", "s", "senza", "annata",
}
# parole "generiche" (vitigni, denominazioni, colori): da sole non identificano un vino specifico,
# perche' una cantina puo' avere "Tintilia del Molise" e "Tintilia del Molise Cru X"
_GENERIC_WORDS = {
    "molise", "biferno", "pentro", "isernia", "tintilia", "terre", "osci", "rotae", "sannio", "campobasso",
    "falanghina", "montepulciano", "aglianico", "trebbiano", "greco", "malvasia", "moscato", "bombino",
    "sangiovese", "cabernet", "sauvignon", "merlot", "chardonnay", "pinot", "nero", "grigio", "syrah",
    "cerasuolo", "fiano", "rosso", "bianco", "rosato", "riserva", "superiore", "spumante", "brut",
    "passito", "metodo", "classico", "reale", "blanc",
}
_DISTINGUISHING = {"riserva", "superiore", "passito", "spumante", "brut", "rosato", "rosso", "bianco",
                   "extra", "dry", "novello", "frizzante", "dolce"}


def name_tokens(name: str) -> List[str]:
    text = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode().lower()
    text = re.sub(r"\b(19|20)\d{2}\b", " ", text)          # annate
    text = re.sub(r"d\.\s*o\.\s*c\.?\s*g?\.?|d\.\s*o\.\s*p\.?|i\.\s*g\.\s*[tp]\.?", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return [t for t in text.split() if t not in _NOISE_WORDS]


def name_key(name: str) -> str:
    return " ".join(name_tokens(name))


def _distinguishing(tokens: Iterable[str]) -> set:
    return {t for t in tokens if t in _DISTINGUISHING}


def compare_names(a: str, b: str) -> Tuple[Optional[str], float]:
    """Restituisce ("exact"|"similar"|None, punteggio 0..1)."""
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return None, 0.0
    ka, kb = " ".join(ta), " ".join(tb)
    if ka == kb:
        return "exact", 1.0
    # "Tintilia" e "Tintilia Riserva" (o "Rosso" e "Rosato") sono vini diversi
    if _distinguishing(ta) != _distinguishing(tb):
        return None, 0.0
    sa, sb = set(ta), set(tb)
    shorter, longer = (sa, sb) if len(sa) <= len(sb) else (sb, sa)
    # contenimento: il nome piu' corto deve avere almeno una parola specifica (non solo vitigno/denominazione)
    if shorter <= longer and shorter - _GENERIC_WORDS:
        return "similar", round(0.9 + 0.1 * len(shorter) / len(longer), 2)
    # refusi: stesse parole a meno di piccole differenze di battitura in ciascuna parola,
    # e almeno una parola specifica in comune ("Uno" e "Due" restano vini diversi)
    ratio = SequenceMatcher(None, ka, kb).ratio()
    if ratio >= SIMILARITY_THRESHOLD and abs(len(ta) - len(tb)) <= 1:
        short_list, long_list = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
        pairs_ok = all(max(SequenceMatcher(None, t, u).ratio() for u in long_list) >= 0.8 for t in short_list)
        if pairs_ok and (set(short_list) - _GENERIC_WORDS):
            return "similar", round(ratio, 2)
    return None, round(ratio, 2)


# tipologie che indicano vini sicuramente diversi anche con lo stesso nome
# (es. "Tintilia del Molise" rosso e rosato della stessa cantina)
_COLOUR_CATEGORIES = {"VINO_ROSSO", "VINO_BIANCO", "ROSATO"}


def different_colour(a: str, b: str) -> bool:
    return bool(a and b and a != b and a in _COLOUR_CATEGORIES and b in _COLOUR_CATEGORIES)


def find_duplicate(name: str, candidates: Iterable[Dict[str, Any]], category: str = "",
                   is_riserva: Optional[bool] = None) -> Optional[Dict[str, Any]]:
    """Trova tra i vini della stessa cantina quello che corrisponde meglio a `name`."""
    best, best_score, best_kind = None, 0.0, None
    for c in candidates:
        kind, score = compare_names(name, c.get("name", ""))
        if not kind:
            continue
        if is_riserva is not None and c.get("is_riserva") is not None and bool(c.get("is_riserva")) != bool(is_riserva):
            continue
        if category and c.get("category") and c["category"] != category \
                and (kind != "exact" or different_colour(category, c["category"])):
            continue
        if score > best_score:
            best, best_score, best_kind = c, score, kind
    if best is None:
        return None
    return {
        "id": str(best["_id"]),
        "name": best.get("name", ""),
        "slug": best.get("slug", ""),
        "status": best.get("status", ""),
        "match": best_kind,
        "score": best_score,
    }
