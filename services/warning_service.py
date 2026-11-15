from sqlalchemy import select

import models
from constants import (
    BMI_NORMAL_UPPER,
    BMI_OVERWEIGHT_UPPER,
    BMI_UNDERWEIGHT,
    BP_DIASTOLIC_ELEVATED,
    BP_DIASTOLIC_LOW,
    BP_DIASTOLIC_NORMAL,
    BP_SYSTOLIC_ELEVATED,
    BP_SYSTOLIC_LOW,
    BP_SYSTOLIC_NORMAL,
    HR_HIGH,
    HR_LOW,
    TEMP_LOW,
    TEMP_NORMAL_HIGH,
)


def check_health_warnings(user_id: int, db) -> list[dict]:
    latest_record = (
        db.execute(
            select(models.HealthRecord)
            .where(models.HealthRecord.user_id == user_id)
            .order_by(models.HealthRecord.record_date.desc())
        )
        .scalars()
        .first()
    )

    if not latest_record:
        # 没有生理记录时仍可能有心理维度的预警（量表危机/情绪低落）
        cross = _cross_warnings(user_id, db, None)
        _persist_warnings(user_id, db, cross)
        return cross

    warnings = []

    if latest_record.bmi:
        if latest_record.bmi < BMI_UNDERWEIGHT:
            warnings.append(
                {
                    "type": "BMI 偏低",
                    "level": "warning",
                    "content": f"您的 BMI 为{latest_record.bmi}，低于正常范围 ({BMI_UNDERWEIGHT}-{BMI_NORMAL_UPPER})。建议加强营养摄入，适当增重。",
                }
            )
        elif latest_record.bmi >= BMI_OVERWEIGHT_UPPER:
            warnings.append(
                {
                    "type": "BMI 过高",
                    "level": "danger",
                    "content": f"您的 BMI 为{latest_record.bmi}，属于肥胖范围。建议控制饮食，增加运动，必要时咨询医生。",
                }
            )
        elif latest_record.bmi >= BMI_NORMAL_UPPER:
            warnings.append(
                {
                    "type": "BMI 偏高",
                    "level": "warning",
                    "content": f"您的 BMI 为{latest_record.bmi}，略高于正常范围。建议适当控制饮食，增加运动量。",
                }
            )

    if latest_record.blood_pressure_systolic and latest_record.blood_pressure_diastolic:
        systolic = latest_record.blood_pressure_systolic
        diastolic = latest_record.blood_pressure_diastolic

        # 高血压优先于低血压：混合读数（170/55 严重高血压+低舒张压、85/90 低收缩压+高血压1级舒张压）
        # 应判高血压而非低血压，避免把更危险的高血压遮蔽为偏低
        if systolic >= BP_SYSTOLIC_ELEVATED or diastolic >= BP_DIASTOLIC_ELEVATED:
            warnings.append(
                {
                    "type": "高血压",
                    "level": "danger",
                    "content": f"您的血压为{systolic}/{diastolic}mmHg，达到高血压标准。建议及时就医检查，遵循医生指导。",
                }
            )
        elif systolic < BP_SYSTOLIC_LOW or diastolic < BP_DIASTOLIC_LOW:
            warnings.append(
                {
                    "type": "低血压",
                    "level": "warning",
                    "content": f"您的血压为{systolic}/{diastolic}mmHg，低于正常范围。建议适当增加营养，避免过度劳累。",
                }
            )
        elif systolic >= BP_SYSTOLIC_NORMAL or diastolic >= BP_DIASTOLIC_NORMAL:
            warnings.append(
                {
                    "type": "血压偏高",
                    "level": "warning",
                    "content": f"您的血压为{systolic}/{diastolic}mmHg，处于正常高值。建议减少盐分摄入，保持规律运动。",
                }
            )

    if latest_record.heart_rate:
        if latest_record.heart_rate < HR_LOW:
            warnings.append(
                {
                    "type": "心率过缓",
                    "level": "warning",
                    "content": f"您的心率为{latest_record.heart_rate}次/分钟，低于正常范围 ({HR_LOW}-{HR_HIGH})。如有不适请及时就医。",
                }
            )
        elif latest_record.heart_rate > HR_HIGH:
            warnings.append(
                {
                    "type": "心率过速",
                    "level": "danger",
                    "content": f"您的心率为{latest_record.heart_rate}次/分钟，高于正常范围。建议休息，如持续过快请就医。",
                }
            )

    if latest_record.temperature:
        if latest_record.temperature > TEMP_NORMAL_HIGH:
            warnings.append(
                {
                    "type": "体温偏高",
                    "level": "warning",
                    "content": f"您的体温为{latest_record.temperature}°C，略高于正常范围。请注意休息，多喝水。",
                }
            )
        elif latest_record.temperature < TEMP_LOW:
            warnings.append(
                {
                    "type": "体温偏低",
                    "level": "warning",
                    "content": f"您的体温为{latest_record.temperature}°C，低于正常范围。注意保暖，适当增加衣物。",
                }
            )

    warnings.extend(_cross_warnings(user_id, db, latest_record))
    _persist_warnings(user_id, db, warnings)
    return warnings


# ── 身心交叉预警（M-LOGIC1） ──
# 睡眠债阈值：近 7 个有记录日累计少睡 10 小时以上（约每天少睡 1.5 小时）
SLEEP_DEBT_WARN_HOURS = 10.0
# 连续低落：近 7 天内至少 3 条打卡且均分 <= 2
LOW_MOOD_AVG = 2.0
LOW_MOOD_MIN_DAYS = 3
LOW_MOOD_WINDOW_DAYS = 7


def _persist_warnings(user_id: int, db, warnings: list[dict]) -> None:
    """未读同类型预警去重后落库。"""
    for warning_data in warnings:
        existing_warning = (
            db.execute(
                select(models.HealthWarning).where(
                    models.HealthWarning.user_id == user_id,
                    models.HealthWarning.warning_type == warning_data["type"],
                    models.HealthWarning.is_read.is_(False),
                )
            )
            .scalars()
            .first()
        )

        if not existing_warning:
            db.add(
                models.HealthWarning(
                    user_id=user_id,
                    warning_type=warning_data["type"],
                    warning_level=warning_data["level"],
                    warning_content=warning_data["content"],
                )
            )

    db.commit()


def _crisis_hint() -> str:
    """危机资源提示；safety_service 未就绪时降级为通用文案，保证预警不因缺依赖而丢失。"""
    try:
        from services.safety_service import crisis_resources

        resources = list(crisis_resources())
    except ImportError:
        resources = []
    if resources:
        return "可联系：" + "；".join(resources)
    return "请尽快联系身边可信任的人或专业心理援助热线 / 医疗机构。"


def _bp_or_hr_elevated(record) -> list[str]:
    reasons = []
    systolic = record.blood_pressure_systolic
    diastolic = record.blood_pressure_diastolic
    if (systolic and systolic >= BP_SYSTOLIC_ELEVATED) or (
        diastolic and diastolic >= BP_DIASTOLIC_ELEVATED
    ):
        reasons.append(f"血压 {systolic}/{diastolic}")
    if record.heart_rate and record.heart_rate > HR_HIGH:
        reasons.append(f"心率 {record.heart_rate}")
    return reasons


def _cross_warnings(user_id: int, db, latest_record) -> list[dict]:
    """身心交叉预警：把心理维度（睡眠债/情绪/量表）与生理指标联动。"""
    from services import mental_service

    warnings: list[dict] = []
    _, sleep_debt, _ = mental_service.sleep_stats(db, user_id)

    # 1) 量表严肃模式：PHQ-9/GAD-7 危机或中重度以上 -> danger
    if mental_service.is_serious_mode(db, user_id):
        warnings.append(
            {
                "type": "心理状态需关注",
                "level": "danger",
                "content": "您近期的心理量表结果提示需要重点关注。"
                "这不是诊断，但您不必独自承担，" + _crisis_hint(),
            }
        )

    # 2) 睡眠债 + 血压/心率偏高：睡眠不足会推高血压和心率
    if sleep_debt is not None and sleep_debt >= SLEEP_DEBT_WARN_HOURS and latest_record:
        reasons = _bp_or_hr_elevated(latest_record)
        if reasons:
            warnings.append(
                {
                    "type": "睡眠不足叠加指标偏高",
                    "level": "warning",
                    "content": f"近 7 个记录日累计睡眠债约 {sleep_debt} 小时，"
                    f"同时 {'、'.join(reasons)} 偏高。长期睡眠不足会加重心血管负担，"
                    "建议优先补觉、规律作息，必要时咨询医生。",
                }
            )

    # 3) 连续情绪低落
    recent = mental_service.list_moods(db, user_id, LOW_MOOD_WINDOW_DAYS)
    scores = [r.mood_score for r in recent if r.mood_score is not None]
    if len(scores) >= LOW_MOOD_MIN_DAYS and sum(scores) / len(scores) <= LOW_MOOD_AVG:
        warnings.append(
            {
                "type": "情绪持续低落",
                "level": "warning",
                "content": f"近 {LOW_MOOD_WINDOW_DAYS} 天内的情绪打卡均分偏低"
                f"（{round(sum(scores) / len(scores), 1)}/5）。"
                "可以试试做一次 PHQ-9 / GAD-7 自测，或和信任的人聊聊。",
            }
        )

    return warnings
