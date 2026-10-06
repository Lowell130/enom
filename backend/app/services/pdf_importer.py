"""Importazione delle schede vino da PDF.

Flusso:
  1. estrazione con IA multimodale (app/services/ai_extractor.py) se e' configurata una chiave;
     altrimenti parser testuale "Etichetta: valore" (solo PDF con testo, nessun dato inventato);
  2. normalizzazione deterministica verso il modello dati del catalogo: nomi degli attributi
     allineati a quelli esistenti, vitigni e abbinamenti ricondotti alle tassonomie del sito,
     campi nativi (gradazione, temperatura, prezzo...) spostati fuori dagli attributi.
"""
import io
import logging
import os
import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pypdf

from app.services.insights import clean_grape, format_grape, normalize_grape_entries, normalize_price_text, normalize_temperature_text
from app.services.ai_extractor import (
    CATEGORIES,
    AIExtractionError,
    active_provider,
    extract_with_ai,
)
from app.services.catalog import clean_wine_title, parse_denominazione_acronym

logger = logging.getLogger("enotecamolise.pdf")

# Vitigni sempre riconosciuti (uniti a quelli presenti nel DB)
VALID_SINGLE_GRAPES = [
    "Aglianico", "Bombino Bianco", "Cabernet Sauvignon", "Chardonnay",
    "Falanghina", "Garganega", "Garganica", "Greco", "Malvasia", "Merlot",
    "Montepulciano", "Moscato", "Moscato Reale", "Pinot Grigio",
    "Pinot Nero", "Riesling", "Sangiovese", "Sauvignon Blanc", "Syrah", "Tintilia",
    "Trebbiano", "Trebbiano del Molise"
]

WHITE_GRAPES = {"falanghina", "trebbiano", "trebbiano del molise", "malvasia", "greco", "bombino bianco",
                "chardonnay", "moscato", "moscato bianco", "pinot grigio", "riesling", "sauvignon blanc",
                "garganega", "garganica", "fiano", "vermentino"}

CANONICAL_PAIRINGS = [
    "Antipasti & Aperitivi", "Arrosti & Tagliate", "Cacciagione & Selvaggina", "Carni Rosse & Grigliate",
    "Pampanella Molisana", "Formaggi Freschi", "Formaggi Stagionati", "Salumi & Affettati",
    "Primi Piatti & Ragù", "Risotti & Tartufo", "Pesce & Frutti di Mare", "Piatti Vegetariani",
    "Pizze & Lievitati", "Pasticceria & Dolci", "Paté & Piatti Freddi",
]

# Regole per ricondurre il testo libero degli abbinamenti alle categorie canoniche
PAIRING_RULES = [
    (r'cacciagione|selvaggina|cinghiale|lepre|capriolo', "Cacciagione & Selvaggina"),
    (r'antipast|aperitiv|finger food|stuzzich', "Antipasti & Aperitivi"),
    (r'carn[ei] ross|griglia|grigliat|brace|bistecc', "Carni Rosse & Grigliate"),
    (r'arrost|tagliat|bollit|stufat|brasat', "Arrosti & Tagliate"),
    (r'pampanella', "Pampanella Molisana"),
    (r'formagg\w*\s+(?:\w+\s+)?fresch|latticin|mozzarell|ricott|spalmabil|formaggi freschi', "Formaggi Freschi"),
    (r'stagionat|pasta filata|erborinat|caciocavall|pecorin', "Formaggi Stagionati"),
    (r'salum|affettat|insaccat|prosciutt|soppressat', "Salumi & Affettati"),
    (r'primi|pasta|sugo|ragù|ragu|zupp|minestr|lasagn', "Primi Piatti & Ragù"),
    (r'risott|tartuf|porcini|funghi', "Risotti & Tartufo"),
    (r'pesce|frutti di mare|crostace|mollusc|brodetto|baccal|crudi|sushi|ostric', "Pesce & Frutti di Mare"),
    (r'vegetarian|verdur|ortagg|legum', "Piatti Vegetariani"),
    (r'pizz|lievitat|focacc', "Pizze & Lievitati"),
    (r'dolc|pasticceri|dessert|biscott|crostat|cioccolat', "Pasticceria & Dolci"),
    (r'paté|pate|piatti freddi|terrin', "Paté & Piatti Freddi"),
]
# Se nella stessa voce compare il pesce, "arrosti/grigliate" si riferiscono al pesce
PAIRING_OVERRIDES = {"Pesce & Frutti di Mare": {"Arrosti & Tagliate", "Carni Rosse & Grigliate"}}

