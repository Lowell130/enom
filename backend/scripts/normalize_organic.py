"""Uniforma nei vini gia' salvati il modo in cui e' indicato il biologico.

Standard del catalogo: attributo "Tipo Vino" = "Biologico" (come nei vini inseriti a mano).
Varianti ricondotte allo standard: "Certificazione: Biologico", "Tipo: Vino Biologico",
"Agricoltura: Biologica", "Biologico: Sì", "Tipo Vino: Vino fermo biologico" (-> "Vino fermo; Biologico")...

Uso (dalla cartella backend/, con il virtualenv attivo):
    python scripts/normalize_organic.py            # anteprima: mostra cosa cambierebbe, non modifica nulla
    python scripts/normalize_organic.py --apply    # applica le modifiche
"""
import argparse
import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.db.mongodb import close_mongo_connection, connect_to_mongo, db  # noqa: E402
from app.services.pdf_importer import ORGANIC_ATTRIBUTE_NAME, normalize_organic_attributes  # noqa: E402
from app.services.taxonomy import sync_custom_attributes_with_master  # noqa: E402


def _fmt(attrs):
    return ", ".join(f"{a.get('name')}={a.get('value')}" for a in attrs) or "(nessuno)"


async def normalize_catalog(database, apply: bool) -> int:
    master = [a["name"] for a in await database.attributes.find({}, {"name": 1}).to_list(1000) if a.get("name")]
    changed = 0
    async for product in database.products.find({}, {"name": 1, "custom_attributes": 1}):
        old = [a for a in (product.get("custom_attributes") or []) if isinstance(a, dict)]
        new, _ = normalize_organic_attributes(old, False, master)
        if new == old:
            continue
        changed += 1
        touched_old = [a for a in old if a not in new]
        touched_new = [a for a in new if a not in old]
        print(f"- {product.get('name')}: {_fmt(touched_old)}  ->  {_fmt(touched_new)}")
        if apply:
            await database.products.update_one(
                {"_id": product["_id"]},
                {"$set": {"custom_attributes": new, "updated_at": datetime.utcnow()}},
            )
            await sync_custom_attributes_with_master(new, database)
    return changed


async def main(apply: bool):
    await connect_to_mongo()
    database = db.client[settings.DATABASE_NAME]
    try:
        print("Modalità:", "APPLICAZIONE" if apply else "ANTEPRIMA (nessuna modifica)")
        changed = await normalize_catalog(database, apply)
        if not changed:
            print("Tutti i vini usano già lo standard: nulla da fare.")
        elif apply:
            print(f"\n{changed} vini aggiornati a '{ORGANIC_ATTRIBUTE_NAME} = Biologico'.")
        else:
            print(f"\n{changed} vini da aggiornare. Riesegui con --apply per salvare le modifiche.")

        # attributi master non piu' usati da nessun vino (es. "Certificazione", "Tipo"): da eliminare a mano
        unused = []
        for name in ("Certificazione", "Tipo", "Agricoltura", "Biologico"):
            master_attr = await database.attributes.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
            if master_attr and not await database.products.count_documents({"custom_attributes.name": master_attr["name"]}):
                unused.append(master_attr["name"])
        if unused and apply:
            print("Attributi ora inutilizzati, eliminabili da Dashboard > Attributi:", ", ".join(unused))
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uniforma l'indicazione del biologico nei vini")
    parser.add_argument("--apply", action="store_true", help="applica le modifiche (senza: solo anteprima)")
    asyncio.run(main(parser.parse_args().apply))
