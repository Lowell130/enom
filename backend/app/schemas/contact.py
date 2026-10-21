"""Messaggi inviati dal modulo "Contatti" del sito (a EnotecaMolise, non a una cantina)."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

CONTACT_REASONS = {
    "CANTINA": "Sono una cantina e voglio essere sul sito",
    "SEGNALAZIONE": "Segnalare un errore o un contenuto",
    "RIMOZIONE": "Richiesta di rimozione",
    "ALTRO": "Altro",
    "RIVENDICAZIONE": "Rivendicazione di una cantina",
}
ContactReason = Literal["CANTINA", "SEGNALAZIONE", "RIMOZIONE", "ALTRO"]


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    reason: ContactReason = "ALTRO"
    message: str = Field(min_length=2, max_length=5000)
    privacy_accepted: bool = Field(default=False, validate_default=True)
    # campo trappola: invisibile alle persone, i programmi di spam lo compilano
    website: Optional[str] = Field(default="", max_length=500)

    @field_validator("name", "message")
    @classmethod
    def strip_text(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("Campo obbligatorio")
        return v

    @field_validator("privacy_accepted")
    @classmethod
    def must_accept_privacy(cls, v):
        if not v:
            raise ValueError("Per inviare il messaggio devi accettare l'informativa sulla privacy")
        return v


class ClaimRequest(BaseModel):
    """Il titolare di una cantina chiede l'accesso alla pagina (email del sito mancante o non piu' valida)."""
    producer_id: str
    name: str = Field(min_length=1, max_length=120)
    role: Optional[str] = Field(default="", max_length=80)       # titolare, socio, responsabile commerciale...
    email: EmailStr
    phone: str = Field(min_length=5, max_length=40)
    message: Optional[str] = Field(default="", max_length=2000)
    privacy_accepted: bool = Field(default=False, validate_default=True)
    website: Optional[str] = Field(default="", max_length=500)   # campo trappola

    @field_validator("name", "phone")
    @classmethod
    def strip_required(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("Campo obbligatorio")
        return v

    @field_validator("privacy_accepted")
    @classmethod
    def must_accept_privacy(cls, v):
        if not v:
            raise ValueError("Per inviare la richiesta devi accettare l'informativa sulla privacy")
        return v


class ContactMessage(BaseModel):
    id: str
    name: str
    email: str
    reason: str = "ALTRO"
    reason_label: str = ""
    message: str
    phone: str = ""
    role: str = ""
    producer_id: Optional[str] = None
    producer_name: str = ""
    producer_slug: str = ""
    producer_account: str = ""   # none / invited / expired / active (solo rivendicazioni)
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
