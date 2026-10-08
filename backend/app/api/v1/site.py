"""Testi del sito modificabili dall'area admin (chi siamo, informativa privacy e cookie policy)."""
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
EnotecaMolise è un progetto personale, gratuito e senza scopo di lucro. Titolare del trattamento è il gestore del sito, [Nome e cognome], persona fisica. Per qualsiasi richiesta sui dati personali puoi scrivere a info@enotecamolise.it.

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
Puoi chiedere in qualsiasi momento l'accesso, la rettifica, la cancellazione o la limitazione dei tuoi dati, opporti al trattamento e chiedere la portabilità, scrivendo a info@enotecamolise.it. Le cantine possono chiedere la cancellazione dell'account anche dall'area riservata. Hai inoltre diritto di proporre reclamo al Garante per la protezione dei dati personali (www.garanteprivacy.it).

## Cookie
Il sito usa cookie tecnici necessari al funzionamento (ad esempio per mantenere l'accesso all'area riservata e ricordare le tue scelte sui cookie). Tutti i dettagli sono nella Cookie policy, raggiungibile dal fondo di ogni pagina insieme alle "Preferenze cookie".

Ultimo aggiornamento: [data].""",
    },
    "cookie": {
        "title": "Cookie policy",
        "body": """Questa pagina spiega quali cookie usa EnotecaMolise, a cosa servono e come puoi gestirli. I cookie sono piccoli file di testo che il sito salva nel tuo browser.

## Titolare del trattamento
Il sito è gestito da EnotecaMolise, progetto personale e senza scopo di lucro: i dati del titolare sono indicati nell'Informativa sulla privacy. Contatti: info@enotecamolise.it.

## Cookie tecnici (sempre attivi)
Sono necessari al funzionamento del sito e non richiedono il consenso.
- auth_token: mantiene l'accesso all'area riservata di cantine e amministratori. Si crea solo quando accedi e dura al massimo 3 giorni, o fino a quando esci.
- em_consenso_cookie: ricorda le scelte fatte nel banner dei cookie, così non te le chiediamo a ogni pagina. Dura 6 mesi, poi ti chiediamo di nuovo.

## Cookie di statistica
Al momento il sito non usa strumenti di statistica. Se verranno attivati, partiranno solo se li accetti dal banner o dalle "Preferenze cookie", e saranno elencati qui. [Aggiornare se verrà aggiunto uno strumento di statistica.]

## Cookie di profilazione e pubblicità
Il sito non usa cookie di profilazione né pubblicitari.

## Servizi esterni
Per mostrare alcuni contenuti il sito carica risorse da servizi esterni, che ricevono l'indirizzo IP del tuo dispositivo per poterle inviare. Questi servizi non vengono usati dal sito per installare cookie.
- Caratteri tipografici: Google Fonts (Google Ireland Ltd.).
- Mappe: tessere cartografiche di OpenStreetMap e libreria Leaflet distribuita da unpkg.com.
[Verificare l'elenco con il consulente prima della messa online.]

## Come cambiare le tue scelte
Puoi cambiare idea in qualsiasi momento con il link "Preferenze cookie" in fondo a ogni pagina o con il pulsante qui sotto. Puoi anche cancellare i cookie dalle impostazioni del browser: in quel caso il banner comparirà di nuovo alla visita successiva.

## I tuoi diritti
Per i diritti sui tuoi dati personali vedi l'Informativa sulla privacy.

Ultimo aggiornamento: [data].""",
    },
    "chi-siamo": {
        "title": "Chi siamo",
        "body": """EnotecaMolise è un progetto indipendente e senza scopo di lucro, nato per far conoscere i vini e le cantine del Molise: una regione piccola, con vitigni autoctoni come la Tintilia e denominazioni che meritano di essere scoperte.

## Cosa trovi sul sito
- Il catalogo dei vini molisani, con schede tecniche, vitigni e abbinamenti.
- Le cantine, con la mappa per trovarle e i contatti per scrivere direttamente ai produttori.
- Gli eventi: degustazioni, visite in vigna, cene e feste del vino.
- L'Osservatorio, con i numeri del vino molisano.

## Gratuito, senza intermediari
Il portale è gratuito per i visitatori e per le cantine: nessun abbonamento, nessuna commissione, nessuna pubblicità. Le richieste dei visitatori arrivano direttamente alla cantina, che risponde e si accorda con loro. Il sito non vende vino e non gestisce pagamenti.

## Per le cantine
Ogni cantina del Molise può avere la sua pagina e aggiornarla in autonomia: storia, foto, schede dei vini ed eventi. Se la vostra cantina non c'è ancora potete registrarla dall'area riservata; se c'è già e volete gestirla voi, scriveteci.

## Contatti
Per segnalazioni, correzioni o qualsiasi domanda: info@enotecamolise.it""",
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
