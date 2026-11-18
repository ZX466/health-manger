"""K-3：AI 分析路由契约与错误行为测试（mock LLM，不触网）。"""

from unittest.mock import AsyncMock, patch

import pytest

import models
from services.cache_service import llm_response_cache


def _seed_health_record(db, user_id: int, **kwargs) -> models.HealthRecord:
    record = models.HealthRecord(user_id=user_id, height=175.0, weight=70.0, bmi=22.86, **kwargs)
    db.add(record)
    db.flush()
    return record


def _seed_analysis(db, user_id: int, content: str = "旧分析") -> models.AIAnalysis:
    row = models.AIAnalysis(
        user_id=user_id,
        request_content="请分析",
        response_content=content,
        analysis_type="健康咨询",
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture(autouse=True)
def _clear_llm_cache():
    llm_response_cache.clear()
    yield
    llm_response_cache.clear()


# ── 鉴权 ──────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/api/ai/analysis"),
        ("get", "/api/ai/analysis/history"),
        ("get", "/api/ai/analysis/1"),
        ("delete", "/api/ai/analysis/1"),
        ("post", "/api/ai/quick-analysis"),
        ("post", "/api/ai/health-evaluation"),
        ("post", "/api/ai/async-analysis"),
        ("get", "/api/ai/task/whatever"),
    ],
)
async def test_ai_endpoints_require_auth(anon_client, method, path):
    kwargs = {"json": {"request_content": "你好"}} if method == "post" else {}
    resp = await getattr(anon_client, method)(path, **kwargs)
    assert resp.status_code == 401


