"""Modulo "Contatti": messaggi dei visitatori a EnotecaMolise.
Ogni messaggio arriva per email agli indirizzi delle notifiche admin (Rispondi = a chi ha scritto),
resta in "Messaggi dal sito" nell'area admin e viene cancellato da solo dopo CONTACT_RETENTION_DAYS."""
from datetime import datetime
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.v1.auth import get_current_admin
from app.core.config import settings
from app.core.utils import client_ip, rate_limiter
from app.db.mongodb import get_database
from app.schemas.contact import CONTACT_REASONS, ContactCreate, ContactMessage
from app.services import email as mail

router = APIRouter()


def _out(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name", ""),
        "email": doc.get("email", ""),
        "reason": doc.get("reason", "ALTRO"),
        "reason_label": CONTACT_REASONS.get(doc.get("reason"), "Altro"),
        "message": doc.get("message", ""),
        "is_read": bool(doc.get("is_read")),
        "created_at": doc.get("created_at") or datetime.utcnow(),
    }


@router.post("")
async def send_contact_message(payload: ContactCreate, request: Request, db=Depends(get_database)):
    rate_limiter.check_and_hit(
        f"contact:{client_ip(request)}",
        settings.INQUIRY_MAX_PER_WINDOW,
        settings.INQUIRY_WINDOW_SECONDS,
        "Hai inviato troppi messaggi in poco tempo. Riprova tra qualche minuto.",
    )
    ok = {"message": "Messaggio inviato. Ti risponderemo al più presto all'indirizzo che hai indicato."}
    if (payload.website or "").strip():
        # campo trappola compilato: quasi certamente spam. Risposta identica, nulla salvato o inviato.
        return ok

    now = datetime.utcnow()
    doc = {
        "name": payload.name,
        "email": str(payload.email).lower(),
        "reason": payload.reason,
        "message": payload.message,
        "is_read": False,
        "created_at": now,
        "privacy_accepted_at": now,
    }
    res = await db.contact_messages.insert_one(doc)
    doc["_id"] = res.inserted_id

    ctx = {
        "nome_mittente": doc["name"],
        "email_mittente": doc["email"],
        "motivo_contatto": CONTACT_REASONS.get(doc["reason"], "Altro"),
        "messaggio": doc["message"],
        "data": mail.format_date(now),
        "link_messaggi": mail.site_url("/dashboard/contatti"),
    }
    related = {"contact_message_id": str(res.inserted_id)}
    # all'amministratore: "Rispondi" va direttamente a chi ha scritto
    await mail.send_template(db, "messaggio_sito_admin", await mail.admin_recipients(db), ctx, related,
                             reply_to=doc["email"])
    await mail.send_template(db, "conferma_messaggio_sito", [doc["email"]], ctx, related)
    return ok


@router.get("", response_model=List[ContactMessage])
async def list_contact_messages(current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    docs = await db.contact_messages.find().sort("created_at", -1).to_list(1000)
    return [_out(d) for d in docs]


def _oid(message_id: str) -> ObjectId:
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="ID non valido")
    return ObjectId(message_id)


@router.put("/{message_id}/read")
async def mark_contact_message(message_id: str, read: bool = True,
                               current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    res = await db.contact_messages.update_one({"_id": _oid(message_id)}, {"$set": {"is_read": read}})
    if not res.matched_count:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
    return {"message": "Aggiornato"}


@router.delete("/{message_id}")
async def delete_contact_message(message_id: str, current_admin: dict = Depends(get_current_admin),
                                 db=Depends(get_database)):
    res = await db.contact_messages.delete_one({"_id": _oid(message_id)})
    if not res.deleted_count:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
    return {"message": "Messaggio eliminato"}
