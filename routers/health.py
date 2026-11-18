from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db
from health_rating import get_rating_bg_color, get_rating_color, get_rating_emoji
from routers._uploads import read_image_upload
from services.health_record_service import (
    create_record,
    delete_record,
    get_analysis_history,
    get_latest_analysis,
    get_record,
    get_records,
)
from services.security_service import check_rate_limit
from services.warning_service import safe_check_health_warnings

router = APIRouter(prefix="/api/health", tags=["健康数据"])

REPORT_OCR_RATE_LIMIT = 10
REPORT_OCR_RATE_WINDOW_SECONDS = 60


@router.post("/records", response_model=schemas.HealthRecordResponse)
def create_health_record(
    record: schemas.HealthRecordCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存健康记录后触发预警检查；预警失败只记日志，不影响已保存的记录。"""
    saved = create_record(record, current_user.id, db)
    safe_check_health_warnings(current_user.id, db)
    return saved


@router.get("/records", response_model=list[schemas.HealthRecordResponse])
def get_health_records(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_records(current_user.id, db)


@router.get("/records/{record_id}", response_model=schemas.HealthRecordResponse)
def get_health_record(
    record_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_record(record_id, current_user.id, db)


@router.delete("/records/{record_id}", response_model=schemas.DeleteRecordResponse)
def delete_health_record(
    record_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_record(record_id, current_user.id, db)


@router.get("/analysis/latest", response_model=schemas.HealthAnalysisResponse)
def get_latest_analysis_endpoint(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_latest_analysis(current_user.id, db)


@router.get("/analysis/history", response_model=list[schemas.HealthAnalysisResponse])
def get_analysis_history_endpoint(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_analysis_history(current_user.id, db)


@router.get("/rating/latest", response_model=schemas.HealthRatingResponse)
def get_latest_rating(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis = get_latest_analysis(current_user.id, db)
    return {
        "rating": analysis.health_rating,
        "score": analysis.health_score,
        "emoji": get_rating_emoji(analysis.health_rating) if analysis.health_rating else "❓",
        "color": get_rating_color(analysis.health_rating) if analysis.health_rating else "#999999",
        "bg_color": get_rating_bg_color(analysis.health_rating)
        if analysis.health_rating
        else "#f5f5f5",
        "bmi_status": analysis.bmi_status,
        "blood_pressure_status": analysis.blood_pressure_status,
        "overall_status": analysis.overall_status,
        "overall_advice": analysis.overall_advice,
        "analysis_date": analysis.analysis_date,
    }


@router.post("/reports/ocr", response_model=schemas.ReportOcrResponse)
async def ocr_health_report_endpoint(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """体检报告 OCR：只回草稿，不写 HealthRecord；用户确认后复用 v1 记录接口。"""
    check_rate_limit(
        f"report_ocr:{current_user.id}",
        REPORT_OCR_RATE_LIMIT,
        REPORT_OCR_RATE_WINDOW_SECONDS,
    )
    raw = await read_image_upload(file)
    from services.report_ocr_service import aextract_report

    return await aextract_report(db, current_user.id, raw)
