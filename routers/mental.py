"""心理维度接口（每日打卡 / PHQ-9 / GAD-7 / 汇总）。

路由只负责鉴权、结构校验、限流与响应装配；业务落库全部委托
`services.mental_service`，危机资源由 `services.safety_service` 提供。
这些服务由并行任务落地，故在函数内延迟导入，保证服务未就绪时应用仍可启动。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db
from services.scale_scoring import SCALES, score
from services.security_service import check_rate_limit
from services.warning_service import safe_check_health_warnings

router = APIRouter(prefix="/api/mental", tags=["心理健康"])

SCALE_DAILY_LIMIT = 3
SCALE_DAILY_WINDOW_SECONDS = 86400


def _mental_service():
    from services import mental_service

    return mental_service


def _crisis_resources() -> list[dict]:
    """危机支持资源（热线/校心理中心）由安全模块按环境变量提供；未配置时为空列表。"""
    try:
        from services.safety_service import crisis_resources
    except (ImportError, AttributeError):
        return []
    return list(crisis_resources())


@router.post("/mood", response_model=schemas.MentalRecordResponse)
def upsert_mood(
    payload: schemas.MoodUpsert,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """每日心理打卡：同一用户同一天重复提交即更新。"""
    return _mental_service().upsert_mood(
        db,
        current_user.id,
        mood_score=payload.mood_score,
        stress_tags=payload.stress_tags,
        sleep_hours=payload.sleep_hours,
        note=payload.note,
    )


@router.get("/mood", response_model=list[schemas.MentalRecordResponse])
def list_moods(
    days: int = Query(30, ge=1, le=365),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _mental_service().list_moods(db, current_user.id, days=days)


@router.get("/trend", response_model=schemas.MoodTrendResponse)
def get_mood_trend(
    days: int = Query(30, ge=1, le=365),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _mental_service().trend(db, current_user.id, days=days)


@router.get("/scales", response_model=list[schemas.ScaleInfoResponse])
def list_scales(current_user: models.User = Depends(get_current_user)):
    """量表定义由评分模块生成，前端不硬编码题目与选项。"""
    return [scale_def.to_dict() for scale_def in SCALES.values()]


@router.get("/scales/history", response_model=list[schemas.ScaleAssessmentResponse])
def list_scale_history(
    scale_type: str | None = Query(None, max_length=16),
    limit: int = Query(20, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if scale_type is not None and scale_type not in SCALES:
        raise HTTPException(status_code=400, detail=f"未知量表类型: {scale_type}")
    return _mental_service().assessment_history(db, current_user.id, scale_type, limit=limit)


@router.post("/scales/{scale_type}/submit", response_model=schemas.ScaleSubmitResponse)
def submit_scale(
    scale_type: str,
    payload: schemas.ScaleSubmitRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交量表作答：先校验量表与作答，再限流（每类每天 3 次），最后落库。"""
    try:
        result = score(scale_type, payload.answers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    check_rate_limit(
        f"scale:{current_user.id}:{scale_type}",
        SCALE_DAILY_LIMIT,
        SCALE_DAILY_WINDOW_SECONDS,
    )

    assessment, _ = _mental_service().save_assessment(
        db, current_user.id, scale_type, payload.answers
    )
    safe_check_health_warnings(current_user.id, db)
    return {
        "id": getattr(assessment, "id", None),
        **result.to_dict(),
        "resources": _crisis_resources() if result.crisis_flag else [],
    }


@router.get("/summary", response_model=schemas.MentalSummaryResponse)
def get_mental_summary(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _mental_service().summary(db, current_user.id)
