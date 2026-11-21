"""今日一件小事：规则优先级、同日幂等、完成与权限测试。"""

from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

import models
from services import daily_action_service
from services.daily_action_service import (
    DailyActionNotCompletableError,
    DailyActionNotFoundError,
    complete_daily_action,
    generate_daily_action,
)

DAY = date(2026, 11, 16)


def _at(day: date, hour: int = 8) -> datetime:
    """按生产语义构造 UTC naive 时间：本地自然日 hour 点。"""
    local_tz = datetime.now().astimezone().tzinfo
    local = datetime.combine(day, time(hour=hour), tzinfo=local_tz)
    return local.astimezone(UTC).replace(tzinfo=None)


def _health(db, user_id: int, day: date, sleep_hours: float | None = None) -> None:
    db.add(models.HealthRecord(user_id=user_id, sleep_hours=sleep_hours, record_date=_at(day)))
    db.flush()


def _mental(db, user_id: int, day: date, mood_score: int | None = None) -> None:
    db.add(models.MentalRecord(user_id=user_id, record_date=day, mood_score=mood_score))
    db.flush()


def _sport(db, user_id: int, day: date, minutes: int) -> None:
    sport = models.Sport(name="快走")
    db.add(sport)
    db.flush()
    db.add(
        models.UserSportRecord(
            user_id=user_id,
            sport_id=sport.id,
            duration_minutes=minutes,
            record_date=_at(day, 12),
        )
    )
    db.flush()


def _food(db, user_id: int, day: date) -> None:
    food = models.Food(name="测试米饭", calories_per_100g=116)
    db.add(food)
    db.flush()
    db.add(
        models.UserFoodRecord(
            user_id=user_id,
            food_id=food.id,
            quantity_grams=100,
            record_date=_at(day, 12),
        )
    )
    db.flush()


def _crisis(db, user_id: int, at: datetime) -> None:
    db.add(
        models.ScaleAssessment(
            user_id=user_id,
            scale_type="phq9",
            crisis_flag=True,
            created_at=at,
        )
    )
    db.flush()


def _seed_baseline_ok(db, user_id: int) -> None:
    """睡眠达标 + 运动达标，用于观察后续规则。"""
    _health(db, user_id, DAY, 8.0)
    _sport(db, user_id, DAY, 150)


# ---------- 规则优先级（service） ----------


def test_no_data_generates_checkin(db, test_user):
    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["action_key"] == "checkin"
    assert data["kind"] == "action"
    assert data["can_complete"] is True
    assert data["completed"] is False
    assert data["week_completed"] == 0
    assert data["action_date"] == DAY
    assert data["reason"] == "今天还没有健康或心情记录"
    assert data["cta_path"] == "/mental"


def test_utc_record_after_local_midnight_counts_as_today(db, test_user):
    # 生产 record_date 默认 _utcnow；本地 00:30 在 UTC 可能还是前一天，
    # 不能因此把今天的记录误判成“今天没记录”。
    local_tz = datetime.now().astimezone().tzinfo
    local = datetime.combine(DAY, time(0, 30), tzinfo=local_tz)
    record_date = local.astimezone(UTC).replace(tzinfo=None)
    db.add(models.HealthRecord(user_id=test_user.id, record_date=record_date))
    db.flush()

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["action_key"] == "move"


def test_low_sleep_generates_sleep(db, test_user):
    _health(db, test_user.id, DAY, 5.0)

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["action_key"] == "sleep"
    assert data["reason"] == "最近一次睡眠 5.0h，离 7h 还差一点"
    assert data["cta_path"] == "/health-record"


def test_low_sport_generates_move(db, test_user):
    _health(db, test_user.id, DAY, 8.0)
    _sport(db, test_user.id, DAY, 30)

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["action_key"] == "move"
    assert data["reason"] == "近 7 天累计运动 30 分钟，还没到 150 分钟"
    assert data["cta_path"] == "/sport-management"


def test_mental_record_today_skips_checkin(db, test_user):
    _mental(db, test_user.id, DAY, mood_score=4)

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["action_key"] == "move"


def test_low_sleep_from_mental_record(db, test_user):
    db.add(
        models.MentalRecord(
            user_id=test_user.id,
            record_date=DAY,
            mood_score=4,
            sleep_hours=6.0,
        )
    )
    db.flush()

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["action_key"] == "sleep"
    assert data["reason"] == "最近一次睡眠 6.0h，离 7h 还差一点"


