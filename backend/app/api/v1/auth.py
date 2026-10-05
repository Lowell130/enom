from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from app.db.mongodb import get_database
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, PasswordForgot, PasswordReset
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token
from app.core.utils import slugify, unique_slug, rate_limiter, client_ip
from bson import ObjectId
from app.services import email as mail
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

router = APIRouter()
logger = logging.getLogger("enotecamolise.auth")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _extract_token(token_bearer: Optional[str], authorization: Optional[str]) -> Optional[str]:
    token = token_bearer
    if not token and authorization:
        token = authorization.split(" ", 1)[1] if authorization.startswith("Bearer ") else authorization
    return token or None


async def _load_user_from_token(token: str, db) -> Optional[dict]:
    payload = decode_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id or not ObjectId.is_valid(user_id):
        return None
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get("is_active", True):
        return None
    changed = user.get("password_changed_at")
    if changed:
        # dopo un cambio password le sessioni aperte in precedenza decadono
        issued = payload.get("iat") or 0
        if issued < int(changed.replace(tzinfo=timezone.utc).timestamp()):
            return None
    user["id"] = str(user["_id"])
    if user.get("producer_id"):
        user["producer_id"] = str(user["producer_id"])
    return user


async def get_current_user(
    token_bearer: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
    db=Depends(get_database)
):
    token = _extract_token(token_bearer, authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header di autenticazione mancante (Bearer Token)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await _load_user_from_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido, scaduto o utente disattivato",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_optional_user(
    token_bearer: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
    db=Depends(get_database)
) -> Optional[dict]:
    """Come get_current_user ma restituisce None per i visitatori anonimi."""
    token = _extract_token(token_bearer, authorization)
    if not token:
        return None
    return await _load_user_from_token(token, db)


async def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso riservato all'Amministratore"
        )
    return current_user


def is_admin(user: Optional[dict]) -> bool:
    return bool(user) and user.get("role") == "ADMIN"


