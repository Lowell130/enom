"""Riscrive i prezzi indicativi gia' salvati nello stesso formato: "17,00 €", "35,00 – 55,00 €".

I prezzi con altre parole ("su richiesta", "15 € in cantina") restano come sono.

Uso (dalla cartella backend/, con il virtualenv attivo):
    python scripts/normalize_prices.py            # anteprima: mostra cosa cambierebbe, non modifica nulla
    python scripts/normalize_prices.py --apply    # applica le modifiche
"""
import argparse
import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.db.mongodb import close_mongo_connection, connect_to_mongo, db  # noqa: E402
from app.services.insights import normalize_price_text  # noqa: E402


async def normalize_catalog(database, apply: bool) -> int:
    changed = 0
    async for product in database.products.find({"indicative_price": {"$nin": [None, ""]}}, {"name": 1, "indicative_price": 1}):
        old = product.get("indicative_price")
        new = normalize_price_text(old)
        if new == old:
            continue
        changed += 1
        print(f"- {product.get('name')}: {old!r}  ->  {new!r}")
        if apply:
            await database.products.update_one(
                {"_id": product["_id"]},
                {"$set": {"indicative_price": new, "updated_at": datetime.utcnow()}},
            )
    return changed


async def main(apply: bool):
    await connect_to_mongo()
    database = db.client[settings.DATABASE_NAME]
    try:
        print("Modalità:", "APPLICAZIONE" if apply else "ANTEPRIMA (nessuna modifica)")
        changed = await normalize_catalog(database, apply)
        if not changed:
            print("Tutti i prezzi sono già nel formato standard: nulla da fare.")
        elif apply:
            print(f"\n{changed} prezzi aggiornati.")
        else:
            print(f"\n{changed} prezzi da aggiornare. Riesegui con --apply per salvare le modifiche.")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uniforma il formato dei prezzi indicativi")
    parser.add_argument("--apply", action="store_true", help="applica le modifiche (senza: solo anteprima)")
    asyncio.run(main(parser.parse_args().apply))
