"""
会话管理模块
参考 TongueDiagnosis 项目的会话管理设计
支持多轮对话和上下文保持
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    insert,
    literal,
    select,
)
from sqlalchemy.orm import Session, relationship

import settings
from database import Base

DEFAULT_MAX_MESSAGES = settings.CHAT_CONTEXT_MAX_MESSAGES
DEFAULT_MAX_TOKENS = settings.CHAT_CONTEXT_MAX_TOKENS
CHARS_PER_TOKEN_ZH = settings.CHARS_PER_TOKEN_ZH


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // CHARS_PER_TOKEN_ZH)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=True)
    context_type = Column(String(50), default="general")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    user = relationship("User", backref="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        order_by="ChatMessage.created_at",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    session = relationship("ChatSession", back_populates="messages")


def create_session(
    db: Session,
    user_id: int,
    title: str | None = None,
    context_type: str = "general",
) -> ChatSession:
    """Create a new chat session for a user."""
    session = ChatSession(
        user_id=user_id,
        title=title or f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        context_type=context_type,
    )
    db.add(session)
    db.commit()
    return session


def get_session(
    db: Session,
    session_id: int,
    user_id: int,
) -> ChatSession | None:
    """Get a chat session by ID, scoped to the owning user."""
    return (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        .first()
    )


def get_user_sessions(
    db: Session,
    user_id: int,
    limit: int = 20,
) -> list[ChatSession]:
    """Get recent chat sessions for a user."""
    return (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == user_id,
        )
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
        .all()
    )


def add_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
    tokens_used: int | None = None,
) -> ChatMessage:
    """Add a message to a chat session.

    会话可能在流式生成期间被用户删除（SQLite 默认未开启外键约束）。
    这里用单条 ``INSERT ... SELECT ... WHERE 会话存在`` 原子完成存在性校验
    与写入，避免「检查后、写入前」被并发删除的窗口（TOCTOU）。
    """
    stmt = (
        insert(ChatMessage)
        .from_select(
            ["session_id", "role", "content", "tokens_used", "created_at"],
            select(
                literal(session_id),
                literal(role),
                literal(content),
                literal(tokens_used, type_=Integer),
                literal(datetime.now(UTC), type_=DateTime),
            )
            .select_from(ChatSession)
            .where(ChatSession.id == session_id),
        )
        .returning(ChatMessage.id)
    )
    row = db.execute(stmt).first()
    db.commit()
    if row is None:
        raise ValueError(f"chat session {session_id} does not exist")
    message = db.get(ChatMessage, row[0])
    if message is None:  # pragma: no cover - 提交后同一事务内不应缺失
        raise ValueError(f"chat session {session_id} does not exist")
    return message


def get_session_messages(
    db: Session,
    session_id: int,
    limit: int = 50,
) -> list[ChatMessage]:
    """Get messages for a chat session in chronological order."""
    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
        )
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )


def get_session_context(
    db: Session,
    session_id: int,
    max_messages: int = DEFAULT_MAX_MESSAGES,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> list[dict[str, str]]:
    """获取最近消息作为 LLM 上下文，支持 token 预算感知截断。

    策略：从最新消息向前累积，直到达到 token 预算或消息数量上限。
    """
    messages = get_session_messages(db, session_id, limit=max_messages * 3)

    if not messages:
        return []

    recent = list(reversed(messages))

    selected: list[ChatMessage] = []
    used_tokens = 0

    for msg in recent:
        msg_tokens = msg.tokens_used or _estimate_tokens(msg.content)

        if selected and used_tokens + msg_tokens > max_tokens:
            break

        selected.append(msg)
        used_tokens += msg_tokens

    selected.reverse()
    return [{"role": msg.role, "content": msg.content} for msg in selected]


def delete_session(
    db: Session,
    session_id: int,
    user_id: int,
) -> bool:
    """Delete a chat session and its messages.

    先删会话行，再按 ``session_id`` 批量清理消息（同一事务）：
    若并发写入在会话行删除后、本事务提交前完成，批量清理仍能把它一并删掉，
    不留无父会话的孤儿消息。
    """
    deleted = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        .delete(synchronize_session=False)
    )
    if not deleted:
        return False

    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete(
        synchronize_session=False
    )
    db.commit()
    return True


def update_session_title(
    db: Session,
    session_id: int,
    user_id: int,
    title: str,
) -> bool:
    """Update the title of a chat session."""
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        .first()
    )

    if not session:
        return False

    session.title = title
    db.flush()
    return True


def session_to_dict(session: ChatSession) -> dict[str, Any]:
    """Convert a ChatSession to a dictionary."""
    return {
        "id": session.id,
        "user_id": session.user_id,
        "title": session.title,
        "context_type": session.context_type,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "message_count": len(session.messages) if session.messages else 0,
    }


def message_to_dict(message: ChatMessage) -> dict[str, Any]:
    """Convert a ChatMessage to a dictionary."""
    return {
        "id": message.id,
        "session_id": message.session_id,
        "role": message.role,
        "content": message.content,
        "tokens_used": message.tokens_used,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }
