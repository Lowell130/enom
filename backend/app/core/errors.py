"""Messaggi di errore leggibili per i dati non validi inviati dai moduli (errori 422).

FastAPI restituisce di default un elenco tecnico in inglese; qui lo si trasforma in una frase in
italiano che il sito puo' mostrare cosi' com'e'. L'elenco originale resta disponibile in "errors".
"""
from typing import Any, Dict, List

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

FIELD_LABELS = {
    "email": "Email", "user_email": "Email", "password": "Password", "company_name": "Nome della cantina",
    "user_name": "Nome e cognome", "user_phone": "Telefono", "message": "Messaggio", "token": "Link",
    "name": "Nome", "subject": "Oggetto", "body": "Testo", "producer_id": "Cantina", "reason": "Motivo",
    "admin_recipients": "Destinatari", "to": "Destinatario",
}


def _label(loc: List[Any]) -> str:
    for part in reversed(loc):
        if isinstance(part, str) and part not in ("body", "query", "path"):
            return FIELD_LABELS.get(part, part.replace("_", " ").capitalize())
    return "Dato"


def readable_error(err: Dict[str, Any]) -> str:
    loc = list(err.get("loc") or [])
    label = _label(loc)
    kind = err.get("type", "")
    ctx = err.get("ctx") or {}
    msg = str(err.get("msg", ""))
    field = loc[-1] if loc else ""
    if kind == "missing":
        return f"{label}: campo obbligatorio."
    if kind == "string_too_short":
        n = ctx.get("min_length", 1)
        return f"{label}: campo obbligatorio." if n <= 1 else f"{label}: almeno {n} caratteri."
    if kind == "string_too_long":
        return f"{label}: massimo {ctx.get('max_length')} caratteri."
    if field in ("email", "user_email", "to") or "email" in msg.lower():
        return ("L'indirizzo email non è valido: controlla di averlo scritto per intero (es. nome@dominio.it). "
                "Non sono accettati domini di prova come .test o .local.")
    if kind == "value_error":
        # messaggi scritti da noi nei validatori ("Value error, ...")
        return msg.split(", ", 1)[1] if msg.lower().startswith("value error, ") else msg
    if kind in ("int_parsing", "float_parsing"):
        return f"{label}: inserisci un numero."
    if kind == "bool_parsing":
        return f"{label}: valore non valido."
    if kind == "literal_error":
        return f"{label}: scelta non valida."
    return f"{label}: valore non valido."


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = list(dict.fromkeys(readable_error(e) for e in errors))
    return JSONResponse(status_code=422, content={
        "detail": " ".join(messages[:3]) or "Dati non validi.",
        "errors": jsonable_encoder(errors, custom_encoder={ValueError: str, Exception: str}),
    })
