import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

import models
import schemas
import settings
from auth import get_current_user
from chat_session import (
    add_message,
    create_session,
    delete_session,
    get_session,
    get_session_context,
    get_session_messages,
    get_user_sessions,
    message_to_dict,
)
from database import SessionLocal, get_db
from services.ai_config_service import build_llm_config_for_user, get_config
from services.llm_service import CHAT_SYSTEM_PROMPT, LLMConfig, call_llm, stream_llm
from services.safety_service import (
    RiskState,
    assess_user_risk,
    build_system_prompt,
    crisis_resources,
)
from services.security_service import check_rate_limit, sanitize_for_prompt

router = APIRouter(prefix="/api/chat", tags=["聊天会话"])

_CHAT_CONFIG = LLMConfig(temperature=settings.CHAT_TEMPERATURE, max_tokens=settings.CHAT_MAX_TOKENS)

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


def _sse(event: str, data: dict) -> str:
    """组装一条 SSE 事件；data 必须是单行 JSON（换行由 json 转义）。"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // settings.CHARS_PER_TOKEN_ZH)


def _resolve_persona_style(db: Session, user_id: int, risk: RiskState) -> str:
    """高风险/危机强制 clinical：与前端隐藏玩梗同步，不让后端继续输出调侃语气。"""
    if risk.level == "high" or risk.crisis:
        return "clinical"
    config = get_config(db=db, user_id=user_id)
    return getattr(config, "persona_style", None) or "humorous"


def _safety_payload(risk: RiskState) -> dict:
    """api-v2 §4：safety {level, crisis, resources}；resources 仅 crisis 时才有内容。"""
    return {
        "level": risk.level,
        "crisis": risk.crisis,
        "resources": crisis_resources() if risk.crisis else [],
    }


def _build_chat_messages(
    db: Session, user_id: int, context: list[dict], content: str
) -> tuple[list[dict], RiskState]:
    """按用户风险等级生成 system prompt，返回 (messages, risk)。

    `assess_user_risk` 只读不写；`build_system_prompt` 在高风险/危机时
    整体替换人设指令为严肃关怀版本（决策 6）。
    """
    risk = assess_user_risk(db=db, user_id=user_id)
    system_prompt = build_system_prompt(
        base=CHAT_SYSTEM_PROMPT,
        persona_style=_resolve_persona_style(db, user_id, risk),
        risk=risk,
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(context)
    messages.append({"role": "user", "content": content})
    return messages, risk


@router.post("/session", response_model=schemas.ChatSessionResponse)
def create_new_session(
    session_data: schemas.ChatSessionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = create_session(
        db=db,
        user_id=current_user.id,
        title=session_data.title,
        context_type=session_data.context_type,
    )
    return schemas.ChatSessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        context_type=session.context_type,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
    )


@router.get("/sessions", response_model=list[schemas.ChatSessionResponse])
def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = get_user_sessions(db=db, user_id=current_user.id, limit=limit)
    return [
        schemas.ChatSessionResponse(
            id=s.id,
            user_id=s.user_id,
            title=s.title,
            context_type=s.context_type,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=len(s.messages) if s.messages else 0,
        )
        for s in sessions
    ]


@router.get(
    "/session/{session_id}/messages",
    response_model=list[schemas.ChatMessageResponse],
)
def get_messages(
    session_id: int,
    limit: int = Query(50, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_session(db=db, session_id=session_id, user_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    messages = get_session_messages(db=db, session_id=session_id, limit=limit)
    return [schemas.ChatMessageResponse(**message_to_dict(m)) for m in messages]


@router.post("/session/{session_id}/message", response_model=schemas.SendMessageResponse)
async def send_message(
    session_id: int,
    message_data: schemas.ChatMessageCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_rate_limit(
        f"chat:{current_user.id}",
        max_requests=settings.CHAT_RATE_LIMIT,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )

    session = get_session(db=db, session_id=session_id, user_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    safe_content = sanitize_for_prompt(message_data.content, max_length=2000)

    # 先取历史上下文（不含本次用户消息，因为尚未落库），再把本次用户消息追加给 LLM
    context = get_session_context(db=db, session_id=session_id, max_messages=10)

    messages, _risk = _build_chat_messages(db, current_user.id, context, safe_content)

    try:
        response_content, tokens_used = await call_llm(
            messages, build_llm_config_for_user(db, current_user.id, _CHAT_CONFIG)
        )

        # LLM 成功后再一起落库（用户 + assistant），避免半提交：
        # 失败时两者都不落库、db.rollback() 有效、重试不会重复追加用户消息
        add_message(db=db, session_id=session_id, role="user", content=safe_content)
        add_message(
            db=db,
            session_id=session_id,
            role="assistant",
            content=response_content,
            tokens_used=tokens_used,
        )

        return {
            "message": "发送成功",
            "response": response_content,
            "tokens_used": tokens_used,
        }
    except Exception:
        db.rollback()
        logger.exception("AI 响应失败")
        raise HTTPException(status_code=500, detail="AI 响应失败，请稍后重试")


@router.post("/session/{session_id}/stream")
async def stream_message(
    session_id: int,
    message_data: schemas.ChatMessageCreate,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SSE 流式对话（M-PERF1/M-PERF4）。事件顺序：safety → delta* → done|error。"""
    check_rate_limit(
        f"chat:{current_user.id}",
        max_requests=settings.CHAT_RATE_LIMIT,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )

    session = get_session(db=db, session_id=session_id, user_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    safe_content = sanitize_for_prompt(message_data.content, max_length=2000)

    # 先取历史（不含本次消息），再把本次用户消息追加给 LLM
    context = get_session_context(
        db=db,
        session_id=session_id,
        max_messages=settings.CHAT_CONTEXT_MAX_MESSAGES,
    )
    config = build_llm_config_for_user(db, current_user.id, _CHAT_CONFIG)
    messages, risk = _build_chat_messages(db, current_user.id, context, safe_content)
    safety_payload = _safety_payload(risk)

    # 决策 5：用户消息先落库；assistant 仅在完整结束后落库，断开即丢弃半截回复
    add_message(db=db, session_id=session_id, role="user", content=safe_content)

    async def event_stream():
        chunks: list[str] = []
        stream_db = SessionLocal()
        try:
            # 契约：safety 至多 1 次且必发首个；crisis 时附求助资源
            yield _sse("safety", safety_payload)

            try:
                async for piece in stream_llm(messages, config):
                    if await request.is_disconnected():
                        logger.info("客户端断开，中止流式响应 (session=%d)", session_id)
                        return
                    chunks.append(piece)
                    yield _sse("delta", {"content": piece})
            except Exception as exc:
                logger.exception("流式 AI 响应失败 (session=%d)", session_id)
                yield _sse("error", {"detail": _public_stream_error(exc)})
                return

            text = "".join(chunks)
            if not text:
                yield _sse("error", {"detail": "AI 未返回内容，请稍后重试"})
                return

            tokens_used = _estimate_tokens(text)
            stored = add_message(
                db=stream_db,
                session_id=session_id,
                role="assistant",
                content=text,
                tokens_used=tokens_used,
            )
            yield _sse("done", {"message_id": stored.id, "tokens_used": tokens_used})
        finally:
            stream_db.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream; charset=utf-8",
        headers=SSE_HEADERS,
    )


