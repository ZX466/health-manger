from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from auth import get_current_user
from chat_session import (
    create_session,
    get_session,
    get_user_sessions,
    add_message,
    get_session_messages,
    delete_session,
    message_to_dict,
    get_session_context,
)
from services.llm_service import call_llm, LLMConfig, CHAT_SYSTEM_PROMPT
from services.security_service import check_rate_limit, sanitize_for_prompt
import settings

router = APIRouter(prefix="/api/chat", tags=["聊天会话"])

_CHAT_CONFIG = LLMConfig(temperature=settings.CHAT_TEMPERATURE, max_tokens=settings.CHAT_MAX_TOKENS)


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


@router.get("/sessions", response_model=List[schemas.ChatSessionResponse])
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
    response_model=List[schemas.ChatMessageResponse],
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
    check_rate_limit(f"chat:{current_user.id}", max_requests=settings.CHAT_RATE_LIMIT, window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS)

    session = get_session(db=db, session_id=session_id, user_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    safe_content = sanitize_for_prompt(message_data.content, max_length=2000)

    # 先取历史上下文（不含本次用户消息，因为尚未落库），再把本次用户消息追加给 LLM
    context = get_session_context(db=db, session_id=session_id, max_messages=10)

    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
    messages.extend(context)
    messages.append({"role": "user", "content": safe_content})

    try:
        response_content, tokens_used = await call_llm(messages, _CHAT_CONFIG)

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
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"AI 响应失败：{str(e)}")


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
        raise HTTPException(
            status_code=404, detail="暂无舌诊记录，请先上传舌象图片"
        )

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
