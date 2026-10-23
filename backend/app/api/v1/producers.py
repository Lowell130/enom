from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.services import activity
from app.db.mongodb import get_database
from app.schemas.producer import ProducerCreate, ProducerUpdate, ProducerResponse, DeletionRequest, InviteRequest
from app.api.v1.auth import get_current_user, get_current_admin, get_optional_user, is_admin, owns_producer, _hash_reset_token
from app.core.config import settings
from app.core.security import get_password_hash
from app.core.utils import client_ip, rate_limiter, slugify, unique_slug
import re
import unicodedata
from bson import ObjectId
from app.services import email as mail
from datetime import datetime, timedelta
from typing import Dict, Optional
import secrets

router = APIRouter()


@router.get("", response_model=list[ProducerResponse])
async def get_producers(
    include_all: bool = False,
    current_user: Optional[dict] = Depends(get_optional_user),
    db=Depends(get_database)
):
    """Elenco pubblico delle cantine approvate.
    Con include_all=true l'amministratore riceve anche cantine in attesa o sospese."""
    if include_all and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Accesso riservato all'Amministratore")

    # 1. Conteggio vini pubblicati per cantina in un'unica aggregazione
    pipeline = [
        {"$match": {"status": "PUBLISHED"}},
        {"$group": {"_id": "$producer_id", "count": {"$sum": 1}}}
    ]
    count_map = {}
    async for c in db.products.aggregate(pipeline):
        if c.get("_id"):
            count_map[str(c["_id"])] = c.get("count", 0)

    total_map = {}
    if include_all:
        async for c in db.products.aggregate([{"$group": {"_id": "$producer_id", "count": {"$sum": 1}}}]):
            if c.get("_id"):
                total_map[str(c["_id"])] = total_map.get(str(c["_id"]), 0) + c.get("count", 0)

    # 2. Cantine
    query = {} if include_all else {"status": "APPROVED"}
    accounts = await _account_map(db) if include_all else {}
    producers = []
    async for doc in db.producers.find(query):
        doc["id"] = str(doc["_id"])
        doc["product_count"] = count_map.get(doc["id"], 0)
        if include_all:
            doc["total_product_count"] = total_map.get(doc["id"], 0)
            doc["account"] = accounts.get(doc["_id"], {"status": "none"})
        else:
            # dati riservati all'area admin
            doc.pop("deletion_requested_at", None)
            doc.pop("deletion_reason", None)
        producers.append(doc)
    return producers


# parole generiche che non distinguono una cantina dall'altra
_GENERIC_WORDS = {
    "cantina", "cantine", "azienda", "aziende", "agricola", "agricole", "vitivinicola", "vinicola", "vini", "vino",
    "tenuta", "tenute", "societa", "soc", "srl", "sas", "snc", "ss", "s", "r", "l", "a", "coop", "cooperativa",
    "il", "lo", "la", "i", "gli", "le", "di", "del", "della", "dei", "degli", "delle", "e", "ed", "da", "in",
    "fattoria", "masseria", "casa", "vigneti", "vigne", "borgo", "molise",
}


def _name_key(name: str) -> str:
    """'CATABBO Cantine' e 'Cantine Catabbo s.r.l.' -> 'catabbo'."""
    t = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower()
    words = [w for w in re.split(r"[^a-z0-9]+", t) if w and w not in _GENERIC_WORDS]
    return " ".join(sorted(words))


@router.get("/similar")
async def similar_producers(name: str = Query("", max_length=150), db=Depends(get_database)):
    """Cantine gia' presenti con un nome simile: alla registrazione si propone di rivendicarle invece di duplicarle."""
    key = _name_key(name)
    if len(key) < 3:
        return []
    out = []
    async for p in db.producers.find({"status": "APPROVED"}, {"company_name": 1, "slug": 1}):
        other = _name_key(p.get("company_name", ""))
        if not other:
            continue
        if key == other or (min(len(key), len(other)) >= 4 and (key in other or other in key)):
            out.append({"company_name": p.get("company_name", ""), "slug": p.get("slug", "")})
        if len(out) >= 3:
            break
    return out


