"""健康周报：聚合口径、日期窗口、用户隔离与 AI 解读接口测试。"""

from datetime import date, datetime, time, timedelta

import pytest

import models


def _day(offset: int, end: date | None = None) -> date:
    return (end or datetime.now().date()) + timedelta(days=offset)


def _at(day: date, hour: int = 8) -> datetime:
    return datetime.combine(day, time(hour=hour))


def _seed_full_week(
    db, user_id: int, end: date | None = None, *, with_crisis: bool = True
) -> list[date]:
    """写入 4 天完整数据；返回这 4 天（窗口内、从旧到新）。"""
    days = [_day(-6, end), _day(-4, end), _day(-2, end), _day(-1, end)]
    sleeps = [6.0, 7.0, 8.0, 5.0]
    moods = [2, 3, 4, 5]

    for index, day in enumerate(days):
        db.add(
            models.HealthRecord(
                user_id=user_id,
                height=175.0,
                weight=70.0,
                bmi=22.9,
                sleep_hours=sleeps[index],
                record_date=_at(day),
            )
        )
        db.add(
            models.MentalRecord(
                user_id=user_id,
                record_date=day,
                mood_score=moods[index],
                stress_tags='["考试", "熬夜"]' if index == 0 else "[]",
                sleep_hours=sleeps[index],
            )
        )
        db.add(
            models.HealthAnalysis(
                user_id=user_id,
                health_score=70 + index * 10,
                health_rating="良好",
                analysis_date=_at(day, 9),
            )
        )

    food = models.Food(name="周报测试米饭", calories_per_100g=116)
    sport = models.Sport(name="周报测试跑步", calories_per_hour=500)
    db.add_all([food, sport])
    db.flush()

    db.add_all(
        [
            models.UserFoodRecord(
                user_id=user_id,
                food_id=food.id,
                quantity_grams=100,
                calories=500,
                record_date=_at(days[0], 12),
                meal_type="lunch",
            ),
            models.UserFoodRecord(
                user_id=user_id,
                food_id=food.id,
                quantity_grams=100,
                calories=700,
                record_date=_at(days[1], 12),
                meal_type="dinner",
            ),
            models.UserSportRecord(
                user_id=user_id,
                sport_id=sport.id,
                duration_minutes=30,
                calories_burned=200,
                record_date=_at(days[0], 18),
            ),
            models.UserSportRecord(
                user_id=user_id,
                sport_id=sport.id,
                duration_minutes=45,
                calories_burned=300,
                record_date=_at(days[1], 18),
            ),
        ]
    )
    db.add(
        models.HealthWarning(
            user_id=user_id,
            warning_type="test",
            warning_level="danger",
            warning_content="周报测试预警",
            created_at=_at(days[-1], 10),
        )
    )
    if with_crisis:
        db.add(
            models.ScaleAssessment(
                user_id=user_id,
                scale_type="phq9",
                answers="[1]",
                score=15,
                risk_level="moderately_severe",
                crisis_flag=True,
                created_at=_at(days[-1], 11),
            )
        )
    db.flush()
    return days


