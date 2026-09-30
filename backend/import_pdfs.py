"""Importazione da riga di comando delle schede vino in PDF o immagine (stesso motore della dashboard).

Uso (dalla cartella backend/):
    python import_pdfs.py --dir pdf_imports --producer "Catabbo"          # vini salvati come BOZZA
    python import_pdfs.py --dir pdf_imports --producer "Catabbo" --publish

Senza --producer la cantina viene riconosciuta automaticamente dal documento.
I vini gia' presenti (stesso nome, stessa cantina) vengono saltati.
Si consiglia comunque l'import dalla dashboard, che permette di rivedere i dati prima del salvataggio.
"""
import argparse
import asyncio
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings  # noqa: E402
from app.db.mongodb import close_mongo_connection, connect_to_mongo, db  # noqa: E402
from app.services.ai_extractor import AIExtractionError, provider_status  # noqa: E402
from app.services.catalog import generate_unique_product_slug  # noqa: E402
from app.services.pdf_importer import CANONICAL_PAIRINGS, SUPPORTED_EXTENSIONS, match_producer, process_document  # noqa: E402
from app.services.taxonomy import (  # noqa: E402
    sync_custom_attributes_with_master,
    sync_grapes_with_master,
    sync_pairings_with_master,
)


async def import_pdfs_cli(pdf_dir: str, producer_name: str = None, publish: bool = False):
    await connect_to_mongo()
    database = db.client[settings.DATABASE_NAME]
    try:
        status = provider_status()
        print("IA:", f"{status['provider']} ({status['model']})" if status["configured"] else "non configurata (solo PDF testuali)")

        producers = await database.producers.find({}).to_list(2000)
        forced = None
        if producer_name:
            forced = next((p for p in producers if producer_name.lower() in p.get("company_name", "").lower()), None)
            if not forced:
                print(f"Cantina contenente '{producer_name}' non trovata.")
                return

        attributes = [a["name"] for a in await database.attributes.find({}).to_list(500) if a.get("name")]
        grapes = [g["name"] for g in await database.grapes.find({}).to_list(500) if g.get("name")]
        pairings = [p["name"] for p in await database.pairings.find({}).to_list(200) if p.get("name")] or CANONICAL_PAIRINGS

        abs_dir = os.path.abspath(pdf_dir)
        os.makedirs(abs_dir, exist_ok=True)
        files = sorted(f for f in os.listdir(abs_dir) if f.lower().endswith(SUPPORTED_EXTENSIONS))
        if not files:
            print(f"Nessun PDF o immagine in '{abs_dir}'.")
            return

        created = 0
        for filename in files:
            print(f"\n{filename}")
            with open(os.path.join(abs_dir, filename), "rb") as f:
                pdf_bytes = f.read()
            try:
                parsed = process_document(pdf_bytes, filename, attributes, grapes, pairings)
            except AIExtractionError as e:
                print(f"  ERRORE: {e}")
                continue

            producer_id = forced["_id"] if forced else match_producer(parsed["producer"], producers)[0]
            if not producer_id:
                print(f"  Cantina non riconosciuta ('{parsed['producer'].get('name')}'): usa --producer")
                continue

            for w in parsed["wines"]:
                dup = await database.products.find_one({
                    "producer_id": producer_id, "name": {"$regex": f"^{re.escape(w['name'])}$", "$options": "i"}
                })
                if dup:
                    print(f"  = {w['name']}: già presente, saltato")
                    continue
                doc = {k: w[k] for k in ("name", "category", "denominazione", "vintage_year", "is_riserva", "alcohol_degrees",
                                         "grape_varieties", "food_pairings", "serving_temperature", "indicative_price",
                                         "description", "tasting_notes", "custom_attributes")}
                now = datetime.utcnow()
                doc.update({
                    "producer_id": producer_id,
                    "slug": await generate_unique_product_slug(database, w["name"], producer_id, w["is_riserva"]),
                    "photos": [],
                    "technical_sheet_pdf": "",
                    "status": "PUBLISHED" if publish else "DRAFT",
                    "created_at": now,
                    "updated_at": now,
                })
                await database.products.insert_one(doc)
                await sync_grapes_with_master(doc["grape_varieties"], database)
                await sync_pairings_with_master(doc["food_pairings"], database)
                await sync_custom_attributes_with_master(doc["custom_attributes"], database)
                created += 1
                print(f"  + {w['name']} ({len(doc['custom_attributes'])} attributi)"
                      + (f" — mancano: {', '.join(w['missing_fields'])}" if w["missing_fields"] else ""))

        print(f"\nImportazione completata: {created} vini creati ({'pubblicati' if publish else 'come bozza'}).")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importa schede vino da PDF")
    parser.add_argument("--dir", default="pdf_imports", help="Cartella con i PDF")
    parser.add_argument("--producer", default=None, help="Parte del nome della cantina (facoltativo)")
    parser.add_argument("--publish", action="store_true", help="Pubblica subito i vini invece di salvarli come bozza")
    args = parser.parse_args()
    asyncio.run(import_pdfs_cli(args.dir, args.producer, args.publish))