# Nome canonico -> sinonimi (confrontati su testo minuscolo senza accenti)
ATTRIBUTE_SYNONYMS: List[Tuple[str, List[str]]] = [
    ("Uvaggio", ["uvaggio", "uve", "uva", "vitigni", "vitigno", "varieta", "varieta di uve", "composizione uvaggio", "blend"]),
    ("Zona di Produzione", ["zona di produzione", "comune di produzione", "zona", "area di produzione", "provenienza",
                            "localita", "territorio", "comune", "luogo di produzione", "origine", "vigneti"]),
    ("Altitudine Vigneto", ["altitudine", "altitudine vigneto", "altitudine vigneti", "altimetria", "quota", "altitudine media"]),
    ("Allevamento", ["allevamento", "sistema di allevamento", "forma di allevamento", "sistema d allevamento"]),
    ("Vendemmia", ["vendemmia", "epoca di vendemmia", "periodo di vendemmia", "epoca vendemmia", "raccolta", "tipo di raccolta"]),
    ("Vinificazione", ["vinificazione", "fermentazione", "tecnica di vinificazione"]),
    ("Affinamento", ["affinamento", "maturazione", "invecchiamento", "elevazione", "affinamento in bottiglia"]),
    ("Formato", ["formato", "formato bottiglia", "formati", "capacita", "bottiglia"]),
    ("Allergeni", ["allergeni", "contiene"]),
    ("Tipologia del Terreno", ["terreno", "tipologia del terreno", "tipo di terreno", "suolo", "composizione del terreno", "natura del terreno"]),
    ("Resa per Ettaro", ["resa", "resa per ettaro", "resa uva", "resa ettaro", "produzione per ettaro"]),
    ("Densità di Impianto", ["densita", "densita di impianto", "densita d impianto", "ceppi per ettaro", "piante per ettaro"]),
    ("Esposizione", ["esposizione", "esposizione vigneto"]),
    ("Bottiglie Prodotte", ["numero di bottiglie prodotte", "numero di bottiglie", "bottiglie prodotte", "produzione annua", "tiratura"]),
    ("Prima Annata di Produzione", ["prima annata di produzione", "prima annata", "prima produzione"]),
    ("Età delle Viti", ["eta delle viti", "eta media delle viti", "eta del vigneto", "eta vigneto"]),
    ("Superficie Vigneto", ["superficie", "superficie vigneto", "estensione vigneto", "ettari vitati"]),
    ("Tipo Vino", ["tipo vino", "tipo", "tipo di vino", "tipologia vino"]),
]

# Voci che hanno un campo dedicato: vengono spostate nel campo e rimosse dagli attributi
NATIVE_FIELDS: List[Tuple[str, List[str]]] = [
    ("denominazione", ["denominazione", "classificazione", "denominazione di origine"]),
    ("alcohol_degrees", ["grado alcolico", "gradazione alcolica", "gradazione", "alcol", "titolo alcolometrico",
                         "titolo alcolometrico volumico", "alcool", "tenore alcolico"]),
    ("serving_temperature", ["temperatura di servizio", "temperatura servizio", "servire a", "temperatura"]),
    ("food_pairings_text", ["abbinamenti", "abbinamento", "abbinamenti gastronomici", "abbinamenti consigliati",
                            "abbinamento gastronomico", "a tavola", "in cucina"]),
    ("indicative_price", ["prezzo", "prezzo indicativo", "prezzo al pubblico"]),
    ("vintage_year", ["annata", "anno di vendemmia", "anno"]),
    ("tasting_visual", ["colore", "esame visivo", "aspetto", "vista", "alla vista"]),
    ("tasting_olfactory", ["profumo", "profumi", "esame olfattivo", "olfatto", "naso", "bouquet", "al naso"]),
    ("tasting_taste", ["gusto", "sapore", "esame gustativo", "palato", "al palato", "in bocca", "bocca"]),
    ("description", ["descrizione", "presentazione", "note"]),
]

