from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.db.mongodb import get_database
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.api.v1.auth import get_current_user
from bson import ObjectId
from datetime import datetime
from typing import Optional, List
import re

router = APIRouter()

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

from html.parser import HTMLParser
import urllib.request

class SimpleHTMLScraper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.og_title = ""
        self.og_desc = ""
        self.og_image = ""
        self.paragraphs = []
        self.in_title = False
        self.in_p = False
        self.current_p = ""

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            prop = attr_dict.get("property", "") or attr_dict.get("name", "")
            content = attr_dict.get("content", "")
            if prop == "og:title":
                self.og_title = content
            elif prop in ["og:description", "description"]:
                self.og_desc = content
            elif prop == "og:image":
                self.og_image = content
        elif tag == "p":
            self.in_p = True
            self.current_p = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "p":
            self.in_p = False
            if len(self.current_p.strip()) > 30:
                self.paragraphs.append(self.current_p.strip())

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_p:
            self.current_p += data

async def format_product_response(doc: dict, db) -> dict:
    doc["id"] = str(doc["_id"])
    doc["producer_id"] = str(doc["producer_id"])
    
    producer = await db.producers.find_one({"_id": ObjectId(doc["producer_id"])})
    if producer:
        doc["producer_name"] = producer.get("company_name", "")
        doc["producer_slug"] = producer.get("slug", "")
    return doc

@router.post("/scrape-url")
async def scrape_url(payload: dict):
    url = payload.get("url", "").strip()
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="URL non valido")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        parser = SimpleHTMLScraper()
        parser.feed(html)
        
        name = parser.og_title or parser.title
        description = parser.og_desc or (parser.paragraphs[0] if parser.paragraphs else "")
        photo_url = parser.og_image
        
        lower_html = html.lower()
        
        category = "VINO_ROSSO"
        if "spumante" in lower_html or "brut" in lower_html:
            category = "SPUMANTE"
        elif "rosato" in lower_html or "rosé" in lower_html:
            category = "ROSATO"
        elif "bianco" in lower_html:
            category = "VINO_BIANCO"
        elif "passito" in lower_html:
            category = "PASSITO"
            
        denominazione = "DOC"
        if "tintilia del molise doc" in lower_html:
            denominazione = "Tintilia del Molise DOC"
        elif "biferno doc" in lower_html:
            denominazione = "Biferno DOC"
        elif "igt" in lower_html:
            denominazione = "IGT"
            
        is_riserva = "riserva" in lower_html
        
        year_match = re.search(r'\b(20[0-2][0-9])\b', lower_html)
        vintage_year = int(year_match.group(1)) if year_match else None
        
        alc_match = re.search(r'(\d{2}(?:[.,]\d)?)\s*%\s*(?:vol)?', lower_html)
        alcohol_degrees = float(alc_match.group(1).replace(',', '.')) if alc_match else None
        
        return {
            "name": name.strip(),
            "category": category,
            "denominazione": denominazione,
            "vintage_year": vintage_year,
            "is_riserva": is_riserva,
            "alcohol_degrees": alcohol_degrees,
            "description": description.strip(),
            "photo_url": photo_url,
            "technical_sheet_pdf": ""
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Errore durante l'analisi dell'URL: {str(e)}")

@router.get("", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    denominazione: Optional[str] = None,
    producer_id: Optional[str] = None,
    vintage_year: Optional[int] = None,
    is_riserva: Optional[bool] = None,
    search: Optional[str] = None,
    status: Optional[str] = "PUBLISHED",
    db=Depends(get_database)
):
    query = {}
    if status and status != "ALL":
        query["status"] = status
    if category:
        query["category"] = category
    if denominazione:
        query["denominazione"] = denominazione
    if vintage_year:
        query["vintage_year"] = vintage_year
    if is_riserva is not None:
        query["is_riserva"] = is_riserva
    if producer_id and ObjectId.is_valid(producer_id):
        query["producer_id"] = ObjectId(producer_id)
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"grape_varieties": {"$elemMatch": {"$regex": search, "$options": "i"}}}
        ]
        
    cursor = db.products.find(query).sort("created_at", -1)
    products = []
    async for doc in cursor:
        formatted = await format_product_response(doc, db)
        products.append(formatted)
    return products

