"""Business logic for sport CRUD, exercise records, and statistics."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

import models
import schemas


def create_sport(sport: schemas.SportCreate, db: Session) -> models.Sport:
    db_sport = models.Sport(**sport.model_dump())
    db.add(db_sport)
    db.commit()
    db.refresh(db_sport)
    return db_sport


def get_sports(
    category: Optional[str], search: Optional[str], db: Session
) -> List[models.Sport]:
    stmt = select(models.Sport)
    if category:
        stmt = stmt.where(models.Sport.category == category)
    if search:
        stmt = stmt.where(models.Sport.name.contains(search))
    return db.execute(stmt.order_by(models.Sport.name)).scalars().all()


def get_sport(sport_id: int, db: Session) -> models.Sport:
    sport = db.execute(select(models.Sport).where(models.Sport.id == sport_id)).scalars().first()
    if not sport:
        raise HTTPException(status_code=404, detail="运动项目不存在")
    return sport


def update_sport(
    sport_id: int, sport: schemas.SportCreate, db: Session
) -> models.Sport:
    db_sport = db.execute(select(models.Sport).where(models.Sport.id == sport_id)).scalars().first()
    if not db_sport:
        raise HTTPException(status_code=404, detail="运动项目不存在")
    for key, value in sport.model_dump().items():
        if value is not None:
            setattr(db_sport, key, value)
    db.commit()
    db.refresh(db_sport)
    return db_sport


def delete_sport(sport_id: int, db: Session) -> dict:
    db_sport = db.execute(select(models.Sport).where(models.Sport.id == sport_id)).scalars().first()
    if not db_sport:
        raise HTTPException(status_code=404, detail="运动项目不存在")
    db.delete(db_sport)
    db.commit()
    return {"message": "删除成功"}


def create_sport_record(
    record: schemas.UserSportRecordCreate, user_id: int, db: Session
) -> models.UserSportRecord:
    sport = db.execute(select(models.Sport).where(models.Sport.id == record.sport_id)).scalars().first()
    if not sport:
        raise HTTPException(status_code=404, detail="运动项目不存在")

    calories_burned = (sport.calories_per_hour or 0) * (record.duration_minutes / 60)

    db_record = models.UserSportRecord(
        user_id=user_id,
        sport_id=record.sport_id,
        duration_minutes=record.duration_minutes,
        calories_burned=calories_burned,
        notes=record.notes,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    return {"id": db_record.id, "user_id": db_record.user_id, "sport_id": db_record.sport_id, "duration_minutes": db_record.duration_minutes, "calories_burned": db_record.calories_burned, "record_date": db_record.record_date, "notes": db_record.notes, "sport_name": sport.name}


def get_sport_records(
    user_id: int,
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list:
    query = (
        select(models.UserSportRecord, models.Sport.name)
        .join(models.Sport, models.UserSportRecord.sport_id == models.Sport.id)
        .where(models.UserSportRecord.user_id == user_id)
    )

    if start_date:
        query = query.where(
            models.UserSportRecord.record_date >= datetime.fromisoformat(start_date)
        )
    if end_date:
        query = query.where(
            models.UserSportRecord.record_date <= datetime.fromisoformat(end_date)
        )

    records = db.execute(query.order_by(models.UserSportRecord.record_date.desc())).all()

    return [
        {
            "id": record.id,
            "user_id": record.user_id,
            "sport_id": record.sport_id,
            "duration_minutes": record.duration_minutes,
            "calories_burned": record.calories_burned,
            "record_date": record.record_date,
            "notes": record.notes,
            "sport_name": sport_name,
        }
        for record, sport_name in records
    ]


def delete_sport_record(record_id: int, user_id: int, db: Session) -> dict:
    record = db.execute(
        select(models.UserSportRecord).where(
            models.UserSportRecord.id == record_id,
            models.UserSportRecord.user_id == user_id,
        )
    ).scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="运动记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "删除成功"}


def get_sport_stats(
    user_id: int,
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    if not start_date:
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    if not end_date:
        end_date = datetime.now(timezone.utc).isoformat()

    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)

    records = db.execute(
        select(models.UserSportRecord).where(
            models.UserSportRecord.user_id == user_id,
            models.UserSportRecord.record_date >= start,
            models.UserSportRecord.record_date <= end,
        )
    ).scalars().all()

    total_calories = sum(r.calories_burned or 0 for r in records)
    total_duration = sum(r.duration_minutes or 0 for r in records)
    total_records = len(records)

    sport_ids = list({r.sport_id for r in records if r.sport_id})
    sports_map = {
        s.id: s.name
        for s in db.execute(select(models.Sport).where(models.Sport.id.in_(sport_ids))).scalars().all()
    } if sport_ids else {}

    sport_type_stats: dict[str, dict] = {}
    for record in records:
        sport_name = sports_map.get(record.sport_id, "未知")
        if sport_name not in sport_type_stats:
            sport_type_stats[sport_name] = {"calories": 0, "duration": 0, "count": 0}
        sport_type_stats[sport_name]["calories"] += record.calories_burned or 0
        sport_type_stats[sport_name]["duration"] += record.duration_minutes or 0
        sport_type_stats[sport_name]["count"] += 1

    return {
        "total_calories": round(total_calories, 2),
        "total_duration_minutes": total_duration,
        "total_records": total_records,
        "sport_type_stats": sport_type_stats,
        "period": f"{start_date} 至 {end_date}",
    }
