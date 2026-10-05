"""Testi del sito modificabili dall'area admin (es. informativa privacy)."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.v1.auth import get_current_admin
from app.db.mongodb import get_database

router = APIRouter()

# Bozza di partenza: i dati tra [parentesi quadre] vanno completati e il testo va fatto
# verificare da un consulente prima della messa online.
DEFAULT_PAGES = {
    "privacy": {
        "title": "Informativa sulla privacy",
        "body": """Questa informativa descrive come EnotecaMolise tratta i dati personali di chi visita il sito, di chi contatta una cantina e delle cantine che si registrano, ai sensi del Regolamento (UE) 2016/679 (GDPR).

## Titolare del trattamento
[Nome e cognome o ragione sociale del titolare], [indirizzo], email: [indirizzo email per la privacy].

## Quali dati raccogliamo
- Cantine registrate: nome della cantina, email e password di accesso (conservata in forma cifrata), dati del profilo pubblico (indirizzo, contatti, testi e immagini) e schede dei vini.
- Visitatori che contattano una cantina: nome, email, telefono se indicato e testo del messaggio.
- Dati tecnici necessari al funzionamento del sito (ad esempio l'indirizzo IP, usato per proteggere i moduli dagli abusi).

## Perché li trattiamo
- Per creare e gestire l'account della cantina e pubblicarne il profilo (esecuzione del servizio richiesto).
- Per inoltrare alla cantina le richieste dei visitatori e inviare al visitatore una copia (esecuzione della richiesta).
- Per inviare email di servizio: conferme, avvisi di approvazione, recupero password.
- Per la sicurezza del sito (legittimo interesse).

## A chi vengono comunicati
I messaggi inviati tramite il modulo di contatto sono inoltrati esclusivamente alla cantina destinataria, che li tratterà come autonomo titolare per rispondere alla richiesta. I dati sono conservati su servizi di hosting e database [indicare i fornitori e la loro sede].

## Per quanto tempo
I dati dell'account restano finché la cantina mantiene il profilo; i messaggi dei visitatori per [indicare il periodo, es. 24 mesi]; i dati tecnici per il tempo strettamente necessario.

## I tuoi diritti
Puoi chiedere in qualsiasi momento l'accesso, la rettifica, la cancellazione o la limitazione dei tuoi dati, opporti al trattamento e chiedere la portabilità, scrivendo a [indirizzo email per la privacy]. Le cantine possono chiedere la cancellazione dell'account anche dall'area riservata. Hai inoltre diritto di proporre reclamo al Garante per la protezione dei dati personali (www.garanteprivacy.it).

## Cookie
Il sito usa solo cookie tecnici necessari al funzionamento (ad esempio per mantenere l'accesso all'area riservata). [Aggiornare se verranno aggiunti strumenti di statistica o di terze parti.]

Ultimo aggiornamento: [data].""",
    },
}


class PageUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    body: Optional[str] = Field(default=None, max_length=60000)


async def get_page(db, key: str) -> dict:
    if key not in DEFAULT_PAGES:
        raise HTTPException(status_code=404, detail="Pagina non trovata")
    doc = await db.site_pages.find_one({"key": key}) or {}
    return {
        "key": key,
        "title": doc.get("title") or DEFAULT_PAGES[key]["title"],
        "body": doc.get("body") or DEFAULT_PAGES[key]["body"],
        "customized": bool(doc.get("body")),
        "updated_at": doc.get("updated_at"),
    }


@router.get("/pages/{key}")
async def read_page(key: str, db=Depends(get_database)):
    return await get_page(db, key)


@router.put("/pages/{key}")
async def update_page(key: str, payload: PageUpdate, current_admin: dict = Depends(get_current_admin),
                      db=Depends(get_database)):
    if key not in DEFAULT_PAGES:
        raise HTTPException(status_code=404, detail="Pagina non trovata")
    update = {k: v.strip() for k, v in payload.model_dump().items() if v is not None and v.strip()}
    update.update({"key": key, "updated_at": datetime.utcnow()})
    await db.site_pages.update_one({"key": key}, {"$set": update}, upsert=True)
    return await get_page(db, key)


@router.post("/pages/{key}/reset")
async def reset_page(key: str, current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    if key not in DEFAULT_PAGES:
        raise HTTPException(status_code=404, detail="Pagina non trovata")
    await db.site_pages.delete_one({"key": key})
    return await get_page(db, key)
