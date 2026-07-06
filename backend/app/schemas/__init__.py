from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class PaperCreate(BaseModel):
    title: str
    journal: Optional[str] = None
    publish_date: Optional[date] = None
    paper_type: Optional[str] = None
    cas_quartile: Optional[str] = None
    jcr_quartile: Optional[str] = None
    impact_factor: Optional[float] = None
    authors: Optional[str] = None
    is_student_first_supervisor_corresponding: Optional[bool] = False
    doi: Optional[str] = None
    affiliation: Optional[str] = None
    discipline: Optional[str] = None
    notes: Optional[str] = None


class PaperUpdate(PaperCreate):
    title: Optional[str] = None


class PaperResponse(PaperCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookCreate(BaseModel):
    title: str
    publisher: Optional[str] = None
    publish_date: Optional[date] = None
    book_type: Optional[str] = None
    isbn: Optional[str] = None
    total_words: Optional[float] = None
    my_words: Optional[float] = None
    authors: Optional[str] = None
    notes: Optional[str] = None


class BookUpdate(BookCreate):
    title: Optional[str] = None


class BookResponse(BookCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    title: str
    project_number: Optional[str] = None
    source: Optional[str] = None
    level: Optional[str] = None
    participant_rank: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    total_funding: Optional[float] = None
    received_funding: Optional[float] = None
    notes: Optional[str] = None


class ProjectUpdate(ProjectCreate):
    title: Optional[str] = None


class ProjectResponse(ProjectCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AwardCreate(BaseModel):
    title: str
    category: Optional[str] = None
    granting_body: Optional[str] = None
    level: Optional[str] = None
    grade: Optional[str] = None
    award_date: Optional[date] = None
    my_rank: Optional[int] = None
    recipients: Optional[str] = None
    notes: Optional[str] = None


class AwardUpdate(AwardCreate):
    title: Optional[str] = None


class AwardResponse(AwardCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdoptionCreate(BaseModel):
    title: str
    department: str
    adoption_date: Optional[date] = None
    notes: Optional[str] = None


class AdoptionUpdate(AdoptionCreate):
    title: Optional[str] = None
    department: Optional[str] = None


class AdoptionResponse(AdoptionCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HonorCreate(BaseModel):
    title: str
    granting_body: Optional[str] = None
    level: Optional[str] = None
    honor_date: Optional[date] = None
    notes: Optional[str] = None


class HonorUpdate(HonorCreate):
    title: Optional[str] = None


class HonorResponse(HonorCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrainingCreate(BaseModel):
    title: str
    organizer: Optional[str] = None
    training_date: Optional[date] = None
    duration: Optional[str] = None
    certificate_number: Optional[str] = None
    notes: Optional[str] = None


class TrainingUpdate(TrainingCreate):
    title: Optional[str] = None


class TrainingResponse(TrainingCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttachmentResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    filename: str
    original_filename: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    label: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
