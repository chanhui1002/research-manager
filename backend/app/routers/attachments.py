import os
import uuid
import base64
import httpx
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Attachment
from app.schemas import AttachmentResponse

router = APIRouter()

STORAGE = os.getenv("ATTACHMENT_STORAGE", "local").lower()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://afjfieukktcjxgvtawjy.supabase.co")
_key_b64 = os.getenv("SUPABASE_SERVICE_KEY_B64", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "") or (base64.b64decode(_key_b64).decode() if _key_b64 else "")
BUCKET_NAME = "attachments"

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
LOCAL_ROOT = os.path.abspath(UPLOAD_DIR)
os.makedirs(LOCAL_ROOT, exist_ok=True)

VALID_TYPES = ["paper", "book", "project", "award", "adoption", "honor", "training"]


def _storage_url(path: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{path}"


def _public_url(path: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{path}"


def _headers():
    return {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
    }


def _local_path(file_path: str) -> str:
    if file_path.startswith(UPLOAD_DIR):
        return os.path.abspath(file_path)
    return os.path.join(LOCAL_ROOT, file_path)


@router.get("/preview/{attachment_id}")
def preview_attachment(attachment_id: str, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    if STORAGE == "supabase":
        return RedirectResponse(url=_public_url(attachment.file_path))
    path = _local_path(attachment.file_path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        path=path,
        media_type=attachment.mime_type or "application/octet-stream",
        headers={"Content-Disposition": "inline"},
    )


@router.get("/download/{attachment_id}")
def download_attachment(attachment_id: str, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    if STORAGE == "supabase":
        return RedirectResponse(url=f"{_public_url(attachment.file_path)}?download={attachment.original_filename}")
    path = _local_path(attachment.file_path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        path=path,
        filename=attachment.original_filename,
        media_type=attachment.mime_type or "application/octet-stream",
    )


@router.delete("/remove/{attachment_id}", status_code=204)
def delete_attachment(attachment_id: str, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    if STORAGE == "supabase":
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.delete(
                    _storage_url(attachment.file_path),
                    headers=_headers(),
                )
                if resp.status_code not in (200, 204):
                    raise HTTPException(
                        status_code=502,
                        detail=f"删除存储文件失败 (HTTP {resp.status_code}): {resp.text[:200]}",
                    )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除存储文件出错: {e}") from e
    else:
        path = _local_path(attachment.file_path)
        if os.path.exists(path):
            os.remove(path)
    db.delete(attachment)
    db.commit()


@router.get("/{entity_type}/{entity_id}", response_model=list[AttachmentResponse])
def list_attachments(entity_type: str, entity_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Attachment)
        .filter(Attachment.entity_type == entity_type, Attachment.entity_id == entity_id)
        .order_by(Attachment.created_at.desc())
        .all()
    )


@router.post("/{entity_type}/{entity_id}", response_model=AttachmentResponse, status_code=201)
async def upload_attachment(
    entity_type: str,
    entity_id: str,
    file: UploadFile = File(...),
    label: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    if entity_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的实体类型，可选: {VALID_TYPES}")

    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    storage_path = f"{entity_type}/{entity_id}/{stored_filename}"

    if STORAGE == "supabase":
        content = await file.read()
        file_size = len(content)
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                _storage_url(storage_path),
                headers={**_headers(), "Content-Type": file.content_type or "application/octet-stream"},
                content=content,
            )
            if resp.status_code not in (200, 201):
                raise HTTPException(status_code=500, detail=f"上传失败: {resp.text}")
    else:
        entity_dir = os.path.join(LOCAL_ROOT, entity_type, entity_id)
        os.makedirs(entity_dir, exist_ok=True)
        path = os.path.join(entity_dir, stored_filename)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = os.path.getsize(path)

    attachment = Attachment(
        entity_type=entity_type,
        entity_id=entity_id,
        filename=stored_filename,
        original_filename=file.filename or "unknown",
        file_path=storage_path,
        file_size=file_size,
        mime_type=file.content_type,
        label=label,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment
