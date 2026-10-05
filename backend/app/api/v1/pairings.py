from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_database
from app.api.v1.auth import get_current_user, get_current_admin
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime
import re
from typing import List, Optional

from app.services.taxonomy import find_same_name, merge_into, rename_in_products

router = APIRouter()

class PairingCreate(BaseModel):
    name: str
    category: str = "GENERALE"

class PairingUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None

class PairingResponse(PairingCreate):
    id: str
    products_updated: Optional[int] = None  # vini aggiornati dopo una rinomina

DEFAULT_PAIRINGS_SEED = [
    {"name": "Antipasti & Aperitivi", "category": "APERITIVI"},
    {"name": "Arrosti & Tagliate", "category": "CARNI"},
    {"name": "Cacciagione & Selvaggina", "category": "CARNI"},
    {"name": "Carni Rosse & Grigliate", "category": "CARNI"},
    {"name": "Pampanella Molisana", "category": "CARNI"},
    {"name": "Formaggi Freschi", "category": "FORMAGGI"},
    {"name": "Formaggi Stagionati", "category": "FORMAGGI"},
    {"name": "Salumi & Affettati", "category": "SALUMI"},
    {"name": "Primi Piatti & Ragù", "category": "PRIMI"},
    {"name": "Risotti & Tartufo", "category": "PRIMI"},
    {"name": "Pesce & Frutti di Mare", "category": "PESCE"},
    {"name": "Piatti Vegetariani", "category": "GENERALE"},
    {"name": "Pizze & Lievitati", "category": "GENERALE"},
    {"name": "Pasticceria & Dolci", "category": "DOLCI"},
    {"name": "Paté & Piatti Freddi", "category": "GENERALE"}
]

@router.get("", response_model=List[PairingResponse])
async def list_pairings(db=Depends(get_database)):
    count = await db.pairings.count_documents({})
    if count == 0:
        for item in DEFAULT_PAIRINGS_SEED:
            item["created_at"] = datetime.utcnow()
            await db.pairings.insert_one(dict(item))
            
    cursor = db.pairings.find().sort("name", 1)
    pairings = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        pairings.append(doc)
    return pairings

@router.post("", response_model=PairingResponse)
async def create_pairing(
    pairing_in: PairingCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    existing = await find_same_name(db.pairings, pairing_in.name)
    if existing:
        existing["id"] = str(existing["_id"])
        return existing
        
    doc = pairing_in.model_dump()
    doc["created_at"] = datetime.utcnow()
    res = await db.pairings.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    return doc

@router.put("/{pairing_id}", response_model=PairingResponse)
async def update_pairing(
    pairing_id: str,
    pairing_in: PairingUpdate,
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(pairing_id):
        raise HTTPException(status_code=400, detail="ID non valido")
        
    existing = await db.pairings.find_one({"_id": ObjectId(pairing_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Abbinamento non trovato")
        
    update_data = {k: v for k, v in pairing_in.model_dump().items() if v is not None}
    old_name = existing.get("name", "")
    if "name" in update_data:
        update_data["name"] = re.sub(r"\s+", " ", update_data["name"]).strip()
        if not update_data["name"]:
            raise HTTPException(status_code=400, detail="Il nome non può essere vuoto")
        # un altro elemento con lo stesso nome creerebbe un doppione
        if await find_same_name(db.pairings, update_data["name"], exclude_id=existing["_id"]):
            raise HTTPException(status_code=409, detail="Esiste già un abbinamento con questo nome")
    update_data["updated_at"] = datetime.utcnow()

    await db.pairings.update_one({"_id": ObjectId(pairing_id)}, {"$set": update_data})
    # il nuovo nome vale anche per i vini che usavano quello vecchio
    products_updated = 0
    if update_data.get("name") and update_data["name"] != old_name:
        products_updated = await rename_in_products(db, "food_pairings", old_name, update_data["name"])
    updated = await db.pairings.find_one({"_id": ObjectId(pairing_id)})
    updated["id"] = str(updated["_id"])
    updated["products_updated"] = products_updated
    return updated

@router.delete("/{pairing_id}")
async def delete_pairing(
    pairing_id: str,
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(pairing_id):
        raise HTTPException(status_code=400, detail="ID non valido")
        
    res = await db.pairings.delete_one({"_id": ObjectId(pairing_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Abbinamento non trovato")
        
    return {"message": "Abbinamento eliminato con successo"}



class MergeRequest(BaseModel):
    target_id: str


@router.post("/{item_id}/merge")
async def merge_item(
    item_id: str,
    payload: MergeRequest,
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    """Unisce questa voce in un'altra: i vini passano al nome di destinazione e questa voce viene eliminata."""
    if not ObjectId.is_valid(item_id) or not ObjectId.is_valid(payload.target_id):
        raise HTTPException(status_code=400, detail="ID non valido")
    if item_id == payload.target_id:
        raise HTTPException(status_code=400, detail="Scegli una voce diversa in cui unire")
    source = await db.pairings.find_one({"_id": ObjectId(item_id)})
    target = await db.pairings.find_one({"_id": ObjectId(payload.target_id)})
    if not source or not target:
        raise HTTPException(status_code=404, detail="Voce non trovata")
    updated = await merge_into(db, db.pairings, "food_pairings", source, target)
    return {"message": f"«{source.get('name')}» unito in «{target.get('name')}»", "products_updated": updated,
            "target": {"id": str(target["_id"]), "name": target.get("name")}}
