"""O-1：AI 分析数据的持久化与跨用户隔离（只加测试，不改生产代码）。

覆盖场景：
- A 用户不能读/改/删 B 用户的分析（历史 / 详情 / 删除）；
- 删除后历史与详情保持一致；
- 创建分析与快速分析只落库到本人，且 B 不可见；
- 持久化内容（user_id / 类型 / 内容 / tokens）与请求一致。
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

import models
from auth import create_access_token, get_password_hash
from services.cache_service import TTLCache


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


def _add_analysis(
    db,
    user_id,
    *,
    request_content="请分析我的健康",
    response_content="分析结果",
    analysis_type="健康咨询",
):
    row = models.AIAnalysis(
        user_id=user_id,
        request_content=request_content,
        response_content=response_content,
        analysis_type=analysis_type,
        tokens_used=10,
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
async def test_analysis_history_is_isolated_between_users(app, db):
    a = _make_user(db, "alice")
    b = _make_user(db, "bob")
    _add_analysis(db, a.id)
    _add_analysis(db, b.id)

    async with await _client(app, a) as ac:
        rows = (await ac.get("/api/ai/analysis/history")).json()

    assert len(rows) == 1
    assert rows[0]["user_id"] == a.id


@pytest.mark.asyncio
async def test_cannot_get_other_users_analysis(app, db):
    a = _make_user(db, "alice")
    b = _make_user(db, "bob")
    b_analysis = _add_analysis(db, b.id)

    async with await _client(app, a) as ac:
        resp = await ac.get(f"/api/ai/analysis/{b_analysis.id}")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cannot_delete_other_users_analysis(app, db):
    a = _make_user(db, "alice")
    b = _make_user(db, "bob")
    b_analysis = _add_analysis(db, b.id)

    async with await _client(app, a) as ac:
        resp = await ac.delete(f"/api/ai/analysis/{b_analysis.id}")

    assert resp.status_code == 404
    assert db.get(models.AIAnalysis, b_analysis.id) is not None


@pytest.mark.asyncio
async def test_delete_own_analysis_keeps_history_and_detail_consistent(app, db):
    a = _make_user(db, "alice")
    own = _add_analysis(db, a.id)

    async with await _client(app, a) as ac:
        assert (await ac.delete(f"/api/ai/analysis/{own.id}")).status_code == 200
        history = (await ac.get("/api/ai/analysis/history")).json()
        detail = await ac.get(f"/api/ai/analysis/{own.id}")

    assert history == []
    assert detail.status_code == 404


@pytest.mark.asyncio
async def test_create_analysis_persists_for_current_user(app, db):
    import routers.ai_analysis as ai_router

    a = _make_user(db, "alice")
    b = _make_user(db, "bob")
    _add_health_record(db, a.id, height=170, weight=70)

    async with await _client(app, a) as ac:
        with (
            patch("routers.ai_analysis.check_rate_limit"),
            patch.object(ai_router, "call_llm", new=AsyncMock(return_value=("定制化回答", 33))),
        ):
            resp = await ac.post("/api/ai/analysis", json={"request_content": "请评估"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == a.id
    assert body["response_content"] == "定制化回答"
    assert body["tokens_used"] == 33

    async with await _client(app, b) as ac:
        b_history = (await ac.get("/api/ai/analysis/history")).json()
    assert b_history == []


@pytest.mark.asyncio
async def test_quick_analysis_persists_and_is_isolated(app, db, monkeypatch):
    import routers.ai_analysis as ai_router

    a = _make_user(db, "alice")
    _add_health_record(db, a.id, height=170, weight=70)
    monkeypatch.setattr(ai_router, "llm_response_cache", TTLCache())

    async with await _client(app, a) as ac:
        with (
            patch("routers.ai_analysis.check_rate_limit"),
            patch.object(ai_router, "call_llm", new=AsyncMock(return_value=("快速结论", 7))),
        ):
            resp = await ac.post("/api/ai/quick-analysis")

    assert resp.status_code == 200
    assert resp.json()["message"] == "分析成功"

    async with await _client(app, a) as ac:
        rows = (await ac.get("/api/ai/analysis/history")).json()

    assert len(rows) == 1
    assert rows[0]["user_id"] == a.id
    assert rows[0]["analysis_type"] == "快速健康分析"
    assert rows[0]["response_content"] == "快速结论"
