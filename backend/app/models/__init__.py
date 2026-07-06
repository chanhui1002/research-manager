import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Text, Date, DateTime, Float, Boolean, Integer
from app.database import Base
import enum


def gen_uuid():
    return str(uuid.uuid4())


# ===== Enums =====

class PaperType(str, enum.Enum):
    SCI = "SCI"
    SSCI = "SSCI"
    EI = "EI"
    CSSCI = "CSSCI"
    PKU_CORE = "北大核心"
    ORDINARY = "普刊"
    CONFERENCE = "会议论文"


class CASQuartile(str, enum.Enum):
    Q1 = "1区"
    Q2 = "2区"
    Q3 = "3区"
    Q4 = "4区"


class JCRQuartile(str, enum.Enum):
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"


class BookType(str, enum.Enum):
    MONOGRAPH = "专著"
    EDITED = "编著"
    TRANSLATED = "译著"
    TEXTBOOK = "教材"


class ProjectSource(str, enum.Enum):
    NSFC = "国家自然科学基金"
    NSSFC = "国家社科基金"
    PROVINCIAL = "省部级项目"
    MUNICIPAL = "厅局级项目"
    HORIZONTAL = "横向项目"
    SCHOOL = "校级项目"
    OTHER = "其他"


class ProjectLevel(str, enum.Enum):
    NATIONAL = "国家级"
    PROVINCIAL = "省部级"
    MUNICIPAL = "厅局级"
    SCHOOL = "校级"


class ProjectStatus(str, enum.Enum):
    ACTIVE = "在研"
    COMPLETED = "已结题"
    ACCEPTED = "已验收"


class AwardCategory(str, enum.Enum):
    RESEARCH = "科研奖励"
    TEACHING = "教学奖励"
    HONOR = "荣誉称号"


class AwardLevel(str, enum.Enum):
    NATIONAL = "国家级"
    PROVINCIAL = "省部级"
    MUNICIPAL = "厅局级"
    SCHOOL = "校级"


class AwardGrade(str, enum.Enum):
    SPECIAL = "特等"
    FIRST = "一等"
    SECOND = "二等"
    THIRD = "三等"


# ===== Models =====

class Paper(Base):
    __tablename__ = "papers"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(500), nullable=False, index=True)
    journal = Column(String(300))
    publish_date = Column(Date)
    paper_type = Column(String(50))
    cas_quartile = Column(String(20))
    jcr_quartile = Column(String(20))
    impact_factor = Column(Float)
    authors = Column(Text)
    is_student_first_supervisor_corresponding = Column(Boolean, default=False)
    doi = Column(String(200))
    affiliation = Column(String(300))
    discipline = Column(String(200))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Book(Base):
    __tablename__ = "books"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(500), nullable=False, index=True)
    publisher = Column(String(300))
    publish_date = Column(Date)
    book_type = Column(String(50))
    isbn = Column(String(50))
    total_words = Column(Float)
    my_words = Column(Float)
    authors = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(500), nullable=False, index=True)
    project_number = Column(String(200))
    source = Column(String(100))
    level = Column(String(50))
    participant_rank = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(50))
    total_funding = Column(Float)
    received_funding = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Award(Base):
    __tablename__ = "awards"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(500), nullable=False, index=True)
    category = Column(String(50))
    granting_body = Column(String(300))
    level = Column(String(50))
    grade = Column(String(50))
    award_date = Column(Date)
    my_rank = Column(Integer)
    recipients = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Adoption(Base):
    __tablename__ = "adoptions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(500), nullable=False, index=True)
    department = Column(String(300), nullable=False)
    adoption_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Honor(Base):
    __tablename__ = "honors"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(500), nullable=False, index=True)
    granting_body = Column(String(300))
    level = Column(String(50))
    honor_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Training(Base):
    __tablename__ = "trainings"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(500), nullable=False, index=True)
    organizer = Column(String(300))
    training_date = Column(Date)
    duration = Column(String(100))
    certificate_number = Column(String(200))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    label = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
