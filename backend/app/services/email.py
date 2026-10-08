"""Email transazionali del portale: modelli modificabili dall'admin, impaginazione e invio.

Modalita' (EMAIL_MODE nel .env):
  - "outbox": nessun invio reale; ogni email viene salvata nella collezione `email_outbox` e si legge
    in Area riservata > Email e testi > Posta in uscita. E' la modalita' di sviluppo (nessun dominio).
  - "smtp":   invio reale con i dati SMTP del .env; l'email viene comunque registrata nella posta in
    uscita con lo stato (inviata / errore).

I modelli predefiniti sono nel codice (DEFAULT_TEMPLATES); quelli modificati dall'admin vengono salvati
nella collezione `email_templates` e prevalgono. "Ripristina" elimina la versione personalizzata.

Sintassi dei testi:
  {{variabile}}              valore (es. {{nome_cantina}})
  riga vuota                 nuovo paragrafo
  [[Testo del pulsante|{{link}}]]   pulsante (su una riga a se')
"""
import asyncio
import html
import logging
import re
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import Any, Dict, Iterable, List, Optional

from app.core.config import settings

logger = logging.getLogger("enotecamolise.email")

SITE_NAME = "EnotecaMolise"

# ---------------------------------------------------------------------------
# Modelli predefiniti
# ---------------------------------------------------------------------------

