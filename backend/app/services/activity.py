"""Registro delle attivita' delle cantine (solo area admin).

Ogni volta che una cantina salva qualcosa (profilo, vini, eventi, account) si scrive una riga
in `activity_log`. Le pagine pubbliche non leggono mai questa raccolta, quindi il sito non
rallenta; le righe si cancellano da sole dopo ACTIVITY_LOG_RETENTION_DAYS (indice TTL).
Le azioni dell'amministratore non vengono registrate: il registro serve a seguire le cantine.
Mai password o testi lunghi copiati per intero: per i campi lunghi si annota solo "modificato".
"""
import logging
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from bson import ObjectId

logger = logging.getLogger("enotecamolise.activity")

# etichette leggibili delle azioni (usate anche dalla pagina admin per i filtri)
ACTIONS: Dict[str, str] = {
    "account.activated": "Ha attivato l'accesso",
    "account.registered": "Si è registrata",
    "account.login": "Ha effettuato l'accesso",
    "account.password_changed": "Ha cambiato la password",
    "account.password_reset": "Ha reimpostato la password",
    "account.email_changed": "Ha cambiato l'email di accesso",
    "producer.updated": "Ha modificato il profilo",
    "producer.deletion_requested": "Ha chiesto la cancellazione dell'account",
    "producer.deletion_cancelled": "Ha annullato la richiesta di cancellazione",
    "product.created": "Ha aggiunto un vino",
    "product.updated": "Ha modificato un vino",
    "product.deleted": "Ha eliminato un vino",
    "product.imported": "Ha importato dei vini",
    "event.created": "Ha creato un evento",
    "event.updated": "Ha modificato un evento",
    "event.duplicated": "Ha duplicato un evento",
    "event.cancelled": "Ha annullato un evento",
    "event.deleted": "Ha eliminato un evento",
}

# Campi seguiti: etichetta e se mostrare il valore prima/dopo (solo campi brevi)
PRODUCER_FIELDS: Dict[str, tuple] = {
    "company_name": ("Nome", True),
    "description": ("Storia", False),
    "logo_url": ("Logo", False),
    "cover_image_url": ("Foto di copertina", False),
    "address.street": ("Indirizzo", True),
    "address.city": ("Comune", True),
    "address.province": ("Provincia", True),
    "address.zip_code": ("CAP", True),
    "address.geo_coordinates": ("Posizione sulla mappa", False),
    "contacts.email_contact": ("Email per le richieste", True),
    "contacts.phone": ("Telefono", True),
    "contacts.whatsapp_number": ("WhatsApp", True),
    "contacts.website": ("Sito web", True),
    "contacts.instagram": ("Instagram", True),
    "contacts.facebook": ("Facebook", True),
}

PRODUCT_FIELDS: Dict[str, tuple] = {
    "name": ("Nome", True),
    "status": ("Stato", True),
    "category": ("Tipologia", True),
    "denominazione": ("Denominazione", True),
    "is_riserva": ("Riserva", True),
    "alcohol_degrees": ("Gradazione", True),
    "grape_varieties": ("Vitigni", True),
    "serving_temperature": ("Temperatura di servizio", True),
    "indicative_price": ("Prezzo indicativo", True),
    "vintage_year": ("Annata", True),
    "description": ("Descrizione", False),
    "tasting_notes": ("Note di degustazione", False),
    "food_pairings": ("Abbinamenti", False),
    "custom_attributes": ("Scheda tecnica", False),
    "photos": ("Foto", False),
    "technical_sheet_pdf": ("Scheda tecnica PDF", False),
}

EVENT_FIELDS: Dict[str, tuple] = {
    "title": ("Titolo", True),
    "type": ("Tipo", True),
    "status": ("Stato", True),
    "description": ("Descrizione", False),
    "cover_image": ("Immagine", False),
    "dates": ("Date", False),
    "location": ("Luogo", False),
    "price_type": ("Prezzo", True),
    "price_text": ("Dettagli prezzo", True),
    "booking_mode": ("Prenotazione", True),
    "external_url": ("Link esterno", True),
    "product_ids": ("Vini in degustazione", False),
    "participant_ids": ("Cantine partecipanti", False),
}

STATUS_LABELS = {"PUBLISHED": "Pubblicato", "DRAFT": "Bozza", "CANCELLED": "Annullato", "ARCHIVED": "Archiviato"}
_MAX_VALUE = 80


def _get(doc: Optional[dict], path: str) -> Any:
    cur: Any = doc or {}
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _norm(v: Any) -> Any:
    if v in ("", [], {}):
        return None
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, list):
        return [_norm(x) for x in v]
    if isinstance(v, dict):
        return {k: _norm(x) for k, x in v.items() if k not in ("updated_at",)}
    return v


def _short(path: str, v: Any) -> str:
    if v is None:
        return "—"
    if path.endswith("status"):
        return STATUS_LABELS.get(str(v), str(v))
    if isinstance(v, bool):
        return "sì" if v else "no"
    if isinstance(v, list):
        v = ", ".join(str(x) for x in v)
    s = str(v).strip()
    return s if len(s) <= _MAX_VALUE else s[: _MAX_VALUE - 1] + "…"


def diff(before: Optional[dict], after: Optional[dict], fields: Dict[str, tuple]) -> List[Dict[str, str]]:
    """Campi cambiati tra due versioni di un documento, in forma leggibile."""
    out = []
    for path, (label, show_values) in fields.items():
        a, b = _norm(_get(before, path)), _norm(_get(after, path))
        if a == b:
            continue
        item = {"field": path, "label": label}
        if show_values:
            item["before"] = _short(path, a)
            item["after"] = _short(path, b)
        else:
            item["note"] = "aggiunto" if a is None else ("rimosso" if b is None else "modificato")
        out.append(item)
    return out


def _oid_str(v: Any) -> Optional[str]:
    if v is None or v == "":
        return None
    return str(v)


async def log_activity(db, user: Optional[dict], action: str, *, producer_id: Any = None,
                       target_type: Optional[str] = None, target_id: Any = None, target_name: str = "",
                       changes: Optional[Iterable[Dict[str, str]]] = None, details: str = "") -> None:
    """Scrive una riga nel registro. Non solleva mai eccezioni e ignora l'amministratore."""
    try:
        if not user or user.get("role") == "ADMIN":
            return
        changes = list(changes or [])
        if action.endswith(".updated") and not changes and not details:
            return  # salvataggio senza modifiche reali: non serve una riga
        pid = _oid_str(producer_id or user.get("producer_id"))
        producer_name = ""
        if pid and ObjectId.is_valid(pid):
            p = await db.producers.find_one({"_id": ObjectId(pid)}, {"company_name": 1})
            producer_name = (p or {}).get("company_name", "")
        await db.activity_log.insert_one({
            "created_at": datetime.utcnow(),
            "action": action,
            "user_id": _oid_str(user.get("_id") or user.get("id")),
            "user_email": user.get("email", ""),
            "producer_id": pid,
            "producer_name": producer_name,
            "target_type": target_type,
            "target_id": _oid_str(target_id),
            "target_name": target_name or "",
            "changes": changes,
            "details": details,
        })
    except Exception as e:  # il registro non deve mai bloccare il salvataggio
        logger.warning("Registro attività non aggiornato (%s): %s", action, e)
