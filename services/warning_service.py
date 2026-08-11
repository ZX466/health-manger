from typing import List, Dict

from sqlalchemy import select

import models
from constants import (
    BMI_UNDERWEIGHT, BMI_NORMAL_UPPER, BMI_OVERWEIGHT_UPPER,
    BP_SYSTOLIC_LOW, BP_SYSTOLIC_NORMAL, BP_SYSTOLIC_ELEVATED,
    BP_DIASTOLIC_LOW, BP_DIASTOLIC_NORMAL, BP_DIASTOLIC_ELEVATED,
    HR_LOW, HR_HIGH,
    TEMP_LOW, TEMP_NORMAL_HIGH,
)


def check_health_warnings(user_id: int, db) -> List[Dict]:
    latest_record = db.execute(
        select(models.HealthRecord)
        .where(models.HealthRecord.user_id == user_id)
        .order_by(models.HealthRecord.record_date.desc())
    ).scalars().first()

    if not latest_record:
        return []

    warnings = []

    if latest_record.bmi:
        if latest_record.bmi < BMI_UNDERWEIGHT:
            warnings.append({
                "type": "BMI 偏低",
                "level": "warning",
                "content": f"您的 BMI 为{latest_record.bmi}，低于正常范围 ({BMI_UNDERWEIGHT}-{BMI_NORMAL_UPPER})。建议加强营养摄入，适当增重。"
            })
        elif latest_record.bmi >= BMI_OVERWEIGHT_UPPER:
            warnings.append({
                "type": "BMI 过高",
                "level": "danger",
                "content": f"您的 BMI 为{latest_record.bmi}，属于肥胖范围。建议控制饮食，增加运动，必要时咨询医生。"
            })
        elif latest_record.bmi >= BMI_NORMAL_UPPER:
            warnings.append({
                "type": "BMI 偏高",
                "level": "warning",
                "content": f"您的 BMI 为{latest_record.bmi}，略高于正常范围。建议适当控制饮食，增加运动量。"
            })

    if latest_record.blood_pressure_systolic and latest_record.blood_pressure_diastolic:
        systolic = latest_record.blood_pressure_systolic
        diastolic = latest_record.blood_pressure_diastolic

        if systolic >= BP_SYSTOLIC_ELEVATED or diastolic >= BP_DIASTOLIC_ELEVATED:
            warnings.append({
                "type": "高血压",
                "level": "danger",
                "content": f"您的血压为{systolic}/{diastolic}mmHg，达到高血压标准。建议及时就医检查，遵循医生指导。"
            })
        elif systolic >= BP_SYSTOLIC_NORMAL or diastolic >= BP_DIASTOLIC_NORMAL:
            warnings.append({
                "type": "血压偏高",
                "level": "warning",
                "content": f"您的血压为{systolic}/{diastolic}mmHg，处于正常高值。建议减少盐分摄入，保持规律运动。"
            })
        elif systolic < BP_SYSTOLIC_LOW or diastolic < BP_DIASTOLIC_LOW:
            warnings.append({
                "type": "低血压",
                "level": "warning",
                "content": f"您的血压为{systolic}/{diastolic}mmHg，低于正常范围。建议适当增加营养，避免过度劳累。"
            })

    if latest_record.heart_rate:
        if latest_record.heart_rate < HR_LOW:
            warnings.append({
                "type": "心率过缓",
                "level": "warning",
                "content": f"您的心率为{latest_record.heart_rate}次/分钟，低于正常范围 ({HR_LOW}-{HR_HIGH})。如有不适请及时就医。"
            })
        elif latest_record.heart_rate > HR_HIGH:
            warnings.append({
                "type": "心率过速",
                "level": "danger",
                "content": f"您的心率为{latest_record.heart_rate}次/分钟，高于正常范围。建议休息，如持续过快请就医。"
            })

    if latest_record.temperature:
        if latest_record.temperature > TEMP_NORMAL_HIGH:
            warnings.append({
                "type": "体温偏高",
                "level": "warning",
                "content": f"您的体温为{latest_record.temperature}°C，略高于正常范围。请注意休息，多喝水。"
            })
        elif latest_record.temperature < TEMP_LOW:
            warnings.append({
                "type": "体温偏低",
                "level": "warning",
                "content": f"您的体温为{latest_record.temperature}°C，低于正常范围。注意保暖，适当增加衣物。"
            })

    for warning_data in warnings:
        existing_warning = db.execute(
            select(models.HealthWarning).where(
                models.HealthWarning.user_id == user_id,
                models.HealthWarning.warning_type == warning_data["type"],
                models.HealthWarning.is_read.is_(False)
            )
        ).scalars().first()

        if not existing_warning:
            db_warning = models.HealthWarning(
                user_id=user_id,
                warning_type=warning_data["type"],
                warning_level=warning_data["level"],
                warning_content=warning_data["content"]
            )
            db.add(db_warning)

    db.commit()
    return warnings
