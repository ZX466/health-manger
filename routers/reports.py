"""健康周报接口：规则聚合 + 可选 AI 解读。"""

import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db
from services.ai_config_service import build_llm_config_for_user
from services.llm_service import LLMConfig, call_llm
from services.security_service import check_rate_limit
from services.weekly_report_service import (
    build_weekly_ai_messages,
    build_weekly_report,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["健康周报"])

# 推理型模型可能先消耗隐藏思考 token，留足预算避免正文被截断。
_WEEKLY_AI_CONFIG = LLMConfig(temperature=0.7, max_tokens=3000)
_WEEKLY_AI_RATE_LIMIT = 5
_WEEKLY_AI_WINDOW_SECONDS = 3600
NO_AI_KEY_DETAIL = "未配置 AI API 密钥，请在「AI 设置」中完善后重试"
EMPTY_WEEK_DETAIL = "本周还没有健康数据，先记录几天再来生成解读"
CRISIS_AI_DETAIL = (
    "本周出现需要认真对待的心理信号，请先联系学校心理咨询中心；"
    "如有危机想法，请立即拨打 120 或 12356"
)


@router.get("/weekly", response_model=schemas.WeeklyReportResponse)
def get_weekly_report(
    end_date: date | None = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """近 7 天健康周报；end_date 缺省为今天，窗口含 end_date 当天。"""
    return build_weekly_report(db, current_user.id, end_date=end_date)


@router.post("/weekly/ai", response_model=schemas.WeeklyReportAIResponse)
async def generate_weekly_ai(
    end_date: date | None = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """让 AI 基于周报事实写一段解读；数据不足时不生成，避免编造。"""
    report = build_weekly_report(db, current_user.id, end_date=end_date)
    if not report["has_data"]:
        raise HTTPException(status_code=400, detail=EMPTY_WEEK_DETAIL)
    if report["crisis_flag"]:
        raise HTTPException(status_code=400, detail=CRISIS_AI_DETAIL)

    check_rate_limit(
        f"weekly_ai:{current_user.id}",
        _WEEKLY_AI_RATE_LIMIT,
        _WEEKLY_AI_WINDOW_SECONDS,
    )

    try:
        content, _ = await call_llm(
            build_weekly_ai_messages(report),
            build_llm_config_for_user(db, current_user.id, _WEEKLY_AI_CONFIG),
        )
    except Exception as exc:
        if isinstance(exc, ValueError) and "密钥" in str(exc):
            raise HTTPException(status_code=503, detail=NO_AI_KEY_DETAIL) from exc
        logger.error("健康周报 AI 解读失败 (error=%s)", type(exc).__name__)
        raise HTTPException(status_code=500, detail="AI 解读失败，请稍后重试") from exc

    return {"content": content, "generated_at": datetime.now()}
