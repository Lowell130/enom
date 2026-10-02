"""Analisi del catalogo per l'Osservatorio e per l'area riservata.

Funzioni pure: ricevono le schede dei vini (documenti Mongo) e restituiscono
strutture pronte per i grafici. I testi delle schede sono scritti a mano o
estratti dall'IA, quindi ogni lettura e' tollerante ai formati diversi
("300/350 mt", "300m slm", "Fine settembre", "€14,00", "35,00€ - 55,00€"...).
"""
import re
import statistics
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Utilita' comuni
# ---------------------------------------------------------------------------

CATEGORY_ORDER = ["VINO_ROSSO", "VINO_BIANCO", "ROSATO", "SPUMANTE", "PASSITO", "LIQUORE"]


def normalize_category(cat: Optional[str]) -> str:
    c = (cat or "").strip().upper().replace(" ", "_")
    if c in CATEGORY_ORDER:
        return c
    for key, target in (("ROSSO", "VINO_ROSSO"), ("BIANCO", "VINO_BIANCO"), ("ROSATO", "ROSATO"),
                        ("SPUMANTE", "SPUMANTE"), ("PASSITO", "PASSITO"), ("LIQUORE", "LIQUORE"), ("GRAPPA", "LIQUORE")):
        if key in c:
            return target
    return c or "ALTRO"


def attr_value(product: dict, *patterns: str) -> Optional[str]:
    """Valore del primo attributo della scheda il cui nome contiene uno dei pattern (minuscolo)."""
    for attr in product.get("custom_attributes") or []:
        if not isinstance(attr, dict):
            continue
        name = str(attr.get("name") or "").lower().strip()
        value = str(attr.get("value") or "").strip()
        if value and any(p in name for p in patterns):
            return value
    return None


_PCT_THEN_NAME = re.compile(r"(\d+(?:[.,]\d+)?\s*%)\s*[-–]?\s*(?=[A-Za-zÀ-ÿ])")


def split_grape_entry(text: str) -> List[str]:
    """Divide una voce con piu' vitigni: 'Montepulciano 55% Sangiovese 45%' -> ['Montepulciano 55%', 'Sangiovese 45%'].
    Solo quando le percentuali sono almeno due: 'Tintilia 100%' o 'Coda di Volpe' restano come sono."""
    t = str(text or "").strip()
    # "Montepulciano in purezza" -> "Montepulciano 100%"
    if re.search(r"\bin\s+purezza\b", t, re.I):
        t = re.sub(r"\s*\bin\s+purezza\b\s*", " ", t, flags=re.I).strip()
        if "%" not in t:
            t = f"{t} 100%"
    if len(re.findall(r"\d+(?:[.,]\d+)?\s*%", t)) < 2:
        return [t] if t else []
    t = _PCT_THEN_NAME.sub(r"\1,", t)
    return [part.strip(" -;/") for part in re.split(r"[,;/+]", t) if part.strip(" -;/")]


def split_grape_list(values: Any) -> Any:
    if not isinstance(values, list):
        return values
    out: List[Any] = []
    for v in values:
        out.extend(split_grape_entry(v) if isinstance(v, str) else [v])
    return out


def clean_grape(name: str) -> str:
    g = re.sub(r"\s*\d+([.,]\d+)?\s*%", "", str(name or "")).strip(" -,;")
    return g[:1].upper() + g[1:] if g else ""


def grapes_of(product: dict) -> List[str]:
    seen, out = set(), []
    for g in product.get("grape_varieties") or []:
        c = clean_grape(g)
        if c and c.lower() not in seen:
            seen.add(c.lower())
            out.append(c)
    return out


def primary_grape(product: dict) -> Optional[str]:
    g = grapes_of(product)
    return g[0] if g else None


def wine_ref(product: dict) -> Dict[str, Any]:
    return {
        "name": product.get("name"),
        "slug": product.get("slug"),
        "producer": product.get("producer_name"),
        "category": normalize_category(product.get("category")),
    }


