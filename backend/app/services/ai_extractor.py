"""Estrazione strutturata delle schede vino da PDF tramite modelli IA multimodali.

Il PDF viene inviato al modello cosi' com'e': funziona sia con schede testuali sia con
PDF composti da immagini (screenshot di pagine web, scansioni). La risposta e' vincolata
a uno schema JSON (Gemini: responseSchema, Claude: tool use), quindi non servono
euristiche per "ripulire" il testo generato.

Provider supportati (via REST, nessuna libreria aggiuntiva):
  - Google Gemini    -> GEMINI_API_KEY    (modello: GEMINI_MODEL)
  - Anthropic Claude -> ANTHROPIC_API_KEY (modello: ANTHROPIC_MODEL)
"""
import base64
import json
import logging
import time
from typing import Any, Dict, List, Optional

import requests

from app.core.config import settings

logger = logging.getLogger("enotecamolise.ai")

CATEGORIES = ["VINO_ROSSO", "VINO_BIANCO", "ROSATO", "SPUMANTE", "PASSITO", "LIQUORE"]
DENOMINATIONS = ["DOCG", "DOC", "DOP", "IGT", "IGP"]


class AIExtractionError(Exception):
    """Errore comprensibile da mostrare all'amministratore."""


class AIServiceBusy(AIExtractionError):
    """Errore temporaneo (sovraccarico, quota): si puo' riprovare o cambiare modello."""

    def __init__(self, message: str, status: int):
        super().__init__(message)
        self.status = status


class AIInvalidOutput(AIExtractionError):
    """Il modello ha risposto ma il JSON e' troncato o malformato: si riprova o si cambia modello."""

    def __init__(self, message: str, recitation: bool = False):
        super().__init__(message)
        # Gemini interrompe la risposta (RECITATION) quando sta copiando alla lettera testi pubblicati sul web
        self.recitation = recitation


# Aggiunta al prompt quando Gemini blocca la copia letterale dei testi (tipico delle pagine web catturate)
REWRITE_HINT = """

ATTENZIONE: il tentativo precedente è stato bloccato perché copiava alla lettera testi pubblicati sul web.
In "description", "tasting_notes" e "food_pairings_text" NON copiare il testo parola per parola:
riformulalo con parole tue, in italiano, in modo sintetico, mantenendo tutti i fatti presenti nel documento
e senza aggiungere nulla. Tutti gli altri campi restano dati da estrarre fedelmente."""


# Codici HTTP temporanei: il servizio e' sovraccarico o la quota del modello e' esaurita
TRANSIENT_STATUSES = {429, 500, 502, 503, 504, 529}
RETRY_DELAYS = (3, 8)
MAX_OUTPUT_TOKENS = 32768  # spazio sufficiente anche per pagine con molti vini e per il ragionamento del modello  # secondi di attesa tra i tentativi sullo stesso modello


# ---------------------------------------------------------------------------
# Configurazione provider
# ---------------------------------------------------------------------------

def active_provider() -> Optional[str]:
    provider = (settings.AI_PROVIDER or "auto").strip().lower()
    if provider == "gemini":
        return "gemini" if settings.GEMINI_API_KEY else None
    if provider == "anthropic":
        return "anthropic" if settings.ANTHROPIC_API_KEY else None
    if settings.GEMINI_API_KEY:
        return "gemini"
    if settings.ANTHROPIC_API_KEY:
        return "anthropic"
    return None


def provider_status() -> Dict[str, Any]:
    provider = active_provider()
    model = None
    if provider == "gemini":
        model = settings.GEMINI_MODEL
    elif provider == "anthropic":
        model = settings.ANTHROPIC_MODEL
    return {"configured": provider is not None, "provider": provider, "model": model}


# ---------------------------------------------------------------------------
# Prompt e schema
# ---------------------------------------------------------------------------

