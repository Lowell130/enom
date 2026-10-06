"""Eventi delle cantine e del territorio, con richiesta di prenotazione (senza pagamenti).

- Le cantine creano eventi propri e li pubblicano subito; l'amministratore riceve un'email e puo' nasconderli.
- L'amministratore crea anche eventi del territorio, con piu' cantine partecipanti.
- Le richieste di prenotazione finiscono tra le "Richieste" (stessa raccolta dei messaggi dei clienti)."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.v1.auth import get_current_admin, get_current_user, get_optional_user, is_admin
from app.core.config import settings
from app.core.utils import client_ip, rate_limiter, slugify, unique_slug
from app.db.mongodb import get_database
from app.schemas.event import (EVENT_TYPES, EventCancelIn, EventIn, EventRequestIn, EventVisibilityIn)
from app.services import email as mail
from app.services.events import date_label, event_end, rome_now, upcoming_dates

router = APIRouter()

MAX_LIST = 300


# ---------------------------------------------------------------------------
# Supporto
# ---------------------------------------------------------------------------

def _oid(value: Optional[str]) -> Optional[ObjectId]:
    return ObjectId(value) if value and ObjectId.is_valid(str(value)) else None


def _own_producer(user: dict) -> Optional[ObjectId]:
    return _oid(user.get("producer_id"))


def _can_edit(user: dict, event: dict) -> bool:
    if is_admin(user):
        return True
    own = _own_producer(user)
    return bool(own) and event.get("producer_id") == own


def _span(dates: List[Dict[str, Any]]) -> Dict[str, datetime]:
    return {"starts_at": min(d["start"] for d in dates), "ends_at": max(event_end(d) for d in dates)}


def _producer_card(p: Optional[dict]) -> Optional[dict]:
    if not p:
        return None
    address = p.get("address") or {}
    return {
        "id": str(p["_id"]), "name": p.get("company_name", ""), "slug": p.get("slug", ""),
        "city": address.get("city", ""), "province": address.get("province", ""),
        "logo_url": p.get("logo_url", ""), "status": p.get("status", "APPROVED"),
    }


def _resolved_location(event: dict, organizer: Optional[dict]) -> dict:
    loc = dict(event.get("location") or {})
    if event.get("use_producer_address") and organizer:
        address = organizer.get("address") or {}
        geo = address.get("geo_coordinates") or {}
        loc = {
            "name": organizer.get("company_name", ""),
            "street": address.get("street", ""), "city": address.get("city", ""),
            "province": address.get("province", ""), "lat": geo.get("lat"), "lng": geo.get("lng"),
        }
    return loc


async def _lookups(db, events: List[dict]) -> Dict[str, Dict]:
    producer_ids, product_ids = set(), set()
    for e in events:
        if e.get("producer_id"):
            producer_ids.add(e["producer_id"])
        producer_ids.update(e.get("participant_ids") or [])
        product_ids.update(e.get("product_ids") or [])
    producers = {p["_id"]: p for p in await db.producers.find({"_id": {"$in": list(producer_ids)}}).to_list(500)} \
        if producer_ids else {}
    products = {p["_id"]: p for p in await db.products.find({"_id": {"$in": list(product_ids)}}).to_list(500)} \
        if product_ids else {}
    return {"producers": producers, "products": products}


def _serialize(event: dict, lookups: Dict[str, Dict], now: datetime, private: bool = False) -> dict:
    producers, products = lookups["producers"], lookups["products"]
    organizer = producers.get(event.get("producer_id")) if event.get("producer_id") else None
    dates = event.get("dates") or []
    next_dates = upcoming_dates(dates, now)
    wines = []
    for pid in event.get("product_ids") or []:
        p = products.get(pid)
        if not p or (p.get("status") != "PUBLISHED" and not private):
            continue
        maker = producers.get(p.get("producer_id")) or {}
        wines.append({"id": str(p["_id"]), "name": p.get("name", ""), "slug": p.get("slug", ""),
                      "photo": (p.get("photos") or [""])[0], "category": p.get("category", ""),
                      "producer_name": maker.get("company_name", "")})
    participants = [_producer_card(producers.get(pid)) for pid in event.get("participant_ids") or []]
    participants = [p for p in participants if p and (private or p["status"] == "APPROVED")]
    out = {
        "id": str(event["_id"]),
        "slug": event.get("slug", ""),
        "title": event.get("title", ""),
        "type": event.get("type", "ALTRO"),
        "type_label": EVENT_TYPES.get(event.get("type"), "Evento"),
        "description": event.get("description", ""),
        "cover_image": event.get("cover_image", ""),
        "dates": [{"start": d["start"], "end": d.get("end"), "label": date_label(d),
                   "is_past": event_end(d) < now} for d in dates],
        "starts_at": event.get("starts_at"),
        "ends_at": event.get("ends_at"),
        "next_date": ({"start": next_dates[0]["start"], "end": next_dates[0].get("end"),
                       "label": date_label(next_dates[0])} if next_dates else None),
        "is_past": not next_dates,
        "use_producer_address": bool(event.get("use_producer_address")),
        "location": _resolved_location(event, organizer),
        "organizer": _producer_card(organizer),
        "participants": participants,
        "wines": wines,
        "price_type": event.get("price_type", "FREE"),
        "price_text": event.get("price_text", ""),
        "booking_mode": event.get("booking_mode", "REQUEST"),
        "external_url": event.get("external_url", ""),
        "status": event.get("status", "PUBLISHED"),
        "cancel_message": event.get("cancel_message", ""),
    }
    if private:
        out.update({
            "producer_id": str(event["producer_id"]) if event.get("producer_id") else None,
            "participant_ids": [str(x) for x in event.get("participant_ids") or []],
            "product_ids": [str(x) for x in event.get("product_ids") or []],
            "raw_location": event.get("location") or {},
            "contact_email": event.get("contact_email") or "",
            "hidden": bool(event.get("hidden")),
            "created_at": event.get("created_at"),
            "updated_at": event.get("updated_at"),
        })
    return out


def _is_public(event: dict, producers: Dict) -> bool:
    if event.get("hidden") or event.get("status") not in ("PUBLISHED", "CANCELLED"):
        return False
    if event.get("producer_id"):
        organizer = producers.get(event["producer_id"])
        return bool(organizer) and organizer.get("status", "APPROVED") == "APPROVED"
    return True


async def _clean_input(db, payload: EventIn, user: dict) -> dict:
    data = payload.model_dump()
    admin = is_admin(user)
    if admin:
        organizer = _oid(data.get("producer_id"))
        if data.get("producer_id") and not organizer:
            raise HTTPException(status_code=400, detail="Cantina organizzatrice non valida")
        if organizer and not await db.producers.find_one({"_id": organizer}, {"_id": 1}):
            raise HTTPException(status_code=404, detail="Cantina organizzatrice non trovata")
        participants = [o for o in (_oid(x) for x in data.get("participant_ids") or []) if o and o != organizer]
        participants = list(dict.fromkeys(participants))
    else:
        organizer = _own_producer(user)
        if not organizer:
            raise HTTPException(status_code=403, detail="Il tuo account non è collegato ad alcuna cantina")
        participants = []  # gli eventi con piu' cantine li crea l'amministratore
    if not organizer and data.get("use_producer_address"):
        data["use_producer_address"] = False
    # vini: per una cantina solo i propri; per gli eventi del territorio quelli delle cantine coinvolte
    product_ids = [o for o in (_oid(x) for x in data.get("product_ids") or []) if o]
    if product_ids:
        allowed = {organizer, *participants} - {None}
        query = {"_id": {"$in": product_ids}}
        if not admin or allowed:
            query["producer_id"] = {"$in": list(allowed)}
        found = {p["_id"] for p in await db.products.find(query, {"_id": 1}).to_list(100)}
        product_ids = [p for p in product_ids if p in found]
    dates = [{"start": d["start"], "end": d.get("end")} for d in data["dates"]]
    clean = {
        "title": data["title"],
        "type": data["type"],
        "description": (data.get("description") or "").strip(),
        "cover_image": data.get("cover_image") or "",
        "dates": dates,
        **_span(dates),
        "use_producer_address": bool(data.get("use_producer_address")),
        "location": data.get("location") or {},
        "producer_id": organizer,
        "participant_ids": participants,
        "product_ids": product_ids,
        "price_type": data["price_type"],
        "price_text": (data.get("price_text") or "").strip() if data["price_type"] == "PAID" else "",
        "booking_mode": data["booking_mode"],
        "external_url": data.get("external_url") or "",
        "contact_email": str(data["contact_email"]) if data.get("contact_email") else "",
        "status": data["status"],
    }
    if not clean["use_producer_address"] and not (clean["location"].get("city") or clean["location"].get("name")):
        raise HTTPException(status_code=400, detail="Indica dove si svolge l'evento (almeno il comune)")
    return clean


async def _get_event(db, event_id: str) -> dict:
    oid = _oid(event_id)
    event = await db.events.find_one({"_id": oid}) if oid else None
    if not event:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    return event


async def _notify_new_event(db, event: dict, organizer: Optional[dict]) -> None:
    if not organizer or event.get("status") != "PUBLISHED":
        return
    ctx = {
        "nome_cantina": organizer.get("company_name", ""),
        "titolo_evento": event["title"],
        "data_evento": date_label(event["dates"][0]),
        "link_evento": mail.site_url(f"/eventi/{event['slug']}"),
        "link_gestione_eventi": mail.site_url("/dashboard/eventi"),
    }
    await mail.send_template(db, "nuovo_evento_admin", await mail.admin_recipients(db), ctx,
                             {"event_id": str(event["_id"]), "producer_id": str(organizer["_id"])})


def _overlaps(event: dict, start: Optional[datetime], end: Optional[datetime]) -> bool:
    for d in event.get("dates") or []:
        if (end is None or d["start"] <= end) and (start is None or event_end(d) >= start):
            return True
    return False


def _period_bounds(period: str, now: datetime):
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "weekend":
        # da venerdi' a domenica; se e' gia' il fine settimana, quello in corso
        wd = today.weekday()  # lunedi' = 0
        friday = today + timedelta(days=4 - wd) if wd <= 4 else today - timedelta(days=wd - 4)
        return max(now, friday), friday + timedelta(days=2, hours=23, minutes=59)
    if period == "month":
        nxt = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
        return now, nxt - timedelta(minutes=1)
    if period == "next30":
        return now, now + timedelta(days=30)
    return now, None


# ---------------------------------------------------------------------------
# Pubblico
# ---------------------------------------------------------------------------

@router.get("")
async def list_events(
    period: str = "",          # weekend | month | next30
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    type: str = "",
    city: str = "",
    free: bool = False,
    producer: str = "",        # eventi organizzati da (o con la partecipazione di) una cantina
    product: str = "",         # eventi in cui e' in degustazione un vino
    past: bool = False,
    limit: int = 100,
    db=Depends(get_database),
):
    now = rome_now()
    query: Dict[str, Any] = {"status": "PUBLISHED", "hidden": {"$ne": True}}
    if past:
        query["ends_at"] = {"$lt": now}
    else:
        query["ends_at"] = {"$gte": now}
    if type and type in EVENT_TYPES:
        query["type"] = type
    if free:
        query["price_type"] = "FREE"
    if producer:
        pid = _oid(producer)
        if not pid:
            return []
        query["$or"] = [{"producer_id": pid}, {"participant_ids": pid}]
    if product:
        prid = _oid(product)
        if not prid:
            return []
        query["product_ids"] = prid
    events = await db.events.find(query).sort("starts_at", -1 if past else 1).to_list(MAX_LIST)
    lookups = await _lookups(db, events)
    start = end = None
    if not past:
        start, end = _period_bounds(period, now)
        try:
            if date_from:
                start = max(now, datetime.fromisoformat(date_from))
            if date_to:
                end = datetime.fromisoformat(date_to).replace(hour=23, minute=59)
        except ValueError:
            raise HTTPException(status_code=400, detail="Data non valida")
    out = []
    for e in events:
        if not _is_public(e, lookups["producers"]):
            continue
        if not past and not _overlaps(e, start, end):
            continue
        item = _serialize(e, lookups, now)
        if city and city.strip().lower() != (item["location"].get("city") or "").strip().lower():
            continue
        out.append(item)
    if not past:
        # in ordine di prossima data (un evento ricorrente compare quando arriva la sua prossima data)
        out.sort(key=lambda x: x["next_date"]["start"] if x["next_date"] else x["starts_at"])
    return out[:max(1, min(limit, MAX_LIST))]


@router.get("/manage")
async def manage_events(
    status: str = "",
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    """Area riservata: la cantina vede i propri eventi (anche quelli del territorio a cui partecipa),
    l'amministratore tutti."""
    query: Dict[str, Any] = {}
    if not is_admin(current_user):
        own = _own_producer(current_user)
        if not own:
            return []
        query["$or"] = [{"producer_id": own}, {"participant_ids": own}]
    if status in ("DRAFT", "PUBLISHED", "CANCELLED"):
        query["status"] = status
    elif status == "HIDDEN":
        query["hidden"] = True
    events = await db.events.find(query).sort("starts_at", -1).to_list(1000)
    lookups = await _lookups(db, events)
    now = rome_now()
    counts: Dict[str, int] = {}
    async for inq in db.inquiries.find({"event_id": {"$in": [e["_id"] for e in events]}}, {"event_id": 1}):
        key = str(inq["event_id"])
        counts[key] = counts.get(key, 0) + 1
    out = []
    for e in events:
        item = _serialize(e, lookups, now, private=True)
        item["requests_count"] = counts.get(item["id"], 0)
        item["can_edit"] = _can_edit(current_user, e)
        out.append(item)
    # prima i prossimi (dal piu' vicino), poi i passati (dal piu' recente)
    upcoming = sorted([x for x in out if not x["is_past"]],
                      key=lambda x: x["next_date"]["start"] if x["next_date"] else x["starts_at"])
    past = [x for x in out if x["is_past"]]
    return upcoming + past


