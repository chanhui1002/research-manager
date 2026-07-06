import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from openpyxl import Workbook
from app.database import get_db
from app.models import Paper, Book, Project, Award, Adoption, Honor, Training

router = APIRouter()

ENTITY_MAP = {
    "paper": Paper,
    "book": Book,
    "project": Project,
    "award": Award,
    "adoption": Adoption,
    "honor": Honor,
    "training": Training,
}

FIELD_LABELS = {
    "paper": {
        "title": "论文题目",
        "journal": "期刊/会议",
        "publish_date": "发表时间",
        "paper_type": "论文类型",
        "cas_quartile": "中科院分区",
        "jcr_quartile": "JCR分区",
        "impact_factor": "影响因子",
        "authors": "全部作者",
        "is_student_first_supervisor_corresponding": "学生一作导师通讯",
        "doi": "DOI",
        "affiliation": "归属单位",
        "discipline": "学科分类",
        "notes": "备注",
    },
    "book": {
        "title": "书名",
        "publisher": "出版社",
        "publish_date": "出版时间",
        "book_type": "类型",
        "isbn": "ISBN",
        "total_words": "总字数(万字)",
        "my_words": "本人撰写(万字)",
        "authors": "全部作者",
        "notes": "备注",
    },
    "project": {
        "title": "项目名称",
        "project_number": "项目编号",
        "source": "项目来源",
        "level": "项目级别",
        "participant_rank": "参与排名",
        "start_date": "立项时间",
        "end_date": "结项时间",
        "status": "项目状态",
        "total_funding": "总经费(万元)",
        "received_funding": "到账经费(万元)",
        "notes": "备注",
    },
    "award": {
        "title": "奖励名称",
        "category": "奖励类别",
        "granting_body": "颁奖单位",
        "level": "获奖级别",
        "grade": "获奖等级",
        "award_date": "获奖时间",
        "my_rank": "本人排名",
        "recipients": "全部获奖人",
        "notes": "备注",
    },
    "adoption": {
        "title": "成果标题",
        "department": "采纳部门",
        "adoption_date": "采纳时间",
        "notes": "备注",
    },
    "honor": {
        "title": "荣誉称号",
        "granting_body": "授予单位",
        "level": "级别",
        "honor_date": "获得时间",
        "notes": "备注",
    },
    "training": {
        "title": "培训名称",
        "organizer": "主办单位",
        "training_date": "培训时间",
        "duration": "培训时长",
        "certificate_number": "证书编号",
        "notes": "备注",
    },
}


@router.get("/{entity_type}")
def export_excel(
    entity_type: str,
    keyword: Optional[str] = None,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    fields: Optional[str] = Query(None, description="逗号分隔的字段名"),
    db: Session = Depends(get_db),
):
    if entity_type not in ENTITY_MAP:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"无效类型，可选: {list(ENTITY_MAP.keys())}")

    model = ENTITY_MAP[entity_type]
    query = db.query(model)

    if keyword:
        query = query.filter(model.title.ilike(f"%{keyword}%"))

    date_field = _get_date_field(model)
    if date_field and year_start:
        query = query.filter(date_field != None).filter(
            db.func.strftime('%Y', date_field) >= str(year_start)
        )
    if date_field and year_end:
        query = query.filter(date_field != None).filter(
            db.func.strftime('%Y', date_field) <= str(year_end)
        )

    if date_field:
        query = query.order_by(date_field.desc().nullslast())

    records = query.all()

    available_fields = FIELD_LABELS.get(entity_type, {})
    if fields:
        selected_fields = [f.strip() for f in fields.split(",") if f.strip() in available_fields]
    else:
        selected_fields = list(available_fields.keys())

    wb = Workbook()
    ws = wb.active
    ws.title = entity_type

    headers = [available_fields[f] for f in selected_fields]
    ws.append(headers)

    for record in records:
        row = []
        for field in selected_fields:
            value = getattr(record, field, None)
            if value is True:
                value = "是"
            elif value is False:
                value = "否"
            elif value is None:
                value = ""
            else:
                value = str(value)
            row.append(value)
        ws.append(row)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"{entity_type}_export.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{entity_type}/fields")
def get_available_fields(entity_type: str):
    if entity_type not in FIELD_LABELS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"无效类型，可选: {list(FIELD_LABELS.keys())}")
    return FIELD_LABELS[entity_type]


def _get_date_field(model):
    if hasattr(model, "publish_date"):
        return model.publish_date
    if hasattr(model, "start_date"):
        return model.start_date
    if hasattr(model, "award_date"):
        return model.award_date
    if hasattr(model, "adoption_date"):
        return model.adoption_date
    if hasattr(model, "honor_date"):
        return model.honor_date
    if hasattr(model, "training_date"):
        return model.training_date
    return None
