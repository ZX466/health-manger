"""Tests for food/sport record deletion.

F4 回归：删除记录必须走 /food|sport/records/{id}（按用户归属校验），
不得误删食物/运动库条目（原前端错误调用 deleteFood/deleteSport）。
"""

import pytest
from fastapi import HTTPException

import models
import schemas
from services.food_service import create_food, create_food_record, delete_food_record
from services.sport_service import (
    create_sport,
    create_sport_record,
    delete_sport_record,
)


@pytest.fixture()
def food(db):
    return create_food(schemas.FoodCreate(name="米饭", calories_per_100g=116), db)


@pytest.fixture()
def sport(db):
    return create_sport(schemas.SportCreate(name="跑步", calories_per_hour=500), db)


def _create_food_record(db, food, user_id=1):
    rec = create_food_record(
        schemas.UserFoodRecordCreate(food_id=food.id, quantity_grams=200, meal_type="lunch"),
        user_id,
        db,
    )
    return rec["id"]


def _create_sport_record(db, sport, user_id=1):
    rec = create_sport_record(
        schemas.UserSportRecordCreate(sport_id=sport.id, duration_minutes=30),
        user_id,
        db,
    )
    return rec["id"]


def test_delete_own_food_record_succeeds(db, food):
    record_id = _create_food_record(db, food)
    result = delete_food_record(record_id, user_id=1, db=db)
    assert result["message"] == "删除成功"
    assert db.get(models.UserFoodRecord, record_id) is None


def test_delete_others_food_record_404(db, food):
    record_id = _create_food_record(db, food, user_id=1)
    with pytest.raises(HTTPException) as exc:
        delete_food_record(record_id, user_id=2, db=db)
    assert exc.value.status_code == 404


def test_delete_missing_food_record_404(db):
    with pytest.raises(HTTPException) as exc:
        delete_food_record(9999, user_id=1, db=db)
    assert exc.value.status_code == 404


def test_delete_own_sport_record_succeeds(db, sport):
    record_id = _create_sport_record(db, sport)
    result = delete_sport_record(record_id, user_id=1, db=db)
    assert result["message"] == "删除成功"
    assert db.get(models.UserSportRecord, record_id) is None


def test_delete_others_sport_record_404(db, sport):
    record_id = _create_sport_record(db, sport, user_id=1)
    with pytest.raises(HTTPException) as exc:
        delete_sport_record(record_id, user_id=2, db=db)
    assert exc.value.status_code == 404