@router.get("/{slug}")
async def get_event(slug: str, current_user: Optional[dict] = Depends(get_optional_user), db=Depends(get_database)):
    event = await db.events.find_one({"slug": slug})
    if not event and ObjectId.is_valid(slug):
        event = await db.events.find_one({"_id": ObjectId(slug)})
    if not event:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    lookups = await _lookups(db, [event])
    private = bool(current_user) and _can_edit(current_user, event)
    if not _is_public(event, lookups["producers"]) and not private:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    out = _serialize(event, lookups, rome_now(), private=private)
    out["can_edit"] = private
    return out


@router.post("/{event_id}/requests")
async def request_booking(event_id: str, payload: EventRequestIn, request: Request, db=Depends(get_database)):
    rate_limiter.check_and_hit(
        f"inquiry:{client_ip(request)}",
        settings.INQUIRY_MAX_PER_WINDOW,
        settings.INQUIRY_WINDOW_SECONDS,
        "Hai inviato troppe richieste in poco tempo. Riprova tra qualche minuto.",
    )
    event = await _get_event(db, event_id)
    lookups = await _lookups(db, [event])
    if not _is_public(event, lookups["producers"]) or event.get("status") != "PUBLISHED":
        raise HTTPException(status_code=404, detail="Evento non disponibile")
    if event.get("booking_mode") != "REQUEST":
        raise HTTPException(status_code=400, detail="Per questo evento non si prenota dal sito")
    dates = event.get("dates") or []
    if payload.date_index >= len(dates):
        raise HTTPException(status_code=400, detail="Data dell'evento non valida")
    chosen = dates[payload.date_index]
    if event_end(chosen) < rome_now():
        raise HTTPException(status_code=400, detail="Questa data dell'evento è già passata")

    organizer = lookups["producers"].get(event.get("producer_id")) if event.get("producer_id") else None
    when = date_label(chosen)
    people = payload.people
    note = (payload.message or "").strip()
    now = datetime.utcnow()
    doc = {
        "producer_id": event.get("producer_id"),
        "product_id": None,
        "event_id": event["_id"],
        "event_title": event["title"],
        "event_date": when,
        "people": people,
        "user_name": payload.user_name.strip(),
        "user_email": str(payload.user_email),
        "user_phone": payload.user_phone or "",
        "message_type": "EVENTO",
        "message": note or "Nessuna nota.",
        "is_read": False,
        "created_at": now,
        "privacy_accepted_at": now,
    }
    res = await db.inquiries.insert_one(doc)

    # chi riceve: la cantina organizzatrice, oppure il contatto dell'evento del territorio o l'amministratore
    if organizer:
        contacts = organizer.get("contacts") or {}
        recipients = [contacts["email_contact"]] if contacts.get("email_contact") else []
        if not recipients:
            users = await db.users.find({"producer_id": organizer["_id"], "is_active": {"$ne": False}},
                                        {"email": 1}).to_list(5)
            recipients = [u["email"] for u in users if u.get("email")]
        if not recipients:
            # cantina senza email (es. inserita dall'amministratore): la richiesta non deve andare persa
            recipients = await mail.admin_recipients(db)
        organizer_name = organizer.get("company_name", "")
    else:
        recipients = [event["contact_email"]] if event.get("contact_email") else await mail.admin_recipients(db)
        organizer_name = mail.SITE_NAME
    ctx = {
        "nome_organizzatore": organizer_name,
        "titolo_evento": event["title"],
        "data_evento": when,
        "persone": str(people),
        "nome_cliente": doc["user_name"],
        "email_cliente": doc["user_email"],
        "telefono_cliente": doc["user_phone"] or "non indicato",
        "messaggio": doc["message"],
        "link_evento": mail.site_url(f"/eventi/{event['slug']}"),
        "link_richieste": mail.site_url("/dashboard/messaggi"),
    }
    related = {"event_id": str(event["_id"]), "inquiry_id": str(res.inserted_id)}
    await mail.send_template(db, "nuova_prenotazione_evento", recipients, ctx, related)
    await mail.send_template(db, "conferma_prenotazione_evento", [doc["user_email"]], ctx, related)
    return {"message": f"Richiesta inviata a {organizer_name}: ti risponderanno all'indirizzo {doc['user_email']}.",
            "id": str(res.inserted_id)}


