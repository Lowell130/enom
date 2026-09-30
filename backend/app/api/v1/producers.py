from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_database
from app.schemas.producer import ProducerCreate, ProducerUpdate, ProducerResponse
from app.api.v1.auth import get_current_user, get_current_admin, get_optional_user, is_admin, owns_producer
from app.core.utils import slugify, unique_slug
from bson import ObjectId
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

    # 2. Cantine
    query = {} if include_all else {"status": "APPROVED"}
    producers = []
    async for doc in db.producers.find(query):
        doc["id"] = str(doc["_id"])
        doc["product_count"] = count_map.get(doc["id"], 0)
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

    # Elimina i vini associati e scollega/disattiva gli account della cantina
    await db.products.delete_many({"producer_id": oid})
    await db.users.update_many(
        {"producer_id": oid, "role": {"$ne": "ADMIN"}},
        {"$set": {"producer_id": None, "is_active": False}}
    )
    return {"message": "Cantina e relativi vini eliminati con successo"}
