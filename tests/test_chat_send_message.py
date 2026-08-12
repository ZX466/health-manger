"""Regression tests for send_message half-commit (review FAIL item ②).

Bug: send_message called add_message(role="user") BEFORE await call_llm, and
add_message commits internally. When call_llm raised, db.rollback() could not
undo the already-committed user message -> the user message persisted without
an assistant reply, and retrying appended duplicate user messages.

Fix: persist user + assistant together only AFTER call_llm succeeds; on
failure neither is written, so rollback is effective and retry is idempotent.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base
import models  # noqa: F401 - register model tables with Base.metadata
import chat_session
from chat_session import ChatMessage, create_session
from routers.chat import send_message
from schemas import ChatMessageCreate


def _make_engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _setup():
    eng = _make_engine()
    Base.metadata.create_all(bind=eng)
    db = Session(eng)
    session = create_session(db=db, user_id=1, title="t")
    return eng, db, session.id


@pytest.mark.asyncio
async def test_send_message_llm_failure_leaves_no_partial_message():
    """LLM 失败时不应落库用户消息（修复半提交 + 重试重复）。"""
    eng, db, session_id = _setup()
    user = SimpleNamespace(id=1)
    msg = ChatMessageCreate(content="hello")

    with patch("routers.chat.check_rate_limit"), \
         patch("routers.chat.call_llm", new=AsyncMock(side_effect=RuntimeError("LLM down"))):
        with pytest.raises(HTTPException) as exc:
            await send_message(
                session_id=session_id,
                message_data=msg,
                current_user=user,
                db=db,
            )
        assert exc.value.status_code == 500

    db2 = Session(eng)
    msgs = db2.query(ChatMessage).filter_by(session_id=session_id).all()
    assert len(msgs) == 0, f"LLM 失败不应落库用户消息，实际 {len(msgs)} 条: {[m.role for m in msgs]}"


@pytest.mark.asyncio
async def test_send_message_llm_success_persists_user_and_assistant():
    """LLM 成功时用户 + assistant 消息都落库。"""
    eng, db, session_id = _setup()
    user = SimpleNamespace(id=1)
    msg = ChatMessageCreate(content="hello")

    with patch("routers.chat.check_rate_limit"), \
         patch("routers.chat.call_llm", new=AsyncMock(return_value=("hi back", 10))):
        result = await send_message(
            session_id=session_id,
            message_data=msg,
            current_user=user,
            db=db,
        )

    assert result["response"] == "hi back"
    db2 = Session(eng)
    msgs = (
        db2.query(ChatMessage)
        .filter_by(session_id=session_id)
        .order_by(ChatMessage.id)
        .all()
    )
    roles = [m.role for m in msgs]
    assert roles == ["user", "assistant"], f"应落库 user+assistant，实际 {roles}"
