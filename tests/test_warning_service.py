"""Regression tests for warning generation ordering + schema type.

Bug A: warning_service checked hypotension AFTER high/normal-high, so a mixed
reading with a low diastolic (130/55) was labeled "血压偏高" instead of "低血压".
Bug B: HealthWarningResponse.warning_type was a Literal of English keys while
the service stores Chinese labels -> /api/warning/list response validation 500.
"""

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base
import models  # noqa: F401
from services.warning_service import check_health_warnings
from schemas import HealthWarningResponse


def _make_engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _seed_record(db, **kwargs):
    rec = models.HealthRecord(user_id=1, **kwargs)
    db.add(rec)
    db.commit()
    return rec


def _run_warnings(**record_kwargs):
    eng = _make_engine()
    Base.metadata.create_all(bind=eng)
    db = Session(eng)
    _seed_record(db, **record_kwargs)
    return check_health_warnings(1, db)


def test_low_pressure_generates_low_pressure_warning():
    warnings = _run_warnings(blood_pressure_systolic=110, blood_pressure_diastolic=55)
    types = [w["type"] for w in warnings]
    assert "低血压" in types, f"110/55 应生成低血压预警，实际 {types}"


def test_mixed_high_systolic_low_diastolic_generates_low_pressure_warning():
    warnings = _run_warnings(blood_pressure_systolic=130, blood_pressure_diastolic=55)
    types = [w["type"] for w in warnings]
    assert "低血压" in types, f"130/55 应生成低血压预警，实际 {types}"
    assert "血压偏高" not in types, f"130/55 不应判为血压偏高，实际 {types}"


def test_health_warning_response_accepts_chinese_type():
    m = HealthWarningResponse(
        id=1,
        user_id=1,
        warning_type="低血压",
        warning_level="warning",
        warning_content="x",
        is_read=False,
        created_at=datetime.now(timezone.utc),
        resolved_at=None,
    )
    assert m.warning_type == "低血压"