def owns_producer(user: Optional[dict], producer_id) -> bool:
    return bool(user) and user.get("producer_id") is not None and str(user.get("producer_id")) == str(producer_id)


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, request: Request, db=Depends(get_database)):
    rate_limiter.check_and_hit(
        f"register:{client_ip(request)}", 5, 3600,
        "Troppe registrazioni da questo indirizzo. Riprova più tardi."
    )
    email = user_data.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")

    hashed_pwd = get_password_hash(user_data.password)

    # La registrazione pubblica crea SEMPRE un account PRODUCER: il ruolo non e' scelto dal client.
    company_name = (user_data.company_name or "").strip() or f"Cantine {email.split('@')[0].capitalize()}"
    slug = await unique_slug(db.producers, slugify(company_name) or "cantina")

    now = datetime.utcnow()
    producer_doc = {
        "company_name": company_name,
        "slug": slug,
        "logo_url": "",
        "cover_image_url": "",
        "description": f"Benvenuti a {company_name}.",
        # nessuna citta' predefinita: la cantina la indica nel profilo (altrimenti finirebbe a Campobasso sulla mappa)
        "address": {"street": "", "city": "", "province": "", "zip_code": ""},
        "contacts": {"email_contact": email, "phone": "", "whatsapp_number": ""},
        "status": "APPROVED" if settings.AUTO_APPROVE_PRODUCERS else "PENDING_APPROVAL",
        "created_at": now,
        "updated_at": now
    }
    res_prod = await db.producers.insert_one(producer_doc)
    producer_id = res_prod.inserted_id

    user_doc = {
        "email": email,
        "password_hash": hashed_pwd,
        "role": "PRODUCER",
        "producer_id": producer_id,
        "is_active": True,
        "privacy_accepted_at": now,
        "created_at": now
    }
    res = await db.users.insert_one(user_doc)
    user_doc["id"] = str(res.inserted_id)
    user_doc["producer_id"] = str(producer_id)

    # email di benvenuto alla cantina e avviso all'amministratore
    ctx = {"nome_cantina": company_name, "email": email, "data": mail.format_date(now),
           "link_area_riservata": mail.site_url("/dashboard"),
           "link_approvazione": mail.site_url("/dashboard/cantine?stato=PENDING_APPROVAL"),
           "link_pagina_cantina": mail.site_url(f"/produttori/{slug}")}
    related = {"producer_id": str(producer_id)}
    await mail.send_template(db, "registrazione_cantina", [email], ctx, related)
    if producer_doc["status"] == "APPROVED":
        await mail.send_template(db, "cantina_approvata", [email], ctx, related)
    else:
        await mail.send_template(db, "nuova_cantina_admin", await mail.admin_recipients(db), ctx, related)
    return user_doc


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, request: Request, db=Depends(get_database)):
    email = login_data.email.lower()
    key = f"login:{client_ip(request)}:{email}"
    if rate_limiter.is_limited(key, settings.LOGIN_MAX_ATTEMPTS, settings.LOGIN_WINDOW_SECONDS):
        raise HTTPException(status_code=429, detail="Troppi tentativi di accesso. Riprova tra qualche minuto.")

    user = await db.users.find_one({"email": email})
    if not user and email != login_data.email:
        user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        rate_limiter.hit(key, settings.LOGIN_WINDOW_SECONDS)
        raise HTTPException(status_code=400, detail="Credenziali non valide")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account disattivato")

    rate_limiter.reset(key)
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
    if current_user.get("producer_id") and ObjectId.is_valid(current_user["producer_id"]):
        producer = await db.producers.find_one({"_id": ObjectId(current_user["producer_id"])})
        if producer:
            producer["id"] = str(producer["_id"])
            del producer["_id"]
            result["producer"] = producer
    return result


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.post("/password/forgot")
async def forgot_password(payload: PasswordForgot, request: Request, db=Depends(get_database)):
    """Invia il link per reimpostare la password. La risposta e' sempre la stessa,
    per non rivelare quali email sono registrate."""
    email = payload.email.lower()
    rate_limiter.check_and_hit(
        f"pwforgot:{client_ip(request)}", 5, 3600,
        "Troppe richieste di recupero password. Riprova più tardi."
    )
    generic = {"message": "Se l'indirizzo è registrato, riceverai un'email con il link per reimpostare la password."}
    user = await db.users.find_one({"email": email})
    if not user or not user.get("is_active", True):
        return generic
    # al massimo 3 link per account ogni ora
    recent = await db.password_resets.count_documents({
        "user_id": user["_id"], "created_at": {"$gt": datetime.utcnow() - timedelta(hours=1)}
    })
    if recent >= 3:
        return generic
    token = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    await db.password_resets.insert_one({
        "user_id": user["_id"],
        "token_hash": _hash_reset_token(token),
        "created_at": now,
        "expires_at": now + timedelta(minutes=settings.PASSWORD_RESET_TTL_MINUTES),
        "used_at": None,
    })
    await mail.send_template(db, "recupero_password", [email], {
        "email": email,
        "link_reimposta": mail.site_url(f"/reimposta-password?token={token}"),
        "minuti_validita": str(settings.PASSWORD_RESET_TTL_MINUTES),
    }, related={"user_id": str(user["_id"])})
    return generic


@router.post("/password/reset")
async def reset_password(payload: PasswordReset, request: Request, db=Depends(get_database)):
    rate_limiter.check_and_hit(
        f"pwreset:{client_ip(request)}", 10, 3600,
        "Troppi tentativi. Riprova più tardi."
    )
    now = datetime.utcnow()
    record = await db.password_resets.find_one({"token_hash": _hash_reset_token(payload.token)})
    if not record or record.get("used_at") or record.get("expires_at", now) < now:
        raise HTTPException(status_code=400, detail="Il link non è valido o è scaduto: richiedine uno nuovo.")
    user = await db.users.find_one({"_id": record["user_id"]})
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Il link non è valido o è scaduto: richiedine uno nuovo.")

    # un secondo di margine: il token di accesso emesso subito dopo resta valido
    changed_at = (now - timedelta(seconds=1)).replace(microsecond=0)
    await db.users.update_one({"_id": user["_id"]}, {"$set": {
        "password_hash": get_password_hash(payload.password), "password_changed_at": changed_at,
    }})
    # il link usato e gli altri ancora aperti per lo stesso account non valgono piu'
    await db.password_resets.update_many({"user_id": user["_id"], "used_at": None}, {"$set": {"used_at": now}})
    await mail.send_template(db, "password_modificata", [user["email"]], {
        "email": user["email"], "data": mail.format_date(now), "link_accesso": mail.site_url("/login"),
    }, related={"user_id": str(user["_id"])})
    return {"message": "Password aggiornata: ora puoi accedere con la nuova password."}
