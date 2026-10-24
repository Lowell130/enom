"""Contatti con le cantine (solo amministratore): chi e' stato contattato, quando, con quale canale
e cosa ha risposto. Vale sia per le cantine gia' presenti nel sito sia per quelle trovate altrove
(«fuori dal sito») e non ancora iscritte. Nessun invio automatico: e' un promemoria per l'amministratore."""
from datetime import date, datetime, time, timedelta
from typing import List, Literal, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.api.v1.auth import get_current_admin
from app.api.v1.producers import _account_map, _name_key
from app.db.mongodb import get_database

router = APIRouter()

CHANNELS = {
    "WHATSAPP": "WhatsApp",
    "EMAIL": "Email",
    "FACEBOOK": "Facebook",
    "INSTAGRAM": "Instagram",
    "TELEFONO": "Telefono",
    "DI_PERSONA": "Di persona",
    "ALTRO": "Altro",
}
Channel = Literal["WHATSAPP", "EMAIL", "FACEBOOK", "INSTAGRAM", "TELEFONO", "DI_PERSONA", "ALTRO"]

PROSPECT_STATUSES = {
    "DA_CONTATTARE": "Da contattare",
    "CONTATTATA": "Contattata",
    "INTERESSATA": "Interessata",
    "NON_INTERESSATA": "Non interessata",
}
ProspectStatus = Literal["DA_CONTATTARE", "CONTATTATA", "INTERESSATA", "NON_INTERESSATA"]

# dopo quanti giorni senza risposta una cantina va risentita
REMIND_AFTER_DAYS = 7


class LogIn(BaseModel):
    target_type: Literal["producer", "prospect"]
    target_id: str
    channel: Channel = "WHATSAPP"
    contacted_on: Optional[date] = None      # vuoto = oggi
    note: Optional[str] = Field(default="", max_length=2000)

    @field_validator("contacted_on")
    @classmethod
    def not_in_future(cls, v):
        if v and v > date.today() + timedelta(days=1):
            raise ValueError("La data del contatto non può essere nel futuro")
        return v


class ProspectIn(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    city: Optional[str] = Field(default="", max_length=100)
    province: Optional[str] = Field(default="", max_length=4)
    email: Optional[str] = Field(default="", max_length=200)
    phone: Optional[str] = Field(default="", max_length=40)
    whatsapp: Optional[str] = Field(default="", max_length=40)
    website: Optional[str] = Field(default="", max_length=300)
    facebook: Optional[str] = Field(default="", max_length=300)
    instagram: Optional[str] = Field(default="", max_length=300)
    notes: Optional[str] = Field(default="", max_length=3000)
    status: ProspectStatus = "DA_CONTATTARE"

    @field_validator("name", "city", "province", "email", "phone", "whatsapp", "website", "facebook", "instagram", "notes")
    @classmethod
    def strip(cls, v):
        return (v or "").strip()


class LinkIn(BaseModel):
    producer_id: str


def _oid(value: str, what: str = "ID") -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=400, detail=f"{what} non valido")
    return ObjectId(value)


def _log_out(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "channel": doc.get("channel", "ALTRO"),
        "channel_label": CHANNELS.get(doc.get("channel"), "Altro"),
        "contacted_at": doc.get("contacted_at"),
        "note": doc.get("note", ""),
        "auto": False,
    }


def _missing(p: dict, wine_count: int) -> List[str]:
    """Cosa manca al profilo: gli stessi passi di «Completa la tua cantina» nella Panoramica della cantina."""
    address = p.get("address") or {}
    contacts = p.get("contacts") or {}
    geo = address.get("geo_coordinates") or {}
    checks = [
        ("comune", bool(address.get("city"))),
        ("posizione sulla mappa", bool(geo.get("lat") and geo.get("lng"))),
        ("logo", bool(p.get("logo_url"))),
        ("foto di copertina", bool(p.get("cover_image_url"))),
        ("storia", len(p.get("description") or "") >= 150),
        ("telefono o sito", bool(contacts.get("phone") or contacts.get("website"))),
        ("vini", wine_count > 0),
    ]
    return [label for label, ok in checks if not ok]


