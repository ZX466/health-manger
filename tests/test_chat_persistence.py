"""Tests for chat write durability (regression: writes were never committed).

Reproduces: chat_session.create_session / add_message / delete_session only
called db.flush(), and routers never committed -> the request's session close
rolled the transaction back, silently losing sessions/messages.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import chat_session
import models  # register model tables with Base.metadata；同时用于外键用例
from chat_session import add_message, create_session, delete_session
from database import Base


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

        msgs = s2.query(chat_session.ChatMessage).filter_by(session_id=session_id).all()
        assert len(msgs) == 1, "消息未落库：add_message 没有 commit"
        assert msgs[0].content == "hello"
    finally:
        s2.close()


def test_add_message_refuses_deleted_session():
    """删除会话后晚到的写入必须被拒绝，不能产生无父会话的孤儿消息。"""
    eng = _make_engine()
    Base.metadata.create_all(bind=eng)

    s1 = Session(eng)
    session = create_session(db=s1, user_id=1)
    session_id = session.id
    assert delete_session(db=s1, session_id=session_id, user_id=1) is True

    with pytest.raises(ValueError):
        add_message(db=s1, session_id=session_id, role="assistant", content="late")

    assert s1.query(chat_session.ChatMessage).filter_by(session_id=session_id).count() == 0
    s1.close()


def test_no_orphan_message_when_write_races_delete(tmp_path):
    """两个独立连接交替提交时，不能留下无父会话的消息。"""
    eng = create_engine(f"sqlite:///{tmp_path / 'chat-race.db'}")
    Base.metadata.create_all(bind=eng)

    writer = Session(eng)
    deleter = Session(eng)
    try:
        # 情形 1：消息先提交、删除后执行 —— 删除会话按 session_id 批量清理，消息一并删除
        session = create_session(db=writer, user_id=1)
        session_id = session.id
        add_message(db=writer, session_id=session_id, role="assistant", content="early")
        writer.rollback()  # 释放 add_message 末尾读取打开的事务，避免持锁
        assert delete_session(db=deleter, session_id=session_id, user_id=1) is True
        assert (
            writer.query(chat_session.ChatMessage)
            .filter_by(session_id=session_id)
            .count()
            == 0
        )
        writer.expunge_all()  # SQLite 会复用 rowid，避免 identity map 残留

        # 情形 2：删除先提交、晚到写入 —— 存在性校验与写入同一语句，原子拒绝
        session2 = create_session(db=writer, user_id=1)
        session_id2 = session2.id
        assert delete_session(db=deleter, session_id=session_id2, user_id=1) is True
        with pytest.raises(ValueError):
            add_message(db=writer, session_id=session_id2, role="assistant", content="late")
        assert (
            writer.query(chat_session.ChatMessage)
            .filter_by(session_id=session_id2)
            .count()
            == 0
        )
    finally:
        writer.close()
        deleter.close()
        eng.dispose()


def test_late_reply_does_not_land_in_reused_session_id():
    """SQLite 复用主键编号时，晚到回复必须按会话身份拒绝，不能落入替换会话。"""
    eng = _make_engine()
    Base.metadata.create_all(bind=eng)

    s = Session(eng)
    try:
        old = create_session(db=s, user_id=1)
        old_id = old.id
        old_created_at = old.created_at
        assert delete_session(db=s, session_id=old_id, user_id=1) is True
        s.expunge_all()  # 编号会复用：移出旧对象，避免 identity map 干扰

        replacement = create_session(db=s, user_id=1)
        assert replacement.id == old_id, "SQLite 未复用编号，本用例前提不成立"

        with pytest.raises(ValueError):
            add_message(
                db=s,
                session_id=old_id,
                role="assistant",
                content="late",
                expected_user_id=1,
                expected_created_at=old_created_at,
            )
        assert (
            s.query(chat_session.ChatMessage).filter_by(session_id=old_id).count() == 0
        )
    finally:
        s.close()
        eng.dispose()


def test_delete_session_with_messages_when_foreign_keys_enabled(tmp_path):
    """开启外键的库中，删除带消息的会话必须成功（先清消息、再删会话）。"""
    eng = create_engine(f"sqlite:///{tmp_path / 'fk-delete.db'}")

    @event.listens_for(eng, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=eng)

    s = Session(eng)
    try:
        user = models.User(name="fk-user", password_hash="x", invite_code="health2026")
        s.add(user)
        s.commit()

        session = create_session(db=s, user_id=user.id)
        session_id = session.id
        add_message(db=s, session_id=session_id, role="user", content="hi")
        s.rollback()  # 结束 add_message 末尾读取打开的事务

        assert delete_session(db=s, session_id=session_id, user_id=user.id) is True
        assert s.query(chat_session.ChatMessage).filter_by(session_id=session_id).count() == 0
        assert s.query(chat_session.ChatSession).filter_by(id=session_id).count() == 0
    finally:
        s.close()
        eng.dispose()


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
