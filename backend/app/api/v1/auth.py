from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from app.db.mongodb import get_database
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.schemas.producer import ProducerCreate
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token
from bson import ObjectId
from datetime import datetime
from typing import Optional
import re

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

async def get_current_user(
    token_bearer: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
    db=Depends(get_database)
):
    token = token_bearer
    if not token and authorization:
        if authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
        else:
            token = authorization
            
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header di autenticazione mancante (Bearer Token)",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido o scaduto",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_id = payload.get("sub")
    if not user_id or not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token payload non valido")
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")
    
    user["id"] = str(user["_id"])
    if user.get("producer_id"):
        user["producer_id"] = str(user["producer_id"])
    return user

async def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso riservato all'Amministratore"
        )
    return current_user

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db=Depends(get_database)):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    hashed_pwd = get_password_hash(user_data.password)
    
    producer_id = None
    if user_data.role == "PRODUCER":
        company_name = user_data.company_name or f"Cantine {user_data.email.split('@')[0].capitalize()}"
        slug = slugify(company_name)
        
        slug_count = await db.producers.count_documents({"slug": slug})
        if slug_count > 0:
            slug = f"{slug}-{slug_count + 1}"
            
        producer_doc = {
            "company_name": company_name,
            "slug": slug,
            "logo_url": "",
            "cover_image_url": "",
            "description": f"Benvenuti a {company_name}.",
            "address": {"street": "", "city": "Campobasso", "province": "CB", "zip_code": ""},
            "contacts": {"email_contact": user_data.email, "phone": "", "whatsapp_number": ""},
            "status": "APPROVED",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        res_prod = await db.producers.insert_one(producer_doc)
        producer_id = res_prod.inserted_id

    user_doc = {
        "email": user_data.email,
        "password_hash": hashed_pwd,
        "role": user_data.role,
        "producer_id": producer_id,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    res = await db.users.insert_one(user_doc)
    user_doc["id"] = str(res.inserted_id)
    if producer_id:
        user_doc["producer_id"] = str(producer_id)
        
    return user_doc

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db=Depends(get_database)):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Credenziali non valide")
    
    producer_id_str = str(user.get("producer_id")) if user.get("producer_id") else None
    token = create_access_token(
        subject=str(user["_id"]),
        role=user.get("role", "PRODUCER"),
        producer_id=producer_id_str
    )
    
    user["id"] = str(user["_id"])
    user["producer_id"] = producer_id_str
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me")
async def read_current_user(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    result = {
        "id": current_user["id"],
        "email": current_user["email"],
        "role": current_user["role"],
        "producer_id": current_user.get("producer_id"),
        "is_active": current_user.get("is_active", True)
    }
    if current_user.get("producer_id"):
        producer = await db.producers.find_one({"_id": ObjectId(current_user["producer_id"])})
        if producer:
            producer["id"] = str(producer["_id"])
            del producer["_id"]
            result["producer"] = producer
    return result
