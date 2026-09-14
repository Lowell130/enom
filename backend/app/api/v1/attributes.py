from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_database
from app.api.v1.auth import get_current_user, get_current_admin
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

router = APIRouter()

class AttributeCreate(BaseModel):
    name: str # e.g. "Vinificazione", "Allevamento", "Vendemmia", "Allergeni", "Formato", "Gradazione Alcolica"
    unit_or_hint: str = "" # e.g. "% Vol", "cl", "°C"
    suggested_values: List[str] = []

class AttributeUpdate(BaseModel):
    name: Optional[str] = None
    unit_or_hint: Optional[str] = None
    suggested_values: Optional[List[str]] = None

class AttributeResponse(AttributeCreate):
    id: str

DEFAULT_ATTRIBUTES_SEED = [
    {
        "name": "Tipo Vino",
        "unit_or_hint": "Tipologia / Certificazione",
        "suggested_values": ["Vino Biologico", "Vino Biodinamico", "Vino Naturale", "Vino Convenzionale"]
    },
    {
        "name": "Gradazione Alcolica",
        "unit_or_hint": "% Vol",
        "suggested_values": ["10.0%", "10.5%", "11.0%", "11.5%", "12.0%", "12.5%", "13.0%", "13.5%", "14.0%", "14.5%", "15.0%", "15.5%", "16.0%"]
    },
    {
        "name": "Temperatura di Servizio",
        "unit_or_hint": "°C",
        "suggested_values": ["6° - 8° C", "8° - 10° C", "10° - 12° C", "12° - 14° C", "14° - 16° C", "16° - 18° C", "18° - 20° C"]
    },
    {
        "name": "Vinificazione",
        "unit_or_hint": "Metodo di lavorazione",
        "suggested_values": ["Acciaio Inox", "Barrique di Rovere Francese", "Botte Grande", "Anfora di Terracotta", "Cemento", "Macerazione sulle bucce"]
    },
    {
        "name": "Allevamento",
        "unit_or_hint": "Sistema di potatura",
        "suggested_values": ["Guyot", "Cordone Speronato", "Alberello", "Tendone", "Pergola Abruzzese/Molisana"]
    },
    {
        "name": "Vendemmia",
        "unit_or_hint": "Periodo o modalità",
        "suggested_values": ["Manuale in cassette", "Meccanizzata", "Prima decade di Settembre", "Fine Settembre", "Inizio Ottobre", "Tarda (Novembre)"]
    },
    {
        "name": "Allergeni",
        "unit_or_hint": "Indicazione etichetta",
        "suggested_values": ["Contiene Solfiti", "Senza Solfiti Aggiunti", "Può contenere tracce di proteine dell'uovo"]
    },
    {
        "name": "Formato Bottiglia",
        "unit_or_hint": "Capacità",
        "suggested_values": ["75 cl (Standard)", "1.5 L (Magnum)", "3.0 L (Jéroboam)", "37.5 cl (Mezza)"]
    },
    {
        "name": "Affinamento",
        "unit_or_hint": "Durata e contenitore",
        "suggested_values": ["6 Mesi in Acciaio", "12 Mesi in Barrique", "24 Mesi (12 Barrique + 12 Bottiglia)", "36 Mesi Riserva"]
    }
]

@router.get("", response_model=List[AttributeResponse])
async def list_attributes(db=Depends(get_database)):
    count = await db.attributes.count_documents({})
    if count == 0:
        for item in DEFAULT_ATTRIBUTES_SEED:
            item["created_at"] = datetime.utcnow()
            await db.attributes.insert_one(dict(item))
            
    cursor = db.attributes.find().sort("name", 1)
    attrs = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        if "suggested_values" not in doc:
            doc["suggested_values"] = []
        attrs.append(doc)
    return attrs

@router.post("", response_model=AttributeResponse)
async def create_attribute(
    attr_in: AttributeCreate,
    current_user: dict = Depends(get_current_user), # Allowed for both Producer and Admin
    db=Depends(get_database)
):
    existing = await db.attributes.find_one({"name": attr_in.name})
    if existing:
        existing["id"] = str(existing["_id"])
        if attr_in.suggested_values:
            new_values = list(set(existing.get("suggested_values", []) + attr_in.suggested_values))
            await db.attributes.update_one({"_id": existing["_id"]}, {"$set": {"suggested_values": new_values}})
            existing["suggested_values"] = new_values
        return existing
        
    doc = attr_in.model_dump()
    doc["created_at"] = datetime.utcnow()
    res = await db.attributes.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    return doc

@router.put("/{attr_id}", response_model=AttributeResponse)
async def update_attribute(
    attr_id: str,
    attr_in: AttributeUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(attr_id):
        raise HTTPException(status_code=400, detail="ID non valido")
        
    existing = await db.attributes.find_one({"_id": ObjectId(attr_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Attributo non trovato")
        
    update_data = {k: v for k, v in attr_in.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.attributes.update_one({"_id": ObjectId(attr_id)}, {"$set": update_data})
    updated = await db.attributes.find_one({"_id": ObjectId(attr_id)})
    updated["id"] = str(updated["_id"])
    return updated

@router.delete("/{attr_id}")
async def delete_attribute(
    attr_id: str,
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(attr_id):
        raise HTTPException(status_code=400, detail="ID non valido")
        
    res = await db.attributes.delete_one({"_id": ObjectId(attr_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Attributo non trovato")
        
    return {"message": "Attributo eliminato con successo"}