@pytest.mark.asyncio
@pytest.mark.integration
async def test_empty_week_returns_seven_days_and_no_data(client):
    resp = await client.get("/api/reports/weekly")
    assert resp.status_code == 200
    data = resp.json()

    assert data["has_data"] is False
    assert data["recorded_days"] == 0
    assert data["score_avg"] is None
    assert data["sleep_avg"] is None
    assert data["mood_avg"] is None
    assert len(data["daily"]) == 7
    assert all(day["has_data"] is False for day in data["daily"])
    assert data["daily"][-1]["date"] == datetime.now().date().isoformat()
    assert data["insights"]
    assert data["suggestions"]
    assert data["summary_text"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_week_aggregates_health_food_sport_mood_and_warnings(client, db, test_user):
    days = _seed_full_week(db, test_user.id)

    resp = await client.get("/api/reports/weekly")
    assert resp.status_code == 200
    data = resp.json()

    assert data["has_data"] is True
    assert data["recorded_days"] == 4
    assert data["sleep_days"] == 4
    assert data["sleep_avg"] == 6.5
    assert data["sleep_debt"] == 6.0
    assert data["mood_avg"] == 3.5
    assert data["mood_days"] == 4
    assert data["food_days"] == 2
    assert data["calories_in_avg"] == 600.0
    assert data["sport_days"] == 2
    assert data["sport_minutes_total"] == 75
    assert data["calories_burned_total"] == 500.0
    assert data["warnings_total"] == 1
    assert data["warnings_danger"] == 1
    assert data["crisis_flag"] is True
    assert data["score_avg"] == 85.0
    assert data["score_change"] == 30
    assert data["top_stress_tags"] == ["考试", "熬夜"]

    by_date = {item["date"]: item for item in data["daily"]}
    first = by_date[days[0].isoformat()]
    assert first["sleep_hours"] == 6.0
    assert first["mood_score"] == 2
    assert first["calories_in"] == 500.0
    assert first["sport_minutes"] == 30
    assert first["has_data"] is True

    kinds = {item["kind"] for item in data["insights"]}
    assert "safety" in kinds
    assert "attention" in kinds
    assert any("睡眠" in item["title"] for item in data["insights"])
    assert any("120" in text or "心理" in text for text in data["suggestions"])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_week_window_excludes_old_and_other_users_data(client, db, test_user):
    end = datetime.now().date()
    days = _seed_full_week(db, test_user.id, end=end)

    # 窗口外：8 天前；另一位用户：窗口内
    db.add(
        models.HealthRecord(
            user_id=test_user.id,
            sleep_hours=1.0,
            record_date=_at(_day(-8, end)),
        )
    )
    other = models.User(name="weekly-other", password_hash="x", invite_code="health2026")
    db.add(other)
    db.flush()
    db.add(
        models.HealthRecord(
            user_id=other.id,
            sleep_hours=10.0,
            record_date=_at(_day(-1, end)),
        )
    )
    db.flush()

    resp = await client.get(f"/api/reports/weekly?end_date={end.isoformat()}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["start_date"] == (end - timedelta(days=6)).isoformat()
    assert data["end_date"] == end.isoformat()
    by_date = {item["date"]: item for item in data["daily"]}
    assert by_date[days[-1].isoformat()]["sleep_hours"] == 5.0  # 排除其他用户的 10h
    assert data["sleep_avg"] == 6.5  # 排除窗口外的 1h


@pytest.mark.asyncio
@pytest.mark.integration
async def test_week_report_rejects_invalid_end_date(client):
    resp = await client.get("/api/reports/weekly?end_date=not-a-date")
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ai_report_refuses_empty_week(client):
    resp = await client.post("/api/reports/weekly/ai")
    assert resp.status_code == 400
    assert "数据" in resp.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ai_report_refuses_crisis_week(client, db, test_user, monkeypatch):
    _seed_full_week(db, test_user.id)
    called = False

    async def fake_call(messages, config=None):
        nonlocal called
        called = True
        return "不应被调用", 0

    monkeypatch.setattr("routers.reports.call_llm", fake_call)

    resp = await client.post("/api/reports/weekly/ai")
    assert resp.status_code == 400
    assert "心理咨询" in resp.json()["detail"]
    assert called is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ai_report_calls_llm_with_aggregated_context(client, db, test_user, monkeypatch):
    _seed_full_week(db, test_user.id, with_crisis=False)

    captured = {}

    async def fake_call(messages, config=None):
        captured["messages"] = messages
        return "本周先照顾好睡眠，再保持运动节奏。", 42

    monkeypatch.setattr("routers.reports.call_llm", fake_call)

    resp = await client.post("/api/reports/weekly/ai")
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "本周先照顾好睡眠，再保持运动节奏。"
    assert data["generated_at"]

    prompt = "\n".join(item["content"] for item in captured["messages"])
    assert "6.5" in prompt
    assert "75" in prompt
    assert "诊断" in prompt
    assert "120/12356" in prompt