def _public_stream_error(exc: Exception) -> str:
    """对外只暴露安全文案，避免把上游响应体/凭据细节透给前端。"""
    message = str(exc)
    if "超时" in message:
        return "AI 服务响应超时，请稍后重试"
    if "密钥" in message:
        return "未配置 AI API 密钥，请先在 AI 设置中完善"
    if "HTTP 4" in message:
        return "AI 服务拒绝了本次请求，请检查 AI 设置"
    return "AI 响应失败，请稍后重试"


@router.post("/session/{session_id}/tongue-context", response_model=schemas.MessageResponse)
async def create_tongue_context_chat(
    session_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_session(db=db, session_id=session_id, user_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    latest_diagnosis = (
        db.query(models.TongueDiagnosis)
        .filter(
            models.TongueDiagnosis.user_id == current_user.id,
            models.TongueDiagnosis.analysis_status == "completed",
        )
        .order_by(models.TongueDiagnosis.created_at.desc())
        .first()
    )

    if not latest_diagnosis:
        raise HTTPException(status_code=404, detail="暂无舌诊记录，请先上传舌象图片")

    context_message = f"""用户的舌诊结果：
- 舌色：{latest_diagnosis.tongue_color}
- 苔色：{latest_diagnosis.coating_color}
- 苔质：{latest_diagnosis.coating_thickness}
- 舌形：{latest_diagnosis.tongue_shape}
- 润燥：{latest_diagnosis.moisture_level}
- 裂纹：{"有" if latest_diagnosis.has_cracks else "无"}
- 齿痕：{"有" if latest_diagnosis.has_teeth_marks else "无"}
- 中医体质：{latest_diagnosis.tcm_syndrome}
- 整体判断：{latest_diagnosis.overall_type}

请根据以上舌诊结果，为用户提供健康咨询。"""

    add_message(db=db, session_id=session_id, role="system", content=context_message)

    return {"message": "舌诊上下文已添加", "session_id": session_id}


@router.delete("/session/{session_id}", response_model=schemas.MessageResponse)
def delete_chat_session(
    session_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = delete_session(db=db, session_id=session_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {"message": "会话已删除"}
