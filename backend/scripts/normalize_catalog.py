"""Uniforma i dati gia' salvati dei vini, come avviene ormai a ogni salvataggio:

- prezzo indicativo:      "€14,00" -> "14,00 €", "35€ - 55€" -> "35,00 – 55,00 €"
- temperatura di servizio: "16 - 18°" -> "16-18°C"  (un testo senza numeri viene svuotato)
- vitigni:                "Montepulciano 55% Sangiovese 45%" in una voce -> due voci

Uso (dalla cartella backend/, con il virtualenv attivo):
    python scripts/normalize_catalog.py            # anteprima: mostra cosa cambierebbe, non modifica nulla
    python scripts/normalize_catalog.py --apply    # applica le modifiche
"""
import argparse
import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.db.mongodb import close_mongo_connection, connect_to_mongo, db  # noqa: E402
from app.services.insights import normalize_price_text, normalize_temperature_text, split_grape_list  # noqa: E402

FIELDS = {
    "indicative_price": normalize_price_text,
    "serving_temperature": normalize_temperature_text,
    "grape_varieties": split_grape_list,
}


async def normalize_catalog(database, apply: bool) -> int:
    changed = 0
    projection = {"name": 1, **{f: 1 for f in FIELDS}}
    async for product in database.products.find({}, projection):
        updates = {}
        for field, fix in FIELDS.items():
            old = product.get(field)
            if old in (None, "", []):
                continue
            new = fix(old)
            if new != old:
                updates[field] = new
        if not updates:
            continue
        changed += 1
        details = "; ".join(f"{f}: {product.get(f)!r} -> {v!r}" for f, v in updates.items())
        print(f"- {product.get('name')}: {details}")
        if apply:
            updates["updated_at"] = datetime.utcnow()
            await database.products.update_one({"_id": product["_id"]}, {"$set": updates})
    return changed


async def main(apply: bool):
    await connect_to_mongo()
    database = db.client[settings.DATABASE_NAME]
    try:
        print("Modalità:", "APPLICAZIONE" if apply else "ANTEPRIMA (nessuna modifica)")
        changed = await normalize_catalog(database, apply)
        if not changed:
            print("Tutti i vini sono già nel formato standard: nulla da fare.")
        elif apply:
            print(f"\n{changed} vini aggiornati.")
        else:
            print(f"\n{changed} vini da aggiornare. Riesegui con --apply per salvare le modifiche.")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uniforma prezzi, temperature e vitigni dei vini salvati")
    parser.add_argument("--apply", action="store_true", help="applica le modifiche (senza: solo anteprima)")
    asyncio.run(main(parser.parse_args().apply))
