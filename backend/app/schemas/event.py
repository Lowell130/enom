"""Eventi: degustazioni, visite, cene, fiere... organizzati da una cantina o dall'amministratore
(eventi del territorio, anche con piu' cantine partecipanti).

Le date sono salvate come ora locale italiana senza fuso (il portale riguarda solo il Molise)."""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

EVENT_TYPES = {
    "DEGUSTAZIONE": "Degustazione",
    "VISITA": "Visita in cantina",
    "CENA": "Cena e abbinamenti",
    "FIERA": "Fiera e festival",
    "CORSO": "Corso",
    "VENDEMMIA": "Vendemmia",
    "ALTRO": "Altro",
}
EventType = Literal["DEGUSTAZIONE", "VISITA", "CENA", "FIERA", "CORSO", "VENDEMMIA", "ALTRO"]


class EventDate(BaseModel):
    start: datetime
    end: Optional[datetime] = None

    @model_validator(mode="after")
    def end_after_start(self):
        # niente fusi orari: e' sempre l'ora italiana
        self.start = self.start.replace(tzinfo=None, second=0, microsecond=0)
        if self.end is not None:
            self.end = self.end.replace(tzinfo=None, second=0, microsecond=0)
            if self.end < self.start:
                raise ValueError("La fine dell'evento non può essere prima dell'inizio")
        return self


class EventLocation(BaseModel):
    name: Optional[str] = Field(default="", max_length=150)      # es. "Piazza del Municipio"
    street: Optional[str] = Field(default="", max_length=200)
    city: Optional[str] = Field(default="", max_length=100)
    province: Optional[str] = Field(default="", max_length=4)
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)


class EventIn(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    type: EventType = "DEGUSTAZIONE"
    description: Optional[str] = Field(default="", max_length=8000)
    cover_image: Optional[str] = Field(default="", max_length=500)
    dates: List[EventDate] = Field(min_length=1, max_length=40)
    use_producer_address: bool = True
    location: EventLocation = Field(default_factory=EventLocation)
    producer_id: Optional[str] = None            # cantina organizzatrice (vuoto = evento del territorio)
    participant_ids: List[str] = Field(default_factory=list, max_length=60)
    product_ids: List[str] = Field(default_factory=list, max_length=30)
    price_type: Literal["FREE", "PAID"] = "FREE"
    price_text: Optional[str] = Field(default="", max_length=120)
    booking_mode: Literal["REQUEST", "EXTERNAL", "NONE"] = "REQUEST"
    external_url: Optional[str] = Field(default="", max_length=500)
    contact_email: Optional[EmailStr] = None    # eventi del territorio: chi riceve le richieste
    status: Literal["DRAFT", "PUBLISHED"] = "PUBLISHED"

    @field_validator("title")
    @classmethod
    def strip_title(cls, v):
        v = (v or "").strip()
        if len(v) < 3:
            raise ValueError("Il titolo deve avere almeno 3 caratteri")
        return v

    @field_validator("external_url")
    @classmethod
    def check_url(cls, v):
        v = (v or "").strip()
        if v and not v.lower().startswith(("http://", "https://")):
            v = "https://" + v
        return v

    @model_validator(mode="after")
    def booking_needs_link(self):
        if self.booking_mode == "EXTERNAL" and not self.external_url:
            raise ValueError("Indica il link per la prenotazione esterna")
        self.dates = sorted(self.dates, key=lambda d: d.start)
        return self


class EventRequestIn(BaseModel):
    """Richiesta di prenotazione di un visitatore (nessun pagamento: la cantina conferma rispondendo)."""
    user_name: str = Field(min_length=1, max_length=120)
    user_email: EmailStr
    user_phone: Optional[str] = Field(default="", max_length=40)
    people: int = Field(default=2, ge=1, le=50)
    date_index: int = Field(default=0, ge=0, le=39)
    message: Optional[str] = Field(default="", max_length=3000)
    privacy_accepted: bool = Field(default=False, validate_default=True)

    @field_validator("privacy_accepted")
    @classmethod
    def must_accept_privacy(cls, v):
        if not v:
            raise ValueError("Per inviare la richiesta devi accettare l'informativa sulla privacy")
        return v


class EventCancelIn(BaseModel):
    message: Optional[str] = Field(default="", max_length=2000)


class EventVisibilityIn(BaseModel):
    hidden: bool
