"""Business logic for food CRUD, consumption records, and statistics."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

import models
import schemas


def create_food(food: schemas.FoodCreate, db: Session) -> models.Food:
    db_food = models.Food(**food.model_dump())
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food


def get_foods(
    category: Optional[str], search: Optional[str], db: Session
) -> List[models.Food]:
    stmt = select(models.Food)
    if category:
        stmt = stmt.where(models.Food.category == category)
    if search:
        stmt = stmt.where(models.Food.name.contains(search))
    return db.execute(stmt.order_by(models.Food.name)).scalars().all()


def get_food(food_id: int, db: Session) -> models.Food:
    food = db.execute(select(models.Food).where(models.Food.id == food_id)).scalars().first()
    if not food:
        raise HTTPException(status_code=404, detail="食物不存在")
    return food


def update_food(
    food_id: int, food: schemas.FoodCreate, db: Session
) -> models.Food:
    db_food = db.execute(select(models.Food).where(models.Food.id == food_id)).scalars().first()
    if not db_food:
        raise HTTPException(status_code=404, detail="食物不存在")
    for key, value in food.model_dump().items():
        if value is not None:
            setattr(db_food, key, value)
    db.commit()
    db.refresh(db_food)
    return db_food


def delete_food(food_id: int, db: Session) -> dict:
    db_food = db.execute(select(models.Food).where(models.Food.id == food_id)).scalars().first()
    if not db_food:
        raise HTTPException(status_code=404, detail="食物不存在")
    db.delete(db_food)
    db.commit()
    return {"message": "删除成功"}


def create_food_record(
    record: schemas.UserFoodRecordCreate, user_id: int, db: Session
) -> models.UserFoodRecord:
    food = db.execute(select(models.Food).where(models.Food.id == record.food_id)).scalars().first()
    if not food:
        raise HTTPException(status_code=404, detail="食物不存在")

    calories = (food.calories_per_100g or 0) * (record.quantity_grams / 100)

    db_record = models.UserFoodRecord(
        user_id=user_id,
        food_id=record.food_id,
        quantity_grams=record.quantity_grams,
        calories=calories,
        meal_type=record.meal_type,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    return {"id": db_record.id, "user_id": db_record.user_id, "food_id": db_record.food_id, "quantity_grams": db_record.quantity_grams, "calories": db_record.calories, "record_date": db_record.record_date, "meal_type": db_record.meal_type, "food_name": food.name}


def get_food_records(
    user_id: int,
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list:
    query = (
        select(models.UserFoodRecord, models.Food.name)
        .join(models.Food, models.UserFoodRecord.food_id == models.Food.id)
        .where(models.UserFoodRecord.user_id == user_id)
    )

    if start_date:
        query = query.where(
            models.UserFoodRecord.record_date >= datetime.fromisoformat(start_date)
        )
    if end_date:
        query = query.where(
            models.UserFoodRecord.record_date <= datetime.fromisoformat(end_date)
        )

    records = db.execute(query.order_by(models.UserFoodRecord.record_date.desc())).all()

    return [
        {
            "id": record.id,
            "user_id": record.user_id,
            "food_id": record.food_id,
            "quantity_grams": record.quantity_grams,
            "calories": record.calories,
            "record_date": record.record_date,
            "meal_type": record.meal_type,
            "food_name": food_name,
        }
        for record, food_name in records
    ]


def delete_food_record(record_id: int, user_id: int, db: Session) -> dict:
    record = db.execute(
        select(models.UserFoodRecord).where(
            models.UserFoodRecord.id == record_id,
            models.UserFoodRecord.user_id == user_id,
        )
    ).scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="饮食记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "删除成功"}


def get_food_stats(
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
        select(models.UserFoodRecord).where(
            models.UserFoodRecord.user_id == user_id,
            models.UserFoodRecord.record_date >= start,
            models.UserFoodRecord.record_date <= end,
        )
    ).scalars().all()

    total_calories = sum(r.calories or 0 for r in records)
    total_records = len(records)

    meal_type_stats: dict[str, float] = {}
    for record in records:
        meal_type = record.meal_type or "未分类"
        meal_type_stats[meal_type] = meal_type_stats.get(meal_type, 0) + (record.calories or 0)

    return {
        "total_calories": round(total_calories, 2),
        "total_records": total_records,
        "meal_type_stats": meal_type_stats,
        "period": f"{start_date} 至 {end_date}",
    }