def _prospect_fields(doc: dict) -> dict:
    return {k: doc.get(k, "") for k in ("city", "province", "email", "phone", "whatsapp", "website", "facebook", "instagram", "notes")}


@router.get("")
async def list_outreach(current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    """Tutte le cantine (del sito e fuori dal sito) con lo storico dei contatti."""
    logs: dict = {}
    async for doc in db.outreach_log.find({}).sort("contacted_at", -1):
        key = str(doc.get("producer_id") or doc.get("prospect_id"))
        logs.setdefault(key, []).append(_log_out(doc))

    accounts = await _account_map(db)
    wines: dict = {}
    async for c in db.products.aggregate([{"$group": {"_id": "$producer_id", "count": {"$sum": 1}}}]):
        if c.get("_id"):
            wines[str(c["_id"])] = wines.get(str(c["_id"]), 0) + c.get("count", 0)

    now = datetime.utcnow()
    remind_before = now - timedelta(days=REMIND_AFTER_DAYS)
    items: List[dict] = []
    producer_keys = {}

    async for p in db.producers.find({}):
        pid = str(p["_id"])
        acc = accounts.get(p["_id"], {"status": "none"})
        history = list(logs.get(pid, []))
        # l'invito mandato dal sito conta come contatto (ultimo invio)
        if acc.get("invited_at"):
            history.append({"id": f"invito-{pid}", "channel": "EMAIL", "channel_label": "Email di invito dal sito",
                            "contacted_at": acc["invited_at"], "note": f"Link di attivazione a {acc.get('email', '')}",
                            "auto": True})
            history.sort(key=lambda h: h["contacted_at"] or now, reverse=True)
        contacts = p.get("contacts") or {}
        address = p.get("address") or {}
        producer_keys[_name_key(p.get("company_name", ""))] = {"id": pid, "name": p.get("company_name", "")}
        items.append({
            "kind": "producer",
            "id": pid,
            "name": p.get("company_name", ""),
            "slug": p.get("slug", ""),
            "city": address.get("city", ""),
            "province": address.get("province", ""),
            "producer_status": p.get("status", "APPROVED"),
            "account": acc.get("status", "none"),
            "account_email": acc.get("email", ""),
            "self_registered": bool(acc.get("self_registered")),
            "wine_count": wines.get(pid, 0),
            "missing": _missing(p, wines.get(pid, 0)),
            "email": contacts.get("email_contact", ""),
            "phone": contacts.get("phone", ""),
            "whatsapp": contacts.get("whatsapp_number", ""),
            "website": contacts.get("website", ""),
            "facebook": contacts.get("facebook", ""),
            "instagram": contacts.get("instagram", ""),
            "history": history,
        })

    async for d in db.prospects.find({}):
        sid = str(d["_id"])
        key = _name_key(d.get("name", ""))
        match = producer_keys.get(key) if key else None
        items.append({
            "kind": "prospect",
            "id": sid,
            "name": d.get("name", ""),
            "status": d.get("status", "DA_CONTATTARE"),
            "status_label": PROSPECT_STATUSES.get(d.get("status"), "Da contattare"),
            # una cantina con lo stesso nome si e' iscritta: probabilmente e' lei
            "maybe_registered": match,
            "history": logs.get(sid, []),
            **_prospect_fields(d),
        })

    for it in items:
        last = it["history"][0]["contacted_at"] if it["history"] else None
        it["last_contact_at"] = last
        if it["kind"] == "producer":
            done = it["account"] == "active"
        else:
            done = it["status"] == "NON_INTERESSATA"
        # da fare: mai contattata, oppure contattata da piu' di una settimana senza risultato
        it["to_do"] = (not done) and (last is None or last < remind_before)
        it["waiting"] = (not done) and last is not None and last >= remind_before
        # accesso attivo ma pagina ancora da completare: da sollecitare a mano
        it["incomplete"] = it["kind"] == "producer" and it["account"] == "active" and bool(it["missing"])

    items.sort(key=lambda i: (i["name"] or "").lower())
    return {"items": items, "channels": CHANNELS, "prospect_statuses": PROSPECT_STATUSES,
            "remind_after_days": REMIND_AFTER_DAYS}


@router.post("/log")
async def add_log(payload: LogIn, current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    oid = _oid(payload.target_id)
    if payload.target_type == "producer":
        target = await db.producers.find_one({"_id": oid}, {"_id": 1})
    else:
        target = await db.prospects.find_one({"_id": oid}, {"_id": 1, "status": 1})
    if not target:
        raise HTTPException(status_code=404, detail="Cantina non trovata")
    now = datetime.utcnow()
    day = payload.contacted_on or date.today()
    # ora attuale se e' oggi, mezzogiorno per i giorni passati (l'ordine resta giusto)
    contacted_at = now if day >= now.date() else datetime.combine(day, time(12, 0))
    doc = {
        f"{payload.target_type}_id": oid,
        "channel": payload.channel,
        "note": (payload.note or "").strip(),
        "contacted_at": contacted_at,
        "created_at": now,
        "created_by": current_admin.get("email"),
    }
    res = await db.outreach_log.insert_one(doc)
    if payload.target_type == "prospect" and target.get("status", "DA_CONTATTARE") == "DA_CONTATTARE":
        await db.prospects.update_one({"_id": oid}, {"$set": {"status": "CONTATTATA", "updated_at": now}})
    doc["_id"] = res.inserted_id
    return {"message": "Contatto registrato", "item": _log_out(doc)}


@router.delete("/log/{log_id}")
async def delete_log(log_id: str, current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    res = await db.outreach_log.delete_one({"_id": _oid(log_id)})
    if not res.deleted_count:
        raise HTTPException(status_code=404, detail="Contatto non trovato")
    return {"message": "Contatto eliminato"}


@router.post("/prospects")
async def create_prospect(payload: ProspectIn, current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    now = datetime.utcnow()
    doc = {**payload.model_dump(), "created_at": now, "updated_at": now}
    res = await db.prospects.insert_one(doc)
    return {"id": str(res.inserted_id), "message": f"{payload.name} aggiunta alle cantine da contattare"}


@router.put("/prospects/{prospect_id}")
async def update_prospect(prospect_id: str, payload: ProspectIn, current_admin: dict = Depends(get_current_admin),
                          db=Depends(get_database)):
    res = await db.prospects.update_one({"_id": _oid(prospect_id)},
                                        {"$set": {**payload.model_dump(), "updated_at": datetime.utcnow()}})
    if not res.matched_count:
        raise HTTPException(status_code=404, detail="Cantina non trovata")
    return {"message": "Dati salvati"}


@router.delete("/prospects/{prospect_id}")
async def delete_prospect(prospect_id: str, current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    oid = _oid(prospect_id)
    res = await db.prospects.delete_one({"_id": oid})
    if not res.deleted_count:
        raise HTTPException(status_code=404, detail="Cantina non trovata")
    await db.outreach_log.delete_many({"prospect_id": oid})
    return {"message": "Cantina tolta dall'elenco, con il suo storico"}


@router.post("/prospects/{prospect_id}/link")
async def link_prospect(prospect_id: str, payload: LinkIn, current_admin: dict = Depends(get_current_admin),
                        db=Depends(get_database)):
    """La cantina si e' iscritta (o e' stata creata): lo storico passa alla sua pagina e la voce sparisce."""
    oid = _oid(prospect_id)
    pid = _oid(payload.producer_id, "Cantina")
    prospect = await db.prospects.find_one({"_id": oid})
    producer = await db.producers.find_one({"_id": pid}, {"company_name": 1})
    if not prospect or not producer:
        raise HTTPException(status_code=404, detail="Cantina non trovata")
    await db.outreach_log.update_many({"prospect_id": oid}, {"$set": {"producer_id": pid}, "$unset": {"prospect_id": ""}})
    if prospect.get("notes"):
        await db.outreach_log.insert_one({
            "producer_id": pid, "channel": "ALTRO", "note": f"Note di quando non era sul sito: {prospect['notes']}",
            "contacted_at": prospect.get("created_at") or datetime.utcnow(), "created_at": datetime.utcnow(),
            "created_by": current_admin.get("email"),
        })
    await db.prospects.delete_one({"_id": oid})
    return {"message": f"Storico spostato su {producer.get('company_name', 'la cantina')}"}
