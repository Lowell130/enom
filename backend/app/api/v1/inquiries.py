from fastapi import APIRouter, Depends, HTTPException, Request
from app.db.mongodb import get_database
from app.schemas.inquiry import InquiryCreate, InquiryResponse
from app.api.v1.auth import get_current_user
from app.core.config import settings
from app.core.utils import rate_limiter, client_ip
from bson import ObjectId
from app.services import email as mail
from datetime import datetime
from typing import List

router = APIRouter()

@router.post("", response_model=InquiryResponse)
async def submit_inquiry(inquiry_in: InquiryCreate, request: Request, db=Depends(get_database)):
    rate_limiter.check_and_hit(
        f"inquiry:{client_ip(request)}",
        settings.INQUIRY_MAX_PER_WINDOW,
        settings.INQUIRY_WINDOW_SECONDS,
        "Hai inviato troppi messaggi in poco tempo. Riprova tra qualche minuto."
    )
    if not ObjectId.is_valid(inquiry_in.producer_id):
        raise HTTPException(status_code=400, detail="ID cantina non valido")

    producer = await db.producers.find_one({"_id": ObjectId(inquiry_in.producer_id)})
    if not producer or producer.get("status", "APPROVED") != "APPROVED":
        raise HTTPException(status_code=404, detail="Cantina non trovata")

    doc = inquiry_in.model_dump()
    doc["producer_id"] = ObjectId(inquiry_in.producer_id)
    
    if inquiry_in.product_id and ObjectId.is_valid(inquiry_in.product_id) and await db.products.find_one(
        {"_id": ObjectId(inquiry_in.product_id), "producer_id": doc["producer_id"]}, {"_id": 1}
    ):
        doc["product_id"] = ObjectId(inquiry_in.product_id)
    else:
        doc["product_id"] = None
        
    doc.pop("privacy_accepted", None)
    doc["is_read"] = False
    doc["created_at"] = datetime.utcnow()
    doc["privacy_accepted_at"] = doc["created_at"]

    res = await db.inquiries.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    doc["producer_id"] = str(doc["producer_id"])
    doc["producer_name"] = producer.get("company_name", "")
    
    if doc.get("product_id"):
        doc["product_id"] = str(doc["product_id"])
        prod = await db.products.find_one({"_id": ObjectId(doc["product_id"])})
        if prod:
            doc["product_name"] = prod.get("name", "")

    await _notify_inquiry(db, producer, doc)
    return doc


async def _notify_inquiry(db, producer: dict, inquiry: dict) -> None:
    """Avvisa la cantina (email di contatto, altrimenti quella di accesso) e manda una copia al cliente."""
    contacts = producer.get("contacts") or {}
    recipients = [contacts.get("email_contact")] if contacts.get("email_contact") else []
    if not recipients:
        users = await db.users.find({"producer_id": producer["_id"], "is_active": {"$ne": False}}, {"email": 1}).to_list(5)
        recipients = [u["email"] for u in users if u.get("email")]
    if not recipients:
        # cantina senza email (es. inserita dall'amministratore): la richiesta non deve andare persa
        recipients = await mail.admin_recipients(db)
    ctx = {
        "nome_cantina": producer.get("company_name", ""),
        "nome_cliente": inquiry.get("user_name", ""),
        "email_cliente": inquiry.get("user_email", ""),
        "telefono_cliente": inquiry.get("user_phone") or "non indicato",
        "tipo_richiesta": mail.INQUIRY_TYPES.get(inquiry.get("message_type"), "Richiesta"),
        "nome_vino": inquiry.get("product_name") or "richiesta generale sulla cantina",
        "messaggio": inquiry.get("message", ""),
        "link_richieste": mail.site_url("/dashboard/messaggi"),
        "link_pagina_cantina": mail.site_url(f"/produttori/{producer.get('slug', '')}"),
    }
    related = {"producer_id": str(producer["_id"]), "inquiry_id": inquiry.get("id")}
    await mail.send_template(db, "nuova_richiesta_cantina", recipients, ctx, related)
    await mail.send_template(db, "conferma_richiesta_cliente", [inquiry.get("user_email", "")], ctx, related)

@router.get("", response_model=List[InquiryResponse])
async def list_inquiries(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    is_admin = current_user.get("role") == "ADMIN"
    user_producer_id = current_user.get("producer_id")
    
    query = {}
    if not is_admin:
        if not user_producer_id or not ObjectId.is_valid(user_producer_id):
            return []
        query["producer_id"] = ObjectId(user_producer_id)
        
    # Pre-fetch producer and product maps to eliminate N+1 queries
    producers = await db.producers.find().to_list(1000)
    producer_map = {str(p["_id"]): p.get("company_name", "") for p in producers}

    products = await db.products.find({}, {"name": 1}).to_list(1000)
    product_map = {str(p["_id"]): p.get("name", "") for p in products}

    events = await db.events.find({}, {"slug": 1}).to_list(2000)
    event_slugs = {str(e["_id"]): e.get("slug", "") for e in events}

    cursor = db.inquiries.find(query).sort("created_at", -1)
    raw_inquiries = await cursor.to_list(1000)
    
    inquiries = []
    for doc in raw_inquiries:
        doc["id"] = str(doc["_id"])
        doc["producer_id"] = str(doc["producer_id"]) if doc.get("producer_id") else None
        doc["producer_name"] = producer_map.get(doc["producer_id"], "") if doc["producer_id"] else ""
        if doc.get("event_id"):
            doc["event_id"] = str(doc["event_id"])
            doc["event_slug"] = event_slugs.get(doc["event_id"], "")
        
        if doc.get("product_id"):
            doc["product_id"] = str(doc["product_id"])
            doc["product_name"] = product_map.get(doc["product_id"], "")
        else:
            doc["product_name"] = ""
            
        inquiries.append(doc)
    return inquiries

@router.put("/{inquiry_id}/read")
async def mark_inquiry_as_read(
    inquiry_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(inquiry_id):
        raise HTTPException(status_code=400, detail="ID non valido")
        
    inquiry = await db.inquiries.find_one({"_id": ObjectId(inquiry_id)})
    if not inquiry:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
        
    is_admin = current_user.get("role") == "ADMIN"
    user_producer_id = current_user.get("producer_id")
    
    if not is_admin and (not inquiry.get("producer_id") or str(inquiry["producer_id"]) != str(user_producer_id)):
        raise HTTPException(status_code=403, detail="Non puoi accedere a questo messaggio")
        
    await db.inquiries.update_one({"_id": ObjectId(inquiry_id)}, {"$set": {"is_read": True}})
    return {"message": "Messaggio segnato come letto"}
