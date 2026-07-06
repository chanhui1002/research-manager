import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Attachment
from app.schemas import AttachmentResponse

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


@router.get("/preview/{attachment_id}")
def preview_attachment(attachment_id: str, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    if not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        path=attachment.file_path,
        media_type=attachment.mime_type or "application/octet-stream",
        headers={"Content-Disposition": "inline"},
    )


@router.get("/download/{attachment_id}")
def download_attachment(attachment_id: str, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    if not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        path=attachment.file_path,
        filename=attachment.original_filename,
        media_type=attachment.mime_type or "application/octet-stream",
    )


@router.delete("/remove/{attachment_id}", status_code=204)
def delete_attachment(attachment_id: str, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)
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
    entity_dir = os.path.join(UPLOAD_DIR, entity_type, str(entity_id))
    os.makedirs(entity_dir, exist_ok=True)
    file_path = os.path.join(entity_dir, stored_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    attachment = Attachment(
        entity_type=entity_type,
        entity_id=entity_id,
        filename=stored_filename,
        original_filename=file.filename or "unknown",
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        label=label,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment
