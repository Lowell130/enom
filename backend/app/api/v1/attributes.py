from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_database
from app.api.v1.auth import get_current_user, get_current_admin
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime
import re
from typing import List, Optional

from app.services.taxonomy import find_same_name, merge_into, name_regex, rename_in_products

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
    products_updated: Optional[int] = None  # vini aggiornati dopo una rinomina

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
    existing = await db.attributes.find_one({"name": name_regex(attr_in.name)})
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
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(attr_id):
        raise HTTPException(status_code=400, detail="ID non valido")
        
    existing = await db.attributes.find_one({"_id": ObjectId(attr_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Attributo non trovato")
        
    update_data = {k: v for k, v in attr_in.model_dump().items() if v is not None}
    old_name = existing.get("name", "")
    if "name" in update_data:
        update_data["name"] = re.sub(r"\s+", " ", update_data["name"]).strip()
        if not update_data["name"]:
            raise HTTPException(status_code=400, detail="Il nome non può essere vuoto")
        # un altro elemento con lo stesso nome creerebbe un doppione
        if await find_same_name(db.attributes, update_data["name"], exclude_id=existing["_id"]):
            raise HTTPException(status_code=409, detail="Esiste già un campo con questo nome")
    update_data["updated_at"] = datetime.utcnow()

    await db.attributes.update_one({"_id": ObjectId(attr_id)}, {"$set": update_data})
    # il nuovo nome vale anche per i vini che usavano quello vecchio
    products_updated = 0
    if update_data.get("name") and update_data["name"] != old_name:
        products_updated = await rename_in_products(db, "custom_attributes", old_name, update_data["name"])
    updated = await db.attributes.find_one({"_id": ObjectId(attr_id)})
    updated["id"] = str(updated["_id"])
    updated["products_updated"] = products_updated
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
    source = await db.attributes.find_one({"_id": ObjectId(item_id)})
    target = await db.attributes.find_one({"_id": ObjectId(payload.target_id)})
    if not source or not target:
        raise HTTPException(status_code=404, detail="Voce non trovata")
    updated = await merge_into(db, db.attributes, "custom_attributes", source, target)
    return {"message": f"«{source.get('name')}» unito in «{target.get('name')}»", "products_updated": updated,
            "target": {"id": str(target["_id"]), "name": target.get("name")}}


# --- Uso dei valori pronti nelle schede dei vini ---

def _key(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


@router.get("/usage")
async def values_usage(current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    """Per ogni campo: quanti vini usano ciascun valore (confronto senza maiuscole e spazi doppi)."""
    attrs = await db.attributes.find({}, {"name": 1}).to_list(1000)
    by_name = {_key(a.get("name")): str(a["_id"]) for a in attrs}
    usage = {str(a["_id"]): {} for a in attrs}
    async for p in db.products.find({}, {"custom_attributes": 1}):
        for ca in p.get("custom_attributes") or []:
            attr_id = by_name.get(_key(ca.get("name")))
            value = _key(ca.get("value"))
            if attr_id and value:
                usage[attr_id][value] = usage[attr_id].get(value, 0) + 1
    return usage


class UnifyValuesRequest(BaseModel):
    target: str
    sources: List[str]


@router.post("/{attr_id}/unify-values")
async def unify_values(attr_id: str, payload: UnifyValuesRequest, current_admin: dict = Depends(get_current_admin),
                       db=Depends(get_database)):
    """Valori uguali scritti in modo diverso ("300m slm", "300 m s.l.m."): i vini passano al valore scelto
    e gli altri spariscono dai valori pronti."""
    if not ObjectId.is_valid(attr_id):
        raise HTTPException(status_code=400, detail="ID non valido")
    attr = await db.attributes.find_one({"_id": ObjectId(attr_id)})
    if not attr:
        raise HTTPException(status_code=404, detail="Campo non trovato")
    target = re.sub(r"\s+", " ", payload.target or "").strip()
    if not target:
        raise HTTPException(status_code=400, detail="Scegli il valore da tenere")
    sources = {_key(s) for s in payload.sources if _key(s)} - {_key(target)}
    if not sources:
        raise HTTPException(status_code=400, detail="Nessun valore da unificare")

    name_key = _key(attr.get("name"))
    updated = 0
    async for p in db.products.find({}, {"custom_attributes": 1}):
        changed = False
        new_list = []
        for ca in p.get("custom_attributes") or []:
            if _key(ca.get("name")) == name_key and _key(ca.get("value")) in sources:
                ca = {**ca, "value": target}
                changed = True
            new_list.append(ca)
        if changed:
            await db.products.update_one({"_id": p["_id"]}, {"$set": {"custom_attributes": new_list}})
            updated += 1

    presets = [v for v in attr.get("suggested_values") or [] if _key(v) not in sources]
    if _key(target) not in {_key(v) for v in presets}:
        presets.append(target)
    await db.attributes.update_one({"_id": attr["_id"]}, {"$set": {"suggested_values": presets, "updated_at": datetime.utcnow()}})
    return {"message": f"Valori unificati in «{target}»", "products_updated": updated, "suggested_values": presets}
