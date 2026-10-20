"""Registro delle attivita' delle cantine: lettura per l'amministratore."""
from datetime import datetime
from typing import Any, Dict, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.auth import get_current_admin
from app.db.mongodb import get_database
from app.services.activity import ACTIONS

router = APIRouter()

GROUPS = {"account": "Accessi e account", "producer": "Profilo cantina", "product": "Vini", "event": "Eventi"}


def _out(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "created_at": doc.get("created_at"),
        "action": doc.get("action", ""),
        "action_label": ACTIONS.get(doc.get("action", ""), doc.get("action", "")),
        "group": (doc.get("action", "").split(".") or [""])[0],
        "user_email": doc.get("user_email", ""),
        "producer_id": doc.get("producer_id"),
        "producer_name": doc.get("producer_name", ""),
        "target_type": doc.get("target_type"),
        "target_id": doc.get("target_id"),
        "target_name": doc.get("target_name", ""),
        "changes": doc.get("changes") or [],
        "details": doc.get("details", ""),
    }


@router.get("")
async def list_activity(
    producer_id: Optional[str] = None,
    group: Optional[str] = None,
    before: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=200),
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database),
):
    query: Dict[str, Any] = {}
    if producer_id:
        if not ObjectId.is_valid(producer_id):
            raise HTTPException(status_code=400, detail="ID cantina non valido")
        query["producer_id"] = producer_id
    if group:
        if group not in GROUPS:
            raise HTTPException(status_code=400, detail="Gruppo non valido")
        query["action"] = {"$in": [k for k in ACTIONS if k.startswith(group + ".")]}
    if before:
        query["created_at"] = {"$lt": before.replace(tzinfo=None)}
    docs = await db.activity_log.find(query).sort("created_at", -1).limit(limit + 1).to_list(limit + 1)
    has_more = len(docs) > limit
    items = [_out(d) for d in docs[:limit]]
    # targhe attuali per i link (un vino o un evento puo' essere stato rinominato o eliminato)
    product_ids = [ObjectId(i["target_id"]) for i in items if i["target_type"] == "product" and ObjectId.is_valid(i["target_id"] or "")]
    event_ids = [ObjectId(i["target_id"]) for i in items if i["target_type"] == "event" and ObjectId.is_valid(i["target_id"] or "")]
    producer_ids = {ObjectId(i["producer_id"]) for i in items if ObjectId.is_valid(i["producer_id"] or "")}
    products = {str(p["_id"]): p.get("slug") for p in await db.products.find({"_id": {"$in": product_ids}}, {"slug": 1}).to_list(500)}
    events = {str(e["_id"]): e.get("slug") for e in await db.events.find({"_id": {"$in": event_ids}}, {"slug": 1}).to_list(500)}
    producers = {str(p["_id"]): p.get("slug") for p in await db.producers.find({"_id": {"$in": list(producer_ids)}}, {"slug": 1}).to_list(500)}
    for i in items:
        i["producer_slug"] = producers.get(i["producer_id"] or "")
        i["target_slug"] = (products if i["target_type"] == "product" else events if i["target_type"] == "event" else producers).get(i["target_id"] or "")
    return {"items": items, "has_more": has_more, "groups": GROUPS}
