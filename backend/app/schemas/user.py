from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    role: str = "PRODUCER" # "ADMIN" or "PRODUCER"
    producer_id: Optional[str] = None
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "PRODUCER"
    producer_id: Optional[str] = None
    company_name: Optional[str] = None # Quick setup for producer profile

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