@router.get("/{identifier}", response_model=ProductResponse)
async def get_product_by_slug_or_id(identifier: str, db=Depends(get_database)):
    query = {"$or": [{"slug": identifier}]}
    if ObjectId.is_valid(identifier):
        query["$or"].append({"_id": ObjectId(identifier)})
        
    doc = await db.products.find_one(query)
    if not doc:
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
        
    return await format_product_response(doc, db)

async def sync_custom_attributes_with_master(custom_attributes: list, db):
    if not custom_attributes:
        return
    for attr in custom_attributes:
        name = attr.get("name", "").strip() if isinstance(attr, dict) else (getattr(attr, "name", "") or "").strip()
        val = attr.get("value", "").strip() if isinstance(attr, dict) else (getattr(attr, "value", "") or "").strip()
        if not name or not val:
            continue
        existing = await db.attributes.find_one({"name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}})
        if existing:
            current_suggs = existing.get("suggested_values", [])
            # Case-insensitive check to prevent duplicates
            if not any(s.strip().lower() == val.strip().lower() for s in current_suggs):
                await db.attributes.update_one(
                    {"_id": existing["_id"]},
                    {"$addToSet": {"suggested_values": val.strip()}}
                )
        else:
            await db.attributes.insert_one({
                "name": name,
                "unit_or_hint": "",
                "suggested_values": [val.strip()],
                "created_at": datetime.utcnow()
            })

async def sync_grapes_with_master(grape_varieties: list, db):
    if not grape_varieties:
        return
    for item in grape_varieties:
        if not item or not isinstance(item, str):
            continue
        clean_name = re.sub(r'\d+\s*%?', '', item).strip()
        if not clean_name:
            continue
        existing = await db.grapes.find_one({"name": {"$regex": f"^{re.escape(clean_name)}$", "$options": "i"}})
        if not existing:
            await db.grapes.insert_one({
                "name": clean_name,
                "category": "AUTOCTONO",
                "created_at": datetime.utcnow()
            })

async def sync_pairings_with_master(food_pairings: list, db):
    if not food_pairings:
        return
    for item in food_pairings:
        if not item or not isinstance(item, str):
            continue
        clean_name = item.strip()
        if not clean_name:
            continue
        existing = await db.pairings.find_one({"name": {"$regex": f"^{re.escape(clean_name)}$", "$options": "i"}})
        if not existing:
            await db.pairings.insert_one({
                "name": clean_name,
                "category": "GENERALE",
                "created_at": datetime.utcnow()
            })

@router.post("", response_model=ProductResponse)
async def create_product(
    product_in: ProductCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    is_admin = current_user.get("role") == "ADMIN"
    
    if is_admin:
        if not product_in.producer_id or not ObjectId.is_valid(product_in.producer_id):
            raise HTTPException(status_code=400, detail="Devi specificare una cantina valida per questo prodotto")
        target_producer_id = ObjectId(product_in.producer_id)
    else:
        # Producer user
        user_producer_id = current_user.get("producer_id")
        if not user_producer_id or not ObjectId.is_valid(user_producer_id):
            raise HTTPException(status_code=400, detail="Il tuo account non è collegato ad alcuna cantina")
        target_producer_id = ObjectId(user_producer_id)
        
    # Verify producer exists
    producer = await db.producers.find_one({"_id": target_producer_id})
    if not producer:
        raise HTTPException(status_code=404, detail="Cantina non trovata")
        
    riserva_tag = "riserva" if product_in.is_riserva else ""
    slug = product_in.slug or slugify(f"{product_in.name} {product_in.vintage_year or ''} {riserva_tag}".strip())
    slug_count = await db.products.count_documents({"slug": slug})
    if slug_count > 0:
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
        
    doc = product_in.model_dump()
    doc["producer_id"] = target_producer_id
    doc["slug"] = slug
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()
    
    res = await db.products.insert_one(doc)
    doc["_id"] = res.inserted_id

    # Auto-sync custom attributes, grapes & food pairings with master collections
    await sync_custom_attributes_with_master(doc.get("custom_attributes", []), db)
    await sync_grapes_with_master(doc.get("grape_varieties", []), db)
    await sync_pairings_with_master(doc.get("food_pairings", []), db)

    return await format_product_response(doc, db)

@router.post("/{product_id}/clone", response_model=ProductResponse)
async def clone_product(
    product_id: str,
    target_producer_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="ID prodotto non valido")
        
    original = await db.products.find_one({"_id": ObjectId(product_id)})
    if not original:
        raise HTTPException(status_code=404, detail="Prodotto da clonare non trovato")
        
    is_admin = current_user.get("role") == "ADMIN"
    user_producer_id = current_user.get("producer_id")
    
    # Check permissions
    if not is_admin and str(original["producer_id"]) != str(user_producer_id):
        raise HTTPException(status_code=403, detail="Non puoi clonare i prodotti di un'altra cantina")
        
    # Determine new producer_id
    if is_admin and target_producer_id and ObjectId.is_valid(target_producer_id):
        new_producer_id = ObjectId(target_producer_id)
    else:
        new_producer_id = original["producer_id"]
        
    cloned_doc = dict(original)
    del cloned_doc["_id"]
    
    cloned_doc["producer_id"] = new_producer_id
    cloned_doc["name"] = f"{original['name']} (Copia)"
    cloned_doc["slug"] = slugify(f"{cloned_doc['name']}-{int(datetime.utcnow().timestamp())}")
    cloned_doc["status"] = "DRAFT" # Draft until user edits
    cloned_doc["created_at"] = datetime.utcnow()
    cloned_doc["updated_at"] = datetime.utcnow()
    
    res = await db.products.insert_one(cloned_doc)
    cloned_doc["_id"] = res.inserted_id
    return await format_product_response(cloned_doc, db)

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_in: ProductUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="ID prodotto non valido")
        
    existing = await db.products.find_one({"_id": ObjectId(product_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
        
    is_admin = current_user.get("role") == "ADMIN"
    user_producer_id = current_user.get("producer_id")
    
    if not is_admin and str(existing["producer_id"]) != str(user_producer_id):
        raise HTTPException(status_code=403, detail="Non puoi modificare questo prodotto")
        
    update_data = {k: v for k, v in product_in.model_dump().items() if v is not None}
    
    # Handle producer_id reassignment by Admin
    if "producer_id" in update_data:
        if is_admin and ObjectId.is_valid(update_data["producer_id"]):
            update_data["producer_id"] = ObjectId(update_data["producer_id"])
        else:
            del update_data["producer_id"]
            
    if "name" in update_data and update_data["name"] != existing.get("name"):
        v_year = update_data.get('vintage_year', existing.get('vintage_year', ''))
        is_ris = update_data.get('is_riserva', existing.get('is_riserva', False))
        ris_tag = "riserva" if is_ris else ""
        update_data["slug"] = slugify(f"{update_data['name']} {v_year or ''} {ris_tag}".strip())
        
    update_data["updated_at"] = datetime.utcnow()
    
    await db.products.update_one({"_id": ObjectId(product_id)}, {"$set": update_data})
    
    if "custom_attributes" in update_data:
        await sync_custom_attributes_with_master(update_data["custom_attributes"], db)
    if "grape_varieties" in update_data:
        await sync_grapes_with_master(update_data["grape_varieties"], db)
    if "food_pairings" in update_data:
        await sync_pairings_with_master(update_data["food_pairings"], db)

    updated = await db.products.find_one({"_id": ObjectId(product_id)})
    return await format_product_response(updated, db)

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="ID prodotto non valido")
        
    existing = await db.products.find_one({"_id": ObjectId(product_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
        
    is_admin = current_user.get("role") == "ADMIN"
    user_producer_id = current_user.get("producer_id")
    
    if not is_admin and str(existing["producer_id"]) != str(user_producer_id):
        raise HTTPException(status_code=403, detail="Non puoi eliminare questo prodotto")
        
    await db.products.delete_one({"_id": ObjectId(product_id)})
    return {"message": "Prodotto eliminato con successo"}