# Riferimenti all'agricoltura biologica (testo gia' normalizzato in minuscolo)
ORGANIC_RE = re.compile(
    r"\bbiologic(?:[oai]|he)\b|\bbio\b|\bagricoltura biologica\b|\borganic\b|\borganico\b"
    r"|\bbioagricert\b|\bccpb\b|\bicea\b|\bsuolo e salute\b|\bvaloritalia bio\b"
    r"|\bit[- ]bio[- ]\d{3}\b"
)
# "in conversione al biologico" non e' ancora un vino biologico certificato
NOT_ORGANIC_RE = re.compile(r"\bin conversione\b|\bnon (?:e |è )?biologic|\bnon bio\b")
# Unico modo in cui il catalogo registra un vino biologico (stesso formato dei vini inseriti a mano)
ORGANIC_ATTRIBUTE_NAME = "Tipo Vino"
ORGANIC_ATTRIBUTE_VALUE = "Biologico"
# attributi in cui le schede indicano il biologico: vengono ricondotti a "Tipo Vino"
_TIPO_KEYS = {"tipo", "tipo vino", "tipo di vino", "tipologia vino"}
_ORGANIC_HOLDER_KEYS = _TIPO_KEYS | {
    "certificazione", "certificazioni", "certificazione biologica", "certificato", "agricoltura",
    "coltivazione", "metodo di coltivazione", "regime", "regime di coltivazione", "regime colturale",
    "conduzione", "conduzione agronomica", "conduzione del vigneto", "biologico", "bio", "produzione",
    "agricoltura biologica", "vino biologico",
}
_YES_VALUES = {"si", "yes", "presente", "x", "vero", "true"}
# parole del biologico da togliere da un valore "Tipo" misto (es. "Vino fermo biologico" -> "Vino fermo")
_ORGANIC_WORDS_RE = re.compile(
    r"\b(?:vino\s+)?(?:da\s+(?:uve|agricoltura)\s+)?biologic(?:[oai]|he)\b|\bbio\b|\borganic[oa]?\b"
    r"|\bcertificat[oa]\b|\bicea\b|\bccpb\b|\bbioagricert\b|\bsuolo e salute\b|\bit[- ]bio[- ]\d{3}\b",
    re.I,
)

LABEL_LINE_RE = re.compile(r"^\s*([A-Za-zÀ-ÿ'’ .()/]{3,45}?)\s*[:：]\s*(.+)$")


# ---------------------------------------------------------------------------
# Utilita'
# ---------------------------------------------------------------------------

def _key(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9%]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _clean(value: Any, limit: int = 2000) -> str:
    if value is None:
        return ""
    text = re.sub(r"[ \t]+", " ", str(value)).strip()
    text = re.sub(r"\s*\n\s*", "\n", text)
    return text[:limit]


def _cap(text: str) -> str:
    text = text.strip()
    return text[:1].upper() + text[1:] if text else text


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join(t for t in (page.extract_text() or "" for page in reader.pages) if t)
    except Exception as e:
        logger.warning("Estrazione testo PDF fallita: %s", e)
        return ""


def _synonym_lookup(table: List[Tuple[str, List[str]]]) -> Dict[str, str]:
    lookup = {}
    for canonical, syns in table:
        lookup[_key(canonical)] = canonical
        for s in syns:
            lookup[_key(s)] = canonical
    return lookup


_ATTR_LOOKUP = _synonym_lookup(ATTRIBUTE_SYNONYMS)
_NATIVE_LOOKUP = _synonym_lookup(NATIVE_FIELDS)


# ---------------------------------------------------------------------------
# Normalizzazione dei singoli campi
# ---------------------------------------------------------------------------

