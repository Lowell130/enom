from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.core.config import settings
from app.api.v1.auth import get_current_user
import os
import uuid
from PIL import Image, ImageOps, UnidentifiedImageError
import io
import logging
import math

router = APIRouter()
logger = logging.getLogger(__name__)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# SVG escluso: puo' contenere script ed essere usato per attacchi XSS.
ALLOWED_IMAGE_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".avif", ".ico"}

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_DOC_SIZE_BYTES = 15 * 1024 * 1024   # 15MB
MAX_IMAGE_PIXELS = 40_000_000           # protezione da "decompression bomb"
MAX_IMAGE_SIDE = 2400                   # lato lungo massimo dopo il ridimensionamento
MAX_FULL_DECODE_PIXELS = 16_000_000     # formati non JPEG (decodificati per intero): ~64 MB in memoria


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
        if image.format != "JPEG" and image.width * image.height > MAX_FULL_DECODE_PIXELS:
            # PNG e simili vanno decodificati per intero: oltre questa soglia la memoria del server non basta
            raise HTTPException(
                status_code=400,
                detail=f"Immagine troppo grande ({image.width}×{image.height} pixel): riducila a meno di 4000 pixel sul lato lungo o salvala in JPG e riprova",
            )
        if image.format == "JPEG" and max(image.size) > MAX_IMAGE_SIDE:
            # i JPEG grandi si decodificano gia' ridotti (1/2, 1/4, 1/8): molta meno memoria
            ratio = MAX_IMAGE_SIDE / max(image.size)
            image.draft("RGB", (math.ceil(image.width * ratio), math.ceil(image.height * ratio)))
        image.load()
        image = _normalize_image(image)
        buffer = io.BytesIO()
        image.save(buffer, "WEBP", quality=85, method=4)
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail="Il file non è un'immagine valida o il formato non è supportato")
    except Exception:
        logger.exception("Conversione immagine non riuscita (%s)", file.filename)
        raise HTTPException(status_code=400, detail="Non è stato possibile elaborare l'immagine: prova a salvarla in PNG o JPG e ricaricala")

    filename = f"{uuid.uuid4().hex}.webp"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(buffer.getvalue())
    return {"url": f"/uploads/{filename}", "filename": filename}


def _normalize_image(image: Image.Image) -> Image.Image:
    """Prepara l'immagine per il WebP: orientamento corretto, colori in RGB/RGBA,
    lato lungo entro MAX_IMAGE_SIDE (il WebP non accetta oltre 16383 px e il sito
    non mostra mai immagini piu' grandi)."""
    if image.getexif().get(0x0112, 1) != 1:  # ruota solo se la foto lo chiede (evita una copia)
        image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "RGBA"):
        has_alpha = image.mode in ("P", "PA", "LA", "La", "RGBa") or "transparency" in image.info
        image = image.convert("RGBA" if has_alpha else "RGB")
    if max(image.size) > MAX_IMAGE_SIDE:
        image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.LANCZOS)
    return image


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
