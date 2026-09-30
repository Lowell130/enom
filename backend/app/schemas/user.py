from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    role: str = "PRODUCER" # "ADMIN" or "PRODUCER"
    producer_id: Optional[str] = None
    is_active: bool = True

class UserCreate(BaseModel):
    """Registrazione pubblica: crea sempre un account PRODUCER.
    Eventuali campi extra inviati dal client (es. "role") vengono ignorati."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_name: Optional[str] = Field(default=None, max_length=150)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
