"""今日一件小事：规则生成、持久化与打卡。

规则优先级见 docs/plans/daily-action.md：
安全 > 没有记录 > 睡眠 < 7h > 运动 < 150min > 饮食 < 4 天 > 心情 < 3 > 休息。
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models

ACTION_RULES: dict[str, dict] = {
    "care": {
        "kind": "safety",
        "title": "先联系学校心理咨询中心",
        "description": "这一周先把自己照顾好。需要时联系学校心理咨询中心；如有危机想法，请拨打 120 或 12356。",
        "reason": "本周出现过危机标记，优先照顾自己",
        "cta_label": "查看心理支持",
        "cta_path": "/mental",
        "can_complete": False,
    },
    "checkin": {
        "kind": "action",
        "title": "花 1 分钟，给今天的状态打个分",
        "description": "不用写很多，一个心情分或一次睡眠记录就够。",
        "reason": "今天还没有健康或心情记录",
        "cta_label": "去打卡",
        "cta_path": "/mental",
        "can_complete": True,
    },
    "sleep": {
        "kind": "action",
        "title": "今晚 23:30 前放下手机",
        "description": "不用一次改很多，今晚比昨晚早 30 分钟就够。",
        "reason": "",
        "cta_label": "去记睡眠",
        "cta_path": "/health-record",
        "can_complete": True,
    },
    "move": {
        "kind": "action",
        "title": "课间快走 20 分钟",
        "description": "不用换衣服去健身房，绕教学楼快走一圈也算。",
        "reason": "",
        "cta_label": "去记运动",
        "cta_path": "/sport-management",
        "can_complete": True,
    },
    "meal": {
        "kind": "action",
        "title": "拍一餐，记录今天的饮食",
        "description": "只拍一餐也行，先让饮食有迹可循。",
        "reason": "",
        "cta_label": "去记饮食",
        "cta_path": "/diet-management",
        "can_complete": True,
    },
    "breathe": {
        "kind": "action",
        "title": "做一轮 1 分钟呼吸",
        "description": "先停 60 秒，把注意力放回呼吸上。",
        "reason": "",
        "cta_label": "去放松",
        "cta_path": "/mental",
        "can_complete": True,
    },
    "rest": {
        "kind": "rest",
        "title": "给自己留 10 分钟不赶任务的空白",
        "description": "这周记录得不错，恢复也是健康的一部分。",
        "reason": "今天的基础健康数据已经不错，做点轻松的小事",
        "cta_label": "看本周周报",
        "cta_path": "/weekly-report",
        "can_complete": True,
    },
}

NOT_COMPLETABLE_DETAIL = "该行动不需要打卡"
SLEEP_TARGET_HOURS = 7.0
SPORT_TARGET_MINUTES = 150
FOOD_TARGET_DAYS = 4
MOOD_TARGET_SCORE = 3.0


class DailyActionNotFoundError(Exception):
    """行动不存在或不属于当前用户。"""


class DailyActionNotCompletableError(Exception):
    """安全类行动不允许打卡。"""


def _today() -> date:
    """本地自然日，与周报的切日方式保持一致。"""
    return datetime.now().date()


def _window(day: date) -> tuple[date, date]:
    start = day - timedelta(days=6)
    return start, day


def _local_tz():
    """服务器本地时区；模型里的 record_date/created_at 按 UTC naive 存储。"""
    return datetime.now().astimezone().tzinfo or UTC


def _utc_bound(day: date, *, end: bool = False) -> datetime:
    """把本地自然日边界转成 UTC naive，供 SQLite DateTime 比较。"""
    local = datetime.combine(day, time.max if end else time.min, tzinfo=_local_tz())
    return local.astimezone(UTC).replace(tzinfo=None)


def _to_local_date(value):
    """把 UTC naive datetime 还原成本地日期；date 原样返回。"""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(_local_tz()).date()
    return value


def _find_for_date(db: Session, user_id: int, day: date) -> models.DailyAction | None:
    stmt = select(models.DailyAction).where(
        models.DailyAction.user_id == user_id,
        models.DailyAction.action_date == day,
    )
    return db.scalars(stmt).first()


def _has_recent_crisis(db: Session, user_id: int, day: date) -> bool:
    start, end = _window(day)
    stmt = (
        select(models.ScaleAssessment.id)
        .where(
            models.ScaleAssessment.user_id == user_id,
            models.ScaleAssessment.created_at >= _utc_bound(start),
            models.ScaleAssessment.created_at <= _utc_bound(end, end=True),
            models.ScaleAssessment.crisis_flag.is_(True),
        )
        .limit(1)
    )
    return db.scalar(stmt) is not None


def _has_today_record(db: Session, user_id: int, day: date) -> bool:
    health = db.scalar(
        select(models.HealthRecord.id)
        .where(
            models.HealthRecord.user_id == user_id,
            models.HealthRecord.record_date >= _utc_bound(day),
            models.HealthRecord.record_date <= _utc_bound(day, end=True),
        )
        .limit(1)
    )
    if health is not None:
        return True
    mental = db.scalar(
        select(models.MentalRecord.id)
        .where(
            models.MentalRecord.user_id == user_id,
            models.MentalRecord.record_date == day,
        )
        .limit(1)
    )
    return mental is not None


def _record_day(record) -> date:
    return _to_local_date(record.record_date)


def _latest_sleep_hours(db: Session, user_id: int, day: date) -> float | None:
    """最近 2 天最新睡眠；缺少时用心理打卡，同一天优先体检。"""
    start = day - timedelta(days=1)
    health = db.scalars(
        select(models.HealthRecord)
        .where(
            models.HealthRecord.user_id == user_id,
            models.HealthRecord.record_date >= _utc_bound(start),
            models.HealthRecord.record_date <= _utc_bound(day, end=True),
            models.HealthRecord.sleep_hours.is_not(None),
        )
        .order_by(models.HealthRecord.record_date.desc())
        .limit(1)
    ).first()
    mental = db.scalars(
        select(models.MentalRecord)
        .where(
            models.MentalRecord.user_id == user_id,
            models.MentalRecord.record_date >= start,
            models.MentalRecord.record_date <= day,
            models.MentalRecord.sleep_hours.is_not(None),
        )
        .order_by(models.MentalRecord.record_date.desc())
        .limit(1)
    ).first()

    if health is None and mental is None:
        return None
    if health is None:
        return float(mental.sleep_hours)
    if mental is None:
        return float(health.sleep_hours)
    if _record_day(health) >= _record_day(mental):
        return float(health.sleep_hours)
    return float(mental.sleep_hours)


def _recent_sport_minutes(db: Session, user_id: int, day: date) -> int:
    start, end = _window(day)
    stmt = select(func.coalesce(func.sum(models.UserSportRecord.duration_minutes), 0)).where(
        models.UserSportRecord.user_id == user_id,
        models.UserSportRecord.record_date >= _utc_bound(start),
        models.UserSportRecord.record_date <= _utc_bound(end, end=True),
    )
    return int(db.scalar(stmt) or 0)


def _recorded_food_days(db: Session, user_id: int, day: date) -> int:
    start, end = _window(day)
    stmt = select(models.UserFoodRecord.record_date).where(
        models.UserFoodRecord.user_id == user_id,
        models.UserFoodRecord.record_date >= _utc_bound(start),
        models.UserFoodRecord.record_date <= _utc_bound(end, end=True),
    )
    days = {_to_local_date(value) for value in db.scalars(stmt) if value is not None}
    return len(days)


def _recent_mood_avg(db: Session, user_id: int, day: date) -> float | None:
    start, end = _window(day)
    stmt = select(func.avg(models.MentalRecord.mood_score)).where(
        models.MentalRecord.user_id == user_id,
        models.MentalRecord.record_date >= start,
        models.MentalRecord.record_date <= end,
        models.MentalRecord.mood_score.is_not(None),
    )
    value = db.scalar(stmt)
    return float(value) if value is not None else None


def _pick_action(db: Session, user_id: int, day: date) -> str:
    """按规则优先级返回 action_key；条件收集失败时自然落到下一档。"""
    if _has_recent_crisis(db, user_id, day):
        return "care"
    if not _has_today_record(db, user_id, day):
        return "checkin"
    sleep_hours = _latest_sleep_hours(db, user_id, day)
    if sleep_hours is not None and sleep_hours < SLEEP_TARGET_HOURS:
        return "sleep"
    if _recent_sport_minutes(db, user_id, day) < SPORT_TARGET_MINUTES:
        return "move"
    if _recorded_food_days(db, user_id, day) < FOOD_TARGET_DAYS:
        return "meal"
    mood_avg = _recent_mood_avg(db, user_id, day)
    if mood_avg is not None and mood_avg < MOOD_TARGET_SCORE:
        return "breathe"
    return "rest"


def _reason_for(db: Session, user_id: int, day: date, action_key: str) -> str:
    if action_key == "sleep":
        sleep_hours = _latest_sleep_hours(db, user_id, day)
        if sleep_hours is not None:
            return f"最近一次睡眠 {sleep_hours:.1f}h，离 7h 还差一点"
    elif action_key == "move":
        minutes = _recent_sport_minutes(db, user_id, day)
        return f"近 7 天累计运动 {minutes} 分钟，还没到 150 分钟"
    elif action_key == "meal":
        days = _recorded_food_days(db, user_id, day)
        return f"最近 7 天有 {days} 天记录了饮食，还没到 4 天"
    elif action_key == "breathe":
        mood_avg = _recent_mood_avg(db, user_id, day)
        if mood_avg is not None:
            return f"最近 7 天心情均值 {mood_avg:.1f}，先给自己一分钟呼吸"
    return ACTION_RULES[action_key]["reason"]


def _week_completed(db: Session, user_id: int, day: date) -> int:
    """近 7 天 completed_at 非空的 action_date 去重计数。"""
    start, end = _window(day)
    stmt = select(func.count(func.distinct(models.DailyAction.action_date))).where(
        models.DailyAction.user_id == user_id,
        models.DailyAction.action_date >= start,
        models.DailyAction.action_date <= end,
        models.DailyAction.completed_at.is_not(None),
    )
    return int(db.scalar(stmt) or 0)


def _serialize(record: models.DailyAction, week_completed: int) -> dict:
    return {
        "id": record.id,
        "action_date": record.action_date,
        "action_key": record.action_key,
        "kind": record.kind or "action",
        "title": record.title,
        "description": record.description,
        "reason": record.reason,
        "cta_label": record.cta_label,
        "cta_path": record.cta_path,
        "can_complete": bool(record.can_complete),
        "completed": record.completed_at is not None,
        "completed_at": record.completed_at,
        "week_completed": week_completed,
    }


def generate_daily_action(db: Session, user_id: int, *, today: date | None = None) -> dict:
    """返回当天的小事；不存在时按规则生成并持久化，同日重复调用返回同一条。"""
    day = today or _today()
    record = _find_for_date(db, user_id, day)
    if record is None:
        action_key = _pick_action(db, user_id, day)
        rule = ACTION_RULES[action_key]
        record = models.DailyAction(
            user_id=user_id,
            action_date=day,
            action_key=action_key,
            kind=rule["kind"],
            title=rule["title"],
            description=rule["description"],
            reason=_reason_for(db, user_id, day, action_key),
            cta_label=rule["cta_label"],
            cta_path=rule["cta_path"],
            can_complete=rule["can_complete"],
        )
        db.add(record)
        try:
            db.commit()
        except IntegrityError:
            # 并发请求抢先插入：放弃本次记录，重查并返回已存在的那条。
            db.rollback()
            record = _find_for_date(db, user_id, day)
            if record is None:
                raise
    return _serialize(record, _week_completed(db, user_id, day))


def complete_daily_action(db: Session, user_id: int, action_id: int) -> dict:
    """完成行动；重复完成幂等，安全类行动拒绝打卡。"""
    record = db.get(models.DailyAction, action_id)
    if record is None or record.user_id != user_id:
        raise DailyActionNotFoundError
    if record.kind == "safety" or not record.can_complete:
        raise DailyActionNotCompletableError
    if record.completed_at is None:
        # 原子抢占首次完成：两个并发 POST 只有一个写入 completed_at，
        # 后到的请求刷新后拿到同一个时间戳，而不是互相覆盖。
        db.execute(
            update(models.DailyAction)
            .where(
                models.DailyAction.id == record.id,
                models.DailyAction.user_id == user_id,
                models.DailyAction.completed_at.is_(None),
            )
            .values(completed_at=models._utcnow())
        )
        db.commit()
        db.refresh(record)
    return _serialize(record, _week_completed(db, user_id, record.action_date))
