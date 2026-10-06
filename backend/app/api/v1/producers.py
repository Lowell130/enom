from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_database
from app.schemas.producer import ProducerCreate, ProducerUpdate, ProducerResponse, DeletionRequest
from app.api.v1.auth import get_current_user, get_current_admin, get_optional_user, is_admin, owns_producer
from app.core.utils import slugify, unique_slug
from bson import ObjectId
from app.services import email as mail
from datetime import datetime
from typing import Optional

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
    producers = []
    async for doc in db.producers.find(query):
        doc["id"] = str(doc["_id"])
        doc["product_count"] = count_map.get(doc["id"], 0)
        if include_all:
            doc["total_product_count"] = total_map.get(doc["id"], 0)
        else:
            # dati riservati all'area admin
            doc.pop("deletion_requested_at", None)
            doc.pop("deletion_reason", None)
        producers.append(doc)
    return producers


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
    return {"message": "Richiesta inviata: l'amministratore ti contatterà per confermare la cancellazione.",
            "deletion_requested_at": now}


@router.delete("/me/deletion-request")
async def cancel_deletion_request(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    pid = current_user.get("producer_id")
    if not pid or not ObjectId.is_valid(pid):
        raise HTTPException(status_code=400, detail="Nessuna cantina collegata a questo account")
    await db.producers.update_one({"_id": ObjectId(pid)}, {"$unset": {"deletion_requested_at": "", "deletion_reason": ""}})
    return {"message": "Richiesta di cancellazione annullata."}
