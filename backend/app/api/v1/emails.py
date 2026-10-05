"""Gestione delle email dall'area admin: modelli, impostazioni, posta in uscita."""
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.api.v1.auth import get_current_admin
from app.core.config import settings
from app.db.mongodb import get_database
from app.services import email as mail

router = APIRouter()


class TemplateUpdate(BaseModel):
    subject: Optional[str] = Field(default=None, max_length=300)
    body: Optional[str] = Field(default=None, max_length=20000)
    enabled: Optional[bool] = None


class TemplatePreview(BaseModel):
    subject: str = Field(max_length=300)
    body: str = Field(max_length=20000)


class TestSend(BaseModel):
    to: Optional[EmailStr] = None


class EmailSettingsUpdate(BaseModel):
    sender_name: Optional[str] = Field(default=None, max_length=120)
    sender_email: Optional[str] = Field(default=None, max_length=200)
    reply_to: Optional[str] = Field(default=None, max_length=200)
    admin_recipients: Optional[List[EmailStr]] = Field(default=None, max_length=10)
    footer_text: Optional[str] = Field(default=None, max_length=1000)


def _check_key(key: str):
    if key not in mail.DEFAULT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Modello email non trovato")


@router.get("/status")
async def email_status(current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    """Come vengono gestite le email ora (per il riquadro informativo dell'area admin)."""
    mode = mail.email_mode()
    return {
        "mode": mode,
        "requested_mode": (settings.EMAIL_MODE or "outbox").lower(),
        "smtp_configured": bool(settings.SMTP_HOST),
        "smtp_host": settings.SMTP_HOST or "",
        "site_url": settings.SITE_URL,
        "outbox_count": await db.email_outbox.count_documents({}),
        "errors_count": await db.email_outbox.count_documents({"status": "error"}),
    }


@router.get("/templates")
async def list_templates(current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    return [await mail.get_template(db, key) for key in mail.DEFAULT_TEMPLATES]


@router.put("/templates/{key}")
async def update_template(key: str, payload: TemplateUpdate,
                          current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    _check_key(key)
    update = {"key": key, "updated_at": datetime.utcnow()}
    if payload.subject is not None:
        if not payload.subject.strip():
            raise HTTPException(status_code=400, detail="L'oggetto non può essere vuoto")
        update["subject"] = payload.subject.strip()
    if payload.body is not None:
        if not payload.body.strip():
            raise HTTPException(status_code=400, detail="Il testo non può essere vuoto")
        update["body"] = payload.body.strip()
    if payload.enabled is not None:
        update["enabled"] = payload.enabled
    await db.email_templates.update_one({"key": key}, {"$set": update}, upsert=True)
    return await mail.get_template(db, key)


@router.post("/templates/{key}/reset")
async def reset_template(key: str, current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    """Torna al testo predefinito (resta valida l'eventuale disattivazione)."""
    _check_key(key)
    await db.email_templates.update_one({"key": key}, {"$unset": {"subject": "", "body": ""}})
    return await mail.get_template(db, key)


@router.post("/templates/{key}/preview")
async def preview_template(key: str, payload: TemplatePreview,
                           current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    _check_key(key)
    cfg = await mail.get_email_settings(db)
    ctx = mail.sample_context()
    subject = mail.fill(payload.subject, ctx).strip()
    return {
        "subject": subject,
        "html": mail.render_html(subject, payload.body, ctx, cfg.get("footer_text", "")),
        "text": mail.render_text(payload.body, ctx),
    }


@router.post("/templates/{key}/test")
async def send_test(key: str, payload: TestSend,
                    current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    """Invia (o salva nella posta in uscita) il modello con dati di esempio."""
    _check_key(key)
    tpl = await mail.get_template(db, key)
    cfg = await mail.get_email_settings(db)
    ctx = mail.sample_context()
    subject = "[PROVA] " + mail.fill(tpl["subject"], ctx).strip()
    to = [payload.to] if payload.to else [current_admin["email"]]
    doc = await mail.deliver(
        db, to=to, subject=subject,
        html_body=mail.render_html(subject, tpl["body"], ctx, cfg.get("footer_text", "")),
        text_body=mail.render_text(tpl["body"], ctx), template=key, related={"test": True},
    )
    return {"status": doc["status"], "mode": doc["mode"], "error": doc.get("error", ""), "to": to}


@router.get("/settings")
async def read_settings(current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    cfg = await mail.get_email_settings(db)
    cfg["effective_admin_recipients"] = await mail.admin_recipients(db)
    return cfg


@router.put("/settings")
async def update_settings(payload: EmailSettingsUpdate,
                          current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "admin_recipients" in update:
        update["admin_recipients"] = list(dict.fromkeys(str(e).lower() for e in update["admin_recipients"]))
    update["updated_at"] = datetime.utcnow()
    await db.site_settings.update_one({"_id": "email"}, {"$set": update}, upsert=True)
    return await read_settings(current_admin, db)


@router.get("/outbox")
async def list_outbox(limit: int = 100, status: Optional[str] = None, template: Optional[str] = None,
                      current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    query = {}
    if status:
        query["status"] = status
    if template:
        query["template"] = template
    cursor = db.email_outbox.find(query, {"html": 0, "text": 0}).sort("created_at", -1).limit(max(1, min(limit, 500)))
    items = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)
    return items


@router.get("/outbox/{email_id}")
async def read_outbox_email(email_id: str, current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    if not ObjectId.is_valid(email_id):
        raise HTTPException(status_code=400, detail="ID non valido")
    doc = await db.email_outbox.find_one({"_id": ObjectId(email_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Email non trovata")
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.delete("/outbox")
async def clear_outbox(current_admin: dict = Depends(get_current_admin), db=Depends(get_database)):
    res = await db.email_outbox.delete_many({})
    return {"deleted": res.deleted_count}
