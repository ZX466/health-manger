import logging
import uuid

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
import settings
from auth import get_current_user
from database import get_db
from services.cache_service import llm_response_cache, make_cache_key
from services.llm_service import (
    LLMConfig,
    build_health_analysis_prompt,
    build_health_rating_llm_prompt,
    build_quick_analysis_prompt,
    call_llm,
)
from services.security_service import check_rate_limit
from services.ai_config_service import (
    build_llm_config_for_user,
    get_config,
    save_config,
    delete_config,
    decrypt_api_key,
    mask_api_key,
)

router = APIRouter(prefix="/api/ai", tags=["AI 健康分析"])

_ANALYSIS_CONFIG = LLMConfig(temperature=settings.AI_ANALYSIS_TEMPERATURE, max_tokens=settings.AI_ANALYSIS_MAX_TOKENS)
_QUICK_CONFIG = LLMConfig(temperature=settings.AI_QUICK_TEMPERATURE, max_tokens=settings.AI_QUICK_MAX_TOKENS)
_EVALUATION_CONFIG = LLMConfig(temperature=settings.AI_EVAL_TEMPERATURE, max_tokens=settings.AI_EVAL_MAX_TOKENS)


def _extract_health_data(record: models.HealthRecord) -> dict:
    return {
        "身高": f"{record.height}cm" if record.height else "未知",
        "体重": f"{record.weight}kg" if record.weight else "未知",
        "BMI": f"{record.bmi}" if record.bmi else "未知",
        "血压": f"{record.blood_pressure_systolic}/{record.blood_pressure_diastolic}" if record.blood_pressure_systolic else "未知",
        "心率": f"{record.heart_rate}次/分钟" if record.heart_rate else "未知",
        "体温": f"{record.temperature}°C" if record.temperature else "未知",
        "睡眠": f"{record.sleep_hours}小时/天" if record.sleep_hours else "未知",
        "运动频率": record.exercise_frequency or "未知",
        "饮食习惯": record.diet_habit or "未知"
    }


