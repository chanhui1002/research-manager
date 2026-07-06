from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Training
from app.schemas import TrainingCreate, TrainingUpdate, TrainingResponse

router = APIRouter()


@router.get("/", response_model=list[TrainingResponse])
def list_trainings(
    keyword: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Training)
    if keyword:
        query = query.filter(Training.title.ilike(f"%{keyword}%"))
    if year:
        query = query.filter(Training.training_date != None).filter(
            db.func.strftime('%Y', Training.training_date) == str(year)
        )
    return query.order_by(Training.training_date.desc().nullslast()).all()


@router.get("/{training_id}", response_model=TrainingResponse)
def get_training(training_id: str, db: Session = Depends(get_db)):
    training = db.query(Training).filter(Training.id == training_id).first()
    if not training:
        raise HTTPException(status_code=404, detail="培训证明不存在")
    return training


@router.post("/", response_model=TrainingResponse, status_code=201)
def create_training(data: TrainingCreate, db: Session = Depends(get_db)):
    training = Training(**data.model_dump())
    db.add(training)
    db.commit()
    db.refresh(training)
    return training


@router.put("/{training_id}", response_model=TrainingResponse)
def update_training(training_id: str, data: TrainingUpdate, db: Session = Depends(get_db)):
    training = db.query(Training).filter(Training.id == training_id).first()
    if not training:
        raise HTTPException(status_code=404, detail="培训证明不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(training, key, value)
    db.commit()
    db.refresh(training)
    return training


@router.delete("/{training_id}", status_code=204)
def delete_training(training_id: str, db: Session = Depends(get_db)):
    training = db.query(Training).filter(Training.id == training_id).first()
    if not training:
        raise HTTPException(status_code=404, detail="培训证明不存在")
    db.delete(training)
    db.commit()