def _pct(part: int, total: int) -> float:
    return round(part * 100 / total, 1) if total else 0.0


# ---------------------------------------------------------------------------
# 1. Calendario della vendemmia
# ---------------------------------------------------------------------------

MONTHS = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6, "luglio": 7,
    "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}
MONTH_LABELS = {v: k.capitalize() for k, v in MONTHS.items()}
_ABBR = {"gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6, "lug": 7, "ago": 8, "set": 9, "sett": 9, "ott": 10, "nov": 11, "dic": 12}
# nomi interi, oppure abbreviazioni come parola a se' ("sett." si', "settimana" no)
_MONTH_RE = re.compile(r"\b(" + "|".join(MONTHS) + r")\b|\b(" + "|".join(_ABBR) + r")\b\.?")


def parse_harvest_months(text: Optional[str]) -> List[int]:
    """Mesi di raccolta citati nel testo; 'settembre-ottobre' o 'da settembre a ottobre' diventano un intervallo."""
    if not text:
        return []
    t = text.lower()
    found = []
    for m in _MONTH_RE.finditer(t):
        month = MONTHS.get(m.group(1) or "") or _ABBR.get(m.group(2) or "")
        if month is None:
            continue
        found.append(month)
    if not found:
        return []
    months = sorted(set(found))
    # intervallo esplicito tra due mesi ("settembre - ottobre", "da settembre a novembre")
    if len(months) >= 2 and re.search(r"[-–/]|\ba\b|\bfino\b|\be\b", t):
        months = list(range(months[0], months[-1] + 1))
    return months


def harvest_calendar(products: Iterable[dict], top_grapes: int = 8) -> Dict[str, Any]:
    by_month: Counter = Counter()
    by_grape: Dict[str, Counter] = defaultdict(Counter)
    grape_total: Counter = Counter()
    with_data = 0
    for p in products:
        months = parse_harvest_months(attr_value(p, "raccolta", "vendemmia"))
        if not months:
            continue
        with_data += 1
        for m in months:
            by_month[m] += 1
        g = primary_grape(p)
        if g:
            grape_total[g] += 1
            for m in months:
                by_grape[g][m] += 1
    if not with_data:
        return {"wines_with_data": 0, "months": [], "grapes": []}
    first, last = min(by_month), max(by_month)
    month_list = list(range(first, last + 1))
    grapes = []
    for g, total in grape_total.most_common(top_grapes):
        counts = by_grape[g]
        peak = max(counts.values())
        grapes.append({
            "grape": g,
            "wines": total,
            "months": [{"month": m, "count": counts.get(m, 0), "intensity": round(counts.get(m, 0) / peak, 2) if peak else 0}
                       for m in month_list],
        })
    return {
        "wines_with_data": with_data,
        "months": [{"month": m, "label": MONTH_LABELS[m], "count": by_month.get(m, 0)} for m in month_list],
        "grapes": grapes,
    }


# ---------------------------------------------------------------------------
# 2. Comuni di produzione (per la mappa)
# ---------------------------------------------------------------------------

_ZONE_RE = re.compile(r"([A-Za-zÀ-ÿ'’\s]+?)\s*\((CB|IS)\)", re.IGNORECASE)


def production_town(product: dict, producer_city: Optional[str]) -> Optional[str]:
    zona = attr_value(product, "zona di produzione")
    if zona:
        m = _ZONE_RE.search(zona)
        if m:
            return m.group(1).strip().title()
    return producer_city


def towns_breakdown(products: Iterable[dict], producer_city: Dict[str, str], producer_info: Dict[str, dict]) -> List[Dict[str, Any]]:
    towns: Dict[str, Dict[str, Any]] = {}
    for p in products:
        pid = str(p.get("producer_id"))
        town = production_town(p, producer_city.get(pid))
        if not town:
            continue
        entry = towns.setdefault(town, {"city": town, "count": 0, "producers": {}, "categories": Counter()})
        entry["count"] += 1
        entry["categories"][normalize_category(p.get("category"))] += 1
        info = producer_info.get(pid)
        if info:
            entry["producers"][pid] = info
    out = []
    for t in sorted(towns.values(), key=lambda x: x["count"], reverse=True):
        out.append({
            "city": t["city"],
            "count": t["count"],
            "producers": list(t["producers"].values()),
            "categories": [{"category": c, "count": n} for c, n in t["categories"].most_common()],
        })
    return out


# ---------------------------------------------------------------------------
# 3. Altitudine dei vigneti
# ---------------------------------------------------------------------------

ALTITUDE_BANDS = [(0, 200, "Fino a 200 m"), (200, 400, "200–400 m"), (400, 600, "400–600 m"), (600, 10000, "Oltre 600 m")]


def parse_altitude(text: Optional[str]) -> Optional[int]:
    """Altitudine media in metri: '300/350 mt' -> 325, '500m s.l.m.' -> 500, '100-120 mt' -> 110."""
    if not text:
        return None
    t = text.lower().replace(".", "")
    nums = [int(n) for n in re.findall(r"\d{2,4}", t)]
    nums = [n for n in nums if 0 < n <= 1500]
    if not nums:
        return None
    nums = nums[:2]
    return round(sum(nums) / len(nums))


def altitude_profile(products: Iterable[dict], min_wines_per_grape: int = 3) -> Dict[str, Any]:
    band_counts: Counter = Counter()
    band_grapes: Dict[str, Counter] = defaultdict(Counter)
    grape_alts: Dict[str, List[int]] = defaultdict(list)
    values = []
    highest: Optional[Tuple[int, dict]] = None
    for p in products:
        alt = parse_altitude(attr_value(p, "altitudine"))
        if alt is None:
            continue
        values.append(alt)
        label = next(lbl for lo, hi, lbl in ALTITUDE_BANDS if lo <= alt < hi)
        band_counts[label] += 1
        g = primary_grape(p)
        if g:
            band_grapes[label][g] += 1
            grape_alts[g].append(alt)
        if highest is None or alt > highest[0]:
            highest = (alt, p)
    total = len(values)
    bands = [{
        "label": lbl, "min": lo, "max": hi if hi < 10000 else None,
        "count": band_counts.get(lbl, 0), "percentage": _pct(band_counts.get(lbl, 0), total),
        "top_grapes": [g for g, _ in band_grapes[lbl].most_common(3)],
    } for lo, hi, lbl in ALTITUDE_BANDS]
    grapes = sorted([
        {"grape": g, "avg_altitude": round(statistics.mean(v)), "wines": len(v)}
        for g, v in grape_alts.items() if len(v) >= min_wines_per_grape
    ], key=lambda x: x["avg_altitude"], reverse=True)
    return {
        "wines_with_data": total,
        "median_altitude": round(statistics.median(values)) if values else None,
        "bands": bands,
        "grapes": grapes[:8],
        "highest": ({"altitude": highest[0], **wine_ref(highest[1])} if highest else None),
    }


# ---------------------------------------------------------------------------
# 4. Terreni
# ---------------------------------------------------------------------------

SOIL_KEYWORDS = [
    ("Argilloso", ("argill",)),
    ("Calcareo", ("calcar",)),
    ("Sabbioso", ("sabbi",)),
    ("Limoso", ("limo", "limos")),
    ("Medio impasto", ("medio impasto", "franco")),
    ("Ricco di scheletro", ("scheletr", "ciottol", "sassos", "pietros", "ghiai")),
    ("Marnoso", ("marn",)),
    ("Tufaceo", ("tufo", "tufac")),
    ("Alluvionale", ("alluvion",)),
    ("Vulcanico", ("vulcan",)),
]


def parse_soils(text: Optional[str]) -> List[str]:
    if not text:
        return []
    t = text.lower()
    return [label for label, keys in SOIL_KEYWORDS if any(k in t for k in keys)]


def soil_profile(products: Iterable[dict]) -> Dict[str, Any]:
    counts: Counter = Counter()
    grapes: Dict[str, Counter] = defaultdict(Counter)
    combos: Counter = Counter()
    with_data = 0
    for p in products:
        soils = parse_soils(attr_value(p, "terreno", "suolo"))
        if not soils:
            continue
        with_data += 1
        combos[" e ".join(s.lower() for s in soils[:2])] += 1
        g = primary_grape(p)
        for s in soils:
            counts[s] += 1
            if g:
                grapes[s][g] += 1
    return {
        "wines_with_data": with_data,
        "soils": [{"soil": s, "count": n, "percentage": _pct(n, with_data), "top_grapes": [g for g, _ in grapes[s].most_common(3)]}
                  for s, n in counts.most_common()],
        "most_common_combo": combos.most_common(1)[0][0] if combos else None,
    }


# ---------------------------------------------------------------------------
# 5. Guida al servizio
# ---------------------------------------------------------------------------

def parse_temperature(text: Optional[str]) -> Optional[Tuple[float, float]]:
    """'16-18°C' -> (16, 18); '10°' -> (10, 10). Scarta valori fuori scala."""
    if not text:
        return None
    nums = [float(n.replace(",", ".")) for n in re.findall(r"\d{1,2}(?:[.,]\d)?", str(text))]
    nums = [n for n in nums if 2 <= n <= 24]
    if not nums:
        return None
    return (min(nums[:2]), max(nums[:2]))


def serving_guide(products: Iterable[dict]) -> List[Dict[str, Any]]:
    temps: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    alcohol: Dict[str, List[float]] = defaultdict(list)
    counts: Counter = Counter()
    for p in products:
        cat = normalize_category(p.get("category"))
        counts[cat] += 1
        t = parse_temperature(p.get("serving_temperature"))
        if t:
            temps[cat].append(t)
        try:
            a = float(p.get("alcohol_degrees")) if p.get("alcohol_degrees") not in (None, "") else None
        except (TypeError, ValueError):
            a = None
        if a and 5 <= a <= 60:
            alcohol[cat].append(a)
    out = []
    for cat in CATEGORY_ORDER + sorted(set(counts) - set(CATEGORY_ORDER)):
        if not counts.get(cat):
            continue
        t = temps.get(cat) or []
        out.append({
            "category": cat,
            "wines": counts[cat],
            "temp_min": round(statistics.median(x[0] for x in t)) if t else None,
            "temp_max": round(statistics.median(x[1] for x in t)) if t else None,
            "avg_alcohol": round(statistics.mean(alcohol[cat]), 1) if alcohol.get(cat) else None,
        })
    return out


# ---------------------------------------------------------------------------
# 6. Prezzi
# ---------------------------------------------------------------------------

PRICE_BANDS = [(0, 15, "Fino a 15 €"), (15, 25, "15–25 €"), (25, 40, "25–40 €"), (40, 100000, "Oltre 40 €")]


def _price_numbers(text: str) -> List[float]:
    nums = []
    for raw in re.findall(r"\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?", text):
        if "," in raw or re.fullmatch(r"\d{1,3}(?:\.\d{3})+", raw):
            raw = raw.replace(".", "").replace(",", ".")
        try:
            n = float(raw)
        except ValueError:
            continue
        if 0 < n < 2000:
            nums.append(n)
    return nums[:2]


def parse_price(text: Any) -> Optional[float]:
    """Prezzo in euro: '17,00 €' -> 17; '€14,00' -> 14; '35,00€ - 55,00€' -> 45 (centro della fascia)."""
    if text is None or text == "":
        return None
    if isinstance(text, (int, float)):
        return float(text) if 0 < text < 2000 else None
    nums = _price_numbers(str(text))
    if not nums:
        return None
    return round(sum(nums) / len(nums), 2)


def normalize_price_text(text: Any) -> Any:
    """Scrive i prezzi sempre allo stesso modo: '€14' -> '14,00 €', '35€-55€' -> '35,00 – 55,00 €'.
    Se il testo contiene altre parole (es. 'su richiesta', '15 € in cantina') resta com'e'."""
    if text is None or isinstance(text, (int, float)):
        return format_price(float(text)) if isinstance(text, (int, float)) and 0 < text < 2000 else text
    t = str(text).strip()
    if not t:
        return t
    rest = re.sub(r"\d|[.,€\s\-–/]|\beur(o)?\b|\ba\b|\bda\b", "", t, flags=re.IGNORECASE)
    nums = _price_numbers(t)
    if rest or not nums:
        return t
    if len(nums) == 2 and nums[0] != nums[1]:
        lo, hi = sorted(nums)
        return f"{format_price(lo)[:-2]} – {format_price(hi)}"
    return format_price(nums[0])


def normalize_temperature_text(text: Any) -> Any:
    """Temperatura di servizio sempre nello stesso formato: '16 - 18°' -> '16-18°C', '15°' -> '15°C'.
    Un testo senza numeri ('Scheda tecnica') non e' una temperatura e viene svuotato."""
    if text is None:
        return text
    t = str(text).strip()
    if not t:
        return t
    nums = [n.replace(",", ".") for n in re.findall(r"\d{1,2}(?:[.,]\d)?", t)]
    nums = [n[:-2] if n.endswith(".0") else n for n in nums if 0 <= float(n) <= 30]
    if not nums:
        return ""
    nums = [n.replace(".", ",") for n in nums]
    if len(nums) >= 2 and nums[0] != nums[1]:
        return f"{nums[0]}-{nums[1]}°C"
    return f"{nums[0]}°C"


def format_price(value: float) -> str:
    """17.0 -> '17,00 €' (stesso formato per tutto il catalogo)."""
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


def price_profile(products: List[dict]) -> Dict[str, Any]:
    prices: List[Tuple[float, dict]] = []
    for p in products:
        v = parse_price(p.get("indicative_price"))
        if v is not None:
            prices.append((v, p))
    total = len(prices)
    bands = []
    for lo, hi, lbl in PRICE_BANDS:
        n = sum(1 for v, _ in prices if lo <= v < hi)
        bands.append({"label": lbl, "min": lo, "max": hi if hi < 100000 else None, "count": n, "percentage": _pct(n, total)})
    by_cat: Dict[str, List[float]] = defaultdict(list)
    for v, p in prices:
        by_cat[normalize_category(p.get("category"))].append(v)
    categories = [{
        "category": c, "wines": len(v), "median": round(statistics.median(v), 2),
        "min": min(v), "max": max(v),
    } for c, v in sorted(by_cat.items(), key=lambda x: CATEGORY_ORDER.index(x[0]) if x[0] in CATEGORY_ORDER else 99)]
    return {
        "wines_with_price": total,
        "wines_total": len(products),
        "coverage": _pct(total, len(products)),
        "median": round(statistics.median(v for v, _ in prices), 2) if prices else None,
        "bands": bands,
        "categories": categories,
    }


# ---------------------------------------------------------------------------
# 7. Autoctoni e internazionali, biologico
# ---------------------------------------------------------------------------

NATIVE_MOLISE = {"tintilia"}
TRADITIONAL = {
    "montepulciano", "aglianico", "falanghina", "trebbiano", "malvasia", "greco", "fiano", "moscato",
    "bombino", "sangiovese", "primitivo", "coda di volpe", "piedirosso", "barbera", "nero di troia",
    "uva di troia", "pecorino", "passerina", "cococciola", "camaiola", "lambrusco", "aleatico",
}
INTERNATIONAL = {
    "cabernet", "merlot", "chardonnay", "sauvignon", "syrah", "shiraz", "pinot", "riesling", "traminer",
    "gewurztraminer", "müller", "muller", "petit verdot", "viognier", "tempranillo", "grenache", "incrocio manzoni",
}

GROUP_LABELS = {
    "tintilia": "Con Tintilia, l'autoctono del Molise",
    "traditional": "Vitigni tradizionali del Centro-Sud",
    "international": "Con vitigni internazionali",
    "other": "Altro o non indicato",
}


def grape_group(name: str) -> str:
    n = name.lower()
    if any(k in n for k in NATIVE_MOLISE):
        return "tintilia"
    if any(k in n for k in INTERNATIONAL):
        return "international"
    if any(k in n for k in TRADITIONAL):
        return "traditional"
    return "other"


def product_grape_group(product: dict) -> str:
    groups = {grape_group(g) for g in grapes_of(product)}
    for g in ("tintilia", "international", "traditional"):
        if g in groups:
            return g
    return "other"


def heritage_profile(products: List[dict], is_organic) -> Dict[str, Any]:
    total = len(products)
    groups: Counter = Counter(product_grape_group(p) for p in products)
    intl: Counter = Counter()
    for p in products:
        for g in grapes_of(p):
            if grape_group(g) == "international":
                intl[g] += 1
    organic_by_cat: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    for p in products:
        cat = normalize_category(p.get("category"))
        organic_by_cat[cat][1] += 1
        if is_organic(p):
            organic_by_cat[cat][0] += 1
    organic_total = sum(v[0] for v in organic_by_cat.values())
    return {
        "groups": [{"group": g, "label": GROUP_LABELS[g], "count": groups.get(g, 0), "percentage": _pct(groups.get(g, 0), total)}
                   for g in ("tintilia", "traditional", "international", "other")],
        "native_share": _pct(groups.get("tintilia", 0) + groups.get("traditional", 0), total),
        "international_grapes": [{"name": g, "count": n} for g, n in intl.most_common(6)],
        "organic": {
            "count": organic_total,
            "percentage": _pct(organic_total, total),
            "categories": [{"category": c, "organic": v[0], "total": v[1], "percentage": _pct(v[0], v[1])}
                           for c, v in sorted(organic_by_cat.items(), key=lambda x: CATEGORY_ORDER.index(x[0]) if x[0] in CATEGORY_ORDER else 99)],
        },
    }


# ---------------------------------------------------------------------------
# 8. Abbinamenti per tipologia ("cosa bere con...")
# ---------------------------------------------------------------------------

def pairing_guide(products: List[dict], top: int = 8, wines_per_pairing: int = 3) -> List[Dict[str, Any]]:
    by_pairing: Dict[str, List[dict]] = defaultdict(list)
    labels: Dict[str, str] = {}
    for p in products:
        for raw in p.get("food_pairings") or []:
            name = str(raw or "").strip()
            if not name:
                continue
            key = name.lower()
            labels.setdefault(key, name)
            by_pairing[key].append(p)
    out = []
    for key, wines in sorted(by_pairing.items(), key=lambda x: len(x[1]), reverse=True)[:top]:
        cats = Counter(normalize_category(w.get("category")) for w in wines)
        # esempi da cantine diverse, preferendo i vini con foto
        examples, seen = [], set()
        for w in sorted(wines, key=lambda w: (not w.get("photos"), w.get("name") or "")):
            pid = str(w.get("producer_id"))
            if pid in seen:
                continue
            seen.add(pid)
            examples.append(wine_ref(w))
            if len(examples) == wines_per_pairing:
                break
        out.append({
            "pairing": labels[key],
            "wines": len(wines),
            "categories": [{"category": c, "count": n, "percentage": _pct(n, len(wines))} for c, n in cats.most_common(3)],
            "examples": examples,
        })
    return out


# ---------------------------------------------------------------------------
# Area riservata: completezza delle schede e richieste
# ---------------------------------------------------------------------------

COMPLETENESS_FIELDS = [
    ("photos", "Foto"),
    ("description", "Descrizione"),
    ("indicative_price", "Prezzo indicativo"),
    ("vintage_year", "Annata"),
    ("alcohol_degrees", "Gradazione"),
    ("serving_temperature", "Temperatura di servizio"),
    ("tasting_notes", "Note di degustazione"),
    ("food_pairings", "Abbinamenti"),
    ("grape_varieties", "Vitigni"),
    ("denominazione", "Denominazione"),
]


def _has(product: dict, field: str) -> bool:
    v = product.get(field)
    if v is None or v == "" or v == []:
        return False
    if isinstance(v, dict):
        return any(str(x or "").strip() for x in v.values())
    if isinstance(v, str):
        return bool(v.strip())
    return True


# Campi mostrati ma non conteggiati: molti vini non hanno un'annata (spumanti, grappe, vini senza annata)
OPTIONAL_FIELDS = {"vintage_year"}


def completeness_report(products: List[dict], worst: int = 15) -> Dict[str, Any]:
    total = len(products)
    fields = [{"field": f, "label": lbl, "optional": f in OPTIONAL_FIELDS,
               "filled": sum(1 for p in products if _has(p, f)),
               "percentage": _pct(sum(1 for p in products if _has(p, f)), total)} for f, lbl in COMPLETENESS_FIELDS]
    counted = [(f, lbl) for f, lbl in COMPLETENESS_FIELDS if f not in OPTIONAL_FIELDS]
    rows = []
    for p in products:
        missing = [lbl for f, lbl in counted if not _has(p, f)]
        score = round((len(counted) - len(missing)) * 100 / len(counted))
        rows.append({"id": str(p.get("_id") or p.get("id")), "score": score, "missing": missing, **wine_ref(p),
                     "status": p.get("status")})
    rows.sort(key=lambda r: (r["score"], r["name"] or ""))
    return {
        "wines": total,
        "average_score": round(statistics.mean(r["score"] for r in rows)) if rows else 0,
        "complete": sum(1 for r in rows if r["score"] == 100),
        "fields": sorted(fields, key=lambda f: (f["optional"], f["percentage"])),
        "to_improve": [r for r in rows if r["score"] < 100][:worst],
    }


def inquiries_report(inquiries: List[dict], products_by_id: Dict[str, dict], producers_by_id: Dict[str, dict], top: int = 10) -> Dict[str, Any]:
    by_product: Counter = Counter()
    last_by_product: Dict[str, Any] = {}
    by_type: Counter = Counter()
    by_producer: Counter = Counter()
    for inq in inquiries:
        by_type[inq.get("message_type") or "ALTRO"] += 1
        by_producer[str(inq.get("producer_id"))] += 1
        pid = inq.get("product_id")
        if pid:
            pid = str(pid)
            by_product[pid] += 1
            created = inq.get("created_at")
            if created and (pid not in last_by_product or created > last_by_product[pid]):
                last_by_product[pid] = created
    top_products = []
    for pid, n in by_product.most_common(top):
        prod = products_by_id.get(pid)
        if not prod:
            continue
        top_products.append({"id": pid, "requests": n, "last_request": last_by_product.get(pid), **wine_ref(prod)})
    return {
        "total": len(inquiries),
        "unread": sum(1 for i in inquiries if not i.get("is_read")),
        "about_a_wine": sum(by_product.values()),
        "types": [{"type": t, "count": n} for t, n in by_type.most_common()],
        "top_wines": top_products,
        "top_producers": [{"id": pid, "name": (producers_by_id.get(pid) or {}).get("company_name"), "requests": n}
                          for pid, n in by_producer.most_common(5) if pid in producers_by_id],
    }
