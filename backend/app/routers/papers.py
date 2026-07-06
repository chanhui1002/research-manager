from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Paper
from app.schemas import PaperCreate, PaperUpdate, PaperResponse

router = APIRouter()


@router.get("/", response_model=list[PaperResponse])
def list_papers(
    keyword: Optional[str] = None,
    year: Optional[int] = None,
    paper_type: Optional[str] = None,
    cas_quartile: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Paper)
    if keyword:
        query = query.filter(Paper.title.ilike(f"%{keyword}%"))
    if year:
        query = query.filter(Paper.publish_date != None).filter(
            db.func.strftime('%Y', Paper.publish_date) == str(year)
        )
    if paper_type:
        query = query.filter(Paper.paper_type == paper_type)
    if cas_quartile:
        query = query.filter(Paper.cas_quartile == cas_quartile)
    return query.order_by(Paper.publish_date.desc().nullslast()).all()


@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: str, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    return paper


@router.post("/", response_model=PaperResponse, status_code=201)
def create_paper(data: PaperCreate, db: Session = Depends(get_db)):
    paper = Paper(**data.model_dump())
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return paper


@router.put("/{paper_id}", response_model=PaperResponse)
def update_paper(paper_id: str, data: PaperUpdate, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(paper, key, value)
    db.commit()
    db.refresh(paper)
    return paper


@router.delete("/{paper_id}", status_code=204)
def delete_paper(paper_id: str, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    db.delete(paper)
    db.commit()
