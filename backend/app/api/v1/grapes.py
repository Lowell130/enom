from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_database
from app.api.v1.auth import get_current_user, get_current_admin
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

router = APIRouter()

class GrapeCreate(BaseModel):
    name: str # e.g. "Tintilia", "Montepulciano", "Trebbiano del Molise", "Malvasia", "Aglianico", "Falanghina"
    category: str = "AUTOCTONO" # "AUTOCTONO" or "INTERNAZIONALE"

class GrapeUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None

class GrapeResponse(GrapeCreate):
    id: str

DEFAULT_GRAPES_SEED = [
    {"name": "Tintilia", "category": "AUTOCTONO"},
    {"name": "Montepulciano", "category": "AUTOCTONO"},
    {"name": "Trebbiano del Molise", "category": "AUTOCTONO"},
    {"name": "Malvasia", "category": "AUTOCTONO"},
    {"name": "Aglianico", "category": "AUTOCTONO"},
    {"name": "Falanghina", "category": "AUTOCTONO"},
    {"name": "Sangiovese", "category": "AUTOCTONO"},
    {"name": "Bombino Bianco", "category": "AUTOCTONO"},
    {"name": "Greco", "category": "AUTOCTONO"},
    {"name": "Cerasuolo", "category": "AUTOCTONO"},
    {"name": "Chardonnay", "category": "INTERNAZIONALE"},
    {"name": "Cabernet Sauvignon", "category": "INTERNAZIONALE"},
    {"name": "Merlot", "category": "INTERNAZIONALE"},
    {"name": "Syrah", "category": "INTERNAZIONALE"},
    {"name": "Pinot Nero", "category": "INTERNAZIONALE"},
    {"name": "Sauvignon Blanc", "category": "INTERNAZIONALE"}
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
    existing = await db.grapes.find_one({"name": grape_in.name})
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
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(grape_id):
        raise HTTPException(status_code=400, detail="ID non valido")
        
    existing = await db.grapes.find_one({"_id": ObjectId(grape_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Vitigno non trovato")
        
    update_data = {k: v for k, v in grape_in.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.grapes.update_one({"_id": ObjectId(grape_id)}, {"$set": update_data})
    updated = await db.grapes.find_one({"_id": ObjectId(grape_id)})
    updated["id"] = str(updated["_id"])
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
