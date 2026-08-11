from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from auth import get_current_user
from health_rating import get_rating_emoji, get_rating_color, get_rating_bg_color
from services.health_record_service import (
    create_record,
    get_records,
    get_record,
    delete_record,
    get_latest_analysis,
    get_analysis_history,
)

router = APIRouter(prefix="/api/health", tags=["健康数据"])


@router.post("/records", response_model=schemas.HealthRecordResponse)
def create_health_record(
    record: schemas.HealthRecordCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_record(record, current_user.id, db)


@router.get("/records", response_model=List[schemas.HealthRecordResponse])
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


@router.delete("/records/{record_id}", )
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


@router.get("/analysis/history", response_model=List[schemas.HealthAnalysisResponse])
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
        "bg_color": get_rating_bg_color(analysis.health_rating) if analysis.health_rating else "#f5f5f5",
        "bmi_status": analysis.bmi_status,
        "blood_pressure_status": analysis.blood_pressure_status,
        "overall_status": analysis.overall_status,
        "overall_advice": analysis.overall_advice,
        "analysis_date": analysis.analysis_date,
    }
