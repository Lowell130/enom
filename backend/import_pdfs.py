import os
import sys
import argparse
import asyncio
from datetime import datetime
from bson import ObjectId

sys.path.insert(0, ".")
from app.db.mongodb import connect_to_mongo, close_mongo_connection, db
from app.core.config import settings
from app.services.pdf_importer import process_pdf_wine_file
from app.api.v1.products import (
    clean_wine_title,
    parse_denominazione_acronym,
    generate_unique_product_slug,
    sync_grapes_with_master,
    sync_pairings_with_master,
    sync_custom_attributes_with_master
)

async def import_pdfs_cli(pdf_dir="pdf_imports", producer_name=None):
    await connect_to_mongo()
    database = db.client[settings.DATABASE_NAME]

    print("==================================================")
    print("ENOTECA MOLISE - PDF BATCH WINE IMPORTER CLI")
    print("==================================================")

    # 1. Resolve Producer
    producers = await database.producers.find({}).to_list(100)
    if not producers:
        print("❌ Error: No producers found in database! Please seed producers first.")
        await close_mongo_connection()
        return

    target_producer = None
    if producer_name:
        for p in producers:
            if producer_name.lower() in p.get("company_name", "").lower():
                target_producer = p
                break
        if not target_producer:
            print(f"❌ Error: Producer containing '{producer_name}' not found!")
            await close_mongo_connection()
            return
    else:
        target_producer = producers[0]

    print(f"📌 Target Winery: {target_producer.get('company_name')} (ID: {target_producer['_id']})")

    # 2. Check PDF Directory
    abs_pdf_dir = os.path.abspath(pdf_dir)
    os.makedirs(abs_pdf_dir, exist_ok=True)
    
    pdf_files = [f for f in os.listdir(abs_pdf_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"⚠️ No PDF files found in '{abs_pdf_dir}'. Place PDF technical sheets inside this folder and run again.")
        await close_mongo_connection()
        return

    print(f"📂 Found {len(pdf_files)} PDF technical sheets in '{abs_pdf_dir}'")
    print("--------------------------------------------------")

    imported_count = 0
    for pdf_filename in pdf_files:
        pdf_path = os.path.join(abs_pdf_dir, pdf_filename)
        print(f"\n🔍 Processing '{pdf_filename}'...")
        
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        extracted = process_pdf_wine_file(pdf_bytes, pdf_filename)
        
        name = clean_wine_title(extracted.get("name", "Vino Senza Nome"))
        denom = parse_denominazione_acronym(extracted.get("denominazione", "DOC"))
        is_riserva = bool(extracted.get("is_riserva", False))
        
        slug = await generate_unique_product_slug(
            db=database,
            name=name,
            producer_id=target_producer["_id"],
            is_riserva=is_riserva
        )

        doc = {
            "producer_id": target_producer["_id"],
            "name": name,
            "slug": slug,
            "category": extracted.get("category", "VINO_ROSSO"),
            "denominazione": denom,
            "vintage_year": extracted.get("vintage_year"),
            "is_riserva": is_riserva,
            "alcohol_degrees": extracted.get("alcohol_degrees"),
            "grape_varieties": extracted.get("grape_varieties") or [],
            "description": extracted.get("description", ""),
            "tasting_notes": extracted.get("tasting_notes") or {},
            "food_pairings": extracted.get("food_pairings") or [],
            "serving_temperature": extracted.get("serving_temperature", "16-18°C"),
            "indicative_price": extracted.get("indicative_price", ""),
            "photos": ["https://images.unsplash.com/photo-1586370434639-0fe43b2d32e6?auto=format&fit=crop&w=600&q=80"],
            "technical_sheet_pdf": "",
            "custom_attributes": extracted.get("custom_attributes") or [],
            "status": "PUBLISHED",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        res = await database.products.insert_one(doc)
        
        # Auto-sync taxonomy
        await sync_grapes_with_master(doc["grape_varieties"], database)
        await sync_pairings_with_master(doc["food_pairings"], database)
        await sync_custom_attributes_with_master(doc["custom_attributes"], database)

        imported_count += 1
        print(f" ✅ Imported [{name}] ({doc['category']}, {doc['denominazione']}) -> ID: {res.inserted_id}")
        print(f"    Vitigni: {doc['grape_varieties']}")
        print(f"    Abbinamenti: {doc['food_pairings']}")

    print("\n==================================================")
    print(f"🎉 BATCH IMPORT COMPLETE: {imported_count} wines saved to MongoDB!")
    print("==================================================")

    await close_mongo_connection()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EnotecaMolise Batch PDF Importer")
    parser.add_argument("--dir", default="pdf_imports", help="Folder containing PDF files")
    parser.add_argument("--producer", default=None, help="Name of target winery")
    args = parser.parse_args()

    asyncio.run(import_pdfs_cli(args.dir, args.producer))
