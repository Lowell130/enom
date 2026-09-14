from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.core.config import settings
from app.api.v1.auth import get_current_user
import os
import uuid
import mimetypes
from PIL import Image
import io

router = APIRouter()

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/webp", "webp")
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".bmp", ".tiff", ".avif", ".ico"}

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_DOC_SIZE_BYTES = 15 * 1024 * 1024   # 15MB

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    ext = os.path.splitext(file.filename.lower())[1] if file.filename else ""
    is_valid_type = (
        (file.content_type and (file.content_type.startswith("image/") or file.content_type == "application/octet-stream"))
        or ext in ALLOWED_IMAGE_EXTENSIONS
    )
    if not is_valid_type:
        raise HTTPException(status_code=400, detail="Il file deve essere un'immagine")
        
    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="L'immagine supera la dimensione massima consentita di 10MB")
    
    # SVG images shouldn't be parsed by PIL as raster
    if ext == ".svg" or (file.content_type and "svg" in file.content_type):
        filename = f"{uuid.uuid4().hex}.svg"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(contents)
        return {"url": f"/uploads/{filename}", "filename": filename}

    filename = f"{uuid.uuid4().hex}.webp"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    try:
        image = Image.open(io.BytesIO(contents))
        # Handle transparency & colorspace conversions correctly for WebP
        if image.mode in ("P", "PA", "LA"):
            image = image.convert("RGBA")
        elif image.mode == "CMYK":
            image = image.convert("RGB")
        # RGBA and RGB are supported natively by WEBP, preserving transparency and colors!
        
        image.save(file_path, "WEBP", quality=85, optimize=True)
    except Exception as e:
        # Fallback to direct write with original extension if PIL processing fails
        out_ext = ext if ext in ALLOWED_IMAGE_EXTENSIONS else ".webp"
        filename = f"{uuid.uuid4().hex}{out_ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(contents)
            
    return {"url": f"/uploads/{filename}", "filename": filename}

@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Il documento deve essere in formato PDF")
        
    contents = await file.read()
    if len(contents) > MAX_DOC_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Il documento supera la dimensione massima consentita di 15MB")
    filename = f"{uuid.uuid4().hex}.pdf"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as f:
        f.write(contents)
        
    return {"url": f"/uploads/{filename}", "filename": filename}
