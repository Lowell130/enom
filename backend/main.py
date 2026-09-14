from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.api.v1 import auth, producers, products, inquiries, uploads, admin, attributes, grapes, pairings, reports
from app.core.security import get_password_hash
from datetime import datetime
import os
import re
import mimetypes

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/webp", "webp")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(producers.router, prefix=f"{settings.API_V1_STR}/producers", tags=["Producers"])
app.include_router(products.router, prefix=f"{settings.API_V1_STR}/products", tags=["Products"])
app.include_router(inquiries.router, prefix=f"{settings.API_V1_STR}/inquiries", tags=["Inquiries"])
app.include_router(uploads.router, prefix=f"{settings.API_V1_STR}/uploads", tags=["Uploads"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin"])
app.include_router(attributes.router, prefix=f"{settings.API_V1_STR}/attributes", tags=["Attributes"])
app.include_router(grapes.router, prefix=f"{settings.API_V1_STR}/grapes", tags=["Grapes"])
app.include_router(pairings.router, prefix=f"{settings.API_V1_STR}/pairings", tags=["Pairings"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports"])

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    db = await get_database()
    
    # 1. Clean up & Seed Master Attributes
    await db.attributes.delete_many({
        "name": {"$regex": "^(Denominazione|Grado Alcolico|Gradazione Alcolica|Temperatura di Servizio)$", "$options": "i"}
    })
    
    attr_count = await db.attributes.count_documents({})
    if attr_count == 0:
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
        print("Master attributes seeded successfully.")

    # 2. Seed Default Admin User if not present
    admin_email = "admin@enotecamolise.it"
    admin_user = await db.users.find_one({"email": admin_email})
    if not admin_user:
        hashed_pwd = get_password_hash("AdminPass2026!")
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hashed_pwd,
            "role": "ADMIN",
            "producer_id": None,
            "is_active": True,
            "created_at": datetime.utcnow()
        })
        print(f"Default Admin created: {admin_email} / AdminPass2026!")

    # Update Castropignano / Il Colle Tinto exact geo_coordinates in DB
    await db.producers.update_many(
        {"$or": [
            {"company_name": {"$regex": "colle tinto", "$options": "i"}},
            {"address.city": {"$regex": "castropignano", "$options": "i"}}
        ]},
        {"$set": {
            "address.geo_coordinates": {"lat": 41.6748, "lng": 14.5768},
            "address.zip_code": "86010",
            "address.city": "Castropignano",
            "address.province": "CB"
        }}
    )

    # 3. Seed Initial Sample Molise Producers & Wines if DB is empty
    producer_count = await db.producers.count_documents({})
    if producer_count == 0:
        print("Seeding initial Molise producers and products...")
        sample_producers = [
            {
                "company_name": "Cantine Valbiferno",
                "slug": "cantine-valbiferno",
                "logo_url": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=300&q=80",
                "cover_image_url": "https://images.unsplash.com/photo-1506377247377-2a5b3b417ebb?auto=format&fit=crop&w=1200&q=80",
                "description": "Fondata nelle colline incontaminate del Biferno, la nostra cantina coltiva vitigni autoctoni molisani con passione artigianale e rispetto della tradizione.",
                "address": {"street": "Contrada Colle di Salcito 14", "city": "Campobasso", "province": "CB", "zip_code": "86100"},
                "contacts": {
                    "phone": "+39 0874 123456",
                    "email_contact": "info@valbiferno.it",
                    "whatsapp_number": "390874123456",
                    "website": "https://valbiferno.it",
                    "instagram": "@cantinevalbiferno",
                    "facebook": "CantineValbiferno"
                },
                "status": "APPROVED",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "company_name": "Tenuta Tintilia del Matese",
                "slug": "tenuta-tintilia-del-matese",
                "logo_url": "https://images.unsplash.com/photo-1528823872057-9c018a7a70b3?auto=format&fit=crop&w=300&q=80",
                "cover_image_url": "https://images.unsplash.com/photo-1516594915697-87eb3b1c14ea?auto=format&fit=crop&w=1200&q=80",
                "description": "Specializzati esclusivamente nel vitigno regale autoctono Tintilia. Vigneti ad alta quota sui pendii del massiccio del Matese.",
                "address": {"street": "Via Matese 45", "city": "Isernia", "province": "IS", "zip_code": "86170"},
                "contacts": {
                    "phone": "+39 0865 987654",
                    "email_contact": "contatti@tintiliamatese.it",
                    "whatsapp_number": "390865987654",
                    "website": "https://tintiliamatese.it",
                    "instagram": "@tintilia_matese",
                    "facebook": "TenutaTintiliaMatese"
                },
                "status": "APPROVED",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        inserted_p1 = await db.producers.insert_one(sample_producers[0])
        inserted_p2 = await db.producers.insert_one(sample_producers[1])
        
        p1_pwd = get_password_hash("CantinaPass2026!")
        await db.users.insert_one({
            "email": "cantina@valbiferno.it",
            "password_hash": p1_pwd,
            "role": "PRODUCER",
            "producer_id": inserted_p1.inserted_id,
            "is_active": True,
            "created_at": datetime.utcnow()
        })
        
        sample_products = [
            {
                "producer_id": inserted_p1.inserted_id,
                "name": "Biferno Rosso Riserva",
                "slug": "biferno-rosso-riserva",
                "category": "VINO_ROSSO",
                "denominazione": "DOC",
                "vintage_year": None,
                "alcohol_degrees": 14.0,
                "grape_varieties": ["Montepulciano 80%", "Aglianico 20%"],
                "description": "Rosso di grande struttura affinato 24 mesi in botti di rovere. Profumi intensi di mora selvatica, vaniglia e spezie mediterranee.",
                "tasting_notes": {
                    "visual": "Rosso rubino intenso con riflessi granati.",
                    "olfactory": "Aroma complesso di frutti rossi maturi, liquirizia e tabacco.",
                    "taste": "Warm, morbido, tannini vellutati e lunghissima persistenza."
                },
                "food_pairings": ["Arrosti di agnello", "Caciocavallo Silano DOP", "Primi con ragù di cinghiale"],
                "serving_temperature": "18°C",
                "indicative_price": "18.00€ - 22.00€",
                "photos": ["https://images.unsplash.com/photo-1586370434639-0fe43b2d32e6?auto=format&fit=crop&w=600&q=80"],
                "custom_attributes": [
                    {"name": "Denominazione", "value": "DOC"},
                    {"name": "Uvaggio", "value": "Montepulciano 80%, Aglianico 20%"},
                    {"name": "Grado Alcolico", "value": "14.0% vol"},
                    {"name": "Vinificazione", "value": "Acciaio e affinamento 24 mesi in rovere"},
                    {"name": "Allevamento", "value": "Guyot"},
                    {"name": "Vendemmia", "value": "Manuale in cassette"},
                    {"name": "Temperatura di Servizio", "value": "18° C"},
                    {"name": "Allergeni", "value": "Contiene Solfiti"},
                    {"name": "Formato", "value": "75 cl"},
                    {"name": "Zona di Produzione", "value": "Campobasso (CB), Molise"}
                ],
                "status": "PUBLISHED",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "producer_id": inserted_p2.inserted_id,
                "name": "Tintilia del Molise Purezza",
                "slug": "tintilia-del-molise-purezza",
                "category": "VINO_ROSSO",
                "denominazione": "DOC",
                "vintage_year": None,
                "alcohol_degrees": 14.5,
                "grape_varieties": ["Tintilia 100%"],
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
                "custom_attributes": [
                    {"name": "Denominazione", "value": "DOC"},
                    {"name": "Uvaggio", "value": "Tintilia 100%"},
                    {"name": "Grado Alcolico", "value": "14.5% vol"},
                    {"name": "Vinificazione", "value": "Acciaio inox a temperatura controllata"},
                    {"name": "Allevamento", "value": "Cordone speronato"},
                    {"name": "Vendemmia", "value": "Manuale prima decade di Ottobre"},
                    {"name": "Temperatura di Servizio", "value": "16° - 18° C"},
                    {"name": "Allergeni", "value": "Contiene Solfiti"},
                    {"name": "Formato", "value": "75 cl"},
                    {"name": "Zona di Produzione", "value": "Isernia (IS), Molise"}
                ],
                "status": "PUBLISHED",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        await db.products.insert_many(sample_products)
        print("Sample data seeded successfully!")

    # 4. Automatic Catalog Migration: Clean up titles, slugs and ensure Senza Annata (S.A.)
    migrated_count = await products.run_products_cleanup_migration(db)
    if migrated_count > 0:
        print(f"Catalog migration: {migrated_count} existing wines updated to Senza Annata (S.A.) and clean slugs.")

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "EnotecaMolise API v1 Running", "docs": "/docs"}
