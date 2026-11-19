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


class SessionMissingError(ValueError):
    """目标会话不存在（或编号已被替换会话复用）：写入/删除必须放弃。"""

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
    expected_user_id: int | None = None,
    expected_created_at: datetime | None = None,
) -> ChatMessage:
    """Add a message to a chat session.

    会话可能在流式生成期间被用户删除（SQLite 默认未开启外键约束），
    且 SQLite 整数主键会复用编号。这里用单条
    ``INSERT ... SELECT ... WHERE 会话存在（且身份匹配）`` 原子完成校验与写入：
    - 避免「检查后、写入前」被并发删除的窗口（TOCTOU）；
    - 传入 ``expected_user_id`` / ``expected_created_at``（请求开始时捕获的
      会话生命周期身份）时，即使编号被新会话复用，晚到的回复也不会误入新会话。
    """
    filters = [ChatSession.id == session_id]
    if expected_user_id is not None:
        filters.append(ChatSession.user_id == expected_user_id)
    if expected_created_at is not None:
        filters.append(ChatSession.created_at == expected_created_at)

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
            .where(*filters),
        )
        .returning(ChatMessage.id)
    )
    row = db.execute(stmt).first()
    db.commit()
    if row is None:
        raise SessionMissingError(f"chat session {session_id} does not exist")
    message = db.get(ChatMessage, row[0])
    if message is None:  # pragma: no cover - 提交后同一事务内不应缺失
        raise SessionMissingError(f"chat session {session_id} does not exist")
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


def _purge_session_messages(
    db: Session,
    session_id: int,
    created_at: datetime,
) -> None:
    """只清理属于指定生命周期（id + created_at）的会话消息。

    编号可能被替换会话复用；子表清理若不绑定原会话身份，
    会把替换会话的消息一起删掉。
    """
    original_exists = (
        select(ChatSession.id)
        .where(
            ChatSession.id == session_id,
            ChatSession.created_at == created_at,
        )
        .exists()
    )
    db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        original_exists,
    ).delete(synchronize_session=False)


def delete_session(
    db: Session,
    session_id: int,
    user_id: int,
) -> bool:
    """Delete a chat session and its messages.

    先清理**原会话**消息、再删会话行（同一事务）：
    - 开启外键且未配置级联的数据库（SQLite PRAGMA / PostgreSQL）也能正常删除；
    - 消息清理与会话删除都绑定生命周期身份（created_at），
      检查之后编号即使被替换会话复用，也不会触碰替换会话。
    """
    session_created_at = (
        db.query(ChatSession.created_at)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        .scalar()
    )
    if session_created_at is None:
        return False

    _purge_session_messages(db, session_id, session_created_at)
    deleted = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
            ChatSession.created_at == session_created_at,
        )
        .delete(synchronize_session=False)
    )
    if not deleted:
        # 检查后原会话已被替换：回滚清理，不提交、不触碰替换会话。
        db.rollback()
        return False
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
