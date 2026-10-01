"""CRUD dei vini e ricerca pubblica.
Import/export: vedi product_io.py. Logica di dominio: app/services/catalog.py."""
import re
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.auth import get_current_user, get_optional_user, is_admin, owns_producer
from app.db.mongodb import get_database
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.catalog import (
    clean_product_slug,
    clean_wine_title,
    ensure_unique_product_slug,
    format_product_response,
    generate_unique_product_slug,
    parse_denominazione_acronym,
    run_products_cleanup_migration,
)
from app.services.taxonomy import (
    sync_custom_attributes_with_master,
    sync_grapes_with_master,
    sync_pairings_with_master,
)

router = APIRouter()


@router.get("", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    denominazione: Optional[str] = None,
    producer_id: Optional[str] = None,
    vintage_year: Optional[int] = None,
    is_riserva: Optional[bool] = None,
    search: Optional[str] = Query(None, max_length=100),
    status: Optional[str] = "PUBLISHED",
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=1000),
    current_user: Optional[dict] = Depends(get_optional_user),
    db=Depends(get_database)
):
    admin = is_admin(current_user)
    requested_status = (status or "PUBLISHED").upper()

    query = {}
    # Visitatori anonimi: solo vini pubblicati. Bozze/ALL solo per admin (tutto)
    # o per il produttore autenticato (limitate alla propria cantina).
    private_view = requested_status != "PUBLISHED"
    if private_view:
        if not current_user:
            raise HTTPException(status_code=401, detail="Autenticazione richiesta per visualizzare le bozze")
        if not admin:
            own_id = current_user.get("producer_id")
            if not own_id or not ObjectId.is_valid(own_id):
                return []
            if producer_id and producer_id != own_id:
                raise HTTPException(status_code=403, detail="Puoi visualizzare solo le bozze della tua cantina")
            producer_id = own_id
    if requested_status != "ALL":
        query["status"] = requested_status
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
        escaped_search = re.escape(search.strip())
        matching_producers = await db.producers.find({
            "$or": [
                {"company_name": {"$regex": escaped_search, "$options": "i"}},
                {"slug": {"$regex": escaped_search, "$options": "i"}}
            ]
        }, {"_id": 1}).to_list(500)
        matching_prod_ids = [p["_id"] for p in matching_producers]

        search_or_conditions = [
            {"name": {"$regex": escaped_search, "$options": "i"}},
            {"description": {"$regex": escaped_search, "$options": "i"}},
            {"denominazione": {"$regex": escaped_search, "$options": "i"}},
            {"grape_varieties": {"$elemMatch": {"$regex": escaped_search, "$options": "i"}}},
            {"food_pairings": {"$elemMatch": {"$regex": escaped_search, "$options": "i"}}},
            {"custom_attributes.value": {"$regex": escaped_search, "$options": "i"}},
            {"custom_attributes.name": {"$regex": escaped_search, "$options": "i"}}
        ]
        if matching_prod_ids:
            search_or_conditions.append({"producer_id": {"$in": matching_prod_ids}})
        query["$or"] = search_or_conditions

    # Mappa cantine (una sola query, niente N+1)
    producers = await db.producers.find().to_list(1000)
    producer_map = {str(p["_id"]): p for p in producers}

    # Nella vista pubblica si escludono i vini di cantine non approvate
    if not private_view:
        approved_ids = [p["_id"] for p in producers if p.get("status", "APPROVED") == "APPROVED"]
        if "producer_id" in query:
            if query["producer_id"] not in approved_ids:
                return []
        else:
            query["producer_id"] = {"$in": approved_ids}

    cursor = db.products.find(query).sort("created_at", -1).skip(skip).limit(limit)
    raw_products = await cursor.to_list(limit)

    products = []
    for doc in raw_products:
        doc["id"] = str(doc["_id"])
        doc["producer_id"] = str(doc["producer_id"])
        prod_obj = producer_map.get(doc["producer_id"])
        doc["producer_name"] = prod_obj.get("company_name", "") if prod_obj else ""
        doc["producer_slug"] = prod_obj.get("slug", "") if prod_obj else ""
        products.append(doc)
    return products

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
        
    cleaned_name = clean_wine_title(product_in.name)
    if product_in.slug:
        slug = await ensure_unique_product_slug(db, product_in.slug)
    else:
        slug = await generate_unique_product_slug(
            db=db,
            name=cleaned_name,
            producer_id=target_producer_id,
            is_riserva=product_in.is_riserva
        )
        
    doc = product_in.model_dump()
    doc["name"] = cleaned_name
    doc["producer_id"] = target_producer_id
    doc["denominazione"] = parse_denominazione_acronym(doc.get("denominazione", "DOC"))
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
        if not await db.producers.find_one({"_id": new_producer_id}, {"_id": 1}):
            raise HTTPException(status_code=404, detail="Cantina di destinazione non trovata")
    else:
        new_producer_id = original["producer_id"]
        
    cloned_doc = dict(original)
    del cloned_doc["_id"]
    cloned_doc["producer_id"] = new_producer_id
    
    cloned_name = f"{clean_wine_title(original['name'])} (Copia)"
    cloned_doc["name"] = cloned_name
    cloned_doc["slug"] = await ensure_unique_product_slug(db, clean_product_slug(cloned_name))
    cloned_doc["vintage_year"] = None # Reset to Senza Annata (S.A.)
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
            if not await db.producers.find_one({"_id": update_data["producer_id"]}, {"_id": 1}):
                raise HTTPException(status_code=404, detail="Cantina di destinazione non trovata")
        else:
            del update_data["producer_id"]
            
    if "denominazione" in update_data:
        update_data["denominazione"] = parse_denominazione_acronym(update_data["denominazione"])

    if "name" in update_data:
        update_data["name"] = clean_wine_title(update_data["name"])
        if update_data["name"] != existing.get("name"):
            is_ris = update_data.get('is_riserva', existing.get('is_riserva', False))
            target_prod_id = update_data.get("producer_id", existing["producer_id"])
            update_data["slug"] = await generate_unique_product_slug(
                db=db,
                name=update_data["name"],
                producer_id=target_prod_id,
                is_riserva=is_ris,
                exclude_id=existing["_id"]
            )

        
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

