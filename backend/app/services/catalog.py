"""Logica di dominio del catalogo vini: normalizzazione di titoli, denominazioni
e slug, formattazione delle risposte e migrazione di pulizia del catalogo."""
import re
from datetime import datetime

from bson import ObjectId

from app.core.utils import slugify


def parse_denominazione_acronym(denom: str) -> str:
    if not denom:
        return "DOC"
    d_upper = str(denom).strip().upper()
    if "DOCG" in d_upper or "D.O.C.G." in d_upper:
        return "DOCG"
    elif "DOC" in d_upper or "D.O.C." in d_upper:
        return "DOC"
    elif "DOP" in d_upper or "D.O.P." in d_upper:
        return "DOP"
    elif "IGP" in d_upper or "I.G.P." in d_upper:
        return "IGP"
    elif "IGT" in d_upper or "I.G.T." in d_upper:
        return "IGT"
    return "DOC"

def clean_wine_title(title: str) -> str:
    if not title:
        return ""
    # Remove denominations (DOCG, DOC, DOP, IGP, IGT with or without dots)
    cleaned = re.sub(
        r'(?i)\b(?:d[\s.]*o[\s.]*c[\s.]*g|d[\s.]*o[\s.]*c|d[\s.]*o[\s.]*p|i[\s.]*g[\s.]*p|i[\s.]*g[\s.]*t)\b\.?',
        '',
        title
    )
    # Remove 4-digit years (e.g. 19xx, 20xx)
    cleaned = re.sub(r'\b(19\d{2}|20\d{2})\b', '', cleaned)
    # Clean extra spaces and punctuation
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(' -.,')
    return cleaned if cleaned else title.strip()

def clean_product_slug(text: str) -> str:
    if not text:
        return ""
    # Normalize hyphens and underscores to spaces so word boundary regex works
    cleaned = str(text).replace('-', ' ').replace('_', ' ')
    
    # Remove denominations
    cleaned = re.sub(
        r'(?i)\b(?:d[\s.]*o[\s.]*c[\s.]*g|d[\s.]*o[\s.]*c|d[\s.]*o[\s.]*p|i[\s.]*g[\s.]*p|i[\s.]*g[\s.]*t)\b\.?',
        '',
        cleaned
    )
    
    # Remove 4-digit years
    cleaned = re.sub(r'\b(19\d{2}|20\d{2})\b', '', cleaned)
    
    # kebab-case senza accenti (stessa regola degli slug delle cantine)
    return slugify(cleaned) or slugify(str(text))

async def generate_unique_product_slug(
    db, 
    name: str, 
    producer_id, 
    is_riserva: bool = False,
    exclude_id = None
) -> str:
    cleaned_name = clean_wine_title(name)
    ris_tag = "riserva" if is_riserva and "riserva" not in cleaned_name.lower() else ""
    base_slug = clean_product_slug(f"{cleaned_name} {ris_tag}")
    if not base_slug:
        base_slug = "vino"
    
    # 1. Check if base_slug is free
    query = {"slug": base_slug}
    if exclude_id:
        query["_id"] = {"$ne": ObjectId(exclude_id)}
        
    existing = await db.products.find_one(query)
    if not existing:
        return base_slug
        
    if exclude_id and str(existing.get("_id")) == str(exclude_id):
        return base_slug
        
    # Collision! Retrieve producer slug
    producer = None
    if producer_id and ObjectId.is_valid(producer_id):
        producer = await db.producers.find_one({"_id": ObjectId(producer_id)})
    prod_slug = producer.get("slug") if producer else ""
    
    # 2. If existing product belongs to another winery, append this winery's slug
    if prod_slug and str(existing.get("producer_id")) != str(producer_id):
        candidate = f"{base_slug}-{prod_slug}"
        c_query = {"slug": candidate}
        if exclude_id:
            c_query["_id"] = {"$ne": ObjectId(exclude_id)}
        if not await db.products.find_one(c_query):
            return candidate

    # 3. Fallback to incremental counter (-2, -3, ...)
    counter = 2
    while True:
        candidate = f"{base_slug}-{counter}"
        c_query = {"slug": candidate}
        if exclude_id:
            c_query["_id"] = {"$ne": ObjectId(exclude_id)}
        if not await db.products.find_one(c_query):
            return candidate
        counter += 1