def parse_alcohol(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        num = float(value)
    else:
        m = re.search(r"(\d{1,2}(?:[.,]\d{1,2})?)", str(value))
        if not m:
            return None
        num = float(m.group(1).replace(",", "."))
    return round(num, 1) if 4 <= num <= 25 else None


def parse_vintage(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    m = re.search(r"\b(19[5-9]\d|20\d{2})\b", str(value))
    if not m:
        return None
    year = int(m.group(1))
    return year if year <= datetime.utcnow().year + 1 else None


def normalize_temperature(value: Any) -> str:
    return normalize_temperature_text(_clean(value, 60)) or ""


def match_grape(raw_name: str, master_grapes: List[str]) -> str:
    name = re.sub(r"\d+(?:[.,]\d+)?\s*%?", "", raw_name or "").strip(" -,.;")
    if not name:
        return ""
    k = _key(name)
    by_key = {_key(g): g for g in master_grapes}
    if k in by_key:
        return by_key[k]
    # nome del catalogo contenuto nel testo (es. "Falanghina del Sannio" -> "Falanghina"): vince il piu' lungo
    candidates = [g for gk, g in by_key.items() if re.search(rf"\b{re.escape(gk)}\b", k)]
    if candidates:
        return max(candidates, key=len)
    return " ".join(w if w.lower() in ("di", "del", "della", "d") else w.capitalize() for w in name.split())


def normalize_grapes(raw: Any, master_grapes: List[str]) -> Tuple[List[str], str]:
    """Restituisce (vitigni canonici, testo uvaggio con percentuali)."""
    items: List[Tuple[str, Optional[float]]] = []

    def add_text(text: str) -> None:
        # "Montepulciano 55% Sangiovese 45%", "Falanghina e Greco", "Montepulciano 85%, Aglianico 15%"
        text = re.sub(r"\s*\bin\s+purezza\b", " 100%", text, flags=re.I)
        text = re.sub(r"(\d+(?:[.,]\d+)?\s*%)\s*[-–]?\s*(?=[A-Za-zÀ-ÿ])", r"\1,", text)
        # la virgola dei decimali ("85,5%") non separa i vitigni
        for part in re.split(r"(?<!\d),|,(?!\d)|[;/+]|\be\b", text):
            pct = re.search(r"(\d+(?:[.,]\d+)?)\s*%", part)
            items.append((part, float(pct.group(1).replace(",", ".")) if pct else None))

    if isinstance(raw, list):
        for g in raw:
            if isinstance(g, dict):
                items.append((str(g.get("name") or ""), g.get("percentage")))
            elif isinstance(g, str):
                add_text(g)
    elif isinstance(raw, str):
        add_text(raw)

    names, entries = [], []
    for name, pct in items:
        canonical = match_grape(name, master_grapes)
        if not canonical or canonical in names:
            continue
        names.append(canonical)
        p = None
        if pct not in (None, ""):
            try:
                p = int(float(str(pct).replace(",", ".")))   # 85,5% -> 85%
            except (TypeError, ValueError):
                p = None
        entries.append(format_grape(canonical, p if p and 0 < p <= 100 else None))
    # formato unico del catalogo: "Tintilia 80%, Montepulciano 20%" dal vitigno principale;
    # le percentuali stanno nei vitigni, quindi non serve ripeterle nel campo "Uvaggio"
    grapes, _ = normalize_grape_entries(entries)
    return grapes, ""


def pairings_from_text(text: str) -> Tuple[List[str], bool]:
    """Categorie canoniche ricavate dal testo e flag 'ci sono voci non riconducibili'."""
    found: List[str] = []
    has_unmatched = False
    parts = [p.strip() for p in re.split(r",|;|\n|\s+e\s+|\s+o\s+", text or "") if p.strip()]
    for part in parts:
        low = part.lower()
        matched = [canonical for pattern, canonical in PAIRING_RULES if re.search(pattern, low)]
        for winner, losers in PAIRING_OVERRIDES.items():
            if winner in matched:
                matched = [m for m in matched if m not in losers]
        if not matched and len(_key(part)) > 3 and not re.fullmatch(r"(ideale|ottimo|perfetto)( con| per)?", _key(part)):
            has_unmatched = True
        for m in matched:
            if m not in found:
                found.append(m)
    return found, has_unmatched


def canonical_attribute_name(name: str, master_attributes: List[str]) -> str:
    k = _key(name)
    master_by_key = {_key(a): a for a in master_attributes}
    if k in master_by_key:
        return master_by_key[k]
    canonical = _ATTR_LOOKUP.get(k)
    if canonical:
        return master_by_key.get(_key(canonical), canonical)
    cleaned = re.sub(r"\s+", " ", name).strip(" :-.")
    small = {"di", "del", "della", "dei", "degli", "delle", "da", "in", "per", "e", "a", "al", "alla", "con", "su", "d", "l"}
    words = cleaned.split(" ")
    titled = [w if (i > 0 and w.lower() in small) or w.isupper() else w[:1].upper() + w[1:] for i, w in enumerate(words)]
    return " ".join(titled)[:60]


# ---------------------------------------------------------------------------
# Normalizzazione di un vino
# ---------------------------------------------------------------------------

def mentions_organic(*texts: Any) -> bool:
    """True se i testi contengono riferimenti al biologico (esclusa la sola conversione)."""
    found = False
    for text in texts:
        low = str(text or "").lower()
        if not low:
            continue
        if NOT_ORGANIC_RE.search(low):
            return False
        if ORGANIC_RE.search(low):
            found = True
    return found


def _is_organic_value(value: str) -> bool:
    return mentions_organic(value) or _key(value) in _YES_VALUES


def normalize_organic_attributes(custom_attributes: List[Dict[str, str]], is_organic: bool = False,
                                 master_attributes: Optional[List[str]] = None) -> Tuple[List[Dict[str, str]], bool]:
    """Riconduce ogni indicazione di biologico all'unico attributo "Tipo Vino: Biologico".

    - "Certificazione: Biologico ICEA", "Agricoltura: biologica", "Tipo: Vino Biologico" ... vengono rimossi
      e sostituiti da "Tipo Vino: Biologico";
    - un "Tipo"/"Tipo Vino" con altre informazioni le conserva (es. "Vino fermo; Biologico").
    Restituisce (attributi normalizzati, il vino e' biologico).
    """
    tipo_name = ORGANIC_ATTRIBUTE_NAME
    if master_attributes:
        tipo_name = next((m for m in master_attributes if _key(m) == _key(ORGANIC_ATTRIBUTE_NAME)), tipo_name)

    organic = bool(is_organic)
    tipo_parts: List[str] = []
    others: List[Dict[str, str]] = []
    for attr in custom_attributes or []:
        if not isinstance(attr, dict):
            continue
        name, value = str(attr.get("name") or "").strip(), str(attr.get("value") or "").strip()
        k = _key(name)
        if k in _ORGANIC_HOLDER_KEYS and value and _is_organic_value(value):
            organic = True
            if k in _TIPO_KEYS:
                rest = _ORGANIC_WORDS_RE.sub(" ", value)
                rest = re.sub(r"\s*[;,/-]\s*(?=[;,/-]|$)|^\s*[;,/-]\s*", "", re.sub(r"\s+", " ", rest)).strip(" ;,/-")
                if rest and _key(rest) not in {"vino", "da", "uve", "agricoltura"}:
                    tipo_parts.append(_cap(rest))
            continue
        if k in _TIPO_KEYS:
            tipo_parts.append(value)
            continue
        others.append({"name": name, "value": value})

    if organic:
        tipo_parts.append(ORGANIC_ATTRIBUTE_VALUE)
    if not tipo_parts:
        return others, organic
    tipo_value = "; ".join(dict.fromkeys(p for p in tipo_parts if p))
    return [{"name": tipo_name, "value": tipo_value}] + others, organic


def _guess_category(text: str, grapes: List[str]) -> str:
    low = (text or "").lower()
    if re.search(r"spumante|metodo classico|charmat|brut|bollicin|frizzant", low):
        return "SPUMANTE"
    if re.search(r"passito|vendemmia tardiva|muffato", low):
        return "PASSITO"
    if re.search(r"grappa|liquore|amaro|distillat", low):
        return "LIQUORE"
    if re.search(r"rosato|rosé|cerasuolo", low):
        return "ROSATO"
    if re.search(r"\bbianco\b", low) or (grapes and all(clean_grape(g).lower() in WHITE_GRAPES for g in grapes)):
        return "VINO_BIANCO"
    return "VINO_ROSSO"


def normalize_wine(raw: Dict[str, Any], master_attributes: List[str], master_grapes: List[str],
                   canonical_pairings: List[str]) -> Dict[str, Any]:
    tasting = raw.get("tasting_notes") if isinstance(raw.get("tasting_notes"), dict) else {}
    wine: Dict[str, Any] = {
        "name": clean_wine_title(_clean(raw.get("name"), 200)),
        "category": raw.get("category") if raw.get("category") in CATEGORIES else "",
        "denominazione": parse_denominazione_acronym(raw["denominazione"]) if raw.get("denominazione") else "",
        "vintage_year": parse_vintage(raw.get("vintage_year")),
        "is_riserva": bool(raw.get("is_riserva")),
        "alcohol_degrees": parse_alcohol(raw.get("alcohol_degrees")),
        "serving_temperature": normalize_temperature(raw.get("serving_temperature")),
        "indicative_price": normalize_price_text(_clean(raw.get("indicative_price"), 50)),
        "description": _clean(raw.get("description"), 5000),
        "tasting_notes": {
            "visual": _clean(tasting.get("visual")),
            "olfactory": _clean(tasting.get("olfactory")),
            "taste": _clean(tasting.get("taste")),
        },
    }
    pairings_text = _clean(raw.get("food_pairings_text"), 1000)

    # --- attributi: spostamento dei campi nativi, nomi canonici, unione dei duplicati
    attributes: Dict[str, str] = {}
    order: List[str] = []
    for attr in raw.get("attributes") or []:
        if not isinstance(attr, dict):
            continue
        a_name, a_value = _clean(attr.get("name"), 80), _clean(attr.get("value"), 1000)
        if not a_name or not a_value:
            continue
        native = _NATIVE_LOOKUP.get(_key(a_name))
        if native:
            if native == "denominazione" and not wine["denominazione"]:
                if re.search(r"\b(docg|doc|dop|igt|igp)\b|d\.o\.", a_value, re.I):
                    wine["denominazione"] = parse_denominazione_acronym(a_value)
            elif native == "alcohol_degrees" and wine["alcohol_degrees"] is None:
                wine["alcohol_degrees"] = parse_alcohol(a_value)
            elif native == "serving_temperature" and not wine["serving_temperature"]:
                wine["serving_temperature"] = normalize_temperature(a_value)
            elif native == "food_pairings_text":
                pairings_text = pairings_text or a_value
            elif native == "indicative_price" and not wine["indicative_price"]:
                wine["indicative_price"] = normalize_price_text(a_value[:50])
            elif native == "vintage_year" and wine["vintage_year"] is None:
                wine["vintage_year"] = parse_vintage(a_value)
            elif native.startswith("tasting_"):
                key = native.split("_", 1)[1]
                if not wine["tasting_notes"][key]:
                    wine["tasting_notes"][key] = a_value
            elif native == "description" and not wine["description"]:
                wine["description"] = a_value
            continue
        canonical = canonical_attribute_name(a_name, master_attributes)
        value = _cap(a_value)
        if canonical in attributes:
            if _key(value) not in _key(attributes[canonical]):
                attributes[canonical] = f"{attributes[canonical]}; {value}"
        else:
            attributes[canonical] = value
            order.append(canonical)

    # --- vitigni
    grapes, uvaggio_text = normalize_grapes(raw.get("grape_varieties"), master_grapes)
    if not grapes and "Uvaggio" in attributes:
        grapes, uvaggio_text = normalize_grapes(attributes["Uvaggio"], master_grapes)
    wine["grape_varieties"] = grapes
    uvaggio_name = canonical_attribute_name("Uvaggio", master_attributes)
    if uvaggio_text and uvaggio_name not in attributes:
        attributes[uvaggio_name] = uvaggio_text
        order.insert(0, uvaggio_name)

    # --- abbinamenti: categorie scelte dall'IA, altrimenti regole sul testo
    canonical_by_key = {_key(p): p for p in canonical_pairings}
    ai_pairings = [canonical_by_key[_key(p)] for p in raw.get("food_pairings") or []
                   if isinstance(p, str) and _key(p) in canonical_by_key]
    rule_pairings, has_unmatched = pairings_from_text(pairings_text)
    rule_pairings = [canonical_by_key.get(_key(p), p) for p in rule_pairings if _key(p) in canonical_by_key]
    pairings = list(dict.fromkeys(ai_pairings or rule_pairings))
    wine["food_pairings"] = pairings
    # le voci non riconducibili alle categorie non vanno perse: testo originale come attributo
    if pairings_text and (has_unmatched or not pairings):
        name = canonical_attribute_name("Abbinamenti Consigliati", master_attributes)
        attributes[name] = _cap(re.sub(r"^(ideale|ottimo|perfetto)\s+(con|per)\s+", "", pairings_text, flags=re.I))
        order.append(name)

    # --- biologico: segnalato dall'IA oppure citato nel testo della scheda
    organic_texts = [wine["name"], wine["description"], pairings_text, _clean(raw.get("notes"))]
    organic_texts += [f"{k}: {v}" for k, v in attributes.items()]
    organic_texts += list(wine["tasting_notes"].values())
    detected = bool(raw.get("is_organic")) or mentions_organic(*organic_texts)
    ordered = [{"name": n, "value": attributes[n]} for n in dict.fromkeys(order) if n in attributes]
    wine["custom_attributes"], wine["is_organic"] = normalize_organic_attributes(ordered, detected, master_attributes)

    # --- categoria
    if not wine["category"]:
        context = " ".join([wine["name"], wine["description"], " ".join(grapes)])
        wine["category"] = _guess_category(context, grapes)
    if not wine["is_riserva"] and re.search(r"\briserva\b", wine["name"], re.I):
        wine["is_riserva"] = True

    # --- avvisi per la revisione
    missing = []
    if not wine["name"]:
        missing.append("nome")
    if wine["alcohol_degrees"] is None:
        missing.append("gradazione alcolica")
    if not grapes:
        missing.append("vitigni")
    if not wine["denominazione"]:
        missing.append("denominazione")
    if not wine["serving_temperature"]:
        missing.append("temperatura di servizio")
    wine["missing_fields"] = missing
    notes = _clean(raw.get("notes"), 500)
    wine["warnings"] = [notes] if notes else []
    wine["name"] = tidy_wine_name(wine["name"], wine["category"])
    return wine


_LOWER_WORDS = {"di", "del", "della", "dello", "dei", "degli", "delle", "da", "dal", "e", "ed", "in", "al", "alla",
                "a", "con", "su", "per", "tra", "fra"}
_ROMAN = re.compile(r"^(?=[IVXLC]+$)(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")


def _title_word(word: str, first: bool) -> str:
    if _ROMAN.match(word):
        return word
    low = word.lower()
    if not first and low in _LOWER_WORDS:
        return low
    # d'uva -> d'Uva, sant'agata -> Sant'Agata
    parts = low.split("'")
    return "'".join(p[:1].upper() + p[1:] if (i > 0 or first or p not in ("d", "l")) else p
                    for i, p in enumerate(parts))


def tidy_wine_name(name: str, category: str = "") -> str:
    """I nomi scritti tutti in maiuscolo come sulle etichette ("TINTILIA DEL MOLISE") diventano
    "Tintilia del Molise"; un rosato senza il colore nel nome riceve "Rosato",
    cosi' non si confonde con il rosso che ha lo stesso nome."""
    name = (name or "").strip()
    letters = [c for c in name if c.isalpha()]
    if len(letters) >= 4 and all(c.isupper() for c in letters):
        name = " ".join(_title_word(w, i == 0) for i, w in enumerate(name.split()))
    if category == "ROSATO" and name and not re.search(r"(?i)\b(rosat[oi]|ros[eé]|cerasuolo|rosa)\b", name):
        name = f"{name} Rosato"
    return name


# ---------------------------------------------------------------------------
# Parser testuale di riserva (senza IA)
# ---------------------------------------------------------------------------

def parse_text_fallback(text: str, filename: str) -> Dict[str, Any]:
    """Estrae le coppie "Etichetta: valore" da un PDF testuale. Non inventa valori mancanti."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    attributes, free_lines, name = [], [], ""
    for line in lines:
        m = LABEL_LINE_RE.match(line)
        if m and len(m.group(1).split()) <= 6:
            attributes.append({"name": m.group(1).strip(), "value": m.group(2).strip()})
        else:
            free_lines.append(line)

    for line in free_lines[:8]:
        if 3 < len(line) <= 90 and not re.search(r"scheda|tecnica|pagina|tel\.?|telefono|e-?mail|www\.|http|€", line, re.I):
            name = line
            break
    if not name:
        name = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ")

    description = " ".join(l for l in free_lines if len(l) > 60)[:5000]
    denom = re.search(r"\b(DOCG|DOC|DOP|IGT|IGP)\b", text)
    return {
        "producer": {"name": None, "city": None, "website": None},
        "wines": [{
            "name": name,
            "category": None,
            "denominazione": denom.group(1) if denom else None,
            "vintage_year": None,
            "is_riserva": bool(re.search(r"\briserva\b", name, re.I)),
            "alcohol_degrees": None,
            "grape_varieties": [],
            "food_pairings": [],
            "food_pairings_text": None,
            "serving_temperature": None,
            "indicative_price": None,
            "description": description,
            "tasting_notes": {"visual": None, "olfactory": None, "taste": None},
            "attributes": attributes,
            "notes": "Estratto senza IA: verifica attentamente i dati.",
        }],
    }


# ---------------------------------------------------------------------------
# Riconoscimento della cantina
# ---------------------------------------------------------------------------

_PRODUCER_STOPWORDS = {
    "cantina", "cantine", "azienda", "aziende", "agricola", "agraria", "vitivinicola", "vinicola", "tenuta", "tenute",
    "vini", "vino", "srl", "s", "r", "l", "sas", "snc", "spa", "societa", "soc", "cooperativa", "coop", "agr", "az",
    "di", "del", "della", "dei", "degli", "de", "la", "le", "il", "lo", "i", "e", "the", "winery", "wines", "estate",
    "fattoria", "masseria", "casa", "vinicola", "www", "it", "com", "http", "https",
}


def _producer_tokens(text: str) -> set:
    return {t for t in _key(text).split() if t not in _PRODUCER_STOPWORDS and len(t) > 1}


def match_producer(hint: Dict[str, Any], producers: Iterable[Dict[str, Any]]) -> Tuple[Optional[Any], float]:
    """Trova la cantina del catalogo piu' simile a quella indicata nel documento."""
    if not isinstance(hint, dict):
        return None, 0.0
    hint_tokens = _producer_tokens(hint.get("name") or "")
    website = (hint.get("website") or "").lower()
    domain = re.sub(r"^(https?://)?(www\.)?", "", website).split("/")[0]
    domain_tokens = _producer_tokens(domain.rsplit(".", 1)[0].replace("-", " ")) if domain else set()

    best, best_score = None, 0.0
    for p in producers:
        p_tokens = _producer_tokens(f"{p.get('company_name', '')} {p.get('slug', '').replace('-', ' ')}")
        if not p_tokens:
            continue
        score = 0.0
        if hint_tokens:
            score = len(hint_tokens & p_tokens) / len(hint_tokens)
        p_site = ((p.get("contacts") or {}).get("website") or "").lower()
        if domain and domain in p_site:
            score = max(score, 1.0)
        elif domain_tokens and domain_tokens & p_tokens:
            score = max(score, 0.8)
        if score > best_score:
            best, best_score = p, score
    return (best["_id"], best_score) if best is not None and best_score >= 0.5 else (None, best_score)


# ---------------------------------------------------------------------------
# Tipi di file accettati
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png", ".webp")
MAX_IMAGE_SIDE = 3000          # px: oltre si ridimensiona (il testo resta leggibile)
MAX_IMAGE_BYTES = 4 * 1024 * 1024


def detect_mime_type(data: bytes) -> Optional[str]:
    """Riconosce il tipo reale del file dai primi byte (non dall'estensione)."""
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def prepare_image(data: bytes, mime_type: str) -> Tuple[bytes, str]:
    """Ridimensiona le immagini troppo grandi e le converte in JPEG; lascia invariate le altre."""
    from PIL import Image, ImageOps

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:
        raise AIExtractionError("L'immagine non è leggibile o è danneggiata")
    if max(img.size) <= MAX_IMAGE_SIDE and len(data) <= MAX_IMAGE_BYTES:
        return data, mime_type
    img = ImageOps.exif_transpose(img)
    img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
    if img.mode not in ("RGB", "L"):
        background = Image.new("RGB", img.size, "white")
        background.paste(img, mask=img.convert("RGBA").split()[-1])
        img = background
    quality = 88
    while True:
        out = io.BytesIO()
        img.save(out, "JPEG", quality=quality, optimize=True)
        if out.tell() <= MAX_IMAGE_BYTES or quality <= 60:
            return out.getvalue(), "image/jpeg"
        quality -= 10


# ---------------------------------------------------------------------------
# Punto di ingresso
# ---------------------------------------------------------------------------

def process_document(file_bytes: bytes, filename: str, master_attributes: List[str], master_grapes: List[str],
                     canonical_pairings: List[str]) -> Dict[str, Any]:
    """Analizza un PDF o un'immagine (JPG, PNG, WebP) e restituisce {method, producer, wines, warnings}.
    Solleva AIExtractionError con un messaggio leggibile se il file non e' elaborabile."""
    grapes = list(dict.fromkeys(list(master_grapes) + VALID_SINGLE_GRAPES))
    pairings = canonical_pairings or CANONICAL_PAIRINGS

    mime_type = detect_mime_type(file_bytes)
    if not mime_type:
        raise AIExtractionError("Formato non supportato: carica un PDF oppure un'immagine JPG, PNG o WebP")

    provider = active_provider()
    if mime_type != "application/pdf":
        if not provider:
            raise AIExtractionError(
                "Per leggere le schede in formato immagine serve l'IA: configura GEMINI_API_KEY "
                "o ANTHROPIC_API_KEY nel file .env del backend."
            )
        file_bytes, mime_type = prepare_image(file_bytes, mime_type)

    if provider:
        raw = extract_with_ai(file_bytes, filename, master_attributes, grapes, pairings, mime_type=mime_type)
        method = f"ai:{provider}"
        model_used = raw.pop("_model_used", None)
    else:
        pdf_bytes = file_bytes
        text = extract_text_from_pdf(pdf_bytes)
        if len(text.strip()) < 40:
            raise AIExtractionError(
                "Il PDF non contiene testo (è uno screenshot o una scansione): per leggerlo serve l'IA. "
                "Configura GEMINI_API_KEY o ANTHROPIC_API_KEY nel file .env del backend."
            )
        raw = parse_text_fallback(text, filename)
        method = "text"
        model_used = None

    wines = []
    for w in raw.get("wines") or []:
        if isinstance(w, dict):
            normalized = normalize_wine(w, master_attributes, grapes, pairings)
            if normalized["name"]:
                wines.append(normalized)

    warnings = []
    if not wines:
        warnings.append("Nessun vino riconosciuto nel documento.")
    producer = raw.get("producer") if isinstance(raw.get("producer"), dict) else {}
    return {
        "file_type": "pdf" if mime_type == "application/pdf" else "image",
        "method": method,
        "model": model_used,
        "producer": {k: _clean(producer.get(k), 200) for k in ("name", "city", "website")},
        "wines": wines,
        "warnings": warnings,
    }


# Nome storico, usato da script esterni
process_pdf = process_document
