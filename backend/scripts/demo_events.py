"""Eventi dimostrativi per provare la sezione Eventi (eseguire dalla cartella backend/).

  python scripts/demo_events.py            crea gli eventi demo (date a partire da oggi)
  python scripts/demo_events.py --rimuovi  cancella gli eventi demo e le eventuali richieste ricevute

Gli eventi sono segnati con demo=True e nella descrizione c'e' scritto che sono dimostrativi:
vanno rimossi prima di mettere il sito online. Rilanciando la creazione, quelli vecchi vengono sostituiti.
"""
import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.core.utils import slugify, unique_slug  # noqa: E402
from app.db.mongodb import close_mongo_connection, connect_to_mongo, db  # noqa: E402
from app.services.events import event_end, rome_now  # noqa: E402
from app.services.insights import primary_grape  # noqa: E402

DEMO_NOTE = "\n\nEvento dimostrativo, creato per provare il sito: date e programma non sono reali."


def at(day: datetime, hour: int, minute: int = 0) -> datetime:
    return day.replace(hour=hour, minute=minute, second=0, microsecond=0)


def next_weekday(start: datetime, weekday: int, weeks_later: int = 0) -> datetime:
    """Prossimo giorno della settimana indicato (lunedi'=0), escluso oggi, piu' eventuali settimane."""
    days = (weekday - start.weekday()) % 7 or 7
    return start + timedelta(days=days + 7 * weeks_later)


async def pick_wineries(database):
    producers = await database.producers.find({"status": "APPROVED"}).to_list(500)
    products = await database.products.find({"status": "PUBLISHED"}).to_list(5000)
    by_producer = {}
    for p in products:
        by_producer.setdefault(p.get("producer_id"), []).append(p)
    wineries = []
    for pr in producers:
        wines = by_producer.get(pr["_id"], [])
        if not wines:
            continue
        geo = (pr.get("address") or {}).get("geo_coordinates") or {}
        wineries.append({"doc": pr, "wines": wines, "has_place": bool((pr.get("address") or {}).get("city") and geo.get("lat"))})
    # prima le cantine con piu' vini e con la posizione sulla mappa
    wineries.sort(key=lambda w: (not w["has_place"], -len(w["wines"])))
    return wineries


def wines_of(winery, grape=None, category=None, limit=3):
    out = []
    for w in winery["wines"]:
        if grape and (primary_grape(w) or "").lower() != grape.lower():
            continue
        if category and w.get("category") != category:
            continue
        out.append(w["_id"])
    return out[:limit]


def choose(wineries, used, grape=None, category=None):
    """Una cantina non ancora usata che abbia vini del vitigno/tipologia richiesti (altrimenti una qualsiasi)."""
    for w in wineries:
        if w["doc"]["_id"] not in used and wines_of(w, grape, category, 1):
            used.add(w["doc"]["_id"])
            return w
    for w in wineries:
        if w["doc"]["_id"] not in used:
            used.add(w["doc"]["_id"])
            return w
    return wineries[0]


async def remove(database) -> None:
    ids = [e["_id"] async for e in database.events.find({"demo": True}, {"_id": 1})]
    if not ids:
        print("Nessun evento demo da rimuovere.")
        return
    req = await database.inquiries.delete_many({"event_id": {"$in": ids}})
    res = await database.events.delete_many({"_id": {"$in": ids}})
    print(f"Rimossi {res.deleted_count} eventi demo e {req.deleted_count} richieste collegate.")


