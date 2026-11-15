"""M-LOGIC1：心理服务 + 身心交叉预警。"""

import sys
import types
from datetime import date, datetime, timedelta

import pytest

import models
from services import mental_service, warning_service
from services.warning_service import check_health_warnings

TODAY = date(2026, 11, 15)


def _mood(db, user_id, day_offset, mood=3, sleep=None):
    return mental_service.upsert_mood(
        db,
        user_id,
        mood_score=mood,
        sleep_hours=sleep,
        stress_tags=["工作"],
        today=TODAY - timedelta(days=day_offset),
    )


def _assessment(db, user_id, scale_type, risk, crisis=False, days_ago=0, score=10):
    row = models.ScaleAssessment(
        user_id=user_id,
        scale_type=scale_type,
        answers="[]",
        score=score,
        risk_level=risk,
        crisis_flag=crisis,
        created_at=datetime.fromisoformat("2026-11-15T12:00:00") - timedelta(days=days_ago),
    )
    db.add(row)
    db.flush()
    return row


def _health_analysis(db, user_id, rating, days_ago=0):
    db.add(
        models.HealthAnalysis(
            user_id=user_id,
            health_rating=rating,
            analysis_date=datetime.fromisoformat("2026-11-15T12:00:00") - timedelta(days=days_ago),
        )
    )
    db.flush()


def test_upsert_mood_same_day_updates_not_inserts(db, test_user):
    first = _mood(db, test_user.id, 0, mood=2)
    second = _mood(db, test_user.id, 0, mood=5, sleep=7.5)
    assert first.id == second.id
    assert second.mood_score == 5
    assert second.mood_label == "很棒"
    assert second.sleep_hours == 7.5
    assert len(mental_service.list_moods(db, test_user.id, 30, today=TODAY)) == 1


def test_trend_is_continuous_with_null_gaps(db, test_user):
    _mood(db, test_user.id, 2, mood=4, sleep=7.0)
    _mood(db, test_user.id, 0, mood=3, sleep=6.5)
    data = mental_service.trend(db, test_user.id, 3, today=TODAY)
    assert data["dates"] == ["2026-11-13", "2026-11-14", "2026-11-15"]
    assert data["mood_score"] == [4, None, 3]
    assert data["sleep_hours"] == [7.0, None, 6.5]


def test_sleep_stats_insufficient_days_returns_none(db, test_user):
    for i in range(3):
        _mood(db, test_user.id, i, sleep=5.0)
    avg, debt, days = mental_service.sleep_stats(db, test_user.id, today=TODAY)
    assert (avg, debt, days) == (None, None, 3)


def test_sleep_debt_uses_recorded_days_and_ignores_surplus(db, test_user):
    # 5 + 6 + 9 + 7 = 27h 共 4 天；债 = 3 + 2 + 0 + 1 = 6
    for offset, hours in enumerate([5.0, 6.0, 9.0, 7.0]):
        _mood(db, test_user.id, offset, sleep=hours)
    avg, debt, days = mental_service.sleep_stats(db, test_user.id, today=TODAY)
    assert days == 4
    assert debt == 6.0
    assert avg == 6.8  # 27 / 4 = 6.75 -> round 6.8


def test_sleep_stats_ignores_stale_records(db, test_user):
    for offset in (30, 31, 32, 33):
        _mood(db, test_user.id, offset, sleep=4.0)
    assert mental_service.sleep_stats(db, test_user.id, today=TODAY) == (None, None, 0)


def test_save_assessment_persists_score_and_crisis(db, test_user):
    answers = [0] * 8 + [1]  # 第 9 题非零 -> 危机
    row, result = mental_service.save_assessment(db, test_user.id, "phq9", answers)
    assert row.score == 1
    assert row.risk_level == "minimal"
    assert row.crisis_flag is True
    assert result.crisis_flag is True


def test_save_assessment_rejects_bad_input(db, test_user):
    with pytest.raises(ValueError):
        mental_service.save_assessment(db, test_user.id, "phq9", [1, 2])
    with pytest.raises(ValueError):
        mental_service.save_assessment(db, test_user.id, "unknown", [0])


def test_assessment_history_filters_and_orders(db, test_user):
    _assessment(db, test_user.id, "phq9", "mild", days_ago=3)
    _assessment(db, test_user.id, "gad7", "mild", days_ago=2)
    _assessment(db, test_user.id, "phq9", "moderate", days_ago=1)
    rows = mental_service.assessment_history(db, test_user.id, "phq9", limit=10)
    assert [r["risk_level"] for r in rows] == ["moderate", "mild"]
    assert rows[0]["max_score"] == 27
    assert rows[0]["label"]
    assert len(mental_service.assessment_history(db, test_user.id, limit=10)) == 3


def test_serious_mode_on_crisis_or_severe_within_30_days(db, test_user):
    assert mental_service.is_serious_mode(db, test_user.id, today=TODAY) is False
    _assessment(db, test_user.id, "gad7", "severe", crisis=True)
    assert mental_service.is_serious_mode(db, test_user.id, today=TODAY) is True


def test_serious_mode_expires_after_30_days(db, test_user):
    _assessment(db, test_user.id, "phq9", "severe", crisis=True, days_ago=45)
    assert mental_service.is_serious_mode(db, test_user.id, today=TODAY) is False


def test_serious_mode_follows_latest_assessment_per_scale(db, test_user):
    _assessment(db, test_user.id, "phq9", "severe", crisis=True, days_ago=5)
    _assessment(db, test_user.id, "phq9", "mild", days_ago=1)
    assert mental_service.is_serious_mode(db, test_user.id, today=TODAY) is False


