"""K-2：GET /api/health/rating/history 契约与隔离测试。"""

from datetime import datetime, timedelta

import pytest

import models


async def _create_record(client, **kwargs) -> dict:
    payload = {"height": 175.0, "weight": 70.0}
    payload.update(kwargs)
    resp = await client.post("/api/health/records", json=payload)
    assert resp.status_code == 200
    return resp.json()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_history_returns_7_day_series_with_today_score(client):
    await _create_record(client)
    resp = await client.get("/api/health/rating/history?days=7")
    assert resp.status_code == 200
    points = resp.json()
    assert len(points) == 7
    dates = [p["date"] for p in points]
    assert dates == sorted(dates)
    assert dates[-1] == datetime.now().date().isoformat()
    assert points[-1]["score"] is not None
    assert points[-1]["level"]
    # 其余缺失日必须有 date 且 score/level 为 null（契约：前端不猜）
    assert all(p["date"] and p["score"] is None and p["level"] is None for p in points[:-1])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_history_supports_30_days(client):
    await _create_record(client)
    resp = await client.get("/api/health/rating/history?days=30")
    assert resp.status_code == 200
    points = resp.json()
    assert len(points) == 30
    assert points[-1]["score"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_history_defaults_to_7_days(client):
    resp = await client.get("/api/health/rating/history")
    assert resp.status_code == 200
    assert len(resp.json()) == 7


@pytest.mark.asyncio
@pytest.mark.integration
async def test_history_empty_data_returns_nulls(client):
    resp = await client.get("/api/health/rating/history?days=7")
    assert resp.status_code == 200
    points = resp.json()
    assert len(points) == 7
    assert all(p["score"] is None and p["level"] is None for p in points)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("days", [0, 1, 14, 31, "abc"])
async def test_history_rejects_invalid_days(client, days):
    resp = await client.get(f"/api/health/rating/history?days={days}")
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_history_isolates_users(client, db, test_user):
    other = models.User(name="other-history", password_hash="x", invite_code="health2026")
    db.add(other)
    db.flush()
    db.add(
        models.HealthAnalysis(
            user_id=other.id,
            health_rating="优秀",
            health_score=98,
            analysis_date=datetime.now(),
        )
    )
    db.flush()

    resp = await client.get("/api/health/rating/history?days=7")
    assert resp.status_code == 200
    points = resp.json()
    assert all(p["score"] is None for p in points), points


@pytest.mark.asyncio
@pytest.mark.integration
async def test_history_keeps_latest_analysis_of_the_day(client, db, test_user):
    old = datetime.now() - timedelta(hours=2)
    db.add_all(
        [
            models.HealthAnalysis(
                user_id=test_user.id, health_rating="中等", health_score=70, analysis_date=old
            ),
            models.HealthAnalysis(
                user_id=test_user.id,
                health_rating="优秀",
                health_score=96,
                analysis_date=datetime.now(),
            ),
        ]
    )
    db.flush()

    resp = await client.get("/api/health/rating/history?days=7")
    assert resp.status_code == 200
    today = resp.json()[-1]
    assert today["score"] == 96
    assert today["level"] == "优秀"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_latest_rating_endpoint_unchanged(client):
    await _create_record(client)
    resp = await client.get("/api/health/rating/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] is not None
    assert data["rating"]
    assert data["emoji"]