DEFAULT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "registrazione_cantina": {
        "label": "Registrazione ricevuta",
        "description": "Alla cantina, subito dopo la registrazione.",
        "recipient": "Cantina (email di accesso)",
        "variables": ["nome_cantina", "email", "link_area_riservata"],
        "subject": "Benvenuta su {{nome_sito}}, {{nome_cantina}}",
        "body": (
            "Ciao,\n\n"
            "abbiamo ricevuto la registrazione di {{nome_cantina}} su {{nome_sito}}, il portale dei vini e delle cantine del Molise.\n\n"
            "Il profilo pubblico sarà attivato dopo una breve verifica da parte del nostro team: riceverai un'email appena la cantina sarà online.\n\n"
            "Nel frattempo puoi già completare il profilo (storia, logo, foto, indirizzo e contatti) e inserire le schede dei tuoi vini.\n\n"
            "[[Vai alla tua area riservata|{{link_area_riservata}}]]\n\n"
            "Accedi sempre con l'indirizzo {{email}}.\n\n"
            "A presto,\nil team di {{nome_sito}}"
        ),
    },
    "nuova_cantina_admin": {
        "label": "Nuova cantina da approvare",
        "description": "All'amministratore, quando una cantina si registra.",
        "recipient": "Amministratore (indirizzi delle notifiche)",
        "variables": ["nome_cantina", "email", "data", "link_approvazione"],
        "subject": "Nuova cantina da approvare: {{nome_cantina}}",
        "body": (
            "Una nuova cantina si è registrata ed è in attesa di approvazione.\n\n"
            "Cantina: {{nome_cantina}}\nEmail: {{email}}\nData: {{data}}\n\n"
            "[[Rivedi e approva|{{link_approvazione}}]]"
        ),
    },
    "cantina_approvata": {
        "label": "Cantina approvata",
        "description": "Alla cantina, quando l'amministratore la approva.",
        "recipient": "Cantina (email di accesso)",
        "variables": ["nome_cantina", "link_pagina_cantina", "link_area_riservata"],
        "subject": "{{nome_cantina}} è online su {{nome_sito}}",
        "body": (
            "Ciao,\n\n"
            "buone notizie: il profilo di {{nome_cantina}} è stato approvato ed è ora visibile a tutti i visitatori di {{nome_sito}}, insieme ai vini pubblicati.\n\n"
            "[[Guarda la pagina della cantina|{{link_pagina_cantina}}]]\n\n"
            "Le richieste dei clienti ti arriveranno via email e le troverai anche nell'area riservata, alla voce Richieste.\n\n"
            "Buon lavoro,\nil team di {{nome_sito}}"
        ),
    },
    "cantina_sospesa": {
        "label": "Cantina sospesa",
        "description": "Alla cantina, quando l'amministratore sospende il profilo.",
        "recipient": "Cantina (email di accesso)",
        "variables": ["nome_cantina", "link_area_riservata"],
        "subject": "Il profilo di {{nome_cantina}} è stato sospeso",
        "body": (
            "Ciao,\n\n"
            "il profilo di {{nome_cantina}} è stato temporaneamente sospeso e al momento non è visibile sul sito.\n\n"
            "Per informazioni rispondi a questa email.\n\n"
            "Il team di {{nome_sito}}"
        ),
    },
    "nuova_richiesta_cantina": {
        "label": "Nuova richiesta di un cliente",
        "description": "Alla cantina, quando un visitatore invia un messaggio dalla scheda di un vino o della cantina.",
        "recipient": "Cantina (email di contatto del profilo)",
        "variables": ["nome_cantina", "nome_cliente", "email_cliente", "telefono_cliente", "tipo_richiesta",
                      "nome_vino", "messaggio", "link_richieste"],
        "subject": "Nuova richiesta da {{nome_cliente}}: {{tipo_richiesta}}",
        "body": (
            "Ciao {{nome_cantina}},\n\n"
            "hai ricevuto una nuova richiesta tramite {{nome_sito}}.\n\n"
            "Da: {{nome_cliente}} ({{email_cliente}})\nTelefono: {{telefono_cliente}}\n"
            "Tipo di richiesta: {{tipo_richiesta}}\nVino: {{nome_vino}}\n\n"
            "Messaggio:\n{{messaggio}}\n\n"
            "Per rispondere scrivi direttamente a {{email_cliente}}.\n\n"
            "[[Apri le richieste nell'area riservata|{{link_richieste}}]]"
        ),
    },
    "conferma_richiesta_cliente": {
        "label": "Conferma al cliente",
        "description": "Al visitatore, come copia della richiesta inviata alla cantina.",
        "recipient": "Cliente (email inserita nel modulo)",
        "variables": ["nome_cliente", "nome_cantina", "nome_vino", "messaggio", "link_pagina_cantina"],
        "subject": "Abbiamo inoltrato la tua richiesta a {{nome_cantina}}",
        "body": (
            "Ciao {{nome_cliente}},\n\n"
            "la tua richiesta è stata inoltrata a {{nome_cantina}}, che ti risponderà direttamente al tuo indirizzo email.\n\n"
            "Vino: {{nome_vino}}\n\nIl tuo messaggio:\n{{messaggio}}\n\n"
            "[[Scopri la cantina|{{link_pagina_cantina}}]]\n\n"
            "Grazie per aver scelto i vini del Molise,\nil team di {{nome_sito}}"
        ),
    },
    "invito_cantina": {
        "label": "Invito a una cantina",
        "description": "Alle cantine inserite dall'amministratore: link per scegliere la password e attivare l'accesso.",
        "recipient": "Cantina (email di contatto del profilo)",
        "variables": ["nome_cantina", "email", "link_attivazione", "giorni_validita", "link_pagina_cantina"],
        "subject": "{{nome_cantina}} è su {{nome_sito}}: attivate il vostro accesso",
        "body": (
            "Buongiorno,\n\n"
            "{{nome_sito}} è il nuovo portale dei vini e delle cantine del Molise: un catalogo dei vini, "
            "una mappa delle cantine e un calendario degli eventi, con le richieste dei visitatori che arrivano "
            "direttamente a voi, senza intermediari.\n\n"
            "Abbiamo già preparato la pagina di {{nome_cantina}} con i vostri vini, usando le schede tecniche "
            "e le foto delle bottiglie che pubblicate sul vostro sito. Attivando l'accesso, gratuito, ci "
            "autorizzate a pubblicarle e potete completare la pagina quando volete: storia, foto e logo, schede "
            "dei vini (anche caricando i PDF delle schede tecniche), eventi e degustazioni. Ogni testo o foto "
            "si può sostituire o togliere in qualsiasi momento; se preferite che non pubblichiamo i vostri "
            "contenuti, basta rispondere a questa email.\n\n"
            "[[Scegliete la password e accedete|{{link_attivazione}}]]\n\n"
            "Il vostro accesso sarà {{email}}. Il link è personale e vale {{giorni_validita}} giorni: "
            "se scade, rispondete a questa email e ve ne mandiamo un altro.\n\n"
            "[[Guarda la pagina della cantina|{{link_pagina_cantina}}]]\n\n"
            "Un saluto,\nil team di {{nome_sito}}"
        ),
    },
    "recupero_password": {
        "label": "Recupero password",
        "description": "A chi chiede di reimpostare la password dalla pagina di accesso.",
        "recipient": "Utente (email di accesso)",
        "variables": ["email", "link_reimposta", "minuti_validita"],
        "subject": "Reimposta la password di {{nome_sito}}",
        "body": (
            "Ciao,\n\n"
            "abbiamo ricevuto una richiesta per reimpostare la password dell'account {{email}}.\n\n"
            "[[Scegli una nuova password|{{link_reimposta}}]]\n\n"
            "Il link è valido per {{minuti_validita}} minuti e si può usare una sola volta.\n\n"
            "Se non hai chiesto tu il cambio password puoi ignorare questa email: la password attuale resta valida."
        ),
    },
    "password_modificata": {
        "label": "Password modificata",
        "description": "Avviso di sicurezza dopo che la password è stata reimpostata.",
        "recipient": "Utente (email di accesso)",
        "variables": ["email", "data", "link_accesso"],
        "subject": "La password di {{nome_sito}} è stata modificata",
        "body": (
            "Ciao,\n\n"
            "la password dell'account {{email}} è stata modificata il {{data}}.\n\n"
            "[[Accedi|{{link_accesso}}]]\n\n"
            "Se non sei stato tu, contattaci subito rispondendo a questa email."
        ),
    },
    "richiesta_cancellazione_admin": {
        "label": "Richiesta di cancellazione",
        "description": "All'amministratore, quando una cantina chiede di cancellare il proprio account.",
        "recipient": "Amministratore (indirizzi delle notifiche)",
        "variables": ["nome_cantina", "email", "motivo", "data", "link_approvazione"],
        "subject": "Richiesta di cancellazione: {{nome_cantina}}",
        "body": (
            "La cantina {{nome_cantina}} ({{email}}) ha chiesto la cancellazione del proprio account e dei dati.\n\n"
            "Motivo indicato: {{motivo}}\nData: {{data}}\n\n"
            "[[Gestisci la cantina|{{link_approvazione}}]]"
        ),
    },
    "nuovo_evento_admin": {
        "label": "Nuovo evento di una cantina",
        "description": "All'amministratore, quando una cantina pubblica un evento (è già visibile: puoi nasconderlo).",
        "recipient": "Amministratore (indirizzi delle notifiche)",
        "variables": ["nome_cantina", "titolo_evento", "data_evento", "link_evento", "link_gestione_eventi"],
        "subject": "Nuovo evento: {{titolo_evento}} ({{nome_cantina}})",
        "body": (
            "Ciao,\n\n"
            "{{nome_cantina}} ha pubblicato un nuovo evento su {{nome_sito}}.\n\n"
            "Evento: {{titolo_evento}}\nData: {{data_evento}}\n\n"
            "L'evento è già visibile sul sito. Se non è adatto puoi nasconderlo dall'area riservata.\n\n"
            "[[Guarda l'evento|{{link_evento}}]]\n\n"
            "[[Gestisci gli eventi|{{link_gestione_eventi}}]]"
        ),
    },
    "nuova_prenotazione_evento": {
        "label": "Nuova richiesta di prenotazione",
        "description": "All'organizzatore (cantina, contatto dell'evento o amministratore) quando un visitatore chiede di partecipare.",
        "recipient": "Organizzatore dell'evento",
        "variables": ["nome_organizzatore", "titolo_evento", "data_evento", "persone", "nome_cliente",
                      "email_cliente", "telefono_cliente", "messaggio", "link_richieste"],
        "subject": "Richiesta di prenotazione: {{titolo_evento}} ({{persone}} persone)",
        "body": (
            "Ciao {{nome_organizzatore}},\n\n"
            "hai ricevuto una richiesta di prenotazione tramite {{nome_sito}}.\n\n"
            "Evento: {{titolo_evento}}\nData: {{data_evento}}\nPersone: {{persone}}\n\n"
            "Da: {{nome_cliente}} ({{email_cliente}})\nTelefono: {{telefono_cliente}}\n\n"
            "Note:\n{{messaggio}}\n\n"
            "La prenotazione non è ancora confermata: rispondi direttamente a {{email_cliente}} per confermarla.\n\n"
            "[[Apri le richieste nell'area riservata|{{link_richieste}}]]"
        ),
    },
    "conferma_prenotazione_evento": {
        "label": "Richiesta di prenotazione ricevuta",
        "description": "Al visitatore, dopo aver chiesto di partecipare a un evento.",
        "recipient": "Visitatore (email inserita nel modulo)",
        "variables": ["nome_cliente", "nome_organizzatore", "titolo_evento", "data_evento", "persone", "link_evento"],
        "subject": "Abbiamo inoltrato la tua richiesta per {{titolo_evento}}",
        "body": (
            "Ciao {{nome_cliente}},\n\n"
            "abbiamo inoltrato a {{nome_organizzatore}} la tua richiesta di partecipare a {{titolo_evento}}.\n\n"
            "Data: {{data_evento}}\nPersone: {{persone}}\n\n"
            "La prenotazione non è ancora confermata: l'organizzatore ti risponderà al tuo indirizzo email.\n\n"
            "[[Rivedi l'evento|{{link_evento}}]]\n\n"
            "A presto,\nil team di {{nome_sito}}"
        ),
    },
    "evento_annullato": {
        "label": "Evento annullato",
        "description": "A chi aveva chiesto di partecipare, quando l'organizzatore annulla l'evento.",
        "recipient": "Visitatori che avevano inviato una richiesta",
        "variables": ["nome_cliente", "nome_organizzatore", "titolo_evento", "data_evento", "motivo", "link_eventi"],
        "subject": "Evento annullato: {{titolo_evento}}",
        "body": (
            "Ciao {{nome_cliente}},\n\n"
            "ci dispiace: {{nome_organizzatore}} ha annullato l'evento {{titolo_evento}} ({{data_evento}}), "
            "per cui avevi inviato una richiesta di partecipazione.\n\n"
            "Motivo: {{motivo}}\n\n"
            "[[Scopri gli altri eventi in programma|{{link_eventi}}]]\n\n"
            "Il team di {{nome_sito}}"
        ),
    },
}

