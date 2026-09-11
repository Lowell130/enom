from fastapi import APIRouter, Depends, HTTPException, status
from app.db.mongodb import get_database
from app.schemas.producer import ProducerCreate, ProducerUpdate, ProducerResponse
from app.api.v1.auth import get_current_user, get_current_admin
from bson import ObjectId
from datetime import datetime
import re

router = APIRouter()

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

@router.get("", response_model=list[ProducerResponse])
async def get_producers(db=Depends(get_database)):
    # 1. Bulk aggregate product counts per producer in 1 query
    pipeline = [
        {"$match": {"status": "PUBLISHED"}},
        {"$group": {"_id": "$producer_id", "count": {"$sum": 1}}}
    ]
    counts_cursor = db.products.aggregate(pipeline)
    count_map = {}
    async for c in counts_cursor:
        if c.get("_id"):
            count_map[str(c["_id"])] = c.get("count", 0)

    # 2. Fetch producers in 1 query
    cursor = db.producers.find({"status": "APPROVED"})
    producers = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc["product_count"] = count_map.get(doc["id"], 0)
        producers.append(doc)
    return producers

@router.get("/{identifier}", response_model=ProducerResponse)
async def get_producer_by_slug_or_id(identifier: str, db=Depends(get_database)):
    query = {"$or": [{"slug": identifier}]}
    if ObjectId.is_valid(identifier):
        query["$or"].append({"_id": ObjectId(identifier)})
        
    doc = await db.producers.find_one(query)
    if not doc:
        raise HTTPException(status_code=404, detail="Cantine non trovata")
    
    doc["id"] = str(doc["_id"])
    prod_count = await db.products.count_documents({"producer_id": doc["_id"], "status": "PUBLISHED"})
    doc["product_count"] = prod_count
    return doc

@router.post("", response_model=ProducerResponse)
async def create_producer(
    producer_in: ProducerCreate,
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    slug = producer_in.slug or slugify(producer_in.company_name)
    existing_slug = await db.producers.find_one({"slug": slug})
    if existing_slug:
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
        
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
        
    # Security check: Admin can edit any producer. Producer can only edit their own producer_id.
    if current_user.get("role") != "ADMIN" and current_user.get("producer_id") != producer_id:
        raise HTTPException(status_code=403, detail="Non hai i permessi per modificare questa cantina")
        
    existing = await db.producers.find_one({"_id": ObjectId(producer_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Cantina non trovata")
        
    update_data = {k: v for k, v in producer_in.model_dump().items() if v is not None}
    if "company_name" in update_data and update_data["company_name"] != existing.get("company_name"):
        update_data["slug"] = slugify(update_data["company_name"])
        
    update_data["updated_at"] = datetime.utcnow()
    
    await db.producers.update_one({"_id": ObjectId(producer_id)}, {"$set": update_data})
    
    updated_doc = await db.producers.find_one({"_id": ObjectId(producer_id)})
    updated_doc["id"] = str(updated_doc["_id"])
    prod_count = await db.products.count_documents({"producer_id": updated_doc["_id"]})
    updated_doc["product_count"] = prod_count
    return updated_doc

@router.delete("/{producer_id}")
async def delete_producer(
    producer_id: str,
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(producer_id):
        raise HTTPException(status_code=400, detail="ID non valido")
    
    # Delete associated products as well
    await db.products.delete_many({"producer_id": ObjectId(producer_id)})
    res = await db.producers.delete_one({"_id": ObjectId(producer_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cantina non trovata")
        
    return {"message": "Cantina e relativi vini eliminati con successo"}
