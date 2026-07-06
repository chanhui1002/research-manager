import os
import uuid
import base64
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Attachment
from app.schemas import AttachmentResponse

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://afjfieukktcjxgvtawjy.supabase.co")
_key_b64 = os.getenv("SUPABASE_SERVICE_KEY_B64", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "") or (base64.b64decode(_key_b64).decode() if _key_b64 else "")
BUCKET_NAME = "attachments"


def _storage_url(path: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{path}"


def _public_url(path: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{path}"


def _headers():
    return {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
    }


@router.get("/preview/{attachment_id}")
def preview_attachment(attachment_id: str, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    storage_path = attachment.file_path
    url = _public_url(storage_path)
    return RedirectResponse(url=url)


@router.get("/download/{attachment_id}")
def download_attachment(attachment_id: str, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    storage_path = attachment.file_path
    url = _public_url(storage_path)
    return RedirectResponse(url=f"{url}?download={attachment.original_filename}")


@router.delete("/remove/{attachment_id}", status_code=204)
def delete_attachment(attachment_id: str, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    storage_path = attachment.file_path
    with httpx.Client(timeout=30) as client:
        client.delete(
            f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}",
            headers=_headers(),
            json={"prefixes": [storage_path]},
        )
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
    valid_types = ["paper", "book", "project", "award", "adoption", "honor", "training"]
    if entity_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效的实体类型，可选: {valid_types}")

    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    storage_path = f"{entity_type}/{entity_id}/{stored_filename}"

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