COMMON_VARIABLES = ["nome_sito", "link_sito", "anno"]

# Dati di esempio per anteprime e invii di prova
SAMPLE_CONTEXT: Dict[str, str] = {
    "nome_cantina": "Cantina Colle dei Venti",
    "email": "info@cantina-esempio.it",
    "data": "5 ottobre 2026, 15:30",
    "nome_cliente": "Maria Rossi",
    "email_cliente": "maria.rossi@esempio.it",
    "telefono_cliente": "333 123 4567",
    "tipo_richiesta": "Informazioni su prezzi e listino",
    "nome_vino": "Tintilia del Molise DOC 2022",
    "messaggio": "Buongiorno, vorrei sapere se il vino è disponibile in cartoni da 6 bottiglie e se spedite in Lombardia.",
    "motivo": "Non produciamo più vino in bottiglia.",
    "minuti_validita": "60",
    "giorni_validita": "14",
    "titolo_evento": "Degustazione in vigna al tramonto",
    "data_evento": "sabato 18 ottobre 2026, ore 18:00–21:00",
    "persone": "4",
    "nome_organizzatore": "Cantina Colle dei Venti",
}

INQUIRY_TYPES = {
    "INFO_PREZZI": "Informazioni su prezzi e listino",
    "DISPONIBILITA": "Disponibilità e acquisto",
    "VISITA_CANTINA": "Visita in cantina e degustazione",
    "EVENTO": "Prenotazione a un evento",
    "ALTRO": "Altro",
}

DEFAULT_EMAIL_SETTINGS: Dict[str, Any] = {
    "sender_name": SITE_NAME,
    "sender_email": "",          # vuoto = l'utente SMTP del .env
    "reply_to": "",
    "admin_recipients": [],      # vuoto = le email degli amministratori
    "footer_text": "Hai ricevuto questa email da EnotecaMolise, il portale dei vini e delle cantine del Molise.",
}

# ---------------------------------------------------------------------------
# Impaginazione
# ---------------------------------------------------------------------------

_VAR_RE = re.compile(r"\{\{\s*([a-z0-9_]+)\s*\}\}")
_BUTTON_RE = re.compile(r"^\[\[(.+?)\|(.+?)\]\]$")


def site_url(path: str = "") -> str:
    return settings.SITE_URL.rstrip("/") + path


def base_context() -> Dict[str, str]:
    return {"nome_sito": SITE_NAME, "link_sito": site_url("/"), "anno": str(datetime.utcnow().year)}


def sample_context() -> Dict[str, str]:
    ctx = base_context()
    ctx.update(SAMPLE_CONTEXT)
    ctx.update({
        "link_area_riservata": site_url("/dashboard"),
        "link_approvazione": site_url("/dashboard/cantine?stato=PENDING_APPROVAL"),
        "link_pagina_cantina": site_url("/produttori/cantina-colle-dei-venti"),
        "link_richieste": site_url("/dashboard/messaggi"),
        "link_reimposta": site_url("/reimposta-password?token=esempio"),
        "link_attivazione": site_url("/attiva-account?token=esempio"),
        "link_accesso": site_url("/login"),
        "link_evento": site_url("/eventi/degustazione-in-vigna-al-tramonto"),
        "link_eventi": site_url("/eventi"),
        "link_gestione_eventi": site_url("/dashboard/eventi"),
    })
    return ctx