@router.post("/cleanup-slugs-and-titles")
async def cleanup_slugs_and_titles(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Solo gli amministratori possono eseguire la pulizia")
    
    migrated_count = await run_products_cleanup_migration(db)
    return {"message": f"Pulizia catalogo completata con successo: {migrated_count} vini aggiornati a Senza Annata (S.A.) e slug puliti."}

@router.get("/{identifier}", response_model=ProductResponse)
async def get_product_by_slug_or_id(
    identifier: str,
    current_user: Optional[dict] = Depends(get_optional_user),
    db=Depends(get_database)
):
    query = {"$or": [{"slug": identifier}]}
    cleaned = clean_product_slug(identifier)
    if cleaned and cleaned != identifier:
        query["$or"].append({"slug": cleaned})
    if ObjectId.is_valid(identifier):
        query["$or"].append({"_id": ObjectId(identifier)})

    doc = await db.products.find_one(query)
    if not doc:
        # Fallback flessibile: ad es. se viene cercato "tintilia-molise", trova "tintilia-del-molise"
        parts = [re.escape(p) for p in identifier.split('-')[:12] if p and p not in ['del', 'di', 'dei', 'della', 'degli', 'doc', 'igt', 'dop', 'docg', 'igp']]
        if parts:
            regex_pattern = ".*".join(parts)
            doc = await db.products.find_one({"slug": {"$regex": f"^{regex_pattern}", "$options": "i"}, "status": "PUBLISHED"})

    if not doc:
        raise HTTPException(status_code=404, detail="Prodotto non trovato")

    # Bozze e vini di cantine non approvate: visibili solo ad admin e proprietario
    if not (is_admin(current_user) or owns_producer(current_user, doc.get("producer_id"))):
        producer = await db.producers.find_one({"_id": doc.get("producer_id")}, {"status": 1})
        if doc.get("status") != "PUBLISHED" or not producer or producer.get("status", "APPROVED") != "APPROVED":
            raise HTTPException(status_code=404, detail="Prodotto non trovato")

    return await format_product_response(doc, db)