# ── POST /analysis ────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analysis_without_health_data_returns_400(client):
    resp = await client.post("/api/ai/analysis", json={"request_content": "帮我看看"})
    assert resp.status_code == 400
    assert "健康" in resp.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analysis_success_persists_record(client, db, test_user):
    _seed_health_record(db, test_user.id)
    with patch(
        "routers.ai_analysis.call_llm",
        new=AsyncMock(return_value=("建议保持规律作息", 42)),
    ):
        resp = await client.post(
            "/api/ai/analysis", json={"request_content": "帮我看看", "analysis_type": "健康咨询"}
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["response_content"] == "建议保持规律作息"
    assert body["tokens_used"] == 42
    assert body["analysis_type"] == "健康咨询"
    assert body["user_id"] == test_user.id

    saved = db.get(models.AIAnalysis, body["id"])
    assert saved is not None and saved.response_content == "建议保持规律作息"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analysis_without_api_key_returns_503_and_writes_nothing(client, db, test_user):
    _seed_health_record(db, test_user.id)
    with patch(
        "routers.ai_analysis.call_llm",
        new=AsyncMock(side_effect=ValueError("未配置 AI API 密钥")),
    ):
        resp = await client.post("/api/ai/analysis", json={"request_content": "帮我看看"})

    assert resp.status_code == 503
    assert "AI 设置" in resp.json()["detail"]
    assert db.query(models.AIAnalysis).filter_by(user_id=test_user.id).count() == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analysis_upstream_failure_returns_500_and_writes_nothing(client, db, test_user):
    _seed_health_record(db, test_user.id)
    with patch(
        "routers.ai_analysis.call_llm",
        new=AsyncMock(side_effect=RuntimeError("AI 服务响应超时")),
    ):
        resp = await client.post("/api/ai/analysis", json={"request_content": "帮我看看"})

    assert resp.status_code == 500
    assert "稍后重试" in resp.json()["detail"]
    assert db.query(models.AIAnalysis).filter_by(user_id=test_user.id).count() == 0


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize(
    "payload",
    [
        {"request_content": ""},
        {"request_content": "x" * 5001},
        {},
    ],
)
async def test_analysis_rejects_invalid_payload(client, payload):
    resp = await client.post("/api/ai/analysis", json=payload)
    assert resp.status_code == 422


# ── GET/DELETE /analysis/{id} ─────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_analysis_returns_own_record(client, db, test_user):
    row = _seed_analysis(db, test_user.id, "我的分析")
    resp = await client.get(f"/api/ai/analysis/{row.id}")
    assert resp.status_code == 200
    assert resp.json()["response_content"] == "我的分析"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_analysis_of_other_user_returns_404(client, db):
    other = models.User(name="ai-other-get", password_hash="x", invite_code="health2026")
    db.add(other)
    db.flush()
    row = _seed_analysis(db, other.id, "别人的分析")

    resp = await client.get(f"/api/ai/analysis/{row.id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_missing_analysis_returns_404(client):
    resp = await client.get("/api/ai/analysis/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_analysis_removes_only_own(client, db, test_user):
    own = _seed_analysis(db, test_user.id)
    other = models.User(name="ai-other-del", password_hash="x", invite_code="health2026")
    db.add(other)
    db.flush()
    foreign = _seed_analysis(db, other.id)

    assert (await client.delete(f"/api/ai/analysis/{own.id}")).status_code == 200
    assert db.get(models.AIAnalysis, own.id) is None

    assert (await client.delete(f"/api/ai/analysis/{foreign.id}")).status_code == 404
    assert db.get(models.AIAnalysis, foreign.id) is not None


# ── GET /analysis/history ─────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_history_isolates_users_and_validates_limit(client, db, test_user):
    _seed_analysis(db, test_user.id, "自己的")
    other = models.User(name="ai-other-hist", password_hash="x", invite_code="health2026")
    db.add(other)
    db.flush()
    _seed_analysis(db, other.id, "别人的")

    resp = await client.get("/api/ai/analysis/history")
    assert resp.status_code == 200
    contents = [item["response_content"] for item in resp.json()]
    assert contents == ["自己的"]

    assert (await client.get("/api/ai/analysis/history?limit=0")).status_code == 422
    assert (await client.get("/api/ai/analysis/history?limit=101")).status_code == 422


# ── POST /quick-analysis ──────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_quick_analysis_without_health_data_returns_400(client):
    resp = await client.post("/api/ai/quick-analysis")
    assert resp.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_quick_analysis_success_and_cache(client, db, test_user):
    _seed_health_record(db, test_user.id)
    mocked = AsyncMock(return_value=("快速结论", 7))
    with patch("routers.ai_analysis.call_llm", new=mocked):
        first = await client.post("/api/ai/quick-analysis")
        second = await client.post("/api/ai/quick-analysis")

    assert first.status_code == 200
    assert first.json()["cached"] is False
    assert second.status_code == 200
    assert second.json()["cached"] is True
    assert mocked.await_count == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_quick_analysis_missing_key_returns_503(client, db, test_user):
    _seed_health_record(db, test_user.id)
    with patch(
        "routers.ai_analysis.call_llm",
        new=AsyncMock(side_effect=ValueError("未配置 AI API 密钥")),
    ):
        resp = await client.post("/api/ai/quick-analysis")
    assert resp.status_code == 503


# ── POST /health-evaluation ───────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_evaluation_without_rule_score_returns_400(client, db, test_user):
    _seed_health_record(db, test_user.id)
    resp = await client.post("/api/ai/health-evaluation")
    assert resp.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_evaluation_success(client, db, test_user):
    _seed_health_record(db, test_user.id)
    db.add(
        models.HealthAnalysis(
            user_id=test_user.id,
            health_rating="良好",
            health_score=88,
        )
    )
    db.flush()
    with patch(
        "routers.ai_analysis.call_llm",
        new=AsyncMock(return_value=("综合评价", 15)),
    ):
        resp = await client.post("/api/ai/health-evaluation")

    assert resp.status_code == 200
    body = resp.json()
    assert body["rule_score"] == 88
    assert body["rule_rating"] == "良好"
    assert body["llm_evaluation"] == "综合评价"
    assert body["analysis_id"]


# ── async 任务 ────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_async_analysis_requires_health_data(client):
    resp = await client.post("/api/ai/async-analysis", json={"request_content": "分析"})
    assert resp.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_async_analysis_submits_and_status_is_pollable(client, db, test_user):
    _seed_health_record(db, test_user.id)
    resp = await client.post("/api/ai/async-analysis", json={"request_content": "分析"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending"
    assert body["task_id"]

    status = await client.get(f"/api/ai/task/{body['task_id']}")
    assert status.status_code == 200
    assert status.json()["task_id"] == body["task_id"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_task_status_unknown_id_returns_404(client):
    resp = await client.get("/api/ai/task/not-a-task")
    assert resp.status_code == 404


def test_run_llm_sync_returns_json_serializable_result(monkeypatch):
    from routers import ai_analysis

    async def fake_call_llm(messages, config):
        return "同步包装结果", 7

    monkeypatch.setattr(ai_analysis, "call_llm", fake_call_llm)
    result = ai_analysis._run_llm_sync([], object())
    assert result == {"content": "同步包装结果", "tokens_used": 7}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_completed_task_result_is_persisted_once(client, db, test_user):
    from async_tasks import TaskResult, task_queue

    task_id = "async-persist-test"
    result = TaskResult(task_id, user_id=test_user.id)
    result.set_completed({"content": "异步健康建议", "tokens_used": 9})
    task_queue.results[task_id] = result
    try:
        first = await client.get(f"/api/ai/task/{task_id}")
        assert first.status_code == 200
        body = first.json()
        assert body["result"]["content"] == "异步健康建议"
        analysis_id = body["result"]["analysis_id"]
        assert analysis_id

        second = await client.get(f"/api/ai/task/{task_id}")
        assert second.status_code == 200
        assert second.json()["result"]["analysis_id"] == analysis_id

        rows = (
            db.query(models.AIAnalysis)
            .filter(models.AIAnalysis.user_id == test_user.id)
            .all()
        )
        assert len(rows) == 1
        assert rows[0].response_content == "异步健康建议"
        assert rows[0].analysis_type == "AI 异步分析"
    finally:
        task_queue.results.pop(task_id, None)
