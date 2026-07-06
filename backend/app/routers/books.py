from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Book
from app.schemas import BookCreate, BookUpdate, BookResponse

router = APIRouter()


@router.get("/", response_model=list[BookResponse])
def list_books(
    keyword: Optional[str] = None,
    year: Optional[int] = None,
    book_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Book)
    if keyword:
        query = query.filter(Book.title.ilike(f"%{keyword}%"))
    if year:
        query = query.filter(Book.publish_date != None).filter(
            db.func.strftime('%Y', Book.publish_date) == str(year)
        )
    if book_type:
        query = query.filter(Book.book_type == book_type)
    return query.order_by(Book.publish_date.desc().nullslast()).all()


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: str, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="专著不存在")
    return book


@router.post("/", response_model=BookResponse, status_code=201)
def create_book(data: BookCreate, db: Session = Depends(get_db)):
    book = Book(**data.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@router.put("/{book_id}", response_model=BookResponse)
def update_book(book_id: str, data: BookUpdate, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="专著不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book


@router.delete("/{book_id}", status_code=204)
def delete_book(book_id: str, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="专著不存在")
    db.delete(book)
    db.commit()
