"""O-1：预警数据的跨用户隔离与一致性（只加测试，不改生产代码）。

覆盖场景：
- A 用户不能读/改/删 B 用户的预警（列表 / 统计 / 单条已读 / 删除）；
- 未读同类型预警去重；
- 删除后列表与统计保持一致；
- 由量表危机触发的跨域预警只落在本人，不泄漏给他人，量表数据相互隔离。
"""

import pytest
from httpx import ASGITransport, AsyncClient

import models
from auth import create_access_token, get_password_hash


async def _client(app, user):
    token = create_access_token(data={"sub": str(user.id)})
    ac = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    ac.headers["Authorization"] = f"Bearer {token}"
    return ac


def _make_user(db, name):
    user = models.User(
        name=name, password_hash=get_password_hash("pw123456"), invite_code="health2026"
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def _add_warning(
    db,
    user_id,
    *,
    warning_type="高血压",
    warning_level="danger",
    is_read=False,
    content="血压偏高，请及时就医",
):
    row = models.HealthWarning(
        user_id=user_id,
        warning_type=warning_type,
        warning_level=warning_level,
        warning_content=content,
        is_read=is_read,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _add_health_record(db, user_id, **kwargs):
    rec = models.HealthRecord(user_id=user_id, **kwargs)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@pytest.mark.asyncio
async def test_warning_list_only_returns_current_user(app, db):
    a = _make_user(db, "alice")
    b = _make_user(db, "bob")
    _add_warning(db, a.id)
    _add_warning(db, b.id)
    _add_warning(db, b.id, warning_type="BMI 过高")

    async with await _client(app, a) as ac:
        resp = await ac.get("/api/warning/list")

    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["user_id"] == a.id


@pytest.mark.asyncio
async def test_warning_stats_is_isolated_between_users(app, db):
    a = _make_user(db, "alice")
    b = _make_user(db, "bob")
    _add_warning(db, a.id)
    _add_warning(db, b.id, is_read=True)

    async with await _client(app, a) as ac:
        a_stats = (await ac.get("/api/warning/stats")).json()
    async with await _client(app, b) as ac:
        b_stats = (await ac.get("/api/warning/stats")).json()

    assert a_stats == {"total": 1, "unread": 1, "danger": 1}
    assert b_stats == {"total": 1, "unread": 0, "danger": 0}


@pytest.mark.asyncio
async def test_cannot_mark_other_users_warning_read(app, db):
    a = _make_user(db, "alice")
    b = _make_user(db, "bob")
    b_warn = _add_warning(db, b.id)

    async with await _client(app, a) as ac:
        resp = await ac.put(f"/api/warning/read/{b_warn.id}")

    assert resp.status_code == 404
    assert db.get(models.HealthWarning, b_warn.id).is_read is False


@pytest.mark.asyncio
async def test_cannot_delete_other_users_warning(app, db):
    a = _make_user(db, "alice")
    b = _make_user(db, "bob")
    b_warn = _add_warning(db, b.id)

    async with await _client(app, a) as ac:
        resp = await ac.delete(f"/api/warning/{b_warn.id}")

    assert resp.status_code == 404
    assert db.get(models.HealthWarning, b_warn.id) is not None


@pytest.mark.asyncio
async def test_mark_all_read_only_affects_self(app, db):
    a = _make_user(db, "alice")
    b = _make_user(db, "bob")
    _add_warning(db, a.id)
    _add_warning(db, b.id)

    async with await _client(app, a) as ac:
        assert (await ac.put("/api/warning/read-all")).status_code == 200

    assert db.query(models.HealthWarning).filter_by(user_id=a.id).first().is_read is True
    assert db.query(models.HealthWarning).filter_by(user_id=b.id).first().is_read is False


@pytest.mark.asyncio
async def test_delete_own_warning_keeps_list_and_stats_consistent(app, db):
    a = _make_user(db, "alice")
    warn = _add_warning(db, a.id)

    async with await _client(app, a) as ac:
        assert (await ac.delete(f"/api/warning/{warn.id}")).status_code == 200
        listing = (await ac.get("/api/warning/list")).json()
        stats = (await ac.get("/api/warning/stats")).json()

    assert listing == []
    assert stats == {"total": 0, "unread": 0, "danger": 0}


@pytest.mark.asyncio
async def test_check_dedups_unread_same_type(app, db):
    a = _make_user(db, "alice")
    _add_health_record(db, a.id, bmi=30.0)

    async with await _client(app, a) as ac:
        for _ in range(2):
            resp = await ac.post("/api/warning/check")
            assert resp.status_code == 200
        listing = (await ac.get("/api/warning/list")).json()

    types = [w["warning_type"] for w in listing]
    assert types.count("BMI 过高") == 1, f"同类型未读预警应去重，实际 {types}"


@pytest.mark.asyncio
async def test_scale_crisis_warning_is_private(app, db):
    from services import mental_service

    a = _make_user(db, "alice")
    b = _make_user(db, "bob")
    mental_service.save_assessment(db, a.id, "phq9", [3] * 9)

    async with await _client(app, a) as ac:
        assert (await ac.post("/api/warning/check")).status_code == 200
        a_list = (await ac.get("/api/warning/list")).json()
    async with await _client(app, b) as ac:
        b_list = (await ac.get("/api/warning/list")).json()
        b_stats = (await ac.get("/api/warning/stats")).json()

    a_types = [w["warning_type"] for w in a_list]
    assert "心理状态需关注" in a_types
    assert all(w["user_id"] == a.id for w in a_list)
    assert b_list == []
    assert b_stats["total"] == 0


@pytest.mark.asyncio
async def test_scale_history_does_not_leak_between_users(app, db):
    from services.mental_service import assessment_history, save_assessment

    a = _make_user(db, "alice")
    b = _make_user(db, "bob")
    save_assessment(db, a.id, "phq9", [3] * 9)

    assert [row["id"] for row in assessment_history(db, a.id)] != []
    assert assessment_history(db, b.id) == []
