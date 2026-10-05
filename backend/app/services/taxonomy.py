"""Sincronizzazione delle tassonomie condivise (attributi, vitigni, abbinamenti)
con i valori inseriti nelle schede dei vini."""
import re
from datetime import datetime


async def sync_custom_attributes_with_master(custom_attributes: list, db, attr_cache: dict = None):
    if not custom_attributes:
        return
    for attr in custom_attributes:
        name = attr.get("name", "").strip() if isinstance(attr, dict) else (getattr(attr, "name", "") or "").strip()
        val = attr.get("value", "").strip() if isinstance(attr, dict) else (getattr(attr, "value", "") or "").strip()
        if not name or not val:
            continue
        name_lower = name.lower()
        existing = None
        if attr_cache is not None:
            existing = attr_cache.get(name_lower)
        else:
            existing = await db.attributes.find_one({"name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}})
        
        if existing:
            current_suggs = existing.get("suggested_values", [])
            if not any(s.strip().lower() == val.strip().lower() for s in current_suggs):
                current_suggs.append(val.strip())
                existing["suggested_values"] = current_suggs
                await db.attributes.update_one(
                    {"_id": existing["_id"]},
                    {"$addToSet": {"suggested_values": val.strip()}}
                )
        else:
            new_doc = {
                "name": name,
                "unit_or_hint": "",
                "suggested_values": [val.strip()],
                "created_at": datetime.utcnow()
            }
            res = await db.attributes.insert_one(new_doc)
            new_doc["_id"] = res.inserted_id
            if attr_cache is not None:
                attr_cache[name_lower] = new_doc

async def sync_grapes_with_master(grape_varieties: list, db, grapes_cache: dict = None):
    if not grape_varieties:
        return
    for item in grape_varieties:
        if not item or not isinstance(item, str):
            continue
        clean_name = re.sub(r'\s+', ' ', re.sub(r'\d+\s*%?', '', item)).strip(' -,;')
        if not clean_name:
            continue
        clean_lower = clean_name.lower()
        existing = None
        if grapes_cache is not None:
            existing = grapes_cache.get(clean_lower)
        else:
            existing = await db.grapes.find_one({"name": {"$regex": f"^{re.escape(clean_name)}$", "$options": "i"}})
        if not existing:
            new_doc = {
                "name": clean_name,
                "category": "AUTOCTONO",
                "created_at": datetime.utcnow()
            }
            res = await db.grapes.insert_one(new_doc)
            new_doc["_id"] = res.inserted_id
            if grapes_cache is not None:
                grapes_cache[clean_lower] = new_doc

async def sync_pairings_with_master(food_pairings: list, db, pairings_cache: dict = None):
    if not food_pairings:
        return
    for item in food_pairings:
        if not item or not isinstance(item, str):
            continue
        clean_name = item.strip()
        if not clean_name:
            continue
        clean_lower = clean_name.lower()
        existing = None
        if pairings_cache is not None:
            existing = pairings_cache.get(clean_lower)
        else:
            existing = await db.pairings.find_one({"name": {"$regex": f"^{re.escape(clean_name)}$", "$options": "i"}})
        if not existing:
            new_doc = {
                "name": clean_name,
                "category": "GENERALE",
                "created_at": datetime.utcnow()
            }
            res = await db.pairings.insert_one(new_doc)
            new_doc["_id"] = res.inserted_id
            if pairings_cache is not None:
                pairings_cache[clean_lower] = new_doc


# ---------------------------------------------------------------------------
# Rinomina di una voce delle tassonomie: il nuovo nome viene applicato anche ai vini
# ---------------------------------------------------------------------------

def name_regex(name: str) -> dict:
    """Filtro MongoDB per un nome uguale, senza badare alle maiuscole."""
    return {"$regex": f"^{re.escape(name.strip())}$", "$options": "i"}


async def find_same_name(collection, name: str, exclude_id=None):
    """Voce con lo stesso nome (maiuscole ignorate), esclusa quella indicata."""
    query = {"name": name_regex(name)}
    if exclude_id is not None:
        query["_id"] = {"$ne": exclude_id}
    return await collection.find_one(query, {"_id": 1, "name": 1})


def _rename_pairings(values: list, old: str, new: str) -> list:
    old_l, out = old.strip().lower(), []
    for v in values or []:
        item = new if isinstance(v, str) and v.strip().lower() == old_l else v
        if not any(isinstance(o, str) and isinstance(item, str) and o.lower() == item.lower() for o in out):
            out.append(item)
    return out


def _rename_grapes(values: list, old: str, new: str) -> list:
    """"Tintilia 85%" -> "<nuovo> 85%": cambia il nome del vitigno e conserva la percentuale."""
    pattern = re.compile(rf"^\s*{re.escape(old.strip())}(?=\s*(?:\d|$|[(,;\-–]))", re.I)
    return [pattern.sub(new, v, count=1).strip() if isinstance(v, str) else v for v in values or []]


def _rename_attributes(values: list, old: str, new: str) -> list:
    """Rinomina il campo; se il vino aveva gia' un campo con il nuovo nome, i valori vengono uniti."""
    old_l, new_l = old.strip().lower(), new.strip().lower()
    out = []
    for attr in values or []:
        if not isinstance(attr, dict):
            out.append(attr)
            continue
        name = str(attr.get("name", "")).strip()
        if name.lower() == old_l:
            attr = {**attr, "name": new}
        target = next((a for a in out if isinstance(a, dict) and str(a.get("name", "")).strip().lower() == new_l), None) \
            if str(attr.get("name", "")).strip().lower() == new_l else None
        if target is not None:
            value = str(attr.get("value", "")).strip()
            if value and value.lower() not in str(target.get("value", "")).lower():
                target["value"] = f"{target.get('value', '')}; {value}".strip("; ")
            continue
        out.append(attr)
    return out


RENAMERS = {
    "food_pairings": (_rename_pairings, lambda old: {"food_pairings": name_regex(old)}),
    "grape_varieties": (
        _rename_grapes,
        lambda old: {"grape_varieties": {"$regex": rf"^\s*{re.escape(old.strip())}(?=\s*(\d|$|[(,;\-–]))", "$options": "i"}},
    ),
    "custom_attributes": (_rename_attributes, lambda old: {"custom_attributes.name": name_regex(old)}),
}


async def rename_in_products(db, field: str, old: str, new: str) -> int:
    """Applica la rinomina a tutti i vini che usano il vecchio nome; restituisce quanti vini sono cambiati."""
    if not old or not new or old.strip() == new.strip():
        return 0
    rename, query = RENAMERS[field]
    changed = 0
    async for product in db.products.find(query(old), {field: 1}):
        updated = rename(product.get(field) or [], old, new)
        if updated != product.get(field):
            await db.products.update_one(
                {"_id": product["_id"]}, {"$set": {field: updated, "updated_at": datetime.utcnow()}}
            )
            changed += 1
    return changed
