"""Business logic for health record CRUD and analysis generation."""

from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

import models
import schemas
from services.health_service import calculate_bmi, analyze_bmi, analyze_blood_pressure
from health_rating import calculate_health_rating


def create_record(
    record: schemas.HealthRecordCreate,
    user_id: int,
    db: Session,
) -> models.HealthRecord:
    bmi = None
    if record.height and record.weight:
        bmi = calculate_bmi(record.height, record.weight)

    db_record = models.HealthRecord(
        user_id=user_id,
        height=record.height,
        weight=record.weight,
        bmi=bmi,
        blood_pressure_systolic=record.blood_pressure_systolic,
        blood_pressure_diastolic=record.blood_pressure_diastolic,
        heart_rate=record.heart_rate,
        temperature=record.temperature,
        vision_left=record.vision_left,
        vision_right=record.vision_right,
        exercise_frequency=record.exercise_frequency,
        sleep_hours=record.sleep_hours,
        diet_habit=record.diet_habit,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    if bmi is not None:
        _generate_analysis(db_record, user_id, db)

    return db_record


def get_records(user_id: int, db: Session) -> List[models.HealthRecord]:
    return (
        db.execute(
            select(models.HealthRecord)
            .where(models.HealthRecord.user_id == user_id)
            .order_by(models.HealthRecord.record_date.desc())
        ).scalars().all()
    )


def get_record(record_id: int, user_id: int, db: Session) -> models.HealthRecord:
    record = db.execute(
        select(models.HealthRecord).where(
            models.HealthRecord.id == record_id,
            models.HealthRecord.user_id == user_id,
        )
    ).scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


def delete_record(record_id: int, user_id: int, db: Session) -> dict:
    record = get_record(record_id, user_id, db)

    analyses = db.execute(
        select(models.HealthAnalysis).where(
            models.HealthAnalysis.health_record_id == record_id
        )
    ).scalars().all()
    for analysis in analyses:
        db.delete(analysis)

    db.delete(record)
    db.commit()
    return {"message": "删除成功", "deleted_id": record_id}


def get_latest_analysis(user_id: int, db: Session) -> models.HealthAnalysis:
    analysis = db.execute(
        select(models.HealthAnalysis)
        .where(models.HealthAnalysis.user_id == user_id)
        .order_by(models.HealthAnalysis.analysis_date.desc())
    ).scalars().first()
    if not analysis:
        raise HTTPException(status_code=404, detail="暂无分析记录，请先添加健康数据")
    return analysis


def get_analysis_history(user_id: int, db: Session) -> List[models.HealthAnalysis]:
    return (
        db.execute(
            select(models.HealthAnalysis)
            .where(models.HealthAnalysis.user_id == user_id)
            .order_by(models.HealthAnalysis.analysis_date.desc())
        ).scalars().all()
    )


def _generate_analysis(record: models.HealthRecord, user_id: int, db: Session) -> None:
    bmi_status, bmi_advice = analyze_bmi(record.bmi)
    blood_pressure_status = "未知"
    blood_pressure_advice = "暂无血压数据"
    if record.blood_pressure_systolic and record.blood_pressure_diastolic:
        blood_pressure_status, blood_pressure_advice = analyze_blood_pressure(
            record.blood_pressure_systolic, record.blood_pressure_diastolic
        )

    overall_statuses = [
        s for s in [bmi_status, blood_pressure_status] if s not in ["未知", "正常"]
    ]
    overall_status = "正常" if not overall_statuses else overall_statuses[0]
    overall_advice = (
        "您的整体健康状况良好，请继续保持！"
        if overall_status == "正常"
        else f"建议关注{overall_status}问题，及时调理。"
    )

    db_analysis = models.HealthAnalysis(
        user_id=user_id,
        health_record_id=record.id,
        bmi_status=bmi_status,
        bmi_advice=bmi_advice,
        blood_pressure_status=blood_pressure_status,
        blood_pressure_advice=blood_pressure_advice,
        overall_status=overall_status,
        overall_advice=overall_advice,
    )
    db.add(db_analysis)
    db.commit()

    health_rating, health_score, _ = calculate_health_rating(record)
    db_analysis.health_rating = health_rating
    db_analysis.health_score = health_score
    db.commit()
    db.refresh(db_analysis)