def fill(text: str, ctx: Dict[str, Any], escape: bool = False) -> str:
    """Sostituisce le {{variabili}}; quelle sconosciute o vuote diventano un trattino o spariscono."""
    def repl(m):
        value = ctx.get(m.group(1))
        value = "" if value is None else str(value)
        return html.escape(value) if escape else value
    return _VAR_RE.sub(repl, text or "")


def render_text(body: str, ctx: Dict[str, Any]) -> str:
    out = []
    for line in fill(body, ctx).split("\n"):
        m = _BUTTON_RE.match(line.strip())
        out.append(f"{m.group(1)}: {m.group(2)}" if m else line)
    return "\n".join(out).strip() + "\n"


def render_html(subject: str, body: str, ctx: Dict[str, Any], footer: str = "") -> str:
    blocks = re.split(r"\n\s*\n", (body or "").strip())
    parts: List[str] = []
    for block in blocks:
        m = _BUTTON_RE.match(block.strip())
        if m:
            label, href = fill(m.group(1), ctx, escape=True), fill(m.group(2), ctx, escape=True)
            parts.append(
                '<table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 22px"><tr>'
                f'<td style="background:#6B1F2E;border-radius:10px"><a href="{href}" '
                'style="display:inline-block;padding:13px 24px;color:#ffffff;font-weight:700;font-size:15px;'
                f'text-decoration:none;font-family:Arial,Helvetica,sans-serif">{label}</a></td></tr></table>'
            )
            continue
        text = "<br>".join(fill(line, ctx, escape=True) for line in block.split("\n"))
        parts.append(f'<p style="margin:0 0 16px;line-height:1.6">{text}</p>')
    title = html.escape(subject)
    foot = html.escape(fill(footer, ctx))
    home = html.escape(ctx.get("link_sito", site_url("/")))
    return f"""<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title></head>
<body style="margin:0;padding:0;background:#F6F1EA">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F6F1EA;padding:28px 12px">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px">
<tr><td style="padding:0 6px 18px;font-family:Georgia,'Times New Roman',serif;font-size:26px;color:#1F1A17">
<a href="{home}" style="color:#1F1A17;text-decoration:none">Enoteca<span style="color:#6B1F2E">Molise</span></a>
<div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;letter-spacing:2px;color:#8A6D3B;text-transform:uppercase;margin-top:2px">I vini del Molise</div>
</td></tr>
<tr><td style="background:#ffffff;border:1px solid #ECE4DA;border-radius:16px;padding:30px 28px;font-family:Arial,Helvetica,sans-serif;font-size:15px;color:#1F1A17">
{''.join(parts)}
</td></tr>
<tr><td style="padding:18px 8px;font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#6E625A;line-height:1.5">{foot}</td></tr>
</table></td></tr></table></body></html>"""


# ---------------------------------------------------------------------------
# Accesso ai dati
# ---------------------------------------------------------------------------

async def get_email_settings(db) -> Dict[str, Any]:
    doc = await db.site_settings.find_one({"_id": "email"}) or {}
    merged = dict(DEFAULT_EMAIL_SETTINGS)
    merged.update({k: v for k, v in doc.items() if k in DEFAULT_EMAIL_SETTINGS and v is not None})
    return merged


async def admin_recipients(db) -> List[str]:
    cfg = await get_email_settings(db)
    recipients = [e for e in (cfg.get("admin_recipients") or []) if e]
    if recipients:
        return recipients
    admins = await db.users.find({"role": "ADMIN", "is_active": {"$ne": False}}, {"email": 1}).to_list(20)
    return [a["email"] for a in admins if a.get("email")]


