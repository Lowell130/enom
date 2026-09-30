"""Correzioni dati una tantum che in passato venivano eseguite a ogni avvio del server
(in main.py). Sono gia' state applicate al database: questo script resta solo per
riferimento o per riallineare un database ripristinato da un vecchio backup.

Uso (dalla cartella backend/):  python scripts/legacy_data_fixes.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.db.mongodb import connect_to_mongo, close_mongo_connection, db  # noqa: E402


async def main():
    await connect_to_mongo()
    database = db.client[settings.DATABASE_NAME]
    try:
        # Collega l'utente cantina@valbiferno.it alla sua cantina
        valbiferno = await database.producers.find_one({"$or": [
            {"company_name": {"$regex": "valbiferno", "$options": "i"}}, {"slug": "cantine-valbiferno"}
        ]})
        if valbiferno:
            await database.users.update_one(
                {"email": "cantina@valbiferno.it", "role": {"$ne": "ADMIN"}},
                {"$set": {"producer_id": valbiferno["_id"], "role": "PRODUCER"}}
            )

        # Coordinate esatte di Castropignano / Il Colle Tinto
        await database.producers.update_many(
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

        geo_updates = [
            ({"slug": "borgo-di-colloredo"}, {"lat": 41.9385, "lng": 15.0118}),
            ({"slug": "tenute-di-giulio"}, {"lat": 41.9421, "lng": 15.0154}),
            ({"slug": "cantina-herero"}, {"lat": 41.5658, "lng": 14.6582}),
            ({"slug": "campi-valerio"}, {"lat": 41.5251, "lng": 14.1788}),
            ({"slug": "cantina-san-zenone"}, {"lat": 41.9588, "lng": 14.7782}),
        ]
        for query, geo in geo_updates:
            await database.producers.update_many(query, {"$set": {"address.geo_coordinates": geo}})

        # Immagine di copertina predefinita
        await database.producers.update_many(
            {"$or": [
                {"cover_image_url": {"$regex": "photo-1506377247377", "$options": "i"}},
                {"cover_image_url": None},
                {"cover_image_url": ""}
            ]},
            {"$set": {"cover_image_url": "https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=1600&q=80"}}
        )
        print("Correzioni applicate.")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