# ---------------------------------------------------------------------------
# Area riservata
# ---------------------------------------------------------------------------

@router.post("")
async def create_event(payload: EventIn, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    data = await _clean_input(db, payload, current_user)
    now = datetime.utcnow()
    data.update({
        "slug": await unique_slug(db.events, slugify(data["title"])[:80] or "evento"),
        "hidden": False,
        "created_by": str(current_user.get("_id", "")),
        "created_at": now,
        "updated_at": now,
    })
    res = await db.events.insert_one(data)
    data["_id"] = res.inserted_id
    organizer = await db.producers.find_one({"_id": data["producer_id"]}) if data.get("producer_id") else None
    if not is_admin(current_user):
        await _notify_new_event(db, data, organizer)
    lookups = await _lookups(db, [data])
    out = _serialize(data, lookups, rome_now(), private=True)
    out["can_edit"] = True
    return out


@router.put("/{event_id}")
async def update_event(event_id: str, payload: EventIn, current_user: dict = Depends(get_current_user),
                       db=Depends(get_database)):
    event = await _get_event(db, event_id)
    if not _can_edit(current_user, event):
        raise HTTPException(status_code=403, detail="Puoi modificare solo gli eventi della tua cantina")
    data = await _clean_input(db, payload, current_user)
    if not is_admin(current_user):
        # una cantina non cambia organizzatore ne' partecipanti decisi dall'amministratore
        data["producer_id"] = event.get("producer_id")
        data["participant_ids"] = event.get("participant_ids") or []
    if event.get("status") == "CANCELLED":
        data["status"] = "CANCELLED"
    if data["title"] != event.get("title"):
        data["slug"] = await unique_slug(db.events, slugify(data["title"])[:80] or "evento", exclude_id=event["_id"])
    data["updated_at"] = datetime.utcnow()
    await db.events.update_one({"_id": event["_id"]}, {"$set": data})
    was_draft = event.get("status") == "DRAFT"
    event.update(data)
    if was_draft and event.get("status") == "PUBLISHED" and not is_admin(current_user):
        organizer = await db.producers.find_one({"_id": event["producer_id"]}) if event.get("producer_id") else None
        await _notify_new_event(db, event, organizer)
    lookups = await _lookups(db, [event])
    out = _serialize(event, lookups, rome_now(), private=True)
    out["can_edit"] = True
    return out


@router.delete("/{event_id}")
async def delete_event(event_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    event = await _get_event(db, event_id)
    if not _can_edit(current_user, event):
        raise HTTPException(status_code=403, detail="Puoi eliminare solo gli eventi della tua cantina")
    await db.events.delete_one({"_id": event["_id"]})
    return {"message": "Evento eliminato"}


@router.post("/{event_id}/duplicate")
async def duplicate_event(event_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    """Copia in bozza, comoda per gli appuntamenti che si ripetono: basta cambiare le date."""
    event = await _get_event(db, event_id)
    if not _can_edit(current_user, event):
        raise HTTPException(status_code=403, detail="Puoi duplicare solo gli eventi della tua cantina")
    copy = {k: v for k, v in event.items() if k not in ("_id", "cancel_message", "cancelled_at")}
    now = datetime.utcnow()
    copy.update({
        "title": f"{event.get('title', '')} (copia)"[:150],
        "status": "DRAFT",
        "hidden": False,
        "created_by": str(current_user.get("_id", "")),
        "created_at": now,
        "updated_at": now,
    })
    copy["slug"] = await unique_slug(db.events, slugify(copy["title"])[:80] or "evento")
    res = await db.events.insert_one(copy)
    return {"id": str(res.inserted_id), "slug": copy["slug"], "message": "Copia creata come bozza"}


@router.post("/{event_id}/cancel")
async def cancel_event(event_id: str, payload: EventCancelIn, current_user: dict = Depends(get_current_user),
                       db=Depends(get_database)):
    event = await _get_event(db, event_id)
    if not _can_edit(current_user, event):
        raise HTTPException(status_code=403, detail="Puoi annullare solo gli eventi della tua cantina")
    if event.get("status") == "CANCELLED":
        raise HTTPException(status_code=400, detail="L'evento è già annullato")
    message = (payload.message or "").strip()
    await db.events.update_one({"_id": event["_id"]}, {"$set": {
        "status": "CANCELLED", "cancel_message": message, "cancelled_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }})
    # avvisa chi aveva chiesto di partecipare (una sola email per indirizzo)
    emails: Dict[str, str] = {}
    async for inq in db.inquiries.find({"event_id": event["_id"]}):
        if inq.get("user_email"):
            emails.setdefault(inq["user_email"].lower(), inq.get("user_name", ""))
    organizer = await db.producers.find_one({"_id": event["producer_id"]}) if event.get("producer_id") else None
    for address, name in emails.items():
        ctx = {
            "nome_cliente": name,
            "nome_organizzatore": organizer.get("company_name", "") if organizer else mail.SITE_NAME,
            "titolo_evento": event.get("title", ""),
            "data_evento": date_label(event["dates"][0]) if event.get("dates") else "",
            "motivo": message or "Non è stato indicato un motivo.",
            "link_eventi": mail.site_url("/eventi"),
        }
        await mail.send_template(db, "evento_annullato", [address], ctx, {"event_id": str(event["_id"])})
    notified = len(emails)
    who = "avvisata 1 persona" if notified == 1 else f"avvisate {notified} persone"
    return {"message": "Evento annullato" + (f": {who}" if notified else ""),
            "notified": len(emails)}


@router.put("/{event_id}/visibility")
async def set_visibility(event_id: str, payload: EventVisibilityIn, current_admin: dict = Depends(get_current_admin),
                         db=Depends(get_database)):
    event = await _get_event(db, event_id)
    await db.events.update_one({"_id": event["_id"]}, {"$set": {"hidden": payload.hidden,
                                                                "updated_at": datetime.utcnow()}})
    return {"message": "Evento nascosto dal sito" if payload.hidden else "Evento di nuovo visibile"}