async def ensure_unique_product_slug(db, raw_slug: str, exclude_id=None) -> str:
    """Pulisce uno slug scelto manualmente e garantisce che sia univoco."""
    base = clean_product_slug(raw_slug) or "vino"
    candidate, counter = base, 2
    while True:
        q = {"slug": candidate}
        if exclude_id is not None:
            q["_id"] = {"$ne": exclude_id}
        if not await db.products.find_one(q, {"_id": 1}):
            return candidate
        candidate = f"{base}-{counter}"
        counter += 1

async def format_product_response(doc: dict, db) -> dict:
    doc["id"] = str(doc["_id"])
    doc["producer_id"] = str(doc["producer_id"])
    
    producer = await db.producers.find_one({"_id": ObjectId(doc["producer_id"])})
    if producer:
        doc["producer_name"] = producer.get("company_name", "")
        doc["producer_slug"] = producer.get("slug", "")
    return doc

async def run_products_cleanup_migration(db) -> int:
    products = await db.products.find({}).to_list(length=10000)
    migrated_count = 0
    for prod in products:
        p_id = prod["_id"]
        old_name = prod.get("name", "")
        old_slug = prod.get("slug", "")
        old_vintage = prod.get("vintage_year")
        old_denom = prod.get("denominazione", "")
        
        # 1. Clean wine title from dates and denominations
        new_name = clean_wine_title(old_name)
        
        # 2. Standardize denominazione acronym
        new_denom = parse_denominazione_acronym(old_denom) if old_denom else "DOC"
        
        # 3. Always set vintage_year = None (Catalogo Senza Annata - S.A.)
        new_vintage = None
        
        # 4. Generate unique clean slug without vintage_year and without denominations
        new_slug = await generate_unique_product_slug(
            db=db,
            name=new_name,
            producer_id=prod.get("producer_id"),
            is_riserva=bool(prod.get("is_riserva", False)),
            exclude_id=p_id
        )
        
        update_fields = {}
        if new_name != old_name:
            update_fields["name"] = new_name
        if new_denom != old_denom:
            update_fields["denominazione"] = new_denom
        if old_vintage is not None:
            update_fields["vintage_year"] = new_vintage
        if new_slug != old_slug:
            update_fields["slug"] = new_slug
            
        if update_fields:
            update_fields["updated_at"] = datetime.utcnow()
            await db.products.update_one({"_id": p_id}, {"$set": update_fields})
            migrated_count += 1
            
    return migrated_count


async def migrate_ascii_slugs(db) -> int:
    """Toglie gli accenti dagli indirizzi gia' salvati ("vietènn-..." -> "vietenn-...").
    Eseguita all'avvio: non fa nulla se tutti gli indirizzi sono gia' senza accenti.
    I vecchi link continuano a funzionare perche' la ricerca per indirizzo li ripulisce allo stesso modo."""
    changed = 0
    for collection, fallback in ((db.products, "vino"), (db.producers, "cantina")):
        async for doc in collection.find({"slug": {"$regex": "[^a-z0-9-]"}}, {"slug": 1}):
            base = slugify(doc.get("slug", "")) or fallback
            candidate, counter = base, 2
            while await collection.find_one({"slug": candidate, "_id": {"$ne": doc["_id"]}}, {"_id": 1}):
                candidate = f"{base}-{counter}"
                counter += 1
            if candidate != doc.get("slug"):
                await collection.update_one({"_id": doc["_id"]}, {"$set": {"slug": candidate}})
                changed += 1
    return changed
