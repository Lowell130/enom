from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_database
from app.api.v1.auth import get_current_user, get_current_admin
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

router = APIRouter()

class PairingCreate(BaseModel):
    name: str
    category: str = "GENERALE"

class PairingUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None

class PairingResponse(PairingCreate):
    id: str

DEFAULT_PAIRINGS_SEED = [
    {"name": "Carne Rossa alla Griglia", "category": "CARNI"},
    {"name": "Cacciagione e Selvaggina", "category": "CARNI"},
    {"name": "Arrosti e Tagliate di Manzo", "category": "CARNI"},
    {"name": "Formaggi Stagionati Molisani", "category": "FORMAGGI"},
    {"name": "Formaggi a Pasta Filata e Erborinati", "category": "FORMAGGI"},
    {"name": "Salumi e Affettati Tipici Molisani", "category": "SALUMI"},
    {"name": "Primi Piatti con Ragù di Carne", "category": "PRIMI"},
    {"name": "Pasta Fresca e Zuppe di Legumi", "category": "PRIMI"},
    {"name": "Risotti ai Funghi Porcini o Tartufo", "category": "PRIMI"},
    {"name": "Pesce alla Griglia e Frutti di Mare", "category": "PESCE"},
    {"name": "Brodetto di Pesce e Zuppe Marinare", "category": "PESCE"},
    {"name": "Aperitivi, Antipasti e Finger Food", "category": "APERITIVI"},
    {"name": "Pampanella Molisana", "category": "CARNI"},
    {"name": "Dolci Secchi, Pasticceria e Frutta", "category": "DOLCI"},
    {"name": "Pizze e Lievitati Artigianali", "category": "GENERALE"}
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
    existing = await db.pairings.find_one({"name": {"$regex": f"^{pairing_in.name}$", "$options": "i"}})
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
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(pairing_id):
        raise HTTPException(status_code=400, detail="ID non valido")
        
    existing = await db.pairings.find_one({"_id": ObjectId(pairing_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Abbinamento non trovato")
        
    update_data = {k: v for k, v in pairing_in.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.pairings.update_one({"_id": ObjectId(pairing_id)}, {"$set": update_data})
    updated = await db.pairings.find_one({"_id": ObjectId(pairing_id)})
    updated["id"] = str(updated["_id"])
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
