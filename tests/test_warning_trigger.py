"""K-1：健康记录/量表写入后自动触发预警（含失败不阻断、未读去重）。"""

from unittest.mock import patch

import pytest
from sqlalchemy import func, select

import models
from services.warning_service import check_health_warnings


def _warning_types(db, user_id: int) -> list[str]:
    return list(
        db.execute(
            select(models.HealthWarning.warning_type).where(models.HealthWarning.user_id == user_id)
        ).scalars()
    )


def _warning_count(db, user_id: int, warning_type: str) -> int:
    return db.execute(
        select(func.count(models.HealthWarning.id)).where(
            models.HealthWarning.user_id == user_id,
            models.HealthWarning.warning_type == warning_type,
        )
    ).scalar_one()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_record_triggers_high_bp_warning(client, db, test_user):
    resp = await client.post(
        "/api/health/records",
        json={
            "height": 175.0,
            "weight": 70.0,
            "blood_pressure_systolic": 150,
            "blood_pressure_diastolic": 95,
        },
    )
    assert resp.status_code == 200
    assert "高血压" in _warning_types(db, test_user.id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_record_triggers_bmi_warning(client, db, test_user):
    # 165cm / 100kg -> BMI ≈ 36.7（肥胖）
    resp = await client.post("/api/health/records", json={"height": 165.0, "weight": 100.0})
    assert resp.status_code == 200
    assert "BMI 过高" in _warning_types(db, test_user.id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scale_crisis_triggers_psychological_warning_without_health_record(
    client, db, test_user
):
    resp = await client.post(
        "/api/mental/scales/phq9/submit",
        json={"answers": [0, 0, 0, 0, 0, 0, 0, 0, 2]},
    )
    assert resp.status_code == 200
    assert resp.json()["crisis_flag"] is True
    assert "心理状态需关注" in _warning_types(db, test_user.id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_repeated_scale_submission_does_not_duplicate_unread_warning(client, db, test_user):
    payload = {"answers": [0, 0, 0, 0, 0, 0, 0, 0, 1]}
    first = await client.post("/api/mental/scales/phq9/submit", json=payload)
    second = await client.post("/api/mental/scales/phq9/submit", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert _warning_count(db, test_user.id, "心理状态需关注") == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_repeated_health_record_does_not_duplicate_unread_warning(client, db, test_user):
    payload = {
        "height": 175.0,
        "weight": 70.0,
        "blood_pressure_systolic": 150,
        "blood_pressure_diastolic": 95,
    }
    assert (await client.post("/api/health/records", json=payload)).status_code == 200
    assert (await client.post("/api/health/records", json=payload)).status_code == 200
    assert _warning_count(db, test_user.id, "高血压") == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_warning_failure_does_not_block_or_rollback_record(client, db, test_user):
    with patch(
        "services.warning_service.check_health_warnings",
        side_effect=RuntimeError("warning engine down"),
    ):
        resp = await client.post(
            "/api/health/records",
            json={
                "height": 175.0,
                "weight": 70.0,
                "blood_pressure_systolic": 150,
                "blood_pressure_diastolic": 95,
            },
        )
    assert resp.status_code == 200
    assert resp.json()["bmi"] is not None

    db.expire_all()
    saved = (
        db.execute(select(models.HealthRecord).where(models.HealthRecord.user_id == test_user.id))
        .scalars()
        .all()
    )
    assert len(saved) == 1
    assert _warning_count(db, test_user.id, "高血压") == 0


def test_check_health_warnings_still_returns_physical_warnings(db, test_user):
    """回归：safe 包装不改变原有 check_health_warnings 结果。"""
    db.add(
        models.HealthRecord(
            user_id=test_user.id,
            bmi=36.7,
            blood_pressure_systolic=150,
            blood_pressure_diastolic=95,
        )
    )
    db.commit()
    types = [w["type"] for w in check_health_warnings(test_user.id, db)]
    assert "高血压" in types
    assert "BMI 过高" in types
