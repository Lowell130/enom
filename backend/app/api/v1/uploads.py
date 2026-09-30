from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.core.config import settings
from app.api.v1.auth import get_current_user
import os
import uuid
from PIL import Image, UnidentifiedImageError
import io

router = APIRouter()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# SVG escluso: puo' contenere script ed essere usato per attacchi XSS.
ALLOWED_IMAGE_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".avif", ".ico"}

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_DOC_SIZE_BYTES = 15 * 1024 * 1024   # 15MB
MAX_IMAGE_PIXELS = 40_000_000           # protezione da "decompression bomb"


async def _read_limited(file: UploadFile, limit: int, label: str) -> bytes:
    contents = await file.read(limit + 1)
    if len(contents) > limit:
        raise HTTPException(status_code=400, detail=f"{label} supera la dimensione massima consentita di {limit // (1024 * 1024)}MB")
    if not contents:
        raise HTTPException(status_code=400, detail="File vuoto")
    return contents


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    ext = os.path.splitext((file.filename or "").lower())[1]
    if ext == ".svg" or (file.content_type and "svg" in file.content_type):
        raise HTTPException(status_code=400, detail="Le immagini SVG non sono consentite: usa PNG, JPG o WebP")
    if ext and ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Il file deve essere un'immagine (PNG, JPG, WebP, GIF, AVIF)")

    contents = await _read_limited(file, MAX_IMAGE_SIZE_BYTES, "L'immagine")

    # Ogni immagine viene decodificata e ri-codificata in WebP: i file che Pillow
    # non riconosce come immagini vengono rifiutati (nessun salvataggio "grezzo").
    try:
        image = Image.open(io.BytesIO(contents))
        if image.width * image.height > MAX_IMAGE_PIXELS:
            raise HTTPException(status_code=400, detail="Immagine con risoluzione troppo elevata")
        image.load()
        if image.mode in ("P", "PA", "LA", "1", "I", "I;16", "F"):
            image = image.convert("RGBA")
        elif image.mode == "CMYK":
            image = image.convert("RGB")
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail="Il file non è un'immagine valida o il formato non è supportato")

    filename = f"{uuid.uuid4().hex}.webp"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    image.save(file_path, "WEBP", quality=85, optimize=True)
    return {"url": f"/uploads/{filename}", "filename": filename}


@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Il documento deve essere in formato PDF")

    contents = await _read_limited(file, MAX_DOC_SIZE_BYTES, "Il documento")
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Il file non è un PDF valido")

    filename = f"{uuid.uuid4().hex}.pdf"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    return {"url": f"/uploads/{filename}", "filename": filename}
