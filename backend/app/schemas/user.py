from pydantic import BaseModel, EmailStr, Field, field_validator
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
    privacy_accepted: bool = Field(default=False, validate_default=True)

    @field_validator("privacy_accepted")
    @classmethod
    def must_accept_privacy(cls, v):
        if not v:
            raise ValueError("Per registrarti devi accettare l'informativa sulla privacy")
        return v


class PasswordForgot(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=8, max_length=128)

class InviteAccept(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=8, max_length=128)
    privacy_accepted: bool = Field(default=False, validate_default=True)

    @field_validator("privacy_accepted")
    @classmethod
    def must_accept_privacy(cls, v):
        if not v:
            raise ValueError("Per attivare l'accesso devi accettare l'informativa sulla privacy")
        return v

    # autorizzazione a pubblicare testi, foto e schede dei vini gia' presenti sulla pagina
    content_consent: bool = Field(default=False, validate_default=True)

    @field_validator("content_consent")
    @classmethod
    def must_authorize_content(cls, v):
        if not v:
            raise ValueError("Per attivare l'accesso serve l'autorizzazione a pubblicare testi e foto della cantina")
        return v

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
