from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class AddressSchema(BaseModel):
    street: Optional[str] = ""
    city: Optional[str] = "Campobasso"
    province: Optional[str] = "CB"
    zip_code: Optional[str] = ""
    geo_coordinates: Optional[Dict[str, Any]] = None

    @field_validator("geo_coordinates", mode="before")
    @classmethod
    def parse_geo_coordinates(cls, v):
        if not v or not isinstance(v, dict):
            return v
        cleaned = {}
        for key in ["lat", "lng"]:
            if key in v:
                val = v[key]
                if isinstance(val, (int, float)):
                    cleaned[key] = float(val)
                elif isinstance(val, str) and val.strip():
                    try:
                        cleaned[key] = float(val.replace(",", ".").strip())
                    except ValueError:
                        pass
        return cleaned if cleaned else None

class ContactsSchema(BaseModel):
    phone: Optional[str] = ""
    email_contact: Optional[str] = ""
    whatsapp_number: Optional[str] = ""
    website: Optional[str] = ""
    instagram: Optional[str] = ""
    facebook: Optional[str] = ""

class ProducerBase(BaseModel):
    company_name: str
    slug: Optional[str] = None
    logo_url: Optional[str] = ""
    cover_image_url: Optional[str] = ""
    description: Optional[str] = ""
    address: Optional[AddressSchema] = Field(default_factory=AddressSchema)
    contacts: Optional[ContactsSchema] = Field(default_factory=ContactsSchema)
    status: str = "APPROVED" # "APPROVED", "PENDING_APPROVAL", "SUSPENDED"

class ProducerCreate(ProducerBase):
    pass

class ProducerUpdate(BaseModel):
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    description: Optional[str] = None
    address: Optional[AddressSchema] = None
    contacts: Optional[ContactsSchema] = None
    status: Optional[str] = None

class ProducerResponse(ProducerBase):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    product_count: Optional[int] = 0