async def get_template(db, key: str) -> Dict[str, Any]:
    if key not in DEFAULT_TEMPLATES:
        raise KeyError(key)
    base = DEFAULT_TEMPLATES[key]
    custom = await db.email_templates.find_one({"key": key}) or {}
    return {
        "key": key,
        "label": base["label"],
        "description": base["description"],
        "recipient": base["recipient"],
        "variables": base["variables"] + COMMON_VARIABLES,
        "subject": custom.get("subject") or base["subject"],
        "body": custom.get("body") or base["body"],
        "enabled": custom.get("enabled", True),
        "customized": bool(custom.get("subject") or custom.get("body")),
        "default_subject": base["subject"],
        "default_body": base["body"],
        "updated_at": custom.get("updated_at"),
    }


def email_mode() -> str:
    mode = (settings.EMAIL_MODE or "outbox").strip().lower()
    if mode == "smtp" and not settings.SMTP_HOST:
        return "outbox"  # SMTP richiesto ma non configurato: meglio non perdere le email
    return "smtp" if mode == "smtp" else "outbox"


# ---------------------------------------------------------------------------
# Invio
# ---------------------------------------------------------------------------

def _smtp_send(message: EmailMessage) -> None:
    security = (settings.SMTP_SECURITY or "starttls").lower()
    timeout = settings.SMTP_TIMEOUT_SECONDS
    if security == "ssl":
        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout,
                                  context=ssl.create_default_context())
    else:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout)
    try:
        if security == "starttls":
            server.starttls(context=ssl.create_default_context())
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
        server.send_message(message)
    finally:
        try:
            server.quit()
        except Exception:
            pass


async def deliver(db, *, to: Iterable[str], subject: str, html_body: str, text_body: str,
                  template: str = "", related: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Registra l'email nella posta in uscita e, in modalita' SMTP, la spedisce.
    Non solleva mai eccezioni: un problema di posta non deve bloccare registrazioni o richieste."""
    recipients = [t.strip() for t in to if t and t.strip()]
    mode = email_mode()
    cfg = await get_email_settings(db)
    doc = {
        "template": template,
        "to": recipients,
        "subject": subject,
        "html": html_body,
        "text": text_body,
        "mode": mode,
        "status": "outbox",
        "error": "",
        "related": related or {},
        "created_at": datetime.utcnow(),
        "sent_at": None,
    }
    if not recipients:
        doc["status"] = "error"
        doc["error"] = "Nessun destinatario"
    elif mode == "smtp":
        sender_email = cfg.get("sender_email") or settings.SMTP_USER or ""
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = formataddr((cfg.get("sender_name") or SITE_NAME, sender_email))
        message["To"] = ", ".join(recipients)
        if cfg.get("reply_to"):
            message["Reply-To"] = cfg["reply_to"]
        message["Message-ID"] = make_msgid(domain=(sender_email.split("@")[-1] or None))
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")
        try:
            await asyncio.to_thread(_smtp_send, message)
            doc["status"] = "sent"
            doc["sent_at"] = datetime.utcnow()
        except Exception as e:  # rete, credenziali, destinatario rifiutato...
            logger.warning("Invio email '%s' non riuscito: %s", template, e)
            doc["status"] = "error"
            doc["error"] = f"{e.__class__.__name__}: {str(e)[:300]}"
    try:
        res = await db.email_outbox.insert_one(doc)
        doc["id"] = str(res.inserted_id)
    except Exception as e:
        logger.error("Impossibile registrare l'email '%s': %s", template, e)
    return doc


async def send_template(db, key: str, to: Iterable[str], context: Optional[Dict[str, Any]] = None,
                        related: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Compone e invia (o salva) l'email del modello indicato. Restituisce None se il modello e' disattivato."""
    try:
        tpl = await get_template(db, key)
        if not tpl["enabled"]:
            return None
        cfg = await get_email_settings(db)
        ctx = base_context()
        ctx.update({k: ("" if v is None else v) for k, v in (context or {}).items()})
        subject = fill(tpl["subject"], ctx).strip()
        return await deliver(
            db, to=to, subject=subject,
            html_body=render_html(subject, tpl["body"], ctx, cfg.get("footer_text", "")),
            text_body=render_text(tpl["body"], ctx) + ("\n--\n" + fill(cfg.get("footer_text", ""), ctx) if cfg.get("footer_text") else ""),
            template=key, related=related,
        )
    except Exception as e:
        logger.error("Email '%s' non composta: %s", key, e)
        return None


def format_date(dt: Optional[datetime] = None) -> str:
    dt = dt or datetime.utcnow()
    months = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
              "settembre", "ottobre", "novembre", "dicembre"]
    return f"{dt.day} {months[dt.month - 1]} {dt.year}, {dt.strftime('%H:%M')} (UTC)"
