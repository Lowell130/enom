from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict

PRODUCT_STATUSES = {"PUBLISHED", "DRAFT"}


def _validate_status(v):
    if v is None:
        return v
    v = str(v).strip().upper()
    if v not in PRODUCT_STATUSES:
        raise ValueError(f"Stato non valido: usa uno tra {sorted(PRODUCT_STATUSES)}")
    return v
from datetime import datetime

from app.services.insights import normalize_price_text, normalize_temperature_text, split_grape_list

class TastingNotesSchema(BaseModel):
    visual: Optional[str] = ""
    olfactory: Optional[str] = ""
    taste: Optional[str] = ""

class CustomAttributeSchema(BaseModel):
    name: str
    value: str

class ProductBase(BaseModel):
    name: str
    slug: Optional[str] = None
    category: str = "VINO_ROSSO"
    denominazione: str = "DOC"
    vintage_year: Optional[int] = 2023
    is_riserva: Optional[bool] = False
    alcohol_degrees: Optional[float] = 13.5
    grape_varieties: List[str] = Field(default_factory=list)
    description: Optional[str] = ""
    tasting_notes: Optional[TastingNotesSchema] = Field(default_factory=TastingNotesSchema)
    food_pairings: List[str] = Field(default_factory=list)
    serving_temperature: Optional[str] = "16-18°C"
    indicative_price: Optional[str] = ""
    photos: List[str] = Field(default_factory=list)
    technical_sheet_pdf: Optional[str] = ""
    custom_attributes: List[CustomAttributeSchema] = Field(default_factory=list)
    status: str = "PUBLISHED"

    @field_validator('vintage_year', mode='before')
    def clean_vintage_year(cls, v):
        if v == "" or v is None or v == "null":
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    @field_validator('alcohol_degrees', mode='before')
    def clean_alcohol_degrees(cls, v):
        if v == "" or v is None or v == "null":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    @field_validator('indicative_price', mode='before')
    def clean_indicative_price(cls, v):
        # stesso formato per tutto il catalogo: "17,00 €", "35,00 – 55,00 €"
        return normalize_price_text(v) if v is not None else v

    @field_validator('grape_varieties', mode='before')
    def split_grape_varieties(cls, v):
        # "Montepulciano 55% Sangiovese 45%" in una sola voce -> due vitigni
        return split_grape_list(v)

    @field_validator('serving_temperature', mode='before')
    def clean_serving_temperature(cls, v):
        # "16 - 18°", "18°" -> "16-18°C", "18°C"
        return normalize_temperature_text(v)

class ProductCreate(ProductBase):
    producer_id: Optional[str] = None

    @field_validator('status', mode='before')
    def check_status(cls, v):
        return _validate_status(v) or "PUBLISHED"

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    producer_id: Optional[str] = None
    category: Optional[str] = None
    denominazione: Optional[str] = None
    vintage_year: Optional[int] = None
    is_riserva: Optional[bool] = None
    alcohol_degrees: Optional[float] = None
    grape_varieties: Optional[List[str]] = None
    description: Optional[str] = None
    tasting_notes: Optional[TastingNotesSchema] = None
    food_pairings: Optional[List[str]] = None
    serving_temperature: Optional[str] = None
    indicative_price: Optional[str] = None
    photos: Optional[List[str]] = None
    technical_sheet_pdf: Optional[str] = None
    custom_attributes: Optional[List[CustomAttributeSchema]] = None
    status: Optional[str] = None

    @field_validator('status', mode='before')
    def check_status(cls, v):
        return _validate_status(v)

    @field_validator('vintage_year', mode='before')
    def clean_vintage_year(cls, v):
        if v == "" or v is None or v == "null":
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    @field_validator('alcohol_degrees', mode='before')
    def clean_alcohol_degrees(cls, v):
        if v == "" or v is None or v == "null":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    @field_validator('indicative_price', mode='before')
    def clean_indicative_price(cls, v):
        # stesso formato per tutto il catalogo: "17,00 €", "35,00 – 55,00 €"
        return normalize_price_text(v) if v is not None else v

    @field_validator('grape_varieties', mode='before')
    def split_grape_varieties(cls, v):
        # "Montepulciano 55% Sangiovese 45%" in una sola voce -> due vitigni
        return split_grape_list(v)

    @field_validator('serving_temperature', mode='before')
    def clean_serving_temperature(cls, v):
        # "16 - 18°", "18°" -> "16-18°C", "18°C"
        return normalize_temperature_text(v)

class ProductResponse(ProductBase):
    id: str
    producer_id: str
    producer_name: Optional[str] = None
    producer_slug: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
