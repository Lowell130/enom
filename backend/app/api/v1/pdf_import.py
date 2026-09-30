"""Importazione guidata dei vini da schede PDF (solo amministratore).

  GET  /products/import/ai-status     stato della configurazione IA
  POST /products/import/parse-pdfs    analizza uno o piu' PDF e propone i vini (nessuna scrittura nel DB)
  POST /products/import/confirm-batch crea/aggiorna i vini revisionati dall'amministratore
"""
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.api.v1.auth import get_current_admin
from app.db.mongodb import get_database
from app.schemas.product import ProductCreate
from app.services.ai_extractor import AIExtractionError, provider_status
from app.services.catalog import (
    clean_wine_title,
    generate_unique_product_slug,
    parse_denominazione_acronym,
)
from app.services.duplicates import compare_names, find_duplicate, name_key
from app.services.pdf_importer import CANONICAL_PAIRINGS, SUPPORTED_EXTENSIONS, match_producer, process_document
from app.services.taxonomy import (
    sync_custom_attributes_with_master,
    sync_grapes_with_master,
    sync_pairings_with_master,
)

logger = logging.getLogger("enotecamolise.pdf")
router = APIRouter()

MAX_PDF_FILES = 30
MAX_PDF_BYTES = 15 * 1024 * 1024
MAX_BATCH_WINES = 200


async def _load_taxonomy(db):
    attributes = [a["name"] for a in await db.attributes.find({}, {"name": 1}).to_list(500) if a.get("name")]
    grapes = [g["name"] for g in await db.grapes.find({}, {"name": 1}).to_list(500) if g.get("name")]
    pairings = [p["name"] for p in await db.pairings.find({}, {"name": 1}).to_list(200) if p.get("name")]
    return attributes, grapes, pairings or CANONICAL_PAIRINGS


async def _producer_wines(db, producer_id: ObjectId) -> List[Dict[str, Any]]:
    return await db.products.find(
        {"producer_id": producer_id},
        {"name": 1, "slug": 1, "status": 1, "category": 1, "is_riserva": 1},
    ).to_list(2000)


def _mark_batch_duplicates(wines: List[Dict[str, Any]]) -> None:
    """Nello stesso import, i vini ripetuti (stessa cantina, stesso nome) dopo il primo non vengono importati."""
    seen: List[Dict[str, Any]] = []
    for w in wines:
        for first in seen:
            if first.get("producer_id") and first.get("producer_id") == w.get("producer_id") \
                    and bool(first.get("is_riserva")) == bool(w.get("is_riserva")) \
                    and compare_names(first["name"], w["name"])[0]:
                w["batch_duplicate_of"] = {"name": first["name"], "source_file": first.get("source_file", "")}
                w["action"] = "skip"
                break
        else:
            seen.append(w)


@router.get("/import/ai-status")
async def ai_status(current_admin: dict = Depends(get_current_admin)):
    return provider_status()


