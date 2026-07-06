from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Award
from app.schemas import AwardCreate, AwardUpdate, AwardResponse

router = APIRouter()


@router.get("/", response_model=list[AwardResponse])
def list_awards(
    keyword: Optional[str] = None,
    year: Optional[int] = None,
    level: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Award)
    if keyword:
        query = query.filter(Award.title.ilike(f"%{keyword}%"))
    if year:
        query = query.filter(Award.award_date != None).filter(
            db.func.strftime('%Y', Award.award_date) == str(year)
        )
    if level:
        query = query.filter(Award.level == level)
    if category:
        query = query.filter(Award.category == category)
    return query.order_by(Award.award_date.desc().nullslast()).all()


@router.get("/{award_id}", response_model=AwardResponse)
def get_award(award_id: str, db: Session = Depends(get_db)):
    award = db.query(Award).filter(Award.id == award_id).first()
    if not award:
        raise HTTPException(status_code=404, detail="奖励不存在")
    return award


@router.post("/", response_model=AwardResponse, status_code=201)
def create_award(data: AwardCreate, db: Session = Depends(get_db)):
    award = Award(**data.model_dump())
    db.add(award)
    db.commit()
    db.refresh(award)
    return award


@router.put("/{award_id}", response_model=AwardResponse)
def update_award(award_id: str, data: AwardUpdate, db: Session = Depends(get_db)):
    award = db.query(Award).filter(Award.id == award_id).first()
    if not award:
        raise HTTPException(status_code=404, detail="奖励不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(award, key, value)
    db.commit()
    db.refresh(award)
    return award


@router.delete("/{award_id}", status_code=204)
def delete_award(award_id: str, db: Session = Depends(get_db)):
    award = db.query(Award).filter(Award.id == award_id).first()
    if not award:
        raise HTTPException(status_code=404, detail="奖励不存在")
    db.delete(award)
    db.commit()
