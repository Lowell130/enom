import logging
import mimetypes
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.services.catalog import migrate_ascii_slugs
from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.api.v1 import auth, producers, products, product_io, pdf_import, inquiries, uploads, admin, attributes, grapes, pairings, reports
from app.core.security import get_password_hash, verify_password

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("enotecamolise")

mimetypes.add_type("image/webp", ".webp")

# Password pubblicate in versioni precedenti del codice: se ancora in uso vanno cambiate.
LEAKED_DEFAULT_PASSWORDS = ("AdminPass2026!", "CantinaPass2026!")


def _safe_verify(password: str, hashed: str) -> bool:
    try:
        return verify_password(password, hashed)
    except Exception:
        return False


async def ensure_indexes(db):
    indexes_to_create = [
        (db.products, "slug", {"unique": True}),
        (db.products, "producer_id", {}),
        (db.products, "status", {}),
        (db.products, "category", {}),
        (db.producers, "slug", {"unique": True}),
        (db.producers, "status", {}),
        (db.users, "email", {"unique": True}),
        (db.attributes, "name", {}),
        (db.inquiries, "producer_id", {}),
    ]
    for collection, field, kwargs in indexes_to_create:
        try:
            await collection.create_index(field, **kwargs)
        except Exception as e:
            err_str = str(e)
            if "IndexKeySpecsConflict" in err_str or "IndexOptionsConflict" in err_str:
                try:
                    await collection.drop_index(f"{field}_1")
                    await collection.create_index(field, **kwargs)
                except Exception as inner:
                    logger.warning("Impossibile ricreare l'indice %s.%s: %s", collection.name, field, inner)
            else:
                logger.warning("Impossibile creare l'indice %s.%s: %s", collection.name, field, e)


async def seed_master_attributes(db):
    # Questi campi sono proprieta' native del vino, non attributi personalizzati
    await db.attributes.delete_many({
        "name": {"$regex": "^(Denominazione|Grado Alcolico|Gradazione Alcolica|Temperatura di Servizio)$", "$options": "i"}
    })
    if await db.attributes.count_documents({}) == 0:
        default_attrs = [
            {"name": "Uvaggio", "unit_or_hint": "es. Tintilia 100%"},
            {"name": "Vinificazione", "unit_or_hint": "es. Acciaio / Barrique"},
            {"name": "Allevamento", "unit_or_hint": "es. Guyot / Cordone speronato"},
            {"name": "Vendemmia", "unit_or_hint": "es. Manuale prima decade di Ottobre"},
            {"name": "Allergeni", "unit_or_hint": "es. Contiene Solfiti"},
            {"name": "Formato", "unit_or_hint": "es. 75 cl"},
            {"name": "Zona di Produzione", "unit_or_hint": "es. Campobasso (CB), Molise"},
            {"name": "Affinamento", "unit_or_hint": "es. 12 mesi in botti di rovere"},
            {"name": "Altitudine Vigneto", "unit_or_hint": "es. 500 m s.l.m."}
        ]
        for a in default_attrs:
            a["created_at"] = datetime.utcnow()
        await db.attributes.insert_many(default_attrs)
        logger.info("Attributi master inizializzati.")


async def ensure_admin_user(db):
    admin_email = settings.ADMIN_EMAIL.lower()
    existing_admin = await db.users.find_one({"role": "ADMIN"})
    if not existing_admin:
        if not settings.ADMIN_PASSWORD or len(settings.ADMIN_PASSWORD) < 12:
            logger.warning(
                "Nessun amministratore presente. Imposta ADMIN_EMAIL e ADMIN_PASSWORD (min. 12 caratteri) "
                "nel file .env oppure esegui: python scripts/manage_users.py create-admin"
            )
            return
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": get_password_hash(settings.ADMIN_PASSWORD),
            "role": "ADMIN",
            "producer_id": None,
            "is_active": True,
            "created_at": datetime.utcnow()
        })
        logger.info("Amministratore creato: %s", admin_email)
        return

    # Avviso se un account usa ancora una password pubblicata nel vecchio codice sorgente
    async for u in db.users.find({"email": {"$in": ["admin@enotecamolise.it", "cantina@colletinto.it"]}}):
        if any(_safe_verify(pwd, u.get("password_hash", "")) for pwd in LEAKED_DEFAULT_PASSWORDS):
            logger.warning(
                "ATTENZIONE: l'account %s usa ancora una password pubblicata nel codice sorgente. "
                "Cambiala subito con: python scripts/manage_users.py set-password %s",
                u["email"], u["email"]
            )


async def seed_sample_data(db):
    """Dati di esempio, solo se SEED_SAMPLE_DATA=true e il DB e' vuoto. Nessun account viene creato."""
    if not settings.SEED_SAMPLE_DATA or await db.producers.count_documents({}) > 0:
        return
    logger.info("Inserimento dati di esempio (cantina e vini molisani)...")
    now = datetime.utcnow()
    inserted_p1 = await db.producers.insert_one({
        "company_name": "Cantina Il Colle Tinto",
        "slug": "cantina-il-colle-tinto",
        "logo_url": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=300&q=80",
        "cover_image_url": "https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=1600&q=80",
        "description": "Fondata nelle colline di Castropignano, Cantina Il Colle Tinto produce vini di eccellenza espressione autentica del territorio molisano.",
        "address": {"street": "Contrada Iannaricciola 27", "city": "Castropignano", "province": "CB", "zip_code": "86010", "geo_coordinates": {"lat": 41.6748, "lng": 14.5768}},
        "contacts": {
            "phone": "+39 0874 98765",
            "email_contact": "info@colletinto.it",
            "whatsapp_number": "39087498765",
            "website": "https://colletinto.it"
        },
        "status": "APPROVED",
        "created_at": now,
        "updated_at": now
    })
    producer_id = inserted_p1.inserted_id

    sample_products = [
        {
            "producer_id": producer_id,
            "name": "Biferno Rosso Riserva",
            "slug": "biferno-rosso-riserva",
            "category": "VINO_ROSSO",
            "denominazione": "DOC",
            "vintage_year": None,
            "is_riserva": True,
            "alcohol_degrees": 14.0,
            "grape_varieties": ["Montepulciano", "Aglianico"],
            "description": "Rosso di grande struttura affinato 24 mesi in botti di rovere. Profumi intensi di mora selvatica, vaniglia e spezie mediterranee.",
            "tasting_notes": {
                "visual": "Rosso rubino intenso con riflessi granati.",
                "olfactory": "Aroma complesso di frutti rossi maturi, liquirizia e tabacco.",
                "taste": "Caldo, morbido, tannini vellutati e lunghissima persistenza."
            },
            "food_pairings": ["Arrosti di agnello", "Caciocavallo Silano DOP", "Primi con ragù di cinghiale"],
            "serving_temperature": "18°C",
            "indicative_price": "18.00€ - 22.00€",
            "photos": ["https://images.unsplash.com/photo-1586370434639-0fe43b2d32e6?auto=format&fit=crop&w=600&q=80"],
            "technical_sheet_pdf": "",
            "custom_attributes": [
                {"name": "Uvaggio", "value": "Montepulciano 80%, Aglianico 20%"},
                {"name": "Vinificazione", "value": "Acciaio e affinamento 24 mesi in rovere"},
                {"name": "Allevamento", "value": "Guyot"},
                {"name": "Vendemmia", "value": "Manuale in cassette"},
                {"name": "Allergeni", "value": "Contiene Solfiti"},
                {"name": "Formato", "value": "75 cl"},
                {"name": "Zona di Produzione", "value": "Campobasso (CB), Molise"}
            ],
            "status": "PUBLISHED",
            "created_at": now,
            "updated_at": now
        },
        {
            "producer_id": producer_id,
            "name": "Tintilia del Molise Purezza",
            "slug": "tintilia-del-molise-purezza",
            "category": "VINO_ROSSO",
            "denominazione": "DOC",
            "vintage_year": None,
            "is_riserva": False,
            "alcohol_degrees": 14.5,
            "grape_varieties": ["Tintilia"],
            "description": "L'espressione pura del vitigno autoctono molisano per eccellenza. Vinificazione in acciaio per preservare l'aroma primario speziato.",
            "tasting_notes": {
                "visual": "Rosso rubino vivido.",
                "olfactory": "Note inconfondibili di pepe nero, prugna secca e macchia mediterranea.",
                "taste": "Gusto fresco, minerale, ben bilanciato da un tannino elegante."
            },
            "food_pairings": ["Pampanella molisana", "Formaggi stagionati", "Carni alla brace"],
            "serving_temperature": "16-18°C",
            "indicative_price": "24.00€",
            "photos": ["https://images.unsplash.com/photo-1558001373-7b9fcc986b26?auto=format&fit=crop&w=600&q=80"],
            "technical_sheet_pdf": "",
            "custom_attributes": [
                {"name": "Tipo Vino", "value": "Biologico"},
                {"name": "Uvaggio", "value": "Tintilia 100%"},
                {"name": "Vinificazione", "value": "Acciaio inox a temperatura controllata"},
                {"name": "Allevamento", "value": "Cordone speronato"},
                {"name": "Vendemmia", "value": "Manuale prima decade di Ottobre"},
                {"name": "Allergeni", "value": "Contiene Solfiti"},
                {"name": "Formato", "value": "75 cl"},
                {"name": "Zona di Produzione", "value": "Campobasso (CB), Molise"}
            ],
            "status": "PUBLISHED",
            "created_at": now,
            "updated_at": now
        }
    ]
    await db.products.insert_many(sample_products)
    logger.info("Dati di esempio inseriti.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    db = await get_database()
    await ensure_indexes(db)
    # indirizzi senza accenti (non fa nulla se sono gia' a posto)
    fixed_slugs = await migrate_ascii_slugs(db)
    if fixed_slugs:
        logging.getLogger("enotecamolise").info("Indirizzi senza accenti: %d aggiornati", fixed_slugs)
    await seed_master_attributes(db)
    await ensure_admin_user(db)
    await seed_sample_data(db)
    # Nota: la pulizia del catalogo (titoli/slug/annate) NON gira piu' a ogni avvio:
    # si esegue su richiesta con POST /api/v1/products/cleanup-slugs-and-titles (admin).
    yield
    await close_mongo_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"^chrome-extension://[a-p]{32}$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if request.url.path.startswith("/uploads/") and not request.url.path.lower().endswith(".pdf"):
        # I file caricati non possono eseguire script anche se aperti direttamente
        response.headers["Content-Security-Policy"] = "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; sandbox"
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response


os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(producers.router, prefix=f"{settings.API_V1_STR}/producers", tags=["Producers"])
# product_io va registrato prima di products: altrimenti GET /products/{identifier}
# intercetterebbe percorsi come /products/export/json
app.include_router(product_io.router, prefix=f"{settings.API_V1_STR}/products", tags=["Products Import/Export"])
app.include_router(pdf_import.router, prefix=f"{settings.API_V1_STR}/products", tags=["Products PDF Import (AI)"])
app.include_router(products.router, prefix=f"{settings.API_V1_STR}/products", tags=["Products"])
app.include_router(inquiries.router, prefix=f"{settings.API_V1_STR}/inquiries", tags=["Inquiries"])
app.include_router(uploads.router, prefix=f"{settings.API_V1_STR}/uploads", tags=["Uploads"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin"])
app.include_router(attributes.router, prefix=f"{settings.API_V1_STR}/attributes", tags=["Attributes"])
app.include_router(grapes.router, prefix=f"{settings.API_V1_STR}/grapes", tags=["Grapes"])
app.include_router(pairings.router, prefix=f"{settings.API_V1_STR}/pairings", tags=["Pairings"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports"])


@app.get("/")
async def root():
    return {"message": "EnotecaMolise API v1 Running", "docs": "/docs"}
