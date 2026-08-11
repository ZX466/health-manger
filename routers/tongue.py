from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from auth import get_current_user
from tongue import get_tongue_color_info, get_coating_color_info
from services.tongue_service import (
    upload_and_analyze,
    get_diagnoses,
    get_diagnosis,
    get_latest_completed,
    delete_diagnosis,
    get_stats,
)

router = APIRouter(prefix="/api/tongue", tags=["舌诊分析"])


@router.post("/upload", response_model=schemas.TongueDiagnosisResponse)
async def upload_tongue_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await upload_and_analyze(file, current_user.id, db)


@router.get("/list", response_model=List[schemas.TongueDiagnosisResponse])
def get_tongue_diagnoses(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return get_diagnoses(current_user.id, db, limit, offset)


@router.get("/latest/result")
def get_latest_tongue_result(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    diagnosis = get_latest_completed(current_user.id, db)
    return {
        "id": diagnosis.id,
        "image_path": diagnosis.image_path,
        "tongue_color": {
            "name": diagnosis.tongue_color,
            **get_tongue_color_info(diagnosis.tongue_color or ""),
        },
        "coating_color": {
            "name": diagnosis.coating_color,
            **get_coating_color_info(diagnosis.coating_color or ""),
        },
        "coating_thickness": diagnosis.coating_thickness,
        "has_cracks": diagnosis.has_cracks,
        "has_teeth_marks": diagnosis.has_teeth_marks,
        "tongue_shape": diagnosis.tongue_shape,
        "moisture_level": diagnosis.moisture_level,
        "tongue_spirit": diagnosis.tongue_spirit,
        "overall_type": diagnosis.overall_type,
        "confidence_score": diagnosis.confidence_score,
        "tcm_syndrome": diagnosis.tcm_syndrome,
        "health_advice": diagnosis.health_advice,
        "diet_suggestion": diagnosis.diet_suggestion,
        "lifestyle_advice": diagnosis.lifestyle_advice,
        "created_at": diagnosis.created_at.isoformat() if diagnosis.created_at else None,
    }


@router.get("/stats/summary")
def get_tongue_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_stats(current_user.id, db)


@router.get("/{diagnosis_id}", response_model=schemas.TongueDiagnosisResponse)
def get_tongue_diagnosis(
    diagnosis_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_diagnosis(diagnosis_id, current_user.id, db)


@router.delete("/{diagnosis_id}", response_model=schemas.MessageResponse)
def delete_tongue_diagnosis(
    diagnosis_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_diagnosis(diagnosis_id, current_user.id, db)