@router.post("/import/parse-pdfs")
async def parse_pdfs_batch(
    files: List[UploadFile] = File(...),
    producer_id: Optional[str] = Form(None),
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    """Analizza i PDF e restituisce i vini proposti, uno o piu' per file. Non salva nulla."""
    if not files:
        raise HTTPException(status_code=400, detail="Nessun file caricato")
    if len(files) > MAX_PDF_FILES:
        raise HTTPException(status_code=400, detail=f"Puoi caricare al massimo {MAX_PDF_FILES} file alla volta")

    forced_producer = None
    if producer_id:
        if not ObjectId.is_valid(producer_id):
            raise HTTPException(status_code=400, detail="ID Cantina non valido")
        forced_producer = await db.producers.find_one({"_id": ObjectId(producer_id)})
        if not forced_producer:
            raise HTTPException(status_code=404, detail="Cantina non trovata")

    attributes, grapes, pairings = await _load_taxonomy(db)
    producers = await db.producers.find({}, {"company_name": 1, "slug": 1, "contacts": 1}).to_list(2000)
    producer_names = {p["_id"]: p.get("company_name", "") for p in producers}

    results = []
    catalog_cache: Dict[Any, List[Dict[str, Any]]] = {}
    seen_hashes: Dict[str, str] = {}
    for file in files:
        filename = file.filename or "documento.pdf"
        entry: Dict[str, Any] = {"filename": filename, "status": "error", "error": None, "wines": []}
        try:
            if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
                raise AIExtractionError("Formato non supportato: carica un PDF oppure un'immagine JPG, PNG o WebP")
            file_bytes = await file.read(MAX_PDF_BYTES + 1)
            if len(file_bytes) > MAX_PDF_BYTES:
                raise AIExtractionError("Il file supera i 15 MB")
            digest = hashlib.sha256(file_bytes).hexdigest()
            entry["file_hash"] = digest
            if digest in seen_hashes:
                entry.update({"status": "duplicate", "error": f"File identico a {seen_hashes[digest]}: analizzato una sola volta"})
                results.append(entry)
                continue
            seen_hashes[digest] = filename

            parsed = await run_in_threadpool(process_document, file_bytes, filename, attributes, grapes, pairings)

            if forced_producer:
                matched_id, score = forced_producer["_id"], 1.0
            else:
                matched_id, score = match_producer(parsed["producer"], producers)

            wines = []
            if matched_id and matched_id not in catalog_cache:
                catalog_cache[matched_id] = await _producer_wines(db, matched_id)
            for w in parsed["wines"]:
                w["producer_id"] = str(matched_id) if matched_id else ""
                w["name_key"] = name_key(w["name"])
                w["existing_product"] = find_duplicate(
                    w["name"], catalog_cache.get(matched_id, []), w.get("category", ""), w.get("is_riserva")
                ) if matched_id else None
                w["action"] = "update" if w["existing_product"] else "create"
                w["batch_duplicate_of"] = None
                w["source_file"] = filename
                wines.append(w)

            entry.update({
                "status": "ok",
                "file_type": parsed.get("file_type", "pdf"),
                "method": parsed["method"],
                "model": parsed.get("model"),
                "producer_hint": parsed["producer"],
                "producer_id": str(matched_id) if matched_id else "",
                "producer_name": producer_names.get(matched_id, "") if matched_id else "",
                "producer_match_score": round(score, 2),
                "warnings": parsed["warnings"],
                "wines": wines,
            })
        except AIExtractionError as e:
            entry["error"] = str(e)
        except Exception:
            logger.exception("Errore durante l'analisi di %s", filename)
            entry["error"] = "Errore imprevisto durante l'analisi del file"
        results.append(entry)

    _mark_batch_duplicates([w for r in results for w in r["wines"]])
    return {
        "files": results,
        "wines": [w for r in results for w in r["wines"]],  # compatibilita' con il vecchio frontend
        "count": sum(len(r["wines"]) for r in results),
        "ai": provider_status(),
    }


class DuplicateCheckPayload(BaseModel):
    producer_id: str
    name: str = Field(max_length=200)
    category: Optional[str] = ""
    is_riserva: Optional[bool] = None


@router.post("/import/check-duplicate")
async def check_duplicate(
    payload: DuplicateCheckPayload,
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    """Ricontrolla i doppioni quando nella revisione si cambia cantina o nome del vino."""
    if not ObjectId.is_valid(payload.producer_id):
        return {"existing_product": None, "name_key": name_key(payload.name)}
    candidates = await _producer_wines(db, ObjectId(payload.producer_id))
    return {
        "existing_product": find_duplicate(payload.name, candidates, payload.category or "", payload.is_riserva),
        "name_key": name_key(payload.name),
    }


class BatchWineRef(BaseModel):
    producer_id: Optional[str] = ""
    name: str = Field(default="", max_length=200)
    is_riserva: Optional[bool] = False
    source_file: Optional[str] = ""


class BatchCheckPayload(BaseModel):
    wines: List[BatchWineRef] = Field(max_length=MAX_BATCH_WINES)


@router.post("/import/check-batch")
async def check_batch(payload: BatchCheckPayload, current_admin: dict = Depends(get_current_admin)):
    """Per ogni vino dell'import indica se ripete un vino precedente dello stesso import (stessa cantina)."""
    wines = [w.model_dump() for w in payload.wines]
    for w in wines:
        w["batch_duplicate_of"] = None
    _mark_batch_duplicates(wines)
    result = []
    for i, w in enumerate(wines):
        dup = w.get("batch_duplicate_of")
        first_index = None
        if dup:
            first_index = next(j for j, o in enumerate(wines[:i])
                               if o["name"] == dup["name"] and o.get("source_file", "") == dup["source_file"])
        result.append({"index": i, "duplicate_of_index": first_index})
    return {"results": result}


class ImportedAttribute(BaseModel):
    name: str = Field(max_length=100)
    value: str = Field(max_length=1000)


class ImportedTastingNotes(BaseModel):
    visual: Optional[str] = ""
    olfactory: Optional[str] = ""
    taste: Optional[str] = ""


class ImportedWine(BaseModel):
    action: Literal["create", "update", "skip"] = "create"
    existing_id: Optional[str] = None
    producer_id: Optional[str] = None
    name: str = Field(default="", max_length=200)
    category: str = "VINO_ROSSO"
    denominazione: Optional[str] = ""
    vintage_year: Optional[Any] = None
    is_riserva: bool = False
    alcohol_degrees: Optional[Any] = None
    grape_varieties: List[str] = Field(default_factory=list, max_length=30)
    food_pairings: List[str] = Field(default_factory=list, max_length=30)
    serving_temperature: Optional[str] = Field(default="", max_length=60)
    indicative_price: Optional[str] = Field(default="", max_length=60)
    description: Optional[str] = Field(default="", max_length=6000)
    tasting_notes: ImportedTastingNotes = Field(default_factory=ImportedTastingNotes)
    custom_attributes: List[ImportedAttribute] = Field(default_factory=list, max_length=60)
    technical_sheet_pdf: Optional[str] = Field(default="", max_length=300)


class ConfirmBatchImportPayload(BaseModel):
    producer_id: Optional[str] = None  # cantina predefinita per i vini che non ne indicano una
    status: Literal["PUBLISHED", "DRAFT"] = "PUBLISHED"
    wines: List[ImportedWine] = Field(max_length=MAX_BATCH_WINES)


def _wine_fields(w: ImportedWine, status: str) -> Dict[str, Any]:
    """Valida i dati con lo stesso schema della creazione manuale e li prepara per il DB."""
    validated = ProductCreate(
        name=w.name.strip() or "Vino Senza Nome",
        category=w.category if w.category in {"VINO_ROSSO", "VINO_BIANCO", "ROSATO", "SPUMANTE", "PASSITO", "LIQUORE"} else "VINO_ROSSO",
        denominazione=(w.denominazione or "").strip(),
        vintage_year=w.vintage_year,
        is_riserva=w.is_riserva,
        alcohol_degrees=w.alcohol_degrees,
        grape_varieties=[g.strip()[:80] for g in w.grape_varieties if g and g.strip()],
        food_pairings=[p.strip()[:80] for p in w.food_pairings if p and p.strip()],
        serving_temperature=(w.serving_temperature or "").strip(),
        indicative_price=(w.indicative_price or "").strip(),
        description=(w.description or "").strip(),
        tasting_notes={
            "visual": (w.tasting_notes.visual or "").strip(),
            "olfactory": (w.tasting_notes.olfactory or "").strip(),
            "taste": (w.tasting_notes.taste or "").strip(),
        },
        photos=[],
        technical_sheet_pdf=(w.technical_sheet_pdf or "").strip() if (w.technical_sheet_pdf or "").startswith("/uploads/") else "",
        custom_attributes=[{"name": a.name.strip(), "value": a.value.strip()} for a in w.custom_attributes if a.name.strip() and a.value.strip()],
        status=status,
    )
    doc = validated.model_dump(exclude={"producer_id", "slug"})
    doc["name"] = clean_wine_title(validated.name)
    doc["denominazione"] = parse_denominazione_acronym(validated.denominazione) if validated.denominazione else ""
    return doc


def _merge_for_update(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Aggiornamento non distruttivo: i valori vuoti del PDF non cancellano i dati gia' presenti,
    gli attributi con lo stesso nome vengono aggiornati e gli altri conservati."""
    update: Dict[str, Any] = {}
    for key in ("name", "category", "denominazione", "vintage_year", "alcohol_degrees", "serving_temperature",
                "indicative_price", "description", "technical_sheet_pdf", "status"):
        if new.get(key) not in (None, ""):
            update[key] = new[key]
    if new.get("is_riserva"):
        update["is_riserva"] = True
    for key in ("grape_varieties", "food_pairings"):
        if new.get(key):
            update[key] = new[key]
    old_notes = existing.get("tasting_notes") or {}
    update["tasting_notes"] = {k: new["tasting_notes"].get(k) or old_notes.get(k, "") for k in ("visual", "olfactory", "taste")}
    merged = {a["name"].lower(): a for a in existing.get("custom_attributes") or [] if isinstance(a, dict) and a.get("name")}
    for a in new.get("custom_attributes") or []:
        merged[a["name"].lower()] = a
    update["custom_attributes"] = list(merged.values())
    return update


@router.post("/import/confirm-batch")
async def confirm_pdf_batch_import(
    payload: ConfirmBatchImportPayload,
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    producer_cache: Dict[str, bool] = {}

    async def producer_exists(pid: str) -> bool:
        if pid not in producer_cache:
            producer_cache[pid] = bool(ObjectId.is_valid(pid) and await db.producers.find_one({"_id": ObjectId(pid)}, {"_id": 1}))
        return producer_cache[pid]

    created, updated, skipped, errors = 0, 0, 0, []
    duplicates: List[str] = []
    created_in_batch: Dict[str, List[Dict[str, Any]]] = {}
    for idx, w in enumerate(payload.wines, 1):
        label = w.name or f"vino {idx}"
        if w.action == "skip":
            skipped += 1
            continue
        pid = w.producer_id or payload.producer_id or ""
        if not await producer_exists(pid):
            errors.append(f"{label}: seleziona una cantina valida")
            continue
        producer_oid = ObjectId(pid)
        try:
            doc = _wine_fields(w, payload.status)
        except Exception as e:
            errors.append(f"{label}: dati non validi ({str(e)[:120]})")
            continue

        existing = None
        if w.action == "update":
            if not w.existing_id or not ObjectId.is_valid(w.existing_id):
                errors.append(f"{label}: vino da aggiornare non indicato")
                continue
            existing = await db.products.find_one({"_id": ObjectId(w.existing_id)})
            if not existing:
                errors.append(f"{label}: il vino da aggiornare non esiste più")
                continue

        now = datetime.utcnow()
        if existing:
            update = _merge_for_update(existing, doc)
            update["producer_id"] = producer_oid
            if update.get("name") and update["name"] != existing.get("name"):
                update["slug"] = await generate_unique_product_slug(
                    db=db, name=update["name"], producer_id=producer_oid,
                    is_riserva=bool(update.get("is_riserva", existing.get("is_riserva"))), exclude_id=existing["_id"]
                )
            update["updated_at"] = now
            await db.products.update_one({"_id": existing["_id"]}, {"$set": update})
            updated += 1
        else:
            # rete di sicurezza: lo stesso vino inviato due volte nella stessa conferma viene creato una sola volta
            twin = next((c for c in created_in_batch.get(pid, [])
                         if bool(c["is_riserva"]) == bool(doc["is_riserva"]) and compare_names(c["name"], doc["name"])[0]), None)
            if twin:
                skipped += 1
                duplicates.append(f"{label}: doppione di \"{twin['name']}\" nello stesso import, non creato")
                continue
            created_in_batch.setdefault(pid, []).append({"name": doc["name"], "is_riserva": doc["is_riserva"]})
            doc["producer_id"] = producer_oid
            doc["slug"] = await generate_unique_product_slug(
                db=db, name=doc["name"], producer_id=producer_oid, is_riserva=bool(doc["is_riserva"])
            )
            doc["created_at"] = now
            doc["updated_at"] = now
            await db.products.insert_one(doc)
            created += 1

        await sync_grapes_with_master(doc["grape_varieties"], db)
        await sync_pairings_with_master(doc["food_pairings"], db)
        await sync_custom_attributes_with_master(doc["custom_attributes"], db)

    def plural(n, one, many):
        return f"{n} {one if n == 1 else many}"

    parts = []
    if created:
        parts.append(plural(created, "vino creato", "vini creati"))
    if updated:
        parts.append(plural(updated, "vino aggiornato", "vini aggiornati"))
    if skipped:
        parts.append(plural(skipped, "saltato", "saltati"))
    if errors:
        parts.append(plural(len(errors), "con errori", "con errori"))
    return {
        "message": ", ".join(parts) or "Nessun vino importato",
        "imported_count": created + updated,
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "duplicates": duplicates,
        "errors": errors,
    }