@router.get("/{identifier}", response_model=ProducerResponse)
async def get_producer_by_slug_or_id(
    identifier: str,
    current_user: Optional[dict] = Depends(get_optional_user),
    db=Depends(get_database)
):
    query = {"$or": [{"slug": identifier}]}
    if ObjectId.is_valid(identifier):
        query["$or"].append({"_id": ObjectId(identifier)})

    doc = await db.producers.find_one(query)
    if not doc:
        raise HTTPException(status_code=404, detail="Cantina non trovata")

    # Le cantine non approvate sono visibili solo all'admin e al proprietario
    if doc.get("status", "APPROVED") != "APPROVED" and not (
        is_admin(current_user) or owns_producer(current_user, doc["_id"])
    ):
        raise HTTPException(status_code=404, detail="Cantina non trovata")

    doc["id"] = str(doc["_id"])
    doc["product_count"] = await db.products.count_documents({"producer_id": doc["_id"], "status": "PUBLISHED"})
    if not (is_admin(current_user) or owns_producer(current_user, doc["_id"])):
        doc.pop("deletion_requested_at", None)
        doc.pop("deletion_reason", None)
    return doc


@router.post("", response_model=ProducerResponse)
async def create_producer(
    producer_in: ProducerCreate,
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    base_slug = slugify(producer_in.slug or producer_in.company_name) or "cantina"
    slug = await unique_slug(db.producers, base_slug)

    doc = producer_in.model_dump()
    doc["slug"] = slug
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()

    res = await db.producers.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    doc["product_count"] = 0
    return doc


@router.put("/{producer_id}", response_model=ProducerResponse)
async def update_producer(
    producer_id: str,
    producer_in: ProducerUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(producer_id):
        raise HTTPException(status_code=400, detail="ID cantina non valido")

    admin = is_admin(current_user)
    # L'admin modifica qualsiasi cantina; il produttore solo la propria.
    if not admin and not owns_producer(current_user, producer_id):
        raise HTTPException(status_code=403, detail="Non hai i permessi per modificare questa cantina")

    existing = await db.producers.find_one({"_id": ObjectId(producer_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Cantina non trovata")

    update_data = {k: v for k, v in producer_in.model_dump().items() if v is not None}

    # Solo l'amministratore puo' approvare/sospendere una cantina
    if not admin:
        update_data.pop("status", None)
        update_data.pop("hide_photos", None)

    if "company_name" in update_data and update_data["company_name"] != existing.get("company_name"):
        update_data["slug"] = await unique_slug(
            db.producers, slugify(update_data["company_name"]) or "cantina", exclude_id=existing["_id"]
        )

    update_data["updated_at"] = datetime.utcnow()
    await db.producers.update_one({"_id": ObjectId(producer_id)}, {"$set": update_data})

    old_status = existing.get("status", "APPROVED")
    new_status = update_data.get("status", old_status)
    if new_status != old_status and new_status in ("APPROVED", "SUSPENDED"):
        await _notify_status_change(db, existing["_id"], new_status)

    updated_doc = await db.producers.find_one({"_id": ObjectId(producer_id)})
    await activity.log_activity(db, current_user, "producer.updated", producer_id=producer_id,
                                target_type="producer", target_id=producer_id,
                                target_name=updated_doc.get("company_name", ""),
                                changes=activity.diff(existing, updated_doc, activity.PRODUCER_FIELDS))
    updated_doc["id"] = str(updated_doc["_id"])
    updated_doc["product_count"] = await db.products.count_documents({"producer_id": updated_doc["_id"]})
    return updated_doc


@router.delete("/{producer_id}")
async def delete_producer(
    producer_id: str,
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(producer_id):
        raise HTTPException(status_code=400, detail="ID non valido")

    oid = ObjectId(producer_id)
    res = await db.producers.delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cantina non trovata")

    # Con la cantina spariscono anche i suoi dati: vini (anche quelli collegati come testo,
    # es. importati da file), richieste dei clienti, account di accesso e dati tecnici collegati.
    # Cosi' l'email della cantina si puo' registrare di nuovo.
    ids = [oid, str(oid)]
    wines = await db.products.delete_many({"producer_id": {"$in": ids}})
    inquiries = await db.inquiries.delete_many({"producer_id": {"$in": ids}})
    accounts = await db.users.find({"producer_id": {"$in": ids}, "role": {"$ne": "ADMIN"}}, {"_id": 1}).to_list(50)
    account_ids = [u["_id"] for u in accounts]
    if account_ids:
        await db.password_resets.delete_many({"user_id": {"$in": account_ids}})
        await db.users.delete_many({"_id": {"$in": account_ids}})
    await db.ai_usage.delete_many({"producer_id": {"$in": ids}})
    # eventi: quelli organizzati dalla cantina spariscono, da quelli del territorio la cantina viene tolta
    await db.events.delete_many({"producer_id": oid})
    await db.events.update_many({"participant_ids": oid}, {"$pull": {"participant_ids": oid}})
    return {
        "message": "Cantina eliminata insieme ai suoi vini, alle richieste e agli account di accesso",
        "products_deleted": wines.deleted_count,
        "inquiries_deleted": inquiries.deleted_count,
        "accounts_deleted": len(account_ids),
    }


async def _producer_user_emails(db, producer_oid) -> list:
    users = await db.users.find({"producer_id": producer_oid, "is_active": {"$ne": False}}, {"email": 1}).to_list(5)
    return [u["email"] for u in users if u.get("email")]


async def _notify_status_change(db, producer_oid, status: str) -> None:
    producer = await db.producers.find_one({"_id": producer_oid})
    if not producer:
        return
    key = "cantina_approvata" if status == "APPROVED" else "cantina_sospesa"
    await mail.send_template(db, key, await _producer_user_emails(db, producer_oid), {
        "nome_cantina": producer.get("company_name", ""),
        "link_pagina_cantina": mail.site_url(f"/produttori/{producer.get('slug', '')}"),
        "link_area_riservata": mail.site_url("/dashboard"),
    }, related={"producer_id": str(producer_oid)})


@router.post("/me/deletion-request")
async def request_deletion(
    payload: DeletionRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """La cantina chiede la cancellazione del proprio account: l'amministratore viene avvisato
    e la cancellazione vera e propria resta una sua decisione (azione irreversibile)."""
    pid = current_user.get("producer_id")
    if not pid or not ObjectId.is_valid(pid):
        raise HTTPException(status_code=400, detail="Nessuna cantina collegata a questo account")
    producer = await db.producers.find_one({"_id": ObjectId(pid)})
    if not producer:
        raise HTTPException(status_code=404, detail="Cantina non trovata")
    now = datetime.utcnow()
    reason = (payload.reason or "").strip()
    await db.producers.update_one({"_id": producer["_id"]}, {"$set": {
        "deletion_requested_at": now, "deletion_reason": reason,
    }})
    await mail.send_template(db, "richiesta_cancellazione_admin", await mail.admin_recipients(db), {
        "nome_cantina": producer.get("company_name", ""),
        "email": current_user.get("email", ""),
        "motivo": reason or "non indicato",
        "data": mail.format_date(now),
        "link_approvazione": mail.site_url("/dashboard/cantine?stato=DELETION"),
    }, related={"producer_id": pid})
    await activity.log_activity(db, current_user, "producer.deletion_requested", producer_id=pid,
                                target_type="producer", target_id=pid, target_name=producer.get("company_name", ""),
                                details=reason)
    return {"message": "Richiesta inviata: l'amministratore ti contatterà per confermare la cancellazione.",
            "deletion_requested_at": now}


@router.delete("/me/deletion-request")
async def cancel_deletion_request(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    pid = current_user.get("producer_id")
    if not pid or not ObjectId.is_valid(pid):
        raise HTTPException(status_code=400, detail="Nessuna cantina collegata a questo account")
    await db.producers.update_one({"_id": ObjectId(pid)}, {"$unset": {"deletion_requested_at": "", "deletion_reason": ""}})
    await activity.log_activity(db, current_user, "producer.deletion_cancelled", producer_id=pid,
                                target_type="producer", target_id=pid)
    return {"message": "Richiesta di cancellazione annullata."}


# ---------------------------------------------------------------------------
# Accesso delle cantine inserite dall'amministratore: invito via email
# ---------------------------------------------------------------------------

async def _account_map(db) -> Dict[ObjectId, dict]:
    """Stato dell'accesso di ogni cantina: none (nessun account), invited, expired (invito scaduto), active."""
    now = datetime.utcnow()
    out: Dict[ObjectId, dict] = {}
    async for u in db.users.find({"role": "PRODUCER", "producer_id": {"$ne": None}},
                                 {"email": 1, "producer_id": 1, "invited_at": 1, "activated_at": 1,
                                  "invite_expires_at": 1, "created_at": 1}):
        pid = u.get("producer_id")
        if not isinstance(pid, ObjectId):
            pid = ObjectId(pid) if ObjectId.is_valid(str(pid)) else None
        if pid is None:
            continue
        if u.get("activated_at") or not u.get("invited_at"):
            info = {"status": "active", "email": u.get("email")}
            if not u.get("invited_at"):
                # iscritta da sola dalla pagina di registrazione: i contenuti sono suoi
                info.update(self_registered=True, registered_at=u.get("created_at"))
        else:
            expired = u.get("invite_expires_at") and u["invite_expires_at"] < now
            info = {"status": "expired" if expired else "invited", "email": u.get("email"),
                    "invited_at": u.get("invited_at"), "expires_at": u.get("invite_expires_at")}
        # se una cantina ha piu' account, conta quello attivo
        if out.get(pid, {}).get("status") != "active":
            out[pid] = info
    return out


async def _invite(db, producer: dict, email: Optional[str] = None) -> dict:
    """Crea (o ritrova) l'account della cantina e manda il link per scegliere la password."""
    email = (email or (producer.get("contacts") or {}).get("email_contact") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail=f"{producer.get('company_name')}: manca l'email di contatto nel profilo")
    now = datetime.utcnow()
    user = await db.users.find_one({"producer_id": producer["_id"], "role": "PRODUCER"})
    if user and (user.get("activated_at") or not user.get("invited_at")):
        raise HTTPException(status_code=400, detail=f"{producer.get('company_name')} ha già un accesso attivo")
    other = await db.users.find_one({"email": email})
    if other and (not user or other["_id"] != user["_id"]):
        raise HTTPException(status_code=400, detail=f"L'email {email} è già usata da un altro account")
    expires = now + timedelta(days=settings.INVITE_TTL_DAYS)
    if user:
        await db.users.update_one({"_id": user["_id"]}, {"$set": {
            "email": email, "invited_at": now, "invite_expires_at": expires, "is_active": True}})
        user_id = user["_id"]
    else:
        res = await db.users.insert_one({
            "email": email,
            # password casuale mai comunicata: si accede solo dopo aver scelto la propria dall'invito
            "password_hash": get_password_hash(secrets.token_urlsafe(32)),
            "role": "PRODUCER", "producer_id": producer["_id"], "is_active": True,
            "created_at": now, "invited_at": now, "invite_expires_at": expires,
        })
        user_id = res.inserted_id
    # i link d'invito precedenti non valgono piu'
    await db.password_resets.update_many({"user_id": user_id, "used_at": None}, {"$set": {"used_at": now}})
    token = secrets.token_urlsafe(32)
    await db.password_resets.insert_one({
        "user_id": user_id, "token_hash": _hash_reset_token(token), "purpose": "invite",
        "created_at": now, "expires_at": expires, "used_at": None,
    })
    sent = await mail.send_template(db, "invito_cantina", [email], {
        "nome_cantina": producer.get("company_name", ""),
        "email": email,
        "link_attivazione": mail.site_url(f"/attiva-account?token={token}"),
        "giorni_validita": str(settings.INVITE_TTL_DAYS),
        "link_pagina_cantina": mail.site_url(f"/produttori/{producer.get('slug', '')}"),
    }, related={"producer_id": str(producer["_id"]), "user_id": str(user_id)})
    return {"producer_id": str(producer["_id"]), "company_name": producer.get("company_name", ""), "email": email,
            "expires_at": expires, "email_status": (sent or {}).get("status", "disattivato")}


@router.post("/invite-all")
async def invite_all(current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    """Invita tutte le cantine che non hanno ancora un accesso (e hanno l'email di contatto)."""
    accounts = await _account_map(db)
    invited, skipped = [], []
    async for producer in db.producers.find({}):
        if accounts.get(producer["_id"], {}).get("status") not in (None, "none"):
            continue
        if not (producer.get("contacts") or {}).get("email_contact"):
            skipped.append({"company_name": producer.get("company_name", ""), "reason": "manca l'email di contatto"})
            continue
        try:
            invited.append(await _invite(db, producer))
        except HTTPException as e:
            skipped.append({"company_name": producer.get("company_name", ""), "reason": e.detail})
    return {"invited": invited, "skipped": skipped,
            "message": f"Inviti mandati: {len(invited)}" + (f" · non invitate: {len(skipped)}" if skipped else "")}


@router.post("/{producer_id}/invite")
async def invite_producer(producer_id: str, payload: InviteRequest, current_admin: dict = Depends(get_current_admin),
                          db=Depends(get_database)):
    if not ObjectId.is_valid(producer_id):
        raise HTTPException(status_code=400, detail="ID non valido")
    producer = await db.producers.find_one({"_id": ObjectId(producer_id)})
    if not producer:
        raise HTTPException(status_code=404, detail="Cantina non trovata")
    result = await _invite(db, producer, str(payload.email) if payload.email else None)
    result["message"] = f"Invito mandato a {result['email']}"
    return result


# ---------------------------------------------------------------------------
# "E' la tua cantina?": il titolare di una cantina senza accesso lo ottiene da solo
# ---------------------------------------------------------------------------

def _mask_email(email: str) -> str:
    local, _, domain = (email or "").partition("@")
    return f"{local[:1]}***@{domain}" if local and domain else ""


async def _public_producer(db, identifier: str) -> dict:
    query = {"$or": [{"slug": identifier}]}
    if ObjectId.is_valid(identifier):
        query["$or"].append({"_id": ObjectId(identifier)})
    producer = await db.producers.find_one(query)
    if not producer or producer.get("status", "APPROVED") != "APPROVED":
        raise HTTPException(status_code=404, detail="Cantina non trovata")
    return producer


async def _account_status(db, producer_id: ObjectId) -> str:
    return (await _account_map(db)).get(producer_id, {}).get("status", "none")


@router.get("/{identifier}/claim")
async def claim_info(identifier: str, db=Depends(get_database)):
    """Se la pagina si puo' rivendicare e a quale indirizzo (mascherato) arriverebbe il link."""
    producer = await _public_producer(db, identifier)
    status = await _account_status(db, producer["_id"])
    email = ((producer.get("contacts") or {}).get("email_contact") or "").strip()
    return {"claimable": status != "active", "has_email": bool(email), "masked_email": _mask_email(email),
            "link_days": settings.INVITE_TTL_DAYS}


@router.post("/{identifier}/claim/email")
async def claim_by_email(identifier: str, request: Request, db=Depends(get_database)):
    """Manda il link di attivazione SOLO all'email della cantina gia' presente nel sito:
    chi puo' leggere quella casella e' il titolare. Mai a un indirizzo scelto da chi clicca."""
    rate_limiter.check_and_hit(f"claim-ip:{client_ip(request)}", 5, 3600,
                               "Troppe richieste in poco tempo. Riprova più tardi.")
    producer = await _public_producer(db, identifier)
    rate_limiter.check_and_hit(f"claim-producer:{producer['_id']}", 3, 86400,
                               "Il link per questa cantina è già stato inviato più volte oggi: controlla la casella (anche lo spam) o riprova domani.")
    if await _account_status(db, producer["_id"]) == "active":
        raise HTTPException(status_code=400, detail="Questa cantina ha già un accesso attivo: usa \"Password dimenticata\" nella pagina di accesso.")
    email = ((producer.get("contacts") or {}).get("email_contact") or "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="Per questa cantina non abbiamo un'email: usa il modulo qui sotto.")
    try:
        result = await _invite(db, producer)
    except HTTPException:
        raise HTTPException(status_code=400, detail="Non possiamo mandare il link a questo indirizzo: usa il modulo qui sotto e ti contatteremo.")
    await activity.log_activity(db, {"role": "VISITOR", "email": ""}, "producer.claim_link_sent",
                                producer_id=producer["_id"], target_type="producer", target_id=producer["_id"],
                                target_name=producer.get("company_name", ""),
                                details=f"Link di accesso inviato a {_mask_email(email)} dalla pagina pubblica")
    return {"message": f"Fatto: abbiamo mandato il link di accesso a {_mask_email(email)}. "
                       f"Controlla anche nello spam; il link vale {settings.INVITE_TTL_DAYS} giorni.",
            "email_status": result.get("email_status")}