def test_sleep_uses_latest_within_two_days(db, test_user):
    _seed_baseline_ok(db, test_user.id)
    _health(db, test_user.id, DAY - timedelta(days=1), 5.0)

    data = generate_daily_action(db, test_user.id, today=DAY)

    # 昨天 5h 被今天 8h 覆盖，睡眠规则不命中，且今天没有饮食记录。
    assert data["action_key"] == "meal"


def test_sleep_two_days_ago_is_outside_window(db, test_user):
    _health(db, test_user.id, DAY - timedelta(days=2), 5.0)
    _seed_baseline_ok(db, test_user.id)
    for offset in range(4):
        day = DAY - timedelta(days=offset)
        _food(db, test_user.id, day)
        _mental(db, test_user.id, day, mood_score=4)

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["action_key"] == "rest"


def test_sport_window_includes_six_days_ago(db, test_user):
    _health(db, test_user.id, DAY, 8.0)
    _sport(db, test_user.id, DAY, 100)
    _sport(db, test_user.id, DAY - timedelta(days=6), 60)

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["action_key"] == "meal"


def test_sport_seven_days_ago_is_outside_window(db, test_user):
    _health(db, test_user.id, DAY, 8.0)
    _sport(db, test_user.id, DAY - timedelta(days=7), 300)

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["action_key"] == "move"
    assert data["reason"] == "近 7 天累计运动 0 分钟，还没到 150 分钟"


def test_low_food_days_generates_meal(db, test_user):
    _seed_baseline_ok(db, test_user.id)
    _food(db, test_user.id, DAY)
    _food(db, test_user.id, DAY - timedelta(days=1))

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["action_key"] == "meal"
    assert data["reason"] == "最近 7 天有 2 天记录了饮食，还没到 4 天"
    assert data["cta_path"] == "/diet-management"


def test_low_mood_generates_breathe(db, test_user):
    _seed_baseline_ok(db, test_user.id)
    for offset in range(4):
        day = DAY - timedelta(days=offset)
        _food(db, test_user.id, day)
        _mental(db, test_user.id, day, mood_score=2)

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["action_key"] == "breathe"
    assert "心情均值 2.0" in data["reason"]
    assert data["cta_path"] == "/mental"


def test_all_good_generates_rest(db, test_user):
    _seed_baseline_ok(db, test_user.id)
    for offset in range(4):
        day = DAY - timedelta(days=offset)
        _food(db, test_user.id, day)
        _mental(db, test_user.id, day, mood_score=4)

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["action_key"] == "rest"
    assert data["kind"] == "rest"
    assert data["cta_path"] == "/weekly-report"


def test_crisis_generates_safety_and_complete_rejected(db, test_user):
    _crisis(db, test_user.id, _at(DAY - timedelta(days=1), 12))

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["action_key"] == "care"
    assert data["kind"] == "safety"
    assert data["can_complete"] is False
    assert data["reason"] == "本周出现过危机标记，优先照顾自己"
    with pytest.raises(DailyActionNotCompletableError):
        complete_daily_action(db, test_user.id, data["id"])


# ---------- 幂等与完成 ----------


def test_same_day_returns_same_action(db, test_user):
    first = generate_daily_action(db, test_user.id, today=DAY)
    second = generate_daily_action(db, test_user.id, today=DAY)

    assert second["id"] == first["id"]
    assert second["action_key"] == first["action_key"]
    rows = db.query(models.DailyAction).filter_by(user_id=test_user.id).all()
    assert len(rows) == 1


def _completed_action(db, user_id: int, day: date) -> models.DailyAction:
    record = models.DailyAction(
        user_id=user_id,
        action_date=day,
        action_key="checkin",
        kind="action",
        title="历史行动",
        description="描述",
        reason="原因",
        cta_label="去打卡",
        cta_path="/mental",
        can_complete=True,
        completed_at=_at(day, 20),
    )
    db.add(record)
    db.flush()
    return record


def test_week_completed_uses_rolling_seven_days(db, test_user):
    _completed_action(db, test_user.id, DAY - timedelta(days=7))
    _completed_action(db, test_user.id, DAY - timedelta(days=6))

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["week_completed"] == 1

    done = complete_daily_action(db, test_user.id, data["id"])
    assert done["week_completed"] == 2


