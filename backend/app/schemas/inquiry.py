from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class InquiryCreate(BaseModel):
    producer_id: str
    product_id: Optional[str] = None
    user_name: str
    user_email: EmailStr
    user_phone: Optional[str] = ""
    message_type: str = "INFO_PREZZI" # INFO_PREZZI, DISPONIBILITA, VISITA_CANTINA, ALTRO
    message: str

class InquiryResponse(InquiryCreate):
    id: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    producer_name: Optional[str] = None
    product_name: Optional[str] = None
