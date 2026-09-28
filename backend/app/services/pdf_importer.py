import io
import os
import re
import json
import pypdf
from typing import List, Dict, Any, Optional
from datetime import datetime

# Whitelist of Valid Single Grapes for EnotecaMolise Taxonomy
VALID_SINGLE_GRAPES = [
    "Aglianico", "Bombino Bianco", "Cabernet Sauvignon", "Cerasuolo", "Chardonnay",
    "Falanghina", "Garganega", "Garganica", "Greco", "Malvasia", "Merlot",
    "Montepulciano", "Moscato", "Moscato Bianco", "Moscato Reale", "Pinot Grigio",
    "Pinot Nero", "Riesling", "Sangiovese", "Sauvignon Blanc", "Syrah", "Tintilia",
    "Trebbiano", "Trebbiano del Molise"
]

# Canonical Food Pairing Rules
PAIRING_RULES = [
    (r'cacciagione|selvaggina', "Cacciagione & Selvaggina"),
    (r'antipast|aperitiv|finger food', "Antipasti & Aperitivi"),
    (r'carne rossa|carni rosse|griglia|grigliat', "Carni Rosse & Grigliate"),
    (r'arrost|tagliat', "Arrosti & Tagliate"),
    (r'pampanella', "Pampanella Molisana"),
    (r'formagg.*fresch|spalmabil', "Formaggi Freschi"),
    (r'formagg.*stagionat|pasta filata|erborinat|media stagionatura', "Formaggi Stagionati"),
    (r'salumi|affettat', "Salumi & Affettati"),
    (r'primi|sugo|ragù|ragu|zupp.*legum', "Primi Piatti & Ragù"),
    (r'risott|tartufo|porcini', "Risotti & Tartufo"),
    (r'pesce|frutti di mare|brodetto', "Pesce & Frutti di Mare"),
    (r'vegetarian', "Piatti Vegetariani"),
    (r'pizz|lievitat', "Pizze & Lievitati"),
    (r'dolc|pasticceri', "Pasticceria & Dolci"),
    (r'paté|pate|piatti freddi', "Paté & Piatti Freddi")
]

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF bytes using pypdf."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        extracted_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                extracted_text.append(t)
        return "\n".join(extracted_text)
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def clean_wine_name(name: str) -> str:
    if not name:
        return ""
    # Remove DOC, DOCG, IGT, DOP, 4-digit years
    cleaned = re.sub(r'(?i)\b(?:d[\s.]*o[\s.]*c[\s.]*g|d[\s.]*o[\s.]*c|d[\s.]*o[\s.]*p|i[\s.]*g[\s.]*p|i[\s.]*g[\s.]*t)\b\.?', '', name)
    cleaned = re.sub(r'\b(19\d{2}|20\d{2})\b', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(' -.,')
    return cleaned if cleaned else name.strip()

def normalize_grapes_list(raw_grapes: Any) -> List[str]:
    """Map raw grape text into list of valid single grapes."""
    if not raw_grapes:
        return []
    
    grapes_str = ""
    if isinstance(raw_grapes, list):
        grapes_str = " ".join(str(g) for g in raw_grapes)
    else:
        grapes_str = str(raw_grapes)

    matched_grapes = set()
    for vg in VALID_SINGLE_GRAPES:
        pattern = r'\b' + re.escape(vg) + r'\b'
        if re.search(pattern, grapes_str, re.IGNORECASE):
            matched_grapes.add(vg)

    # Fallback if no whitelist match
    if not matched_grapes and grapes_str:
        cleaned_parts = [g.strip() for g in re.split(r'[,;\-\/]', grapes_str) if g.strip()]
        for part in cleaned_parts:
            no_pct = re.sub(r'\d+\s*%', '', part).strip()
            if no_pct:
                matched_grapes.add(no_pct.capitalize())

    return sorted(list(matched_grapes))

def normalize_food_pairings(raw_pairings: Any) -> List[str]:
    """Map raw pairings into canonical taxonomy list."""
    if not raw_pairings:
        return []
    
    pairings_list = []
    if isinstance(raw_pairings, list):
        pairings_list = [str(p).strip() for p in raw_pairings if str(p).strip()]
    elif isinstance(raw_pairings, str):
        pairings_list = [p.strip() for p in raw_pairings.split(',') if p.strip()]

    canonical_set = set()
    for item in pairings_list:
        matched = False
        for pattern, canonical in PAIRING_RULES:
            if re.search(pattern, item, re.IGNORECASE):
                canonical_set.add(canonical)
                matched = True
                break
        if not matched and len(item) > 2:
            canonical_set.add(item.capitalize())

    return sorted(list(canonical_set))

def parse_with_gemini_ai(text_content: str, filename: str) -> Optional[Dict[str, Any]]:
    """Use Gemini AI API if GEMINI_API_KEY environment variable is present."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
Sei un esperto sommelier e data-extractor per EnotecaMolise.
Analizza il seguente testo estratto dalla scheda tecnica PDF di un vino (Nome file: {filename}).

TESTO SCHEDA TECNICA:
---
{text_content}
---

Estrai le informazioni in formato JSON RIGIDO con i seguenti campi esattamente denominati:
- "name": Nome commerciale del vino (stringa senza annata e senza DOC/IGT, es. "Tintilia del Molise Riserva")
- "category": Una tra ["VINO_ROSSO", "VINO_BIANCO", "ROSATO", "SPUMANTE", "PASSITO", "LIQUORE"]
- "denominazione": Una tra ["DOC", "DOCG", "IGT", "IGP", "DOP"]
- "vintage_year": Anno vendemmia (numero intero o null se non specificata / Senza Annata)
- "is_riserva": boolean (true se menzione Riserva, false altrimenti)
- "alcohol_degrees": numero float (es. 14.5 o 13.0)
- "grape_varieties": array di stringhe dei vitigni (es. ["Tintilia"] o ["Montepulciano", "Aglianico"])
- "food_pairings": array di stringhe degli abbinamenti consigliati
- "serving_temperature": stringa (es. "16° - 18° C")
- "description": descrizione o presentazione del vino
- "tasting_notes": oggetto con keys "visual", "olfactory", "taste"
- "custom_attributes": array di oggetti {{"name": "...", "value": "..."}} per dettagli come Vinificazione, Affinamento, Allevamento, Formato Bottiglia, Allergeni.

Restituisci SOLO il JSON valido senza marcatori markdown.
"""
        response = model.generate_content(prompt)
        raw_resp = response.text.strip()
        raw_resp = re.sub(r'^```json\s*', '', raw_resp, flags=re.MULTILINE)
        raw_resp = re.sub(r'```$', '', raw_resp, flags=re.MULTILINE).strip()
        data = json.loads(raw_resp)
        return data
    except Exception as e:
        print(f"Gemini AI parsing fallback: {e}")
        return None

def parse_with_sommelier_nlp(text_content: str, filename: str) -> Dict[str, Any]:
    """NLP & Regex Sommelier Heuristic Parser for offline/fallback PDF extraction."""
    lines = [l.strip() for l in text_content.splitlines() if l.strip()]
    full_text = " ".join(lines)
    lower_text = full_text.lower()

    # 1. Determine Title / Name
    raw_title = ""
    # Try finding title from first line or filename
    clean_fn = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
    if lines:
        for line in lines[:5]:
            if len(line) > 3 and not re.search(r'scheda|tecnica|pagina|telefono|email|www\.', line, re.I):
                raw_title = line
                break
    if not raw_title:
        raw_title = clean_fn

    name = clean_wine_name(raw_title)

    # 2. Category
    category = "VINO_ROSSO"
    if re.search(r'spumante|brut|bollicin', lower_text):
        category = "SPUMANTE"
    elif re.search(r'rosato|rosé', lower_text):
        category = "ROSATO"
    elif re.search(r'bianco|falanghina|trebbiano|malvasia|chardonnay|greco', lower_text):
        category = "VINO_BIANCO"
    elif re.search(r'passito|moscato reale', lower_text):
        category = "PASSITO"

    # 3. Denomination
    denominazione = "DOC"
    if re.search(r'docg|d\.o\.c\.g\.', lower_text):
        denominazione = "DOCG"
    elif re.search(r'igt|i\.g\.t\.', lower_text):
        denominazione = "IGT"
    elif re.search(r'dop|d\.o\.p\.', lower_text):
        denominazione = "DOP"

    # 4. Alcohol Degrees
    alc_match = re.search(r'(\d{2}(?:[.,]\d)?)\s*%\s*(?:vol)?', lower_text)
    alcohol_degrees = float(alc_match.group(1).replace(',', '.')) if alc_match else 13.5

    # 5. Vintage Year & Riserva
    year_match = re.search(r'\b(20[0-2]\d)\b', full_text)
    vintage_year = int(year_match.group(1)) if year_match else None
    is_riserva = bool(re.search(r'riserva', lower_text))

    # 6. Serving Temperature
    temp_match = re.search(r'(\d{1,2}\s*[-–°]\s*\d{1,2}\s*°?\s*C)', full_text, re.I)
    serving_temperature = temp_match.group(1).strip() if temp_match else "16° - 18° C"

    # 7. Grapes
    grapes = normalize_grapes_list(full_text)

    # 8. Food Pairings
    pairings = normalize_food_pairings(full_text)

    # 9. Custom Attributes
    custom_attributes = []
    
    # Vinificazione
    vin_match = re.search(r'(?:vinificazione|lavorazione|fermentazione)[:\s]+([^.\n]+)', full_text, re.I)
    if vin_match:
        custom_attributes.append({"name": "Vinificazione", "value": vin_match.group(1).strip()})

    # Affinamento
    aff_match = re.search(r'(?:affinamento|maturazione|invecchiamento)[:\s]+([^.\n]+)', full_text, re.I)
    if aff_match:
        custom_attributes.append({"name": "Affinamento", "value": aff_match.group(1).strip()})

    # Allevamento
    all_match = re.search(r'(?:allevamento|potatura|sistema)[:\s]+([^.\n]+)', full_text, re.I)
    if all_match:
        custom_attributes.append({"name": "Allevamento", "value": all_match.group(1).strip()})

    # Formato Bottiglia
    fmt_match = re.search(r'(75\s*cl|1\.5\s*L|37\.5\s*cl|3\.0\s*L|magnum)', full_text, re.I)
    bottle_format = fmt_match.group(1).strip() if fmt_match else "75 cl (Standard)"
    custom_attributes.append({"name": "Formato Bottiglia", "value": bottle_format})

    # Allergeni
    custom_attributes.append({"name": "Allergeni", "value": "Contiene Solfiti"})

    # Description & Tasting Notes
    desc = full_text[:400] + "..." if len(full_text) > 400 else full_text

    return {
        "name": name,
        "category": category,
        "denominazione": denominazione,
        "vintage_year": vintage_year,
        "is_riserva": is_riserva,
        "alcohol_degrees": alcohol_degrees,
        "grape_varieties": grapes,
        "food_pairings": pairings,
        "serving_temperature": serving_temperature,
        "description": desc,
        "tasting_notes": {
            "visual": "Rosso rubino vivido" if category == "VINO_ROSSO" else "Giallo paglierino brillante",
            "olfactory": "Profumi intensi e complessi",
            "taste": "Gusto equilibrato e persistente"
        },
        "custom_attributes": custom_attributes
    }

def process_pdf_wine_file(pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Master entry point to extract structured wine product from PDF."""
    text_content = extract_text_from_pdf(pdf_bytes)
    
    # Attempt AI Gemini parsing first
    ai_data = parse_with_gemini_ai(text_content, filename)
    if ai_data and isinstance(ai_data, dict) and ai_data.get("name"):
        # Post-process & normalize AI output
        ai_data["name"] = clean_wine_name(ai_data.get("name", ""))
        ai_data["grape_varieties"] = normalize_grapes_list(ai_data.get("grape_varieties"))
        ai_data["food_pairings"] = normalize_food_pairings(ai_data.get("food_pairings"))
        return ai_data

    # Fallback to Sommelier NLP parser
    nlp_data = parse_with_sommelier_nlp(text_content, filename)
    return nlp_data