def test_moderate_alone_is_not_serious(db, test_user):
    _assessment(db, test_user.id, "phq9", "moderate")
    assert mental_service.is_serious_mode(db, test_user.id, today=TODAY) is False


def test_summary_shape(db, test_user):
    _mood(db, test_user.id, 0, mood=4, sleep=6.0)
    _assessment(db, test_user.id, "phq9", "moderately_severe", days_ago=0)
    data = mental_service.summary(db, test_user.id, today=TODAY)
    assert data["latest_mood"].mood_score == 4
    assert data["sleep_avg_7d"] is None and data["sleep_debt_7d"] is None
    assert data["latest_phq9"]["risk_level"] == "moderately_severe"
    assert data["latest_gad7"] is None
    assert data["serious_mode"] is True


# ── 交叉预警（warning_service 使用真实今天，故用相对今天的偏移） ──


def _real_mood(db, user_id, offset, mood=3, sleep=None):
    return mental_service.upsert_mood(
        db,
        user_id,
        mood_score=mood,
        sleep_hours=sleep,
        today=datetime.now().date() - timedelta(days=offset),
    )


def _health_record(db, user_id, **kwargs):
    db.add(models.HealthRecord(user_id=user_id, **kwargs))
    db.flush()


def test_cross_warning_sleep_debt_with_high_bp(db, test_user):
    for i in range(5):
        _real_mood(db, test_user.id, i, sleep=5.0)  # 债 15h
    _health_record(db, test_user.id, blood_pressure_systolic=150, blood_pressure_diastolic=95)
    types = [w["type"] for w in check_health_warnings(test_user.id, db)]
    assert "睡眠不足叠加指标偏高" in types


def test_no_cross_warning_when_sleep_debt_but_vitals_normal(db, test_user):
    for i in range(5):
        _real_mood(db, test_user.id, i, sleep=5.0)
    _health_record(db, test_user.id, blood_pressure_systolic=115, blood_pressure_diastolic=75)
    types = [w["type"] for w in check_health_warnings(test_user.id, db)]
    assert "睡眠不足叠加指标偏高" not in types


def test_cross_warning_for_serious_scale_without_health_record(db, test_user):
    _assessment(db, test_user.id, "phq9", "severe", crisis=True, score=22)
    warnings = check_health_warnings(test_user.id, db)
    assert [w["type"] for w in warnings] == ["心理状态需关注"]
    assert warnings[0]["level"] == "danger"


def test_cross_warning_persistent_low_mood(db, test_user):
    for i in range(3):
        _real_mood(db, test_user.id, i, mood=1)
    types = [w["type"] for w in check_health_warnings(test_user.id, db)]
    assert "情绪持续低落" in types


def test_cross_warning_is_deduplicated_when_unread(db, test_user):
    for i in range(3):
        _real_mood(db, test_user.id, i, mood=1)
    check_health_warnings(test_user.id, db)
    check_health_warnings(test_user.id, db)
    rows = (
        db.query(models.HealthWarning)
        .filter(models.HealthWarning.warning_type == "情绪持续低落")
        .all()
    )
    assert len(rows) == 1


def test_no_warnings_for_user_without_any_data(db, test_user):
    assert check_health_warnings(test_user.id, db) == []


# ── Codex 评审修订：安全资源对象化 + 健康评级“危险”对齐 ──


def test_serious_mode_on_danger_health_rating(db, test_user):
    _health_analysis(db, test_user.id, "危险")
    assert mental_service.is_serious_mode(db, test_user.id, today=TODAY) is True


def test_serious_mode_ignores_non_danger_and_stale_rating(db, test_user):
    _health_analysis(db, test_user.id, "较差")
    assert mental_service.is_serious_mode(db, test_user.id, today=TODAY) is False
    _health_analysis(db, test_user.id, "危险", days_ago=45)
    assert mental_service.is_serious_mode(db, test_user.id, today=TODAY) is False


def test_summary_serious_mode_includes_danger_health_rating(db, test_user):
    _health_analysis(db, test_user.id, "危险")
    assert mental_service.summary(db, test_user.id, today=TODAY)["serious_mode"] is True


def test_crisis_hint_formats_object_resources(monkeypatch):
    fake = types.ModuleType("services.safety_service")
    fake.crisis_resources = lambda: [
        {"name": "学校心理咨询中心", "phone": "123456", "description": "工作日 9-17 点"},
        {"name": "当地精神卫生中心"},
    ]
    monkeypatch.setitem(sys.modules, "services.safety_service", fake)
    hint = warning_service._crisis_hint()
    assert "学校心理咨询中心 123456 工作日 9-17 点" in hint
    assert "当地精神卫生中心" in hint


def test_crisis_hint_keeps_string_resources(monkeypatch):
    fake = types.ModuleType("services.safety_service")
    fake.crisis_resources = lambda: ["学校心理咨询中心"]
    monkeypatch.setitem(sys.modules, "services.safety_service", fake)
    assert warning_service._crisis_hint() == "可联系：学校心理咨询中心"


def test_crisis_hint_without_resources_has_no_fabricated_number(monkeypatch):
    fake = types.ModuleType("services.safety_service")
    fake.crisis_resources = list
    monkeypatch.setitem(sys.modules, "services.safety_service", fake)
    hint = warning_service._crisis_hint()
    assert "可联系" not in hint
    assert not any(ch.isdigit() for ch in hint)