async def create(database) -> None:
    await remove(database)
    wineries = await pick_wineries(database)
    if len(wineries) < 4:
        print("Servono almeno 4 cantine approvate con vini pubblicati.")
        return
    now = rome_now()
    used = set()
    names = lambda ws: ", ".join(w["doc"]["company_name"] for w in ws)  # noqa: E731

    tint = choose(wineries, used, grape="Tintilia")
    harvest = choose(wineries, used, category="VINO_ROSSO")
    white = choose(wineries, used, category="VINO_BIANCO")
    dinner = choose(wineries, used, category="VINO_ROSSO")
    visit = choose(wineries, used)
    course = choose(wineries, used)
    fair_wineries = [w for w in wineries if w["doc"]["_id"] not in used][:5] or wineries[:5]
    martino_wineries = wineries[:4]

    sat = next_weekday(now, 5)
    sun = next_weekday(now, 6)
    fri = next_weekday(now, 4)
    # San Martino: 11 novembre (dell'anno prossimo se e' gia' passato)
    martino = datetime(now.year, 11, 11)
    if martino < now:
        martino = datetime(now.year + 1, 11, 11)

    def own(w, title, type_, description, dates, price=None, products=None, booking="REQUEST"):
        return {
            "title": title, "type": type_, "description": description + DEMO_NOTE,
            "dates": dates, "use_producer_address": True, "location": {},
            "producer_id": w["doc"]["_id"], "participant_ids": [], "product_ids": products or [],
            "price_type": "PAID" if price else "FREE", "price_text": price or "",
            "booking_mode": booking, "external_url": "", "contact_email": "",
        }

    def territory(title, type_, description, dates, place, participants, price=None):
        return {
            "title": title, "type": type_, "description": description + DEMO_NOTE,
            "dates": dates, "use_producer_address": False, "location": place,
            "producer_id": None, "participant_ids": [w["doc"]["_id"] for w in participants],
            "product_ids": [p for w in participants for p in wines_of(w, limit=1)],
            "price_type": "PAID" if price else "FREE", "price_text": price or "",
            "booking_mode": "NONE", "external_url": "", "contact_email": "",
        }

    events = [
        own(tint, "Cantina aperta: degustazione di Tintilia", "DEGUSTAZIONE",
            "Un pomeriggio in cantina per conoscere la Tintilia, il vitigno simbolo del Molise.\n\n"
            "- Visita della bottaia con l'enologo\n- Degustazione di tre vini accompagnata da pane, olio e formaggi locali\n"
            "- Durata circa due ore e mezza",
            [{"start": at(sat, 17), "end": at(sat, 19, 30)}], "15 € a persona", wines_of(tint, grape="Tintilia")),
        own(harvest, "Vendemmia in famiglia", "VENDEMMIA",
            "Una mattina tra i filari per raccogliere l'uva insieme ai vignaioli, adatta anche ai bambini.\n\n"
            "Forbici e cassette le mettiamo noi: porta scarpe comode e un cappello. A fine raccolta merenda in cantina.",
            [{"start": at(sun, 9, 30), "end": at(sun, 13)}], None, wines_of(harvest, category="VINO_ROSSO", limit=2)),
        own(white, "Aperitivo in vigna al tramonto", "DEGUSTAZIONE",
            "Tre venerdì per brindare tra le vigne con i bianchi della cantina e prodotti del territorio.\n\n"
            "In caso di pioggia l'aperitivo si sposta sotto il portico.",
            [{"start": at(next_weekday(now, 4, i), 18, 30), "end": at(next_weekday(now, 4, i), 20, 30)} for i in range(3)],
            "12 € a persona", wines_of(white, category="VINO_BIANCO")),
        own(dinner, "Cena in cantina: vino e piatti della tradizione", "CENA",
            "Cinque portate della cucina molisana abbinate ai vini della cantina, raccontati dal produttore.\n\n"
            "Posti limitati: segnala nella richiesta eventuali allergie o intolleranze.",
            [{"start": at(next_weekday(now, 5, 2), 20), "end": at(next_weekday(now, 5, 2), 23)}],
            "45 € a persona", wines_of(dinner, category="VINO_ROSSO")),
        own(visit, "Visita guidata della cantina e del vigneto", "VISITA",
            "Ogni sabato mattina: passeggiata nel vigneto, visita della cantina e assaggio di due vini.",
            [{"start": at(next_weekday(now, 5, i), 10, 30), "end": at(next_weekday(now, 5, i), 12)} for i in range(4)],
            "10 € a persona", wines_of(visit, limit=2)),
        own(course, "Corso base di degustazione", "CORSO",
            "Due serate per imparare a riconoscere colori, profumi e sapori del vino, con sei assaggi per serata.\n\n"
            "Il prezzo comprende entrambe le serate e il materiale del corso.",
            [{"start": at(next_weekday(now, 2, w), 19), "end": at(next_weekday(now, 2, w), 21)} for w in (1, 2)],
            "60 € per le due serate", wines_of(course, limit=3)),
        territory("Festa del vino molisano", "FIERA",
                  "Due giorni di banchi d'assaggio con le cantine del Molise, musica e prodotti tipici nel centro storico.\n\n"
                  "Ingresso libero; i calici di degustazione si acquistano sul posto.",
                  [{"start": at(next_weekday(now, 5, 4), 16), "end": at(next_weekday(now, 5, 4) + timedelta(days=1), 23)}],
                  {"name": "Centro storico", "street": "", "city": "Larino", "province": "CB", "lat": None, "lng": None},
                  fair_wineries),
        territory("Calici di San Martino", "FIERA",
                  "La sera di San Martino si stappa il vino nuovo: banchi d'assaggio delle cantine, castagne e caldarroste.",
                  [{"start": at(martino, 18), "end": at(martino, 23)}],
                  {"name": "Lungomare Nord", "street": "", "city": "Termoli", "province": "CB", "lat": None, "lng": None},
                  martino_wineries, "Calice e 5 assaggi 10 €"),
    ]

    created = []
    for ev in events:
        dates = ev["dates"]
        ev.update({
            "starts_at": min(d["start"] for d in dates),
            "ends_at": max(event_end(d) for d in dates),
            "status": "PUBLISHED",
            "hidden": False,
            "demo": True,
            "slug": await unique_slug(database.events, slugify(ev["title"])[:80]),
            "created_by": "demo",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        await database.events.insert_one(ev)
        organizer = next((w["doc"]["company_name"] for w in wineries if w["doc"]["_id"] == ev["producer_id"]), "evento del territorio")
        created.append(f"  {dates[0]['start']:%d/%m %H:%M}  {ev['title']}  ({organizer})")
    print(f"Creati {len(created)} eventi demo:")
    print("\n".join(created))
    print(f"\nCantine della festa: {names(fair_wineries)}")
    print("Per toglierli: python scripts/demo_events.py --rimuovi")


async def main():
    parser = argparse.ArgumentParser(description="Eventi dimostrativi")
    parser.add_argument("--rimuovi", action="store_true", help="cancella gli eventi demo")
    args = parser.parse_args()
    await connect_to_mongo()
    database = db.client[settings.DATABASE_NAME]
    try:
        await (remove(database) if args.rimuovi else create(database))
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