def test_complete_is_idempotent_and_counts_current_week(db, test_user):
    first = generate_daily_action(db, test_user.id, today=DAY)
    assert first["week_completed"] == 0

    done = complete_daily_action(db, test_user.id, first["id"])
    assert done["completed"] is True
    assert done["completed_at"] is not None
    assert done["week_completed"] == 1

    again = complete_daily_action(db, test_user.id, first["id"])
    assert again["completed_at"] == done["completed_at"]
    assert again["week_completed"] == 1

    nxt = generate_daily_action(db, test_user.id, today=DAY + timedelta(days=1))
    assert nxt["week_completed"] == 1
    done_nxt = complete_daily_action(db, test_user.id, nxt["id"])
    assert done_nxt["week_completed"] == 2


def test_complete_other_users_action_raises_not_found(db, test_user):
    other = models.User(name="otheruser", password_hash="x", invite_code="health2026")
    db.add(other)
    db.flush()
    action = models.DailyAction(
        user_id=other.id,
        action_date=DAY,
        action_key="checkin",
        kind="action",
        title="别人的行动",
        description="描述",
        reason="原因",
        cta_label="去打卡",
        cta_path="/mental",
        can_complete=True,
    )
    db.add(action)
    db.flush()

    with pytest.raises(DailyActionNotFoundError):
        complete_daily_action(db, test_user.id, action.id)


def test_unique_conflict_returns_existing_row(db, test_user, monkeypatch):
    existing = models.DailyAction(
        id=987,
        user_id=test_user.id,
        action_date=DAY,
        action_key="checkin",
        kind="action",
        title="已存在的行动",
        description="描述",
        reason="原因",
        cta_label="去打卡",
        cta_path="/mental",
        can_complete=True,
    )
    calls = {"count": 0}

    def flaky_find(session, user_id, day):
        calls["count"] += 1
        if calls["count"] == 1:
            return None
        return existing

    def raise_conflict():
        raise IntegrityError(
            "INSERT INTO daily_actions", {}, Exception("UNIQUE constraint failed")
        )

    db.autoflush = False
    monkeypatch.setattr(daily_action_service, "_find_for_date", flaky_find)
    monkeypatch.setattr(db, "commit", raise_conflict)
    monkeypatch.setattr(db, "rollback", lambda: None)

    data = generate_daily_action(db, test_user.id, today=DAY)

    assert data["id"] == existing.id
    assert data["action_key"] == "checkin"
    assert calls["count"] == 2


# ---------- 路由 ----------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_today_endpoint_generates_and_is_idempotent(client, db, test_user):
    first = await client.get("/api/daily-action/today")
    assert first.status_code == 200
    body = first.json()
    assert body["action_key"] == "checkin"
    assert body["action_date"] == datetime.now().date().isoformat()

    second = await client.get("/api/daily-action/today")
    assert second.status_code == 200
    assert second.json()["id"] == body["id"]

    rows = db.query(models.DailyAction).filter_by(user_id=test_user.id).all()
    assert len(rows) == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_today_endpoint_requires_auth(anon_client):
    response = await anon_client.get("/api/daily-action/today")
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_endpoint_marks_completed(client, db):
    today = await client.get("/api/daily-action/today")
    action_id = today.json()["id"]

    response = await client.post(f"/api/daily-action/{action_id}/complete")

    assert response.status_code == 200
    body = response.json()
    assert body["completed"] is True
    assert body["completed_at"] is not None
    assert body["week_completed"] == 1
    assert db.get(models.DailyAction, action_id).completed_at is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_safety_endpoint_returns_400(client, db, test_user):
    _crisis(db, test_user.id, _at(datetime.now().date(), datetime.now().hour))

    today = await client.get("/api/daily-action/today")
    body = today.json()
    assert body["kind"] == "safety"
    assert body["can_complete"] is False

    response = await client.post(f"/api/daily-action/{body['id']}/complete")

    assert response.status_code == 400
    assert response.json()["detail"] == "该行动不需要打卡"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_missing_action_returns_404(client):
    response = await client.post("/api/daily-action/999999/complete")

    assert response.status_code == 404
    assert response.json()["detail"] == "行动不存在"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_other_users_action_returns_404(client, db):
    other = models.User(name="otheruser", password_hash="x", invite_code="health2026")
    db.add(other)
    db.flush()
    action = models.DailyAction(
        user_id=other.id,
        action_date=DAY,
        action_key="checkin",
        kind="action",
        title="别人的行动",
        description="描述",
        reason="原因",
        cta_label="去打卡",
        cta_path="/mental",
        can_complete=True,
    )
    db.add(action)
    db.flush()

    response = await client.post(f"/api/daily-action/{action.id}/complete")

    assert response.status_code == 404
    assert response.json()["detail"] == "行动不存在"
