from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Literal, Optional
from datetime import datetime

class InquiryCreate(BaseModel):
    producer_id: str
    product_id: Optional[str] = None
    user_name: str = Field(min_length=1, max_length=120)
    user_email: EmailStr
    user_phone: Optional[str] = Field(default="", max_length=40)
    message_type: Literal["INFO_PREZZI", "DISPONIBILITA", "VISITA_CANTINA", "ALTRO"] = "INFO_PREZZI"
    message: str = Field(min_length=1, max_length=5000)
    privacy_accepted: bool = Field(default=False, validate_default=True)

    @field_validator("privacy_accepted")
    @classmethod
    def must_accept_privacy(cls, v):
        if not v:
            raise ValueError("Per inviare il messaggio devi accettare l'informativa sulla privacy")
        return v

class InquiryResponse(BaseModel):
    # Campi non vincolati: i messaggi gia' salvati devono restare leggibili
    producer_id: str
    product_id: Optional[str] = None
    user_name: str
    user_email: str
    user_phone: Optional[str] = ""
    message_type: str = "INFO_PREZZI"
    message: str
    id: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    producer_name: Optional[str] = None
    product_name: Optional[str] = None
