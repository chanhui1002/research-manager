from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Adoption
from app.schemas import AdoptionCreate, AdoptionUpdate, AdoptionResponse

router = APIRouter()


@router.get("/", response_model=list[AdoptionResponse])
def list_adoptions(
    keyword: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Adoption)
    if keyword:
        query = query.filter(
            (Adoption.title.ilike(f"%{keyword}%")) | (Adoption.department.ilike(f"%{keyword}%"))
        )
    if year:
        query = query.filter(Adoption.adoption_date != None).filter(
            db.func.strftime('%Y', Adoption.adoption_date) == str(year)
        )
    return query.order_by(Adoption.adoption_date.desc().nullslast()).all()


@router.get("/{adoption_id}", response_model=AdoptionResponse)
def get_adoption(adoption_id: str, db: Session = Depends(get_db)):
    adoption = db.query(Adoption).filter(Adoption.id == adoption_id).first()
    if not adoption:
        raise HTTPException(status_code=404, detail="采纳证明不存在")
    return adoption


@router.post("/", response_model=AdoptionResponse, status_code=201)
def create_adoption(data: AdoptionCreate, db: Session = Depends(get_db)):
    adoption = Adoption(**data.model_dump())
    db.add(adoption)
    db.commit()
    db.refresh(adoption)
    return adoption


@router.put("/{adoption_id}", response_model=AdoptionResponse)
def update_adoption(adoption_id: str, data: AdoptionUpdate, db: Session = Depends(get_db)):
    adoption = db.query(Adoption).filter(Adoption.id == adoption_id).first()
    if not adoption:
        raise HTTPException(status_code=404, detail="采纳证明不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(adoption, key, value)
    db.commit()
    db.refresh(adoption)
    return adoption


@router.delete("/{adoption_id}", status_code=204)
def delete_adoption(adoption_id: str, db: Session = Depends(get_db)):
    adoption = db.query(Adoption).filter(Adoption.id == adoption_id).first()
    if not adoption:
        raise HTTPException(status_code=404, detail="采纳证明不存在")
    db.delete(adoption)
    db.commit()
