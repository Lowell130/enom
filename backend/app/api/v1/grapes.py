from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_database
from app.api.v1.auth import get_current_user, get_current_admin
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime
import re
from typing import List, Optional

from app.services.taxonomy import find_same_name, name_regex, rename_in_products

router = APIRouter()

class GrapeCreate(BaseModel):
    name: str # e.g. "Tintilia", "Montepulciano", "Trebbiano del Molise", "Malvasia", "Aglianico", "Falanghina"
    category: str = "AUTOCTONO" # "AUTOCTONO" or "INTERNAZIONALE"

class GrapeUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None

class GrapeResponse(GrapeCreate):
    id: str
    products_updated: Optional[int] = None  # vini aggiornati dopo una rinomina

DEFAULT_GRAPES_SEED = [
    {"name": "Aglianico", "category": "AUTOCTONO"},
    {"name": "Bombino Bianco", "category": "AUTOCTONO"},
    {"name": "Cabernet Sauvignon", "category": "INTERNAZIONALE"},
    {"name": "Cerasuolo", "category": "AUTOCTONO"},
    {"name": "Chardonnay", "category": "INTERNAZIONALE"},
    {"name": "Falanghina", "category": "AUTOCTONO"},
    {"name": "Garganega", "category": "AUTOCTONO"},
    {"name": "Garganica", "category": "AUTOCTONO"},
    {"name": "Greco", "category": "AUTOCTONO"},
    {"name": "Malvasia", "category": "AUTOCTONO"},
    {"name": "Merlot", "category": "INTERNAZIONALE"},
    {"name": "Montepulciano", "category": "AUTOCTONO"},
    {"name": "Moscato", "category": "AUTOCTONO"},
    {"name": "Moscato Bianco", "category": "AUTOCTONO"},
    {"name": "Moscato Reale", "category": "AUTOCTONO"},
    {"name": "Pinot Grigio", "category": "INTERNAZIONALE"},
    {"name": "Pinot Nero", "category": "INTERNAZIONALE"},
    {"name": "Riesling", "category": "INTERNAZIONALE"},
    {"name": "Sangiovese", "category": "AUTOCTONO"},
    {"name": "Sauvignon Blanc", "category": "INTERNAZIONALE"},
    {"name": "Syrah", "category": "INTERNAZIONALE"},
    {"name": "Tintilia", "category": "AUTOCTONO"},
    {"name": "Trebbiano", "category": "AUTOCTONO"},
    {"name": "Trebbiano del Molise", "category": "AUTOCTONO"}
]

@router.get("", response_model=List[GrapeResponse])
async def list_grapes(db=Depends(get_database)):
    count = await db.grapes.count_documents({})
    if count == 0:
        for item in DEFAULT_GRAPES_SEED:
            item["created_at"] = datetime.utcnow()
            await db.grapes.insert_one(dict(item))
            
    cursor = db.grapes.find().sort("name", 1)
    grapes = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        grapes.append(doc)
    return grapes

@router.post("", response_model=GrapeResponse)
async def create_grape(
    grape_in: GrapeCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    existing = await db.grapes.find_one({"name": name_regex(grape_in.name)})
    if existing:
        existing["id"] = str(existing["_id"])
        return existing
        
    doc = grape_in.model_dump()
    doc["created_at"] = datetime.utcnow()
    res = await db.grapes.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    return doc

@router.put("/{grape_id}", response_model=GrapeResponse)
async def update_grape(
    grape_id: str,
    grape_in: GrapeUpdate,
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(grape_id):
        raise HTTPException(status_code=400, detail="ID non valido")
        
    existing = await db.grapes.find_one({"_id": ObjectId(grape_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Vitigno non trovato")
        
    update_data = {k: v for k, v in grape_in.model_dump().items() if v is not None}
    old_name = existing.get("name", "")
    if "name" in update_data:
        update_data["name"] = re.sub(r"\s+", " ", update_data["name"]).strip()
        if not update_data["name"]:
            raise HTTPException(status_code=400, detail="Il nome non può essere vuoto")
        # un altro elemento con lo stesso nome creerebbe un doppione
        if await find_same_name(db.grapes, update_data["name"], exclude_id=existing["_id"]):
            raise HTTPException(status_code=409, detail="Esiste già un vitigno con questo nome")
    update_data["updated_at"] = datetime.utcnow()

    await db.grapes.update_one({"_id": ObjectId(grape_id)}, {"$set": update_data})
    # il nuovo nome vale anche per i vini che usavano quello vecchio
    products_updated = 0
    if update_data.get("name") and update_data["name"] != old_name:
        products_updated = await rename_in_products(db, "grape_varieties", old_name, update_data["name"])
    updated = await db.grapes.find_one({"_id": ObjectId(grape_id)})
    updated["id"] = str(updated["_id"])
    updated["products_updated"] = products_updated
    return updated

@router.delete("/{grape_id}")
async def delete_grape(
    grape_id: str,
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(grape_id):
        raise HTTPException(status_code=400, detail="ID non valido")
        
    res = await db.grapes.delete_one({"_id": ObjectId(grape_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vitigno non trovato")
        
    return {"message": "Vitigno eliminato con successo"}