def build_prompt(filename: str, master_attributes: List[str], master_grapes: List[str], canonical_pairings: List[str]) -> str:
    attrs = ", ".join(master_attributes) or "(nessuno)"
    grapes = ", ".join(master_grapes) or "(nessuno)"
    pairings = ", ".join(canonical_pairings)
    return f"""Sei un sommelier esperto e un estrattore di dati per EnotecaMolise, il catalogo dei vini del Molise.
Il documento allegato ("{filename}") è la scheda tecnica di uno o più vini: può essere una scheda PDF
dell'azienda, una foto/immagine della scheda oppure la cattura (screenshot) di una pagina web del produttore.

COMPITO: estrai TUTTI i dati presenti per ogni vino descritto e restituiscili con lo strumento/schema richiesto.

REGOLE FONDAMENTALI
1. NON INVENTARE NULLA. Se un dato non è scritto nel documento usa null (o lista vuota). Non dedurre gradazione,
   annata, note di degustazione o abbinamenti che non sono presenti.
2. Estrai solo i vini che hanno una propria scheda/descrizione nel documento. IGNORA "prodotti correlati",
   "potrebbe interessarti", caroselli, carrello, menu, footer, cookie, recensioni e prezzi di altri vini.
   Se la pagina elenca più vini ciascuno con la propria descrizione, restituiscili tutti.
3. "name": il nome commerciale del vino come appare nel titolo, SENZA annata e SENZA sigla di denominazione
   (DOC/DOP/IGT...). Es. "Colle del Limone – Falanghina del Molise DOP" -> "Colle del Limone – Falanghina del Molise".
4. "vintage_year": solo l'annata della bottiglia descritta. NON usare "prima annata di produzione", anni di
   fondazione, anni di premi o l'anno del copyright.
5. "denominazione": solo la sigla (DOCG, DOC, DOP, IGT, IGP) se indicata; altrimenti null.
6. "category": deduci la tipologia (rosso, bianco, rosato, spumante, passito, liquore) dal documento e dalle uve.
7. "grape_varieties": un elemento per vitigno con la percentuale se indicata. Usa, quando corrisponde, il nome
   presente in questo elenco di vitigni già a catalogo: {grapes}.
8. "food_pairings": scegli SOLO tra queste categorie canoniche quelle coerenti con gli abbinamenti indicati nel
   documento: {pairings}. Riporta inoltre il testo originale degli abbinamenti in "food_pairings_text".
9. "serving_temperature": es. "10-12°C". "indicative_price": il prezzo del vino descritto, es. "15,00 €".
10. "description": il testo descrittivo/di presentazione del vino, riportato fedelmente (puoi solo correggere
    a capo e spazi). "tasting_notes": compila visivo/olfattivo/gustativo SOLO con frasi presenti nel documento
    (puoi estrarle dalla descrizione); altrimenti null.
11. "attributes": TUTTI gli altri dati tecnici presenti (es. comune/zona di produzione, altitudine, terreno,
    resa per ettaro, sistema di allevamento, densità d'impianto, epoca di vendemmia, raccolta, fermentazione,
    vinificazione, maturazione, affinamento, numero di bottiglie, prima annata, formato, allergeni, esposizione...).
    Un attributo per ogni voce, con valori puliti e completi (unità di misura incluse).
    Quando il significato coincide, usa ESATTAMENTE uno di questi nomi già esistenti: {attrs}.
    Altrimenti usa un nome breve in italiano con l'iniziale maiuscola (es. "Tipologia del Terreno").
    Non ripetere negli attributi denominazione, gradazione alcolica, temperatura di servizio, prezzo e abbinamenti,
    che hanno già un campo dedicato. Correggi le righe spezzate dall'impaginazione
    (es. "Temperatura di fermentazione: 16° C" e "Durata della fermentazione: 20 gg" sono due voci distinte).
12. "is_organic": true se il documento indica che il vino è biologico o da agricoltura biologica: parole come
    "biologico/biologica", "bio", "da uve biologiche", "agricoltura biologica", "organic", "certificazione biologica",
    il logo europeo del biologico (foglia di stelle) o enti certificatori del biologico (es. ICEA, CCPB, Bioagricert,
    Suolo e Salute, Valoritalia Bio). Se il vino è solo "in conversione al biologico" o non c'è alcun riferimento, false.
    NON creare attributi separati per il biologico (es. "Certificazione", "Agricoltura"): lo registra il sistema
    a partire da questo campo.
13. "producer": il nome dell'azienda/cantina produttrice, il comune e il sito web se presenti.
14. "notes": eventuali avvisi utili alla revisione (es. dati illeggibili o ambigui), altrimenti null.
"""


