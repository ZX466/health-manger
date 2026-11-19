"""心理维度业务服务：每日打卡、睡眠统计、量表落库、汇总与严肃模式判定。

口径见 `.orca/talking.txt` 关键决策与 `.orca/contracts/api-v2.md`：
- 打卡每人每天一条，同日重复提交 = 更新；
- 睡眠债 = 近 7 个有睡眠记录日 Σ max(0, 8 - hours)，有记录日 < 4 天返回 None；
- 量表分数/风险/危机标记在落库前由 `scale_scoring.score` 计算并持久化；
- 严肃模式：近 30 天内最新量表出现危机标记或中重度以上风险。
"""

import json
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
from services.scale_scoring import SCALES, ScoreResult, risk_label, score

SLEEP_TARGET_HOURS = 8.0
SLEEP_WINDOW_RECORDS = 7
SLEEP_MIN_DAYS = 4
# 睡眠统计只看近 14 天内的记录，避免几个月前的旧数据被当成“近期”
SLEEP_LOOKBACK_DAYS = 14
# 量表/健康评级只在 30 天内影响严肃模式，过期后由新的测评或自然衰减解除
SERIOUS_LOOKBACK_DAYS = 30
SERIOUS_RISK_LEVELS = frozenset({"moderately_severe", "severe"})
# 与 safety_service.assess_user_risk 的 high 口径对齐：健康评级“危险”
HEALTH_DANGER_RATING = "危险"

MOOD_LABELS = {1: "很糟", 2: "低落", 3: "一般", 4: "不错", 5: "很棒"}


def _today() -> date:
    # 项目统一本地 naive 时间（见 pyproject DTZ005 说明），打卡日期取本地日历日
    return datetime.now().date()


def _dump_tags(tags: list[str] | None) -> str:
    return json.dumps(list(tags or []), ensure_ascii=False)


def _load_answers(raw: str | None) -> list[int]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except ValueError:
        return []
    return parsed if isinstance(parsed, list) else []


def upsert_mood(
    db: Session,
    user_id: int,
    *,
    mood_score: int,
    stress_tags: list[str] | None = None,
    sleep_hours: float | None = None,
    note: str | None = None,
    today: date | None = None,
) -> models.MentalRecord:
    """写入当天心理打卡；同一天重复提交整体覆盖，不新增行。"""
    record_date = today or _today()
    values = {
        "mood_score": mood_score,
        "mood_label": MOOD_LABELS.get(mood_score),
        "stress_tags": _dump_tags(stress_tags),
        "sleep_hours": sleep_hours,
        "note": note,
    }

    def _find() -> models.MentalRecord | None:
        return db.execute(
            select(models.MentalRecord).where(
                models.MentalRecord.user_id == user_id,
                models.MentalRecord.record_date == record_date,
            )
        ).scalar_one_or_none()

    record = _find()
    if record is None:
        record = models.MentalRecord(user_id=user_id, record_date=record_date, **values)
        db.add(record)
        try:
            db.commit()
        except IntegrityError:
            # 并发下另一请求先插入了同日记录：回滚后改走更新分支
            db.rollback()
            record = _find()
            if record is None:
                raise
            for key, value in values.items():
                setattr(record, key, value)
            db.commit()
    else:
        for key, value in values.items():
            setattr(record, key, value)
        db.commit()

    db.refresh(record)
    return record


def list_moods(
    db: Session, user_id: int, days: int = 30, *, today: date | None = None
) -> list[models.MentalRecord]:
    """近 days 天（含今天）的打卡，按日期倒序。"""
    since = (today or _today()) - timedelta(days=days - 1)
    return list(
        db.execute(
            select(models.MentalRecord)
            .where(
                models.MentalRecord.user_id == user_id,
                models.MentalRecord.record_date >= since,
            )
            .order_by(models.MentalRecord.record_date.desc())
        )
        .scalars()
        .all()
    )


def trend(db: Session, user_id: int, days: int = 30, *, today: date | None = None) -> dict:
    """连续日期序列的情绪/睡眠趋势，缺失日用 None 占位，三个数组等长。"""
    end = today or _today()
    records = {r.record_date: r for r in list_moods(db, user_id, days, today=end)}
    dates: list[str] = []
    moods: list[int | None] = []
    sleeps: list[float | None] = []
    for offset in range(days - 1, -1, -1):
        day = end - timedelta(days=offset)
        record = records.get(day)
        dates.append(day.isoformat())
        moods.append(record.mood_score if record else None)
        sleeps.append(record.sleep_hours if record else None)
    return {"dates": dates, "mood_score": moods, "sleep_hours": sleeps}


def sleep_stats(
    db: Session, user_id: int, *, today: date | None = None
) -> tuple[float | None, float | None, int]:
    """返回 (7 日均睡眠, 7 日睡眠债, 有记录天数)；有记录日不足 4 天时前两项为 None。"""
    since = (today or _today()) - timedelta(days=SLEEP_LOOKBACK_DAYS - 1)
    rows = db.execute(
        select(models.MentalRecord.sleep_hours)
        .where(
            models.MentalRecord.user_id == user_id,
            models.MentalRecord.record_date >= since,
            models.MentalRecord.sleep_hours.is_not(None),
        )
        .order_by(models.MentalRecord.record_date.desc())
        .limit(SLEEP_WINDOW_RECORDS)
    ).all()
    hours = [row[0] for row in rows]
    if len(hours) < SLEEP_MIN_DAYS:
        return None, None, len(hours)
    average = round(sum(hours) / len(hours), 1)
    debt = round(sum(max(0.0, SLEEP_TARGET_HOURS - h) for h in hours), 1)
    return average, debt, len(hours)


def save_assessment(
    db: Session, user_id: int, scale_type: str, answers: list[int]
) -> tuple[models.ScaleAssessment, ScoreResult]:
    """评分并落库；非法量表或作答抛 ValueError（由路由转 400）。"""
    result = score(scale_type, answers)
    assessment = models.ScaleAssessment(
        user_id=user_id,
        scale_type=scale_type,
        answers=json.dumps(list(answers)),
        score=result.score,
        risk_level=result.risk_level,
        crisis_flag=result.crisis_flag,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment, result


def _assessment_to_dict(row: models.ScaleAssessment, *, include_answers: bool) -> dict:
    scale_def = SCALES.get(row.scale_type)
    data = {
        "id": row.id,
        "scale_type": row.scale_type,
        "score": row.score or 0,
        "max_score": scale_def.max_score if scale_def else 0,
        "risk_level": row.risk_level or "minimal",
        "label": risk_label(row.risk_level or "minimal"),
        "crisis_flag": bool(row.crisis_flag),
        "created_at": row.created_at,
    }
    if include_answers:
        data["user_id"] = row.user_id
        data["answers"] = _load_answers(row.answers)
    return data


def assessment_history(
    db: Session, user_id: int, scale_type: str | None = None, *, limit: int = 20
) -> list[dict]:
    """测评历史，按创建时间倒序；ScaleAssessmentResponse 需要 max_score/label，故返回字典。"""
    stmt = select(models.ScaleAssessment).where(models.ScaleAssessment.user_id == user_id)
    if scale_type is not None:
        stmt = stmt.where(models.ScaleAssessment.scale_type == scale_type)
    stmt = stmt.order_by(
        models.ScaleAssessment.created_at.desc(), models.ScaleAssessment.id.desc()
    ).limit(limit)
    return [_assessment_to_dict(row, include_answers=True) for row in db.execute(stmt).scalars()]


def latest_assessment(db: Session, user_id: int, scale_type: str) -> models.ScaleAssessment | None:
    return (
        db.execute(
            select(models.ScaleAssessment)
            .where(
                models.ScaleAssessment.user_id == user_id,
                models.ScaleAssessment.scale_type == scale_type,
            )
            .order_by(models.ScaleAssessment.created_at.desc(), models.ScaleAssessment.id.desc())
        )
        .scalars()
        .first()
    )


def _is_recent(row: models.ScaleAssessment | None, today: date) -> bool:
    if row is None or row.created_at is None:
        return False
    return row.created_at.date() >= today - timedelta(days=SERIOUS_LOOKBACK_DAYS)


def _is_serious(row: models.ScaleAssessment | None, today: date) -> bool:
    return (
        _is_recent(row, today)
        and row is not None
        and (bool(row.crisis_flag) or row.risk_level in SERIOUS_RISK_LEVELS)
    )


def _health_rating_danger(db: Session, user_id: int, today: date) -> bool:
    """最新健康评级为“危险”且在 30 天内，与 safety 的 high 口径对齐。"""
    row = (
        db.execute(
            select(models.HealthAnalysis)
            .where(models.HealthAnalysis.user_id == user_id)
            .order_by(models.HealthAnalysis.analysis_date.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    if row is None or row.analysis_date is None:
        return False
    return (
        row.analysis_date.date() >= today - timedelta(days=SERIOUS_LOOKBACK_DAYS)
        and row.health_rating == HEALTH_DANGER_RATING
    )


def serious_sources(db: Session, user_id: int, *, today: date | None = None) -> set[str]:
    """返回触发严肃模式的来源集合：health_rating / scale。

    预警文案需要区分生理评级与心理量表，不能把“健康评级危险”写成
    “心理量表结果”。保留独立来源便于调用方选择合适措辞。
    """
    now = today or _today()
    sources: set[str] = set()
    if _health_rating_danger(db, user_id, now):
        sources.add("health_rating")
    if any(
        _is_serious(latest_assessment(db, user_id, scale_type), now) for scale_type in SCALES
    ):
        sources.add("scale")
    return sources


def is_serious_mode(db: Session, user_id: int, *, today: date | None = None) -> bool:
    """是否需要后端强制严肃关怀 Prompt、前端隐藏玩梗文案（决策 6）。

    与 safety_service 的 high 来源对齐：量表危机/中重度以上、健康评级“危险”；
    保留 PHQ-9 15–19 的保守展示策略。
    """
    return bool(serious_sources(db, user_id, today=today))


def summary(db: Session, user_id: int, *, today: date | None = None) -> dict:
    """首页/预警汇总（GET /api/mental/summary）。"""
    now = today or _today()
    latest_mood = (
        db.execute(
            select(models.MentalRecord)
            .where(models.MentalRecord.user_id == user_id)
            .order_by(models.MentalRecord.record_date.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    average, debt, _ = sleep_stats(db, user_id, today=now)
    phq9 = latest_assessment(db, user_id, "phq9")
    gad7 = latest_assessment(db, user_id, "gad7")
    return {
        "latest_mood": latest_mood,
        "sleep_avg_7d": average,
        "sleep_debt_7d": debt,
        "latest_phq9": _assessment_to_dict(phq9, include_answers=False) if phq9 else None,
        "latest_gad7": _assessment_to_dict(gad7, include_answers=False) if gad7 else None,
        "serious_mode": is_serious_mode(db, user_id, today=now),
    }
