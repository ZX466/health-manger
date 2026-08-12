import uuid

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
        response_content, tokens_used = await call_llm(messages, _ANALYSIS_CONFIG)

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
        raise HTTPException(status_code=500, detail=f"AI 分析失败：{str(e)}")


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
            response_content, tokens_used = await call_llm(messages, _QUICK_CONFIG)
            llm_response_cache.set(cache_key, (response_content, tokens_used))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI 分析失败：{str(e)}")

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
            response_content, tokens_used = await call_llm(messages, _EVALUATION_CONFIG)
            llm_response_cache.set(cache_key, (response_content, tokens_used))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM 健康评价失败：{str(e)}")

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
        args=(messages, _ANALYSIS_CONFIG),
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