def _wine_properties(canonical_pairings: List[str]) -> Dict[str, Any]:
    """Schema JSON standard (usato da Claude); convertito per Gemini da _to_gemini_schema."""
    nullable_str = {"type": ["string", "null"]}
    return {
        "name": {"type": "string"},
        "category": {"type": "string", "enum": CATEGORIES},
        "denominazione": {"type": ["string", "null"], "enum": DENOMINATIONS + [None]},
        "vintage_year": {"type": ["integer", "null"]},
        "is_riserva": {"type": "boolean"},
        "is_organic": {"type": "boolean"},
        "alcohol_degrees": {"type": ["number", "null"]},
        "grape_varieties": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "percentage": {"type": ["number", "null"]}},
                "required": ["name", "percentage"],
            },
        },
        "food_pairings": {"type": "array", "items": {"type": "string", "enum": canonical_pairings}},
        "food_pairings_text": nullable_str,
        "serving_temperature": nullable_str,
        "indicative_price": nullable_str,
        "description": nullable_str,
        "tasting_notes": {
            "type": "object",
            "properties": {"visual": nullable_str, "olfactory": nullable_str, "taste": nullable_str},
            "required": ["visual", "olfactory", "taste"],
        },
        "attributes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "value": {"type": "string"}},
                "required": ["name", "value"],
            },
        },
        "notes": nullable_str,
    }


def build_json_schema(canonical_pairings: List[str]) -> Dict[str, Any]:
    wine_props = _wine_properties(canonical_pairings)
    return {
        "type": "object",
        "properties": {
            "producer": {
                "type": "object",
                "properties": {
                    "name": {"type": ["string", "null"]},
                    "city": {"type": ["string", "null"]},
                    "website": {"type": ["string", "null"]},
                },
                "required": ["name", "city", "website"],
            },
            "wines": {
                "type": "array",
                "items": {"type": "object", "properties": wine_props, "required": list(wine_props.keys())},
            },
        },
        "required": ["producer", "wines"],
    }