@router.post("/analysis", response_model=schemas.AIAnalysisResponse)
async def create_ai_analysis(
    analysis: schemas.AIAnalysisCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_rate_limit(f"ai_analysis:{current_user.id}", max_requests=settings.AI_ANALYSIS_RATE_LIMIT, window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS)
    health_records = db.query(models.HealthRecord).filter(
        models.HealthRecord.user_id == current_user.id
    ).order_by(models.HealthRecord.record_date.desc()).limit(5).all()

    if not health_records:
        raise HTTPException(status_code=400, detail="暂无健康数据，请先添加健康记录")

    health_data = _extract_health_data(health_records[0])
    messages = build_health_analysis_prompt(health_data, analysis.request_content)

    try:
        response_content, tokens_used = await call_llm(messages, build_llm_config_for_user(db, current_user.id, _ANALYSIS_CONFIG))

        db_analysis = models.AIAnalysis(
            user_id=current_user.id,
            request_content=analysis.request_content,
            response_content=response_content,
            analysis_type=analysis.analysis_type or "健康咨询",
            tokens_used=tokens_used
        )
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)

        return db_analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error("AI 分析失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="AI 分析失败，请稍后重试")


@router.get("/analysis/history", response_model=list[schemas.AIAnalysisResponse])
def get_analysis_history(
    limit: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analyses = db.query(models.AIAnalysis).filter(
        models.AIAnalysis.user_id == current_user.id
    ).order_by(models.AIAnalysis.created_at.desc()).limit(limit).all()

    return analyses


@router.get("/analysis/{analysis_id}", response_model=schemas.AIAnalysisResponse)
def get_analysis(
    analysis_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = db.query(models.AIAnalysis).filter(
        models.AIAnalysis.id == analysis_id,
        models.AIAnalysis.user_id == current_user.id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="分析记录不存在")

    return analysis


@router.delete("/analysis/{analysis_id}", response_model=schemas.MessageResponse)
def delete_analysis(
    analysis_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = db.query(models.AIAnalysis).filter(
        models.AIAnalysis.id == analysis_id,
        models.AIAnalysis.user_id == current_user.id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="分析记录不存在")

    db.delete(analysis)
    db.commit()

    return {"message": "删除成功"}


@router.post("/quick-analysis", response_model=schemas.QuickAnalysisResponse)
async def quick_health_analysis(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_rate_limit(f"ai_quick:{current_user.id}", max_requests=settings.AI_QUICK_RATE_LIMIT, window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS)
    latest_record = db.query(models.HealthRecord).filter(
        models.HealthRecord.user_id == current_user.id
    ).order_by(models.HealthRecord.record_date.desc()).first()

    if not latest_record:
        raise HTTPException(status_code=400, detail="暂无健康数据")

    health_data = _extract_health_data(latest_record)
    cache_key = make_cache_key("quick", str(current_user.id), str(latest_record.id))
    cached = llm_response_cache.get(cache_key)

    if cached:
        response_content, tokens_used = cached
    else:
        messages = build_quick_analysis_prompt(health_data)
        try:
            response_content, tokens_used = await call_llm(messages, build_llm_config_for_user(db, current_user.id, _QUICK_CONFIG))
            llm_response_cache.set(cache_key, (response_content, tokens_used))
        except Exception as e:
            logger.error("AI 快速分析失败: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail="AI 分析失败，请稍后重试")

    db_analysis = models.AIAnalysis(
        user_id=current_user.id,
        request_content="请根据我的最新健康数据，给出全面的健康评估和建议",
        response_content=response_content,
        analysis_type="快速健康分析",
        tokens_used=tokens_used,
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    return {"message": "分析成功", "analysis_id": db_analysis.id, "cached": cached is not None}


@router.post("/health-evaluation", response_model=schemas.HealthEvaluationResponse)
async def llm_health_evaluation(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """LLM 增强健康评价：基于规则评分结果，调用 LLM 进行综合健康评价"""
    check_rate_limit(f"ai_eval:{current_user.id}", max_requests=settings.AI_EVAL_RATE_LIMIT, window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS)

    latest_record = db.query(models.HealthRecord).filter(
        models.HealthRecord.user_id == current_user.id
    ).order_by(models.HealthRecord.record_date.desc()).first()

    if not latest_record:
        raise HTTPException(status_code=400, detail="暂无健康数据，请先添加健康记录")

    latest_analysis = db.query(models.HealthAnalysis).filter(
        models.HealthAnalysis.user_id == current_user.id
    ).order_by(models.HealthAnalysis.analysis_date.desc()).first()

    if not latest_analysis or latest_analysis.health_score is None:
        raise HTTPException(status_code=400, detail="暂无规则评分数据，请先添加含 BMI 的健康记录")

    health_data = _extract_health_data(latest_record)
    cache_key = make_cache_key("eval", str(current_user.id), str(latest_record.id), str(latest_analysis.id))
    cached = llm_response_cache.get(cache_key)

    if cached:
        response_content, tokens_used = cached
    else:
        messages = build_health_rating_llm_prompt(
            health_data,
            rule_score=latest_analysis.health_score,
            rule_rating=latest_analysis.health_rating or "未知",
        )
        try:
            response_content, tokens_used = await call_llm(messages, build_llm_config_for_user(db, current_user.id, _EVALUATION_CONFIG))
            llm_response_cache.set(cache_key, (response_content, tokens_used))
        except Exception as e:
            logger.error("LLM 健康评价失败: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail="健康评价失败，请稍后重试")

    db_eval = models.AIAnalysis(
        user_id=current_user.id,
        request_content=f"基于规则评分 {latest_analysis.health_score}/100（{latest_analysis.health_rating}）的 LLM 综合健康评价",
        response_content=response_content,
        analysis_type="LLM 健康评价",
        tokens_used=tokens_used,
    )
    db.add(db_eval)
    db.commit()
    db.refresh(db_eval)

    return {
        "message": "评价成功",
        "rule_score": latest_analysis.health_score,
        "rule_rating": latest_analysis.health_rating,
        "llm_evaluation": response_content,
        "tokens_used": tokens_used,
        "analysis_id": db_eval.id,
        "cached": cached is not None,
    }


def _run_llm_sync(messages: list, config: LLMConfig) -> tuple:
    """同步包装：在工作线程中运行异步 LLM 调用"""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(call_llm(messages, config))
    finally:
        loop.close()


@router.post("/async-analysis", response_model=schemas.AsyncTaskStatus)
async def async_ai_analysis(
    analysis: schemas.AIAnalysisCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """异步 AI 分析：提交到后台队列，通过 task_id 轮询结果"""
    check_rate_limit(f"ai_async:{current_user.id}", max_requests=5, window_seconds=60)

    health_records = db.query(models.HealthRecord).filter(
        models.HealthRecord.user_id == current_user.id
    ).order_by(models.HealthRecord.record_date.desc()).limit(5).all()

    if not health_records:
        raise HTTPException(status_code=400, detail="暂无健康数据，请先添加健康记录")

    health_data = _extract_health_data(health_records[0])
    messages = build_health_analysis_prompt(health_data, analysis.request_content)

    task_id = uuid.uuid4().hex[:12]

    from async_tasks import task_queue
    task_queue.submit_task(
        task_id,
        _run_llm_sync,
        args=(messages, build_llm_config_for_user(db, current_user.id, _ANALYSIS_CONFIG)),
        user_id=current_user.id,
    )

    return schemas.AsyncTaskStatus(
        task_id=task_id,
        status="pending",
    )


@router.get("/task/{task_id}", response_model=schemas.AsyncTaskStatus)
async def get_task_status(
    task_id: str,
    current_user: models.User = Depends(get_current_user),
):
    """查询异步任务状态"""
    from async_tasks import task_queue
    status = task_queue.get_task_status(task_id, user_id=current_user.id)
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return schemas.AsyncTaskStatus(**status)


# ── AI 配置（每用户自定义供应商/模型） ──────────────

@router.get("/config", response_model=schemas.AIConfigResponse)
def get_ai_config(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户 AI 配置（API Key 仅返回掩码）。"""
    cfg = get_config(db, current_user.id)
    if not cfg:
        return schemas.AIConfigResponse(
            provider="zhipu", model="glm-4.5-Air", base_url=None,
            api_key_masked="", has_api_key=False,
        )
    masked = ""
    if cfg.api_key_encrypted:
        masked = mask_api_key(decrypt_api_key(cfg.api_key_encrypted))
    return schemas.AIConfigResponse(
        provider=cfg.provider,
        model=cfg.model,
        base_url=cfg.base_url,
        api_key_masked=masked,
        has_api_key=bool(cfg.api_key_encrypted),
    )


@router.put("/config", response_model=schemas.AIConfigResponse)
def update_ai_config(
    payload: schemas.AIConfigUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存用户 AI 配置（api_key 为空则保留原值）。"""
    cfg = save_config(
        db, current_user.id,
        provider=payload.provider,
        model=payload.model,
        base_url=payload.base_url,
        api_key=payload.api_key,
    )
    masked = mask_api_key(decrypt_api_key(cfg.api_key_encrypted)) if cfg.api_key_encrypted else ""
    return schemas.AIConfigResponse(
        provider=cfg.provider, model=cfg.model, base_url=cfg.base_url,
        api_key_masked=masked, has_api_key=bool(cfg.api_key_encrypted),
    )


@router.delete("/config", response_model=schemas.MessageResponse)
def remove_ai_config(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """清除用户 AI 配置，恢复默认智谱。"""
    delete_config(db, current_user.id)
    return {"message": "已恢复默认 AI 配置"}


@router.post("/config/test", response_model=schemas.AIConfigTestResponse)
async def test_ai_config(
    payload: schemas.AIConfigUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用提交的配置测试连接（不保存）。api_key 缺省时用已保存的密钥。"""
    api_key = payload.api_key
    if not api_key:
        cfg = get_config(db, current_user.id)
        if cfg and cfg.api_key_encrypted:
            api_key = decrypt_api_key(cfg.api_key_encrypted)

    config = LLMConfig(
        provider=payload.provider,
        model=payload.model,
        base_url=payload.base_url,
        api_key=api_key,
        temperature=0.1,
        max_tokens=8,
    )
    try:
        content, _ = await call_llm(
            [{"role": "user", "content": "ping"}],
            config,
        )
        return schemas.AIConfigTestResponse(success=True, message="连接成功", model=payload.model)
    except Exception as e:
        logger.info("AI 配置测试失败: %s", e)
        return schemas.AIConfigTestResponse(success=False, message=f"连接失败：请检查 Base URL/API Key/模型名")
