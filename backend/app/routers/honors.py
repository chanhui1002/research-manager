from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Honor
from app.schemas import HonorCreate, HonorUpdate, HonorResponse

router = APIRouter()


@router.get("/", response_model=list[HonorResponse])
def list_honors(
    keyword: Optional[str] = None,
    year: Optional[int] = None,
    level: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Honor)
    if keyword:
        query = query.filter(Honor.title.ilike(f"%{keyword}%"))
    if year:
        query = query.filter(Honor.honor_date != None).filter(
            db.func.strftime('%Y', Honor.honor_date) == str(year)
        )
    if level:
        query = query.filter(Honor.level == level)
    return query.order_by(Honor.honor_date.desc().nullslast()).all()


@router.get("/{honor_id}", response_model=HonorResponse)
def get_honor(honor_id: str, db: Session = Depends(get_db)):
    honor = db.query(Honor).filter(Honor.id == honor_id).first()
    if not honor:
        raise HTTPException(status_code=404, detail="荣誉称号不存在")
    return honor


@router.post("/", response_model=HonorResponse, status_code=201)
def create_honor(data: HonorCreate, db: Session = Depends(get_db)):
    honor = Honor(**data.model_dump())
    db.add(honor)
    db.commit()
    db.refresh(honor)
    return honor


@router.put("/{honor_id}", response_model=HonorResponse)
def update_honor(honor_id: str, data: HonorUpdate, db: Session = Depends(get_db)):
    honor = db.query(Honor).filter(Honor.id == honor_id).first()
    if not honor:
        raise HTTPException(status_code=404, detail="荣誉称号不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(honor, key, value)
    db.commit()
    db.refresh(honor)
    return honor


@router.delete("/{honor_id}", status_code=204)
def delete_honor(honor_id: str, db: Session = Depends(get_db)):
    honor = db.query(Honor).filter(Honor.id == honor_id).first()
    if not honor:
        raise HTTPException(status_code=404, detail="荣誉称号不存在")
    db.delete(honor)
    db.commit()
