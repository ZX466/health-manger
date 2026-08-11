"""Tests for chat write durability (regression: writes were never committed).

Reproduces: chat_session.create_session / add_message / delete_session only
called db.flush(), and routers never committed -> the request's session close
rolled the transaction back, silently losing sessions/messages.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base
import models  # noqa: F401 - register model tables with Base.metadata
import chat_session
from chat_session import create_session, add_message, delete_session


def _make_engine():
    # StaticPool: share ONE in-memory connection across sessions so committed
    # data is visible from a second session (same as a real file DB).
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def test_session_and_messages_survive_session_close():
    """A created session and its messages must be durable after the writing session closes."""
    eng = _make_engine()
    Base.metadata.create_all(bind=eng)

    s1 = Session(eng)
    session = create_session(db=s1, user_id=1, title="persist-test")
    session_id = session.id  # capture while attached (commit expires attributes)
    add_message(db=s1, session_id=session_id, role="user", content="hello")
    s1.close()  # simulate request end (previously rolled back uncommitted writes)

    s2 = Session(eng)
    try:
        persisted = s2.query(chat_session.ChatSession).filter_by(id=session_id).first()
        assert persisted is not None, "会话未落库：create_session 没有 commit"
        assert persisted.title == "persist-test"

        msgs = (
            s2.query(chat_session.ChatMessage)
            .filter_by(session_id=session_id)
            .all()
        )
        assert len(msgs) == 1, "消息未落库：add_message 没有 commit"
        assert msgs[0].content == "hello"
    finally:
        s2.close()


def test_delete_session_is_durable():
    """Deleting a session must remove it durably (previously the delete was never committed)."""
    eng = _make_engine()
    Base.metadata.create_all(bind=eng)

    s1 = Session(eng)
    session = create_session(db=s1, user_id=1)
    session_id = session.id  # capture while attached
    add_message(db=s1, session_id=session_id, role="user", content="x")
    s1.close()

    s2 = Session(eng)
    ok = delete_session(db=s2, session_id=session_id, user_id=1)
    assert ok is True
    s2.close()

    s3 = Session(eng)
    try:
        gone = s3.query(chat_session.ChatSession).filter_by(id=session_id).first()
        assert gone is None, "删除未生效：delete_session 没有 commit"
    finally:
        s3.close()
