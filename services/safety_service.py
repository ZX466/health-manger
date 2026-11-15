"""Mental safety policy; support signals are screening aids, never diagnoses."""

import json
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

import models

_MEDICAL_BOUNDARIES = (
    "你是提供一般健康信息和情绪支持的 AI，不能替代医生或专业心理服务。"
    "量表仅用于初筛，不是诊断。不得诊断、治疗、给药或建议具体药物剂量；"
    "不得嘲笑、贬低或夸大用户的感受与症状。"
)
_HUMOROUS_STYLE = "使用轻松、友好、懂梗的表达，保持尊重；遇到痛苦话题先认真倾听。"
_CLINICAL_STYLE = "使用专业、克制、清晰的表达，提供温和、可执行的建议。"
_CRISIS_PROMPT = (
    "你是提供情绪支持的 AI。使用温和、严肃、克制的语气，只使用平实文字，"
    "不得调侃、戏谑或使用符号装饰。先接纳对方的感受，避免责备和夸大。"
    "AI 不能诊断或治疗，不能替代医生或专业心理服务；不得给药或建议药物剂量。"
    "建议尽快联系学校心理咨询中心或当地精神卫生中心，"
    "也可联系身边可信任的人陪伴。"
    "如有紧急危险，请拨打 120/110，并尽快获得现场帮助。"
    "不追问自伤方式与操作细节，不承诺绝对保密。"
)


@dataclass(frozen=True)
class RiskState:
    level: Literal["normal", "elevated", "high"]
    reasons: tuple[str, ...]
    crisis: bool


def _now() -> datetime:
    # SQLAlchemy's SQLite DateTime drops the tzinfo from models._utcnow (UTC).
    return datetime.now(UTC).replace(tzinfo=None)


def _q9_positive(raw: str | None) -> bool:
    """Guard against inconsistent legacy flags, without echoing stored answers."""
    try:
        answers = json.loads(raw or "null")
    except (ValueError, TypeError):
        return False
    return (
        isinstance(answers, list)
        and len(answers) == 9
        and all(type(answer) is int and 0 <= answer <= 3 for answer in answers)
        and answers[8] > 0
    )


def _latest_scale(
    db: Session, user_id: int, scale_type: str, since: datetime, now: datetime
) -> models.ScaleAssessment | None:
    return db.scalar(
        select(models.ScaleAssessment)
        .where(
            models.ScaleAssessment.user_id == user_id,
            models.ScaleAssessment.scale_type == scale_type,
            models.ScaleAssessment.created_at >= since,
            models.ScaleAssessment.created_at <= now,
        )
        .order_by(models.ScaleAssessment.created_at.desc(), models.ScaleAssessment.id.desc())
        .limit(1)
    )


def _scale_risk(row: models.ScaleAssessment | None) -> RiskState:
    if row is None:
        return RiskState("normal", (), False)
    total = row.score or 0
    is_phq9 = row.scale_type == "phq9"
    label = "PHQ-9" if is_phq9 else "GAD-7"
    crisis = (
        bool(row.crisis_flag) or _q9_positive(row.answers) or total >= 20
        if is_phq9
        else total >= 15
    )
    if crisis:
        return RiskState("high", (f"近期 {label} 结果提示需要及时获得专业支持",), True)
    if total >= 10:
        return RiskState("elevated", (f"近期 {label} 评分达到关注阈值",), False)
    return RiskState("normal", (), False)


def _health_risk(db: Session, user_id: int, since: datetime, now: datetime) -> RiskState:
    rating = db.scalar(
        select(models.HealthAnalysis.health_rating)
        .where(
            models.HealthAnalysis.user_id == user_id,
            models.HealthAnalysis.analysis_date >= since,
            models.HealthAnalysis.analysis_date <= now,
        )
        .order_by(models.HealthAnalysis.analysis_date.desc(), models.HealthAnalysis.id.desc())
        .limit(1)
    )
    if rating == "危险":
        return RiskState("high", ("近期健康分析评级为危险",), True)
    if rating == "较差":
        return RiskState("elevated", ("近期健康分析评级为较差",), False)
    return RiskState("normal", (), False)


def _warning_risk(db: Session, user_id: int, since: datetime, now: datetime) -> RiskState:
    warning_id = db.scalar(
        select(models.HealthWarning.id)
        .where(
            models.HealthWarning.user_id == user_id,
            models.HealthWarning.warning_level == "danger",
            models.HealthWarning.is_read.is_(False),
            models.HealthWarning.created_at >= since,
            models.HealthWarning.created_at <= now,
        )
        .limit(1)
    )
    if warning_id is not None:
        return RiskState("elevated", ("存在近 30 天未读的高等级预警",), False)
    return RiskState("normal", (), False)


def assess_user_risk(db: Session, user_id: int) -> RiskState:
    """Read the user's latest signals in [now - 30 days, now]; never write/commit."""
    now = _now()
    since = now - timedelta(days=30)
    with db.no_autoflush:
        signals = (
            _scale_risk(_latest_scale(db, user_id, "phq9", since, now)),
            _scale_risk(_latest_scale(db, user_id, "gad7", since, now)),
            _health_risk(db, user_id, since, now),
            _warning_risk(db, user_id, since, now),
        )
    reasons = tuple(reason for signal in signals for reason in signal.reasons)
    if any(signal.crisis for signal in signals):
        return RiskState("high", reasons, True)
    return RiskState("elevated" if reasons else "normal", reasons, False)


def build_system_prompt(base: str, persona_style: str, risk: RiskState) -> str:
    """Replace all persona instructions for high risk, even with inconsistent flags."""
    if risk.level == "high" or risk.crisis:
        return _CRISIS_PROMPT
    style = _HUMOROUS_STYLE if persona_style == "humorous" else _CLINICAL_STYLE
    return "\n\n".join(part for part in (base.strip(), _MEDICAL_BOUNDARIES, style) if part)


def _resource_text(raw: str) -> str:
    # Configuration is display text only. Remove controls, bidi and zero-width marks.
    return " ".join("".join(c for c in raw if not unicodedata.category(c).startswith("C")).split())


def crisis_resources() -> list[dict[str, str]]:
    """Return fresh display data; never invent a telephone or copy one from a model."""
    hotline = _resource_text(os.getenv("MENTAL_HOTLINE", ""))
    campus = _resource_text(os.getenv("CAMPUS_COUNSELING", ""))[:300]
    general = {
        "name": "学校心理咨询中心",
        "description": campus or "请联系学校心理咨询中心/当地精神卫生中心",
    }
    # Reject rather than truncate a malformed/overlong phone: a prefix could be wrong.
    if re.fullmatch(r"\+?[0-9][0-9 ()-]{2,39}", hotline):
        return [
            {
                "name": "心理援助热线",
                "phone": hotline,
                "description": "请核实服务地区与开放时间。",
            },
            general,
        ]
    return [general]