def _to_gemini_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Converte lo schema JSON standard nel sottoinsieme OpenAPI accettato da Gemini (responseSchema)."""
    out: Dict[str, Any] = {}
    typ = schema.get("type")
    nullable = False
    if isinstance(typ, list):
        nullable = "null" in typ
        typ = next(t for t in typ if t != "null")
    out["type"] = typ.upper()
    if nullable:
        out["nullable"] = True
    if "enum" in schema:
        values = [v for v in schema["enum"] if v is not None]
        if values:
            out["format"] = "enum"
            out["enum"] = values
    if typ == "object":
        out["properties"] = {k: _to_gemini_schema(v) for k, v in schema.get("properties", {}).items()}
        if schema.get("required"):
            out["required"] = schema["required"]
            out["propertyOrdering"] = list(schema.get("properties", {}).keys())
    if typ == "array":
        out["items"] = _to_gemini_schema(schema["items"])
    return out


# ---------------------------------------------------------------------------
# Chiamate ai provider
# ---------------------------------------------------------------------------

def _post(url: str, headers: Dict[str, str], body: Dict[str, Any]) -> Dict[str, Any]:
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=settings.AI_TIMEOUT_SECONDS)
    except requests.Timeout:
        # si passa subito al modello successivo, senza ripetere un'attesa cosi' lunga
        raise AIServiceBusy("Il servizio IA non ha risposto in tempo: riprova con un file più piccolo.", 408)
    except requests.RequestException as e:
        raise AIExtractionError(f"Servizio IA non raggiungibile: {e.__class__.__name__}")

    if resp.status_code in (401, 403):
        raise AIExtractionError("Chiave API dell'IA non valida o senza permessi: controlla il file .env.")
    if resp.status_code >= 400:
        detail = ""
        try:
            err = resp.json().get("error", {})
            detail = err.get("message", "") if isinstance(err, dict) else str(err)
        except Exception:
            detail = resp.text[:300]
        if resp.status_code == 429:
            raise AIServiceBusy("Limite di richieste dell'IA raggiunto: attendi qualche minuto e riprova.", 429)
        if resp.status_code in TRANSIENT_STATUSES:
            raise AIServiceBusy(
                "Il servizio IA è momentaneamente sovraccarico: riprova tra qualche minuto.", resp.status_code
            )
        if resp.status_code == 404 and "model" in detail.lower():
            raise AIServiceBusy(f"Modello IA non disponibile: {detail[:200]}", 404)
        raise AIExtractionError(f"Errore del servizio IA ({resp.status_code}): {detail[:300]}")
    try:
        return resp.json()
    except ValueError:
        raise AIExtractionError("Risposta del servizio IA non valida.")


# Modelli che hanno appena fallito (sovraccarichi, quota esaurita, troppo lenti): per qualche minuto
# si prova prima con gli altri, cosi' i documenti successivi non ripetono le stesse attese.
MODEL_COOLDOWN_SECONDS = 600
_MODEL_COOLDOWN: Dict[str, float] = {}


def _ordered_models(models: List[str]) -> List[str]:
    now = time.time()
    ready = [m for m in models if _MODEL_COOLDOWN.get(m, 0) <= now]
    resting = [m for m in models if _MODEL_COOLDOWN.get(m, 0) > now]
    return ready + resting


def gemini_models() -> List[str]:
    """Modello principale seguito dai modelli di riserva (senza duplicati)."""
    models = [settings.GEMINI_MODEL] + [m.strip() for m in (settings.GEMINI_FALLBACK_MODELS or "").split(",")]
    return [m for m in dict.fromkeys(models) if m]


def _call_gemini(file_bytes: bytes, mime_type: str, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """Prova il modello principale; se sovraccarico riprova con attese crescenti e poi passa ai modelli di riserva."""
    last_error: Optional[AIExtractionError] = None
    rewrite = False  # vale anche per i modelli di riserva: il blocco riguarda il testo, non il modello
    for model in _ordered_models(gemini_models()):
        bad_outputs = 0
        for attempt in range(len(RETRY_DELAYS) + 1):
            try:
                # dopo una risposta malformata si riprova con un po' di variabilita'
                temperature = 0.4 if bad_outputs else 0
                prompt_used = prompt + REWRITE_HINT if rewrite else prompt
                result = _call_gemini_model(model, file_bytes, mime_type, prompt_used, schema, temperature)
                _MODEL_COOLDOWN.pop(model, None)
                if isinstance(result, dict):
                    result["_model_used"] = model
                return result
            except AIInvalidOutput as e:
                last_error = e
                bad_outputs += 1
                rewrite = rewrite or e.recitation
                logger.warning("Gemini %s: risposta non valida (%s), tentativo %d", model, e, attempt + 1)
                # un secondo tentativo sullo stesso modello, poi si passa al successivo
                if bad_outputs >= 2:
                    break
            except AIServiceBusy as e:
                last_error = e
                logger.warning("Gemini %s non disponibile (%s), tentativo %d", model, e.status, attempt + 1)
                # quota esaurita, modello inesistente o troppo lento: inutile insistere, si passa al successivo
                if e.status in (404, 408, 429) or attempt == len(RETRY_DELAYS):
                    _MODEL_COOLDOWN[model] = time.time() + MODEL_COOLDOWN_SECONDS
                    break
                time.sleep(RETRY_DELAYS[attempt])
    raise last_error or AIExtractionError("Servizio IA non disponibile.")


def _call_gemini_model(model: str, file_bytes: bytes, mime_type: str, prompt: str, schema: Dict[str, Any],
                       temperature: float = 0) -> Dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{
            "role": "user",
            "parts": [
                {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(file_bytes).decode()}},
                {"text": prompt},
            ],
        }],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
            "responseMimeType": "application/json",
            "responseSchema": _to_gemini_schema(schema),
        },
    }
    data = _post(url, {"x-goog-api-key": settings.GEMINI_API_KEY, "Content-Type": "application/json"}, body)
    candidates = data.get("candidates") or []
    if not candidates:
        reason = (data.get("promptFeedback") or {}).get("blockReason", "nessun risultato")
        raise AIExtractionError(f"L'IA non ha restituito risultati ({reason}).")
    finish = candidates[0].get("finishReason", "")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    # le parti "thought" sono il ragionamento del modello, non la risposta
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    result = parse_json_lenient(text)
    if result is None:
        logger.warning("Gemini %s: JSON non valido (finishReason=%s, %d caratteri, fine: %r)",
                       model, finish, len(text), text[-300:])
        if finish == "MAX_TOKENS":
            raise AIInvalidOutput("La risposta dell'IA è stata troncata perché troppo lunga")
        if finish == "RECITATION":
            raise AIInvalidOutput("L'IA si è fermata perché stava copiando alla lettera i testi della pagina web",
                                  recitation=True)
        raise AIInvalidOutput(f"L'IA ha restituito un JSON non valido ({finish or 'motivo sconosciuto'})")
    return result


def parse_json_lenient(text: str) -> Optional[Any]:
    """JSON della risposta, tollerando recinti ```json e testo prima o dopo l'oggetto."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    try:
        return json.loads(text)
    except ValueError:
        pass
    start = text.find("{")
    if start < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
        return obj
    except ValueError:
        return None


def _call_anthropic(file_bytes: bytes, mime_type: str, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    block_type = "document" if mime_type == "application/pdf" else "image"
    body = {
        "model": settings.ANTHROPIC_MODEL,
        "max_tokens": 8000,
        "temperature": 0,
        "tools": [{
            "name": "registra_vini",
            "description": "Registra i dati estratti dalla scheda del vino.",
            "input_schema": schema,
        }],
        "tool_choice": {"type": "tool", "name": "registra_vini"},
        "messages": [{
            "role": "user",
            "content": [
                {"type": block_type, "source": {"type": "base64", "media_type": mime_type,
                                                "data": base64.b64encode(file_bytes).decode()}},
                {"type": "text", "text": prompt},
            ],
        }],
    }
    headers = {
        "x-api-key": settings.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    data = None
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            data = _post("https://api.anthropic.com/v1/messages", headers, body)
            break
        except AIServiceBusy as e:
            if attempt == len(RETRY_DELAYS) or e.status == 404:
                raise
            time.sleep(RETRY_DELAYS[attempt])
    for block in data.get("content") or []:
        if block.get("type") == "tool_use" and isinstance(block.get("input"), dict):
            return block["input"]
    raise AIExtractionError("L'IA non ha restituito i dati nel formato previsto.")


def extract_with_ai(file_bytes: bytes, filename: str, master_attributes: List[str],
                    master_grapes: List[str], canonical_pairings: List[str],
                    mime_type: str = "application/pdf") -> Dict[str, Any]:
    provider = active_provider()
    if not provider:
        raise AIExtractionError("Nessuna chiave IA configurata.")
    prompt = build_prompt(filename, master_attributes, master_grapes, canonical_pairings)
    schema = build_json_schema(canonical_pairings)
    logger.info("Estrazione IA di %s con %s", filename, provider)
    if provider == "gemini":
        result = _call_gemini(file_bytes, mime_type, prompt, schema)
    else:
        result = _call_anthropic(file_bytes, mime_type, prompt, schema)
    if not isinstance(result, dict) or not isinstance(result.get("wines"), list):
        raise AIExtractionError("Risposta dell'IA incompleta.")
    return result
