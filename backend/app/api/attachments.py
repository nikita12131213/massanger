import imghdr
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.config import get_settings
from app.db.session import get_db
from app.schemas.common import AttachmentOut

router = APIRouter(prefix="/attachments", tags=["attachments"])
settings = get_settings()


@router.post("", response_model=AttachmentOut)
async def upload_attachment(file: UploadFile = File(...), _: object = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    content = await file.read()
    if len(content) > settings.max_image_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")
    image_type = imghdr.what(None, h=content)
    if image_type not in {"png", "jpeg", "webp"}:
        raise HTTPException(status_code=400, detail="Only png/jpeg/webp allowed")

    media_dir = Path(settings.media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)
    ext = "jpg" if image_type == "jpeg" else image_type
    name = f"{uuid4().hex}.{ext}"
    path = media_dir / name
    path.write_bytes(content)
    return AttachmentOut(id=0, url=f"{settings.media_url}/{name}", kind="image", mime=file.content_type or "image/*", size=len(content))
